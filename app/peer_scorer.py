"""
Peer Scoring System - Il Sistema Immunitario di Synapse-NG

Questo modulo implementa un sistema di scoring per valutare la "salute" dei peer connessi,
permettendo alla rete di ottimizzare automaticamente la sua topologia WebRTC.

Formula di Scoring:
    score = (w_rep * rep_norm) + (w_stab * stab_norm) - (w_lat * lat_norm)

Dove:
    - rep_norm: Reputazione normalizzata del peer (0-1)
    - stab_norm: Stabilità della connessione (uptime/total_time)
    - lat_norm: Latenza normalizzata della connessione (0-1, invertita)
    - w_*: Pesi configurabili via governance
"""

import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PeerConnectionMetrics:
    """Metriche per una singola connessione peer."""
    peer_id: str
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    total_uptime: float = 0.0  # Tempo totale di connessione (secondi)
    disconnect_count: int = 0  # Numero di disconnessioni
    latency_ms: float = 100.0  # Latenza stimata (millisecondi)
    bytes_sent: int = 0  # Byte inviati (per statistiche future)
    bytes_received: int = 0  # Byte ricevuti (per statistiche future)

    def update_uptime(self):
        """Aggiorna l'uptime della connessione."""
        now = time.time()
        self.total_uptime += (now - self.last_seen)
        self.last_seen = now

    def get_stability(self) -> float:
        """
        Calcola la stabilità della connessione (0-1).
        Una connessione stabile ha poche disconnessioni e lungo uptime.
        """
        now = time.time()
        total_time = now - self.connected_at
        if total_time == 0:
            return 0.0

        # Stabilità basata su uptime ratio
        uptime_ratio = min(self.total_uptime / total_time, 1.0)

        # Penalità per disconnessioni frequenti
        disconnect_penalty = 1.0 / (1.0 + self.disconnect_count * 0.1)

        return uptime_ratio * disconnect_penalty


