"""
WebRTC P2P connections per Synapse-NG
Usa aiortc per stabilire data channels diretti tra nodi
"""

import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaBlackhole


class WebRTCPeer:
    """Gestisce connessione WebRTC con un singolo peer"""

    def __init__(self, peer_id: str, on_message_callback):
        self.peer_id = peer_id
        self.on_message = on_message_callback
        self.pc = None
        self.channel = None
        self.connected = False

        # Configurazione STUN (Google pubblico)
        self.config = RTCConfiguration(
            iceServers=[
                RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
                RTCIceServer(urls=["stun:stun1.l.google.com:19302"])
            ]
        )

    async def create_offer(self) -> dict:
        """Crea offerta WebRTC per iniziare connessione"""
        self.pc = RTCPeerConnection(configuration=self.config)

        # Crea data channel
        self.channel = self.pc.createDataChannel("synapse-gossip")
        self._setup_channel_handlers()

        # Gestione ICE connection state
        @self.pc.on("iceconnectionstatechange")
        async def on_ice_connection_state_change():
            print(f"🧊 ICE connection state: {self.pc.iceConnectionState} (peer: {self.peer_id[:8]})")
            if self.pc.iceConnectionState == "connected":
                self.connected = True
            elif self.pc.iceConnectionState in ["failed", "closed"]:
                self.connected = False

        # Crea offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)

        # Attendi che ICE gathering sia completo
        await self._wait_for_ice_gathering()

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp
        }

    async def handle_offer(self, offer_data: dict) -> dict:
        """Riceve offerta e crea risposta"""
        self.pc = RTCPeerConnection(configuration=self.config)

        # Gestione data channel in arrivo
        @self.pc.on("datachannel")
        def on_datachannel(channel):
            self.channel = channel
            self._setup_channel_handlers()

        # Gestione ICE connection state
        @self.pc.on("iceconnectionstatechange")
        async def on_ice_connection_state_change():
            print(f"🧊 ICE connection state: {self.pc.iceConnectionState} (peer: {self.peer_id[:8]})")
            if self.pc.iceConnectionState == "connected":
                self.connected = True
            elif self.pc.iceConnectionState in ["failed", "closed"]:
                self.connected = False

        # Imposta remote description
        offer = RTCSessionDescription(sdp=offer_data["sdp"], type=offer_data["type"])
        await self.pc.setRemoteDescription(offer)

        # Crea answer
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        # Attendi ICE gathering
        await self._wait_for_ice_gathering()

        return {
            "type": self.pc.localDescription.type,
            "sdp": self.pc.localDescription.sdp
        }

    async def handle_answer(self, answer_data: dict):
        """Riceve risposta e completa connessione"""
        answer = RTCSessionDescription(sdp=answer_data["sdp"], type=answer_data["type"])
        await self.pc.setRemoteDescription(answer)

    def _setup_channel_handlers(self):
        """Configura handlers per data channel"""
        @self.channel.on("open")
        def on_open():
            print(f"✅ Data channel aperto con {self.peer_id[:8]}")
            self.connected = True

        @self.channel.on("message")
        def on_message(message):
            try:
                data = json.loads(message)
                asyncio.create_task(self.on_message(self.peer_id, data))
            except Exception as e:
                print(f"❌ Errore parsing messaggio WebRTC: {e}")

        @self.channel.on("close")
        def on_close():
            print(f"❌ Data channel chiuso con {self.peer_id[:8]}")
            self.connected = False

    async def _wait_for_ice_gathering(self):
        """Attendi che ICE gathering sia completo"""
        if self.pc.iceGatheringState == "complete":
            return

        # Timeout di 5 secondi
        for _ in range(50):
            await asyncio.sleep(0.1)
            if self.pc.iceGatheringState == "complete":
                return

        print(f"⚠️  ICE gathering timeout per {self.peer_id[:8]}")

    async def send_message(self, data: dict):
        """Invia messaggio attraverso data channel"""
        if self.channel and self.channel.readyState == "open":
            message = json.dumps(data)
            self.channel.send(message)
            return True
        return False

    async def close(self):
        """Chiudi connessione"""
        self.connected = False
        if self.channel:
            self.channel.close()
        if self.pc:
            await self.pc.close()


class WebRTCManager:
    """Gestisce tutte le connessioni WebRTC del nodo"""

    def __init__(self, node_id: str, on_gossip_received):
        self.node_id = node_id
        self.on_gossip_received = on_gossip_received
        self.peers = {}  # peer_id -> WebRTCPeer
        self.pending_offers = {}  # peer_id -> offer_data
        self.enabled = True

    async def initiate_connection(self, peer_id: str) -> dict:
        """Inizia connessione WebRTC con un peer"""
        if peer_id in self.peers:
            return None  # Già connesso

        peer = WebRTCPeer(peer_id, self._on_message_received)
        offer = await peer.create_offer()

        # Salva peer
        self.peers[peer_id] = peer

        return {
            "from": self.node_id,
            "to": peer_id,
            "offer": offer
        }

    async def handle_webrtc_signal(self, signal_data: dict):
        """Gestisce segnale WebRTC (offer/answer)"""
        from_peer = signal_data.get("from")

        if "offer" in signal_data:
            # Ricevuto offer
            if from_peer not in self.peers:
                peer = WebRTCPeer(from_peer, self._on_message_received)
                answer = await peer.handle_offer(signal_data["offer"])
                self.peers[from_peer] = peer

                # Ritorna answer da inviare
                return {
                    "from": self.node_id,
                    "to": from_peer,
                    "answer": answer
                }

        elif "answer" in signal_data:
            # Ricevuto answer
            if from_peer in self.peers:
                await self.peers[from_peer].handle_answer(signal_data["answer"])

        return None

    async def _on_message_received(self, peer_id: str, data: dict):
        """Callback quando arriva messaggio da peer"""
        await self.on_gossip_received(data)

    async def send_to_peer(self, peer_id: str, data: dict) -> bool:
        """Invia dati a peer specifico via WebRTC"""
        if peer_id in self.peers and self.peers[peer_id].connected:
            return await self.peers[peer_id].send_message(data)
        return False

    async def broadcast(self, data: dict):
        """Invia a tutti i peer connessi"""
        tasks = []
        for peer_id, peer in self.peers.items():
            if peer.connected:
                tasks.append(peer.send_message(data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_connected_peers(self) -> list:
        """Ritorna lista peer connessi via WebRTC"""
        return [
            peer_id for peer_id, peer in self.peers.items()
            if peer.connected
        ]

    async def cleanup_dead_connections(self):
        """Rimuovi connessioni morte"""
        dead = [
            peer_id for peer_id, peer in self.peers.items()
            if not peer.connected and peer.pc and peer.pc.iceConnectionState in ["failed", "closed"]
        ]

        for peer_id in dead:
            await self.peers[peer_id].close()
            del self.peers[peer_id]

    async def shutdown(self):
        """Chiudi tutte le connessioni"""
        for peer in self.peers.values():
            await peer.close()
        self.peers.clear()
