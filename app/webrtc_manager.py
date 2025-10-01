import asyncio
import json
import logging
from typing import Dict, Optional, Callable
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCDataChannel
from aiortc.contrib.media import MediaBlackhole
import httpx

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Gestisce le connessioni WebRTC peer-to-peer.
    Supporta sia Rendezvous Server che P2P signaling.
    """

    def __init__(self, node_id: str, rendezvous_url: str = None):
        self.node_id = node_id
        self.rendezvous_url = rendezvous_url
        self.use_p2p_signaling = (rendezvous_url is None)

        # Mappa peer_id -> RTCPeerConnection
        self.connections: Dict[str, RTCPeerConnection] = {}

        # Mappa peer_id -> RTCDataChannel
        self.data_channels: Dict[str, RTCDataChannel] = {}

        # Callback quando arriva un messaggio su un data channel
        self.on_message_callback: Optional[Callable] = None

        # Callback per inviare messaggi di signaling P2P
        self.on_p2p_signal_callback: Optional[Callable] = None

        # Polling task per signaling (solo se usa Rendezvous)
        self._polling_task: Optional[asyncio.Task] = None

    async def start(self):
        """Avvia il polling dei messaggi di signaling (solo se usa Rendezvous)"""
        if not self.use_p2p_signaling and not self._polling_task:
            self._polling_task = asyncio.create_task(self._poll_signaling_messages())
            logger.info("🔌 ConnectionManager avviato con Rendezvous signaling...")
        elif self.use_p2p_signaling:
            logger.info("🔌 ConnectionManager avviato con P2P signaling...")

    async def stop(self):
        """Ferma tutte le connessioni"""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        for pc in self.connections.values():
            await pc.close()

        self.connections.clear()
        self.data_channels.clear()

    async def connect_to_peer(self, peer_id: str):
        """
        Inizia una connessione WebRTC con un peer.
        Questo nodo agisce da "caller".
        """
        if peer_id in self.connections:
            logger.debug(f"Connessione con {peer_id[:16]}... già esistente")
            return

        pc = RTCPeerConnection()
        self.connections[peer_id] = pc

        # Crea un DataChannel
        channel = pc.createDataChannel("synapse-data")
        self.data_channels[peer_id] = channel

        @channel.on("open")
        def on_open():
            logger.info(f"✅ DataChannel aperto con {peer_id[:16]}...")

        @channel.on("message")
        def on_message(message):
            if self.on_message_callback:
                asyncio.create_task(self.on_message_callback(peer_id, message))

        @pc.on("icecandidate")
        async def on_ice_candidate(candidate):
            if candidate:
                await self._send_signaling_message(peer_id, "ice-candidate", {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex
                })

        # Crea e invia l'offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        await self._send_signaling_message(peer_id, "offer", {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })

        logger.info(f"📤 Offer inviata a {peer_id[:16]}...")

    async def send_message(self, peer_id: str, message: str):
        """Invia un messaggio su un DataChannel esistente"""
        if peer_id in self.data_channels:
            channel = self.data_channels[peer_id]
            if channel.readyState == "open":
                channel.send(message)
                logger.debug(f"📨 Messaggio inviato a {peer_id[:16]}...")
            else:
                logger.warning(f"DataChannel con {peer_id[:16]}... non aperto (stato: {channel.readyState})")
        else:
            logger.warning(f"Nessun DataChannel con {peer_id[:16]}...")

    async def _send_signaling_message(self, to_peer: str, msg_type: str, payload: dict):
        """Invia un messaggio di signaling (Rendezvous o P2P)"""
        if self.use_p2p_signaling:
            # Usa callback P2P per il signaling
            if self.on_p2p_signal_callback:
                await self.on_p2p_signal_callback(to_peer, msg_type, payload)
            else:
                logger.warning("P2P signaling callback non configurata")
        else:
            # Usa Rendezvous Server
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{self.rendezvous_url}/signal/send",
                        json={
                            "from_peer": self.node_id,
                            "to_peer": to_peer,
                            "type": msg_type,
                            "payload": payload
                        },
                        timeout=5
                    )
            except Exception as e:
                logger.error(f"Errore invio signaling a {to_peer[:16]}...: {e}")

    async def _poll_signaling_messages(self):
        """Polling continuo per ricevere messaggi di signaling"""
        while True:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.rendezvous_url}/signal/poll/{self.node_id}",
                        timeout=5
                    )

                    if response.status_code == 200:
                        messages = response.json()
                        for msg in messages:
                            await self._handle_signaling_message(
                                msg["from_peer"],
                                msg["type"],
                                msg["payload"]
                            )
            except Exception as e:
                logger.debug(f"Errore polling signaling: {e}")

            await asyncio.sleep(2)  # Poll ogni 2 secondi

    async def _handle_signaling_message(self, from_peer: str, msg_type: str, payload: dict):
        """Gestisce i messaggi di signaling in arrivo"""

        if msg_type == "offer":
            # Riceviamo un'offer: creiamo una connessione e rispondiamo
            logger.info(f"📥 Offer ricevuta da {from_peer[:16]}...")

            pc = RTCPeerConnection()
            self.connections[from_peer] = pc

            @pc.on("datachannel")
            def on_datachannel(channel: RTCDataChannel):
                self.data_channels[from_peer] = channel

                @channel.on("open")
                def on_open():
                    logger.info(f"✅ DataChannel aperto con {from_peer[:16]}... (callee)")

                @channel.on("message")
                def on_message(message):
                    if self.on_message_callback:
                        asyncio.create_task(self.on_message_callback(from_peer, message))

            @pc.on("icecandidate")
            async def on_ice_candidate(candidate):
                if candidate:
                    await self._send_signaling_message(from_peer, "ice-candidate", {
                        "candidate": candidate.candidate,
                        "sdpMid": candidate.sdpMid,
                        "sdpMLineIndex": candidate.sdpMLineIndex
                    })

            # Imposta remote description e crea answer
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=payload["sdp"],
                type=payload["type"]
            ))

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            await self._send_signaling_message(from_peer, "answer", {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            })

            logger.info(f"📤 Answer inviata a {from_peer[:16]}...")

        elif msg_type == "answer":
            # Riceviamo una risposta alla nostra offer
            logger.info(f"📥 Answer ricevuta da {from_peer[:16]}...")

            if from_peer in self.connections:
                pc = self.connections[from_peer]
                await pc.setRemoteDescription(RTCSessionDescription(
                    sdp=payload["sdp"],
                    type=payload["type"]
                ))

        elif msg_type == "ice-candidate":
            # Riceviamo un ICE candidate
            if from_peer in self.connections:
                pc = self.connections[from_peer]
                candidate = RTCIceCandidate(
                    candidate=payload["candidate"],
                    sdpMid=payload["sdpMid"],
                    sdpMLineIndex=payload["sdpMLineIndex"]
                )
                await pc.addIceCandidate(candidate)
                logger.debug(f"🧊 ICE candidate aggiunto per {from_peer[:16]}...")

    def set_message_callback(self, callback: Callable):
        """Imposta la callback per i messaggi ricevuti sui data channels"""
        self.on_message_callback = callback

    def set_p2p_signal_callback(self, callback: Callable):
        """Imposta la callback per inviare messaggi di signaling P2P"""
        self.on_p2p_signal_callback = callback
