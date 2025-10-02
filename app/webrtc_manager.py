import asyncio
import json
import logging
import os
import time
from typing import Dict, Optional, Callable, Set, List
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCIceCandidate,
    RTCDataChannel,
    RTCConfiguration,
    RTCIceServer
)
from aiortc.contrib.media import MediaBlackhole
import httpx

from app.peer_scorer import PeerScorer

logger = logging.getLogger(__name__)

# Default STUN servers for NAT traversal
# These are public, free, and reliable Google STUN servers
DEFAULT_STUN_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
    {"urls": "stun:stun2.l.google.com:19302"},
    {"urls": "stun:stun3.l.google.com:19302"},
    {"urls": "stun:stun4.l.google.com:19302"},
]

class ConnectionManager:
    """
    Gestisce le connessioni WebRTC peer-to-peer.
    Supporta sia Rendezvous Server che P2P signaling.
    Include il "Sistema Immunitario" per ottimizzare la topologia della mesh.
    """

    def __init__(self, node_id: str, rendezvous_url: str = None, default_config: dict = None, ice_servers: List[dict] = None):
        self.node_id = node_id
        self.rendezvous_url = rendezvous_url
        self.use_p2p_signaling = (rendezvous_url is None)

        # Configurazione ICE servers per NAT traversal
        self.ice_servers = self._load_ice_servers(ice_servers)
        self.rtc_configuration = self._create_rtc_configuration()

        # Mappa peer_id -> RTCPeerConnection
        self.connections: Dict[str, RTCPeerConnection] = {}

        # Mappa peer_id -> RTCDataChannel
        self.data_channels: Dict[str, RTCDataChannel] = {}

        # Callback quando arriva un messaggio su un data channel
        self.on_message_callback: Optional[Callable] = None

        # Callback per inviare messaggi di signaling P2P
        self.on_p2p_signal_callback: Optional[Callable] = None

        # Callback per ottenere lo stato della rete (per calcolare score)
        self.get_network_state_callback: Optional[Callable] = None

        # Callback per ottenere i nodi scoperti (per trovare nuovi candidati)
        self.get_discovered_nodes_callback: Optional[Callable] = None

        # Peer Scorer (sistema immunitario)
        self.peer_scorer = PeerScorer(default_config or {})

        # Polling task per signaling (solo se usa Rendezvous)
        self._polling_task: Optional[asyncio.Task] = None

        # Task di ottimizzazione mesh
        self._mesh_optimization_task: Optional[asyncio.Task] = None

        # Metriche ICE per monitoring
        self.ice_metrics = {
            "total_connections_attempted": 0,
            "total_connections_established": 0,
            "total_connections_failed": 0,
            "ice_candidates_sent": 0,
            "ice_candidates_received": 0,
            "connection_states": {},  # peer_id -> state history
        }

    def _load_ice_servers(self, ice_servers: List[dict] = None) -> List[dict]:
        """
        Carica la configurazione ICE servers da diverse fonti con priorità:
        1. Parametro ice_servers passato al costruttore
        2. Variabile d'ambiente ICE_SERVERS_JSON
        3. Default STUN servers
        """
        # Priorità 1: ice_servers passato esplicitamente
        if ice_servers is not None:
            logger.info(f"🔧 Usando ICE servers da parametro: {len(ice_servers)} server")
            return ice_servers

        # Priorità 2: Variabile d'ambiente
        ice_servers_env = os.getenv("ICE_SERVERS_JSON")
        if ice_servers_env:
            try:
                parsed_servers = json.loads(ice_servers_env)
                logger.info(f"🔧 Usando ICE servers da env ICE_SERVERS_JSON: {len(parsed_servers)} server")
                return parsed_servers
            except json.JSONDecodeError as e:
                logger.error(f"Errore parsing ICE_SERVERS_JSON: {e}. Uso default STUN servers.")

        # Priorità 3: Default
        logger.info(f"🔧 Usando default STUN servers: {len(DEFAULT_STUN_SERVERS)} server")
        return DEFAULT_STUN_SERVERS

    def _create_rtc_configuration(self) -> RTCConfiguration:
        """
        Crea un oggetto RTCConfiguration con i server ICE configurati.
        Supporta STUN e TURN con credenziali.
        """
        ice_servers_list = []

        for server in self.ice_servers:
            # Estrai parametri
            urls = server.get("urls")
            username = server.get("username")
            credential = server.get("credential")

            # Crea RTCIceServer con o senza credenziali
            if username and credential:
                # TURN server con autenticazione
                ice_server = RTCIceServer(
                    urls=urls,
                    username=username,
                    credential=credential
                )
                logger.info(f"🔐 TURN server configurato: {urls} (user: {username})")
            else:
                # STUN server (no auth)
                ice_server = RTCIceServer(urls=urls)
                logger.info(f"📡 STUN server configurato: {urls}")

            ice_servers_list.append(ice_server)

        config = RTCConfiguration(iceServers=ice_servers_list)
        logger.info(f"✅ RTCConfiguration creata con {len(ice_servers_list)} ICE server(s)")

        return config

    async def start(self):
        """Avvia il polling dei messaggi di signaling e l'ottimizzazione mesh"""
        if not self.use_p2p_signaling and not self._polling_task:
            self._polling_task = asyncio.create_task(self._poll_signaling_messages())
            logger.info("🔌 ConnectionManager avviato con Rendezvous signaling...")
        elif self.use_p2p_signaling:
            logger.info("🔌 ConnectionManager avviato con P2P signaling...")

        # Avvia ottimizzazione mesh (sistema immunitario)
        if not self._mesh_optimization_task:
            self._mesh_optimization_task = asyncio.create_task(self._optimize_mesh_periodically())
            logger.info("🧬 Sistema Immunitario avviato (mesh optimization)")

    async def stop(self):
        """Ferma tutte le connessioni"""
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        if self._mesh_optimization_task:
            self._mesh_optimization_task.cancel()
            try:
                await self._mesh_optimization_task
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

        # Metriche: Nuovo tentativo di connessione
        self.ice_metrics["total_connections_attempted"] += 1

        # Usa configurazione con ICE servers per NAT traversal
        pc = RTCPeerConnection(configuration=self.rtc_configuration)
        self.connections[peer_id] = pc

        # Traccia cambiamenti di stato della connessione
        @pc.on("connectionstatechange")
        async def on_connection_state_change():
            state = pc.connectionState
            logger.info(f"🔄 Connection state con {peer_id[:16]}...: {state}")

            # Registra nella storia
            if peer_id not in self.ice_metrics["connection_states"]:
                self.ice_metrics["connection_states"][peer_id] = []
            self.ice_metrics["connection_states"][peer_id].append({
                "state": state,
                "timestamp": time.time()
            })

            # Aggiorna metriche aggregate
            if state == "connected":
                self.ice_metrics["total_connections_established"] += 1
            elif state == "failed" or state == "closed":
                self.ice_metrics["total_connections_failed"] += 1

        # Crea un DataChannel
        channel = pc.createDataChannel("synapse-data")
        self.data_channels[peer_id] = channel

        @channel.on("open")
        def on_open():
            logger.info(f"✅ DataChannel aperto con {peer_id[:16]}...")
            # Registra peer nel sistema di scoring
            self.peer_scorer.add_peer(peer_id)

        @channel.on("message")
        def on_message(message):
            # Aggiorna attività peer
            self.peer_scorer.update_peer_activity(peer_id)
            if self.on_message_callback:
                asyncio.create_task(self.on_message_callback(peer_id, message))

        @pc.on("icecandidate")
        async def on_ice_candidate(candidate):
            if candidate:
                # Metriche: Contatore candidati ICE inviati
                self.ice_metrics["ice_candidates_sent"] += 1

                # ICE Trickle: invia candidati appena disponibili (già supportato!)
                logger.debug(
                    f"🧊 ICE candidate per {peer_id[:16]}...: "
                    f"type={getattr(candidate, 'type', 'unknown')}, "
                    f"protocol={getattr(candidate, 'protocol', 'unknown')}"
                )
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

            # Usa configurazione con ICE servers per NAT traversal
            pc = RTCPeerConnection(configuration=self.rtc_configuration)
            self.connections[from_peer] = pc

            @pc.on("datachannel")
            def on_datachannel(channel: RTCDataChannel):
                self.data_channels[from_peer] = channel

                @channel.on("open")
                def on_open():
                    logger.info(f"✅ DataChannel aperto con {from_peer[:16]}... (callee)")
                    # Registra peer nel sistema di scoring
                    self.peer_scorer.add_peer(from_peer)

                @channel.on("message")
                def on_message(message):
                    # Aggiorna attività peer
                    self.peer_scorer.update_peer_activity(from_peer)
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

    def set_network_state_callback(self, callback: Callable):
        """Imposta la callback per ottenere lo stato della rete"""
        self.get_network_state_callback = callback

    def set_discovered_nodes_callback(self, callback: Callable):
        """Imposta la callback per ottenere i nodi scoperti"""
        self.get_discovered_nodes_callback = callback

    async def disconnect_peer(self, peer_id: str):
        """
        Disconnette un peer specifico (usato per ottimizzazione mesh).
        """
        if peer_id in self.connections:
            logger.info(f"🔌 Disconnessione peer {peer_id[:16]}... (ottimizzazione mesh)")

            # Chiudi connessione
            pc = self.connections[peer_id]
            await pc.close()

            # Rimuovi da strutture dati
            del self.connections[peer_id]
            if peer_id in self.data_channels:
                del self.data_channels[peer_id]

            # Registra nel sistema di scoring
            self.peer_scorer.record_disconnect(peer_id)

    async def _optimize_mesh_periodically(self):
        """
        Task in background che ottimizza periodicamente la topologia della mesh.

        Logica:
        1. Calcola score per tutti i peer connessi
        2. Identifica i top N peer da proteggere
        3. Se sopra il limite MAX_PEER_CONNECTIONS, disconnetti il peer più debole
        4. Cerca nuovi candidati migliori e connettiti
        """
        # Attendi che il sistema si stabilizzi prima di iniziare
        await asyncio.sleep(60)

        while True:
            try:
                # Ottieni configurazione corrente
                if not self.get_network_state_callback:
                    await asyncio.sleep(300)  # 5 minuti
                    continue

                network_state = await self.get_network_state_callback()
                config = network_state.get("global", {}).get("config", {})

                # Parametri configurabili via governance
                MAX_PEER_CONNECTIONS = config.get("max_peer_connections", 20)
                PROTECTED_PEER_COUNT = config.get("protected_peer_count", 5)

                # Calcola reputazioni
                reputations = {}
                for node_id, node_data in network_state.get("global", {}).get("nodes", {}).items():
                    if node_id != self.node_id:
                        # Calcola reputazione (come in calculate_reputations)
                        rep = 0
                        for channel_id, channel_data in network_state.items():
                            if channel_id != "global":
                                for task in channel_data.get("tasks", {}).values():
                                    if task.get("status") == "completed" and task.get("assignee") == node_id:
                                        rep += config.get("task_completion_reputation_reward", 10)
                            for prop in channel_data.get("proposals", {}).values():
                                if node_id in prop.get("votes", {}):
                                    rep += config.get("proposal_vote_reputation_reward", 1)
                        reputations[node_id] = rep

                # Calcola scores per tutti i peer connessi
                scores = self.peer_scorer.get_all_scores(reputations, config)

                logger.debug(f"🧬 Mesh optimization: {len(self.connections)} connessioni, {len(scores)} con score")

                # Se sopra il limite, disconnetti il peer più debole
                if len(self.connections) > MAX_PEER_CONNECTIONS:
                    # Identifica peer protetti (top N)
                    top_peers = self.peer_scorer.get_top_peers(reputations, config, PROTECTED_PEER_COUNT)
                    protected_set = set(top_peers)

                    # Trova il peer più debole (escludendo i protetti)
                    weakest = self.peer_scorer.get_weakest_peer(reputations, config, protected_set)

                    if weakest and weakest in self.connections:
                        logger.info(
                            f"🧬 Mesh optimization: Disconnetto peer debole {weakest[:16]}... "
                            f"(score={scores.get(weakest, 0):.3f})"
                        )
                        await self.disconnect_peer(weakest)

                # Cerca nuovo candidato da connettere
                if len(self.connections) < MAX_PEER_CONNECTIONS:
                    if self.get_discovered_nodes_callback:
                        discovered = await self.get_discovered_nodes_callback()

                        # Filtra nodi non connessi
                        candidates = [
                            node_id for node_id in discovered
                            if node_id not in self.connections and node_id != self.node_id
                        ]

                        if candidates:
                            # Scegli candidato con reputazione più alta
                            best_candidate = max(
                                candidates,
                                key=lambda nid: reputations.get(nid, 0)
                            )

                            logger.info(
                                f"🧬 Mesh optimization: Connetto nuovo candidato {best_candidate[:16]}... "
                                f"(rep={reputations.get(best_candidate, 0)})"
                            )

                            await self.connect_to_peer(best_candidate)

            except Exception as e:
                logger.error(f"Errore durante ottimizzazione mesh: {e}")

            # Esegui ogni 5 minuti
            await asyncio.sleep(300)
