"""
SynapseSub Protocol - PubSub messaging over WebRTC

Formato messaggi:
{
    "type": "ANNOUNCE|MESSAGE|I_HAVE|I_WANT|PING|PONG",
    "topic": "global-discovery|channel:sviluppo_ui:state|...",
    "payload": {...},
    "sender_id": "node_id",
    "timestamp": 1234567890.123,
    "message_id": "unique_msg_id"
}
"""

import time
import uuid
import json
import logging
from typing import Dict, Set, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipi di messaggi SynapseSub"""
    ANNOUNCE = "ANNOUNCE"      # Discovery: annuncio presenza su un topic
    MESSAGE = "MESSAGE"        # Gossip: messaggio con stato/dati
    I_HAVE = "I_HAVE"         # Ottimizzazione: annuncio possesso di dati
    I_WANT = "I_WANT"         # Ottimizzazione: richiesta dati mancanti
    PING = "PING"             # Keepalive
    PONG = "PONG"             # Risposta a PING


@dataclass
class SynapseSubMessage:
    """Messaggio SynapseSub"""
    type: str
    topic: str
    payload: dict
    sender_id: str
    timestamp: float
    message_id: str

    def to_json(self) -> str:
        """Serializza a JSON"""
        return json.dumps(asdict(self))

    @staticmethod
    def from_json(data: str) -> 'SynapseSubMessage':
        """Deserializza da JSON"""
        obj = json.loads(data)
        return SynapseSubMessage(**obj)

    @staticmethod
    def create(msg_type: MessageType, topic: str, payload: dict, sender_id: str) -> 'SynapseSubMessage':
        """Factory per creare un messaggio"""
        return SynapseSubMessage(
            type=msg_type.value,
            topic=topic,
            payload=payload,
            sender_id=sender_id,
            timestamp=time.time(),
            message_id=str(uuid.uuid4())
        )


class TopicMesh:
    """
    Gestisce la mesh di peer per un singolo topic.
    Mantiene i peer interessati al topic e la lista dei messaggi visti.
    """

    def __init__(self, topic_name: str, max_seen_messages: int = 1000):
        self.topic_name = topic_name
        self.peers: Set[str] = set()  # peer_id interessati al topic
        self.seen_messages: Dict[str, float] = {}  # message_id -> timestamp
        self.max_seen_messages = max_seen_messages

        # Cache per ottimizzazione I_HAVE/I_WANT
        self.pending_ihave: Dict[str, List[str]] = {}  # peer_id -> [message_ids]
        self.pending_iwant: Dict[str, List[str]] = {}  # peer_id -> [message_ids]

    def add_peer(self, peer_id: str):
        """Aggiunge un peer alla mesh"""
        if peer_id not in self.peers:
            self.peers.add(peer_id)
            logger.info(f"📌 Peer {peer_id[:16]}... aggiunto al topic '{self.topic_name}'")

    def remove_peer(self, peer_id: str):
        """Rimuove un peer dalla mesh"""
        if peer_id in self.peers:
            self.peers.discard(peer_id)
            logger.info(f"📌 Peer {peer_id[:16]}... rimosso dal topic '{self.topic_name}'")

    def has_seen(self, message_id: str) -> bool:
        """Verifica se un messaggio è già stato visto"""
        return message_id in self.seen_messages

    def mark_seen(self, message_id: str):
        """Marca un messaggio come visto"""
        self.seen_messages[message_id] = time.time()

        # Limita la dimensione della cache
        if len(self.seen_messages) > self.max_seen_messages:
            # Rimuovi i messaggi più vecchi
            sorted_msgs = sorted(self.seen_messages.items(), key=lambda x: x[1])
            to_remove = len(self.seen_messages) - self.max_seen_messages + 100
            for msg_id, _ in sorted_msgs[:to_remove]:
                del self.seen_messages[msg_id]

    def get_peers_except(self, exclude_peer: str) -> List[str]:
        """Restituisce tutti i peer del topic tranne uno"""
        return [p for p in self.peers if p != exclude_peer]

    def cleanup_old_seen_messages(self, max_age_seconds: int = 300):
        """Rimuove i messaggi visti più vecchi di max_age_seconds"""
        now = time.time()
        to_remove = [
            msg_id for msg_id, ts in self.seen_messages.items()
            if now - ts > max_age_seconds
        ]
        for msg_id in to_remove:
            del self.seen_messages[msg_id]


class PubSubManager:
    """
    Gestisce il protocollo PubSub per tutti i topic.
    Coordina l'invio/ricezione di messaggi e mantiene le mesh.
    """

    def __init__(self, node_id: str, webrtc_manager):
        self.node_id = node_id
        self.webrtc_manager = webrtc_manager

        # Mesh per topic
        self.meshes: Dict[str, TopicMesh] = {}

        # Callbacks
        self.on_message_callback: Optional[Callable] = None
        self.on_peer_discovered_callback: Optional[Callable] = None

    def subscribe_topic(self, topic: str):
        """Sottoscrivi a un topic"""
        if topic not in self.meshes:
            self.meshes[topic] = TopicMesh(topic)
            logger.info(f"📡 Sottoscritto al topic '{topic}'")

            # Invia ANNOUNCE a tutti i peer connessi
            self._announce_topic(topic)

    def unsubscribe_topic(self, topic: str):
        """Disiscriviti da un topic"""
        if topic in self.meshes:
            del self.meshes[topic]
            logger.info(f"📡 Disiscritto dal topic '{topic}'")

    def publish(self, topic: str, payload: dict) -> Optional[SynapseSubMessage]:
        """
        Pubblica un messaggio su un topic.
        Il messaggio viene inviato a tutti i peer nella mesh del topic.
        """
        if topic not in self.meshes:
            logger.warning(f"Tentativo di pubblicare su topic non sottoscritto: {topic}")
            return None

        # Crea il messaggio
        msg = SynapseSubMessage.create(
            MessageType.MESSAGE,
            topic,
            payload,
            self.node_id
        )

        # Marca come visto localmente
        mesh = self.meshes[topic]
        mesh.mark_seen(msg.message_id)

        # Invia a tutti i peer nella mesh
        self._broadcast_to_mesh(topic, msg)

        return msg

    def handle_message(self, sender_peer_id: str, msg: SynapseSubMessage):
        """
        Gestisce un messaggio ricevuto da un peer.
        Implementa la logica di routing e forwarding.
        """
        msg_type = MessageType(msg.type)

        if msg_type == MessageType.ANNOUNCE:
            self._handle_announce(sender_peer_id, msg)

        elif msg_type == MessageType.MESSAGE:
            self._handle_message_gossip(sender_peer_id, msg)

        elif msg_type == MessageType.I_HAVE:
            self._handle_ihave(sender_peer_id, msg)

        elif msg_type == MessageType.I_WANT:
            self._handle_iwant(sender_peer_id, msg)

        elif msg_type == MessageType.PING:
            self._handle_ping(sender_peer_id, msg)

        elif msg_type == MessageType.PONG:
            self._handle_pong(sender_peer_id, msg)

    def _announce_topic(self, topic: str):
        """Annuncia interesse per un topic a tutti i peer connessi"""
        msg = SynapseSubMessage.create(
            MessageType.ANNOUNCE,
            topic,
            {"channels": list(self.meshes.keys())},  # Condividi tutti i topic sottoscritti
            self.node_id
        )

        # Invia a tutti i peer WebRTC connessi
        for peer_id in self.webrtc_manager.data_channels.keys():
            self._send_to_peer(peer_id, msg)

    def _handle_announce(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un ANNOUNCE ricevuto"""
        topic = msg.topic
        announced_channels = msg.payload.get("channels", [])

        logger.info(f"📢 ANNOUNCE da {sender_peer_id[:16]}... per topic '{topic}'")

        # Aggiungi il peer alla mesh del topic
        if topic not in self.meshes:
            self.subscribe_topic(topic)

        self.meshes[topic].add_peer(sender_peer_id)

        # Aggiungi il peer anche agli altri topic che ha annunciato
        for channel in announced_channels:
            if channel in self.meshes:
                self.meshes[channel].add_peer(sender_peer_id)

        # Notifica la callback
        if self.on_peer_discovered_callback:
            self.on_peer_discovered_callback(sender_peer_id, announced_channels)

    def _handle_message_gossip(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un MESSAGE (gossip) ricevuto"""
        topic = msg.topic

        if topic not in self.meshes:
            logger.debug(f"Messaggio ricevuto per topic non sottoscritto: {topic}")
            return

        mesh = self.meshes[topic]

        # Deduplica: ignora se già visto
        if mesh.has_seen(msg.message_id):
            logger.debug(f"Messaggio duplicato ignorato: {msg.message_id[:8]}...")
            return

        mesh.mark_seen(msg.message_id)

        logger.info(f"📨 MESSAGE da {sender_peer_id[:16]}... su topic '{topic}'")

        # Notifica la callback per processare il payload
        if self.on_message_callback:
            self.on_message_callback(topic, msg.payload, msg.sender_id)

        # Forward ai peer nella mesh (tranne il sender)
        peers_to_forward = mesh.get_peers_except(sender_peer_id)
        for peer_id in peers_to_forward:
            self._send_to_peer(peer_id, msg)

    def _handle_ihave(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un I_HAVE (ottimizzazione)"""
        topic = msg.topic
        message_ids = msg.payload.get("message_ids", [])

        if topic not in self.meshes:
            return

        mesh = self.meshes[topic]

        # Trova messaggi che non abbiamo
        missing_ids = [mid for mid in message_ids if not mesh.has_seen(mid)]

        if missing_ids:
            logger.info(f"🔍 I_HAVE: {len(missing_ids)} messaggi mancanti da {sender_peer_id[:16]}...")

            # Invia I_WANT per richiedere i messaggi mancanti
            iwant_msg = SynapseSubMessage.create(
                MessageType.I_WANT,
                topic,
                {"message_ids": missing_ids},
                self.node_id
            )
            self._send_to_peer(sender_peer_id, iwant_msg)

    def _handle_iwant(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un I_WANT (ottimizzazione)"""
        # In questa implementazione semplificata, non manteniamo una cache dei messaggi
        # Questa funzionalità può essere implementata in futuro
        logger.debug(f"📬 I_WANT ricevuto da {sender_peer_id[:16]}... (non implementato)")

    def _handle_ping(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un PING"""
        pong_msg = SynapseSubMessage.create(
            MessageType.PONG,
            "keepalive",
            {"ping_id": msg.message_id},
            self.node_id
        )
        self._send_to_peer(sender_peer_id, pong_msg)

    def _handle_pong(self, sender_peer_id: str, msg: SynapseSubMessage):
        """Gestisce un PONG"""
        logger.debug(f"🏓 PONG ricevuto da {sender_peer_id[:16]}...")

    def _broadcast_to_mesh(self, topic: str, msg: SynapseSubMessage):
        """Invia un messaggio a tutti i peer nella mesh di un topic"""
        if topic not in self.meshes:
            return

        mesh = self.meshes[topic]
        for peer_id in mesh.peers:
            self._send_to_peer(peer_id, msg)

    def _send_to_peer(self, peer_id: str, msg: SynapseSubMessage):
        """Invia un messaggio a un peer specifico via WebRTC"""
        try:
            self.webrtc_manager.send_message(peer_id, msg.to_json())
        except Exception as e:
            logger.error(f"Errore invio messaggio a {peer_id[:16]}...: {e}")

    def set_message_callback(self, callback: Callable):
        """Imposta la callback per i messaggi ricevuti"""
        self.on_message_callback = callback

    def set_peer_discovered_callback(self, callback: Callable):
        """Imposta la callback per peer scoperti"""
        self.on_peer_discovered_callback = callback

    def cleanup_old_messages(self):
        """Cleanup periodico dei messaggi vecchi"""
        for mesh in self.meshes.values():
            mesh.cleanup_old_seen_messages()

    def get_stats(self) -> dict:
        """Restituisce statistiche sul PubSub"""
        return {
            "subscribed_topics": len(self.meshes),
            "topics": {
                topic: {
                    "peers": len(mesh.peers),
                    "seen_messages": len(mesh.seen_messages)
                }
                for topic, mesh in self.meshes.items()
            }
        }