class PeerScorer:
    """
    Calcola lo score di salute per ogni peer connesso.
    Lo score determina quali connessioni mantenere e quali sostituire.
    """

    def __init__(self, default_config: dict):
        """
        Args:
            default_config: Configurazione di default della rete
        """
        self.metrics: Dict[str, PeerConnectionMetrics] = {}
        self.default_config = default_config

    def add_peer(self, peer_id: str):
        """Registra un nuovo peer connesso."""
        if peer_id not in self.metrics:
            self.metrics[peer_id] = PeerConnectionMetrics(peer_id=peer_id)
            logger.debug(f"📊 Peer {peer_id[:16]}... registrato nel sistema di scoring")

    def remove_peer(self, peer_id: str):
        """Rimuove un peer dal sistema di scoring."""
        if peer_id in self.metrics:
            del self.metrics[peer_id]
            logger.debug(f"📊 Peer {peer_id[:16]}... rimosso dal sistema di scoring")

    def update_peer_activity(self, peer_id: str):
        """Aggiorna l'attività di un peer (chiamato quando si ricevono messaggi)."""
        if peer_id in self.metrics:
            self.metrics[peer_id].update_uptime()
            self.metrics[peer_id].last_seen = time.time()

    def update_peer_latency(self, peer_id: str, latency_ms: float):
        """Aggiorna la latenza stimata di un peer."""
        if peer_id in self.metrics:
            self.metrics[peer_id].latency_ms = latency_ms

    def record_disconnect(self, peer_id: str):
        """Registra una disconnessione di un peer."""
        if peer_id in self.metrics:
            self.metrics[peer_id].disconnect_count += 1
            logger.debug(f"📊 Peer {peer_id[:16]}... disconnessione #{self.metrics[peer_id].disconnect_count}")

    def normalize_reputation(self, reputation: int, max_reputation: int = 1000) -> float:
        """
        Normalizza la reputazione in un range 0-1.

        Args:
            reputation: Reputazione grezza del nodo
            max_reputation: Reputazione massima attesa (per normalizzazione)

        Returns:
            Valore normalizzato 0-1
        """
        if max_reputation == 0:
            return 0.0
        return min(reputation / max_reputation, 1.0)

    def normalize_latency(self, latency_ms: float, max_latency_ms: float = 1000.0) -> float:
        """
        Normalizza la latenza in un range 0-1 (0 = latenza bassa, 1 = latenza alta).

        Args:
            latency_ms: Latenza in millisecondi
            max_latency_ms: Latenza massima tollerata

        Returns:
            Valore normalizzato 0-1
        """
        return min(latency_ms / max_latency_ms, 1.0)

    def calculate_score(
        self,
        peer_id: str,
        reputation: int,
        config: dict,
        max_reputation: int = 1000
    ) -> Optional[float]:
        """
        Calcola lo score di salute di un peer.

        Args:
            peer_id: ID del peer
            reputation: Reputazione del peer dal network_state
            config: Configurazione corrente della rete (per i pesi)
            max_reputation: Reputazione massima nella rete (per normalizzazione)

        Returns:
            Score normalizzato (0-1), o None se il peer non è tracciato
        """
        if peer_id not in self.metrics:
            return None

        metrics = self.metrics[peer_id]

        # Ottieni pesi dalla config (governabili via proposte!)
        w_rep = config.get("peer_score_weight_reputation", 0.5)
        w_stab = config.get("peer_score_weight_stability", 0.3)
        w_lat = config.get("peer_score_weight_latency", 0.2)

        # Normalizza i valori
        rep_norm = self.normalize_reputation(reputation, max_reputation)
        stab_norm = metrics.get_stability()
        lat_norm = self.normalize_latency(metrics.latency_ms)

        # Calcola score
        score = (w_rep * rep_norm) + (w_stab * stab_norm) - (w_lat * lat_norm)

        # Clamp tra 0 e 1
        score = max(0.0, min(1.0, score))

        logger.debug(
            f"📊 Score per {peer_id[:16]}...: {score:.3f} "
            f"(rep={rep_norm:.2f}, stab={stab_norm:.2f}, lat={lat_norm:.2f})"
        )

        return score

    def get_all_scores(
        self,
        reputations: Dict[str, int],
        config: dict
    ) -> Dict[str, float]:
        """
        Calcola gli score per tutti i peer connessi.

        Args:
            reputations: Mappa peer_id -> reputazione
            config: Configurazione corrente della rete

        Returns:
            Mappa peer_id -> score
        """
        if not reputations:
            max_rep = 1000  # Default se non ci sono reputazioni
        else:
            max_rep = max(reputations.values()) if reputations else 1000

        scores = {}
        for peer_id in self.metrics:
            rep = reputations.get(peer_id, 0)
            score = self.calculate_score(peer_id, rep, config, max_rep)
            if score is not None:
                scores[peer_id] = score

        return scores

    def get_weakest_peer(
        self,
        reputations: Dict[str, int],
        config: dict,
        protected_peers: set = None
    ) -> Optional[str]:
        """
        Identifica il peer con lo score più basso (candidato per disconnessione).

        Args:
            reputations: Mappa peer_id -> reputazione
            config: Configurazione corrente della rete
            protected_peers: Set di peer_id da proteggere (non disconnettere)

        Returns:
            ID del peer più debole, o None se non ci sono candidati
        """
        scores = self.get_all_scores(reputations, config)

        if not scores:
            return None

        # Filtra i peer protetti
        if protected_peers:
            scores = {pid: score for pid, score in scores.items() if pid not in protected_peers}

        if not scores:
            return None

        # Trova il peer con lo score più basso
        weakest_peer = min(scores, key=scores.get)
        logger.info(f"🎯 Peer più debole identificato: {weakest_peer[:16]}... (score={scores[weakest_peer]:.3f})")

        return weakest_peer

    def get_top_peers(
        self,
        reputations: Dict[str, int],
        config: dict,
        top_n: int = 5
    ) -> list:
        """
        Identifica i top N peer con gli score più alti (da proteggere).

        Args:
            reputations: Mappa peer_id -> reputazione
            config: Configurazione corrente della rete
            top_n: Numero di peer da proteggere

        Returns:
            Lista di peer_id ordinati per score (dal migliore al peggiore)
        """
        scores = self.get_all_scores(reputations, config)

        if not scores:
            return []

        # Ordina per score decrescente
        sorted_peers = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        top_peers = [peer_id for peer_id, _ in sorted_peers[:top_n]]
        logger.debug(f"🛡️  Top {top_n} peer protetti: {[p[:16] + '...' for p in top_peers]}")

        return top_peers

    def get_metrics(self, peer_id: str) -> Optional[PeerConnectionMetrics]:
        """Ottiene le metriche grezze di un peer."""
        return self.metrics.get(peer_id)

    def get_all_metrics(self) -> Dict[str, dict]:
        """
        Ottiene tutte le metriche in formato serializzabile (per API).

        Returns:
            Mappa peer_id -> metriche (dict)
        """
        return {
            peer_id: {
                "connected_at": m.connected_at,
                "last_seen": m.last_seen,
                "total_uptime": m.total_uptime,
                "disconnect_count": m.disconnect_count,
                "latency_ms": m.latency_ms,
                "stability": m.get_stability(),
                "bytes_sent": m.bytes_sent,
                "bytes_received": m.bytes_received
            }
            for peer_id, m in self.metrics.items()
        }
