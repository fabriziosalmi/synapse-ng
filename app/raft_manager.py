"""
RaftManager - Simplified Raft Consensus per il Consiglio Direttivo

Questo modulo implementa le fondamenta per un algoritmo Raft semplificato,
utilizzato dal Consiglio Direttivo (validator set) per ratificare operazioni
di rete che richiedono consenso forte.

Architettura:
- Solo i validatori (top N nodi per reputazione) partecipano al consenso Raft
- Un leader viene eletto tra i validatori
- Il leader coordina la ratifica delle network_operation
- Tutti i nodi non-validatori rispettano le decisioni del consiglio

Flusso di ratifica:
1. Una network_operation viene approvata dal voto ponderato (CRDT)
2. Entra in stato "pending_ratification"
3. Il leader Raft propone l'operazione al consiglio
4. I validatori votano tramite Raft (consenso maggioranza semplice)
5. Se approvata, l'operazione viene eseguita su tutta la rete

TODO per implementazione completa:
- Elezione leader (RequestVote RPC)
- Log replication (AppendEntries RPC)
- Timeout e heartbeat
- State machine per operazioni di rete (split_channel, merge_channels)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class RaftState(Enum):
    """Stato di un nodo Raft"""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class RaftLogEntry:
    """Entry nel log replicato Raft"""
    term: int
    index: int
    operation: str  # "split_channel", "merge_channels", etc.
    params: dict
    proposal_id: str  # Collegamento alla proposta originale


@dataclass
class RaftPersistentState:
    """Stato persistente (dovrebbe essere salvato su disco)"""
    current_term: int = 0
    voted_for: Optional[str] = None  # node_id
    log: List[RaftLogEntry] = field(default_factory=list)


@dataclass
class RaftVolatileState:
    """Stato volatile (può essere ricreato al riavvio)"""
    commit_index: int = 0
    last_applied: int = 0
    state: RaftState = RaftState.FOLLOWER
    leader_id: Optional[str] = None


@dataclass
class RaftLeaderState:
    """Stato aggiuntivo per il leader"""
    next_index: Dict[str, int] = field(default_factory=dict)  # Per ogni follower
    match_index: Dict[str, int] = field(default_factory=dict)


class RaftManager:
    """
    Gestisce il consenso Raft per il Consiglio Direttivo.

    Questo è un'implementazione semplificata che si concentra sulla ratifica
    di operazioni di rete già approvate dal voto ponderato della comunità.
    """

    def __init__(self, node_id: str, validator_set: List[str]):
        self.node_id = node_id
        self.validator_set = validator_set  # Lista dei validatori correnti

        # Stati Raft
        self.persistent = RaftPersistentState()
        self.volatile = RaftVolatileState()
        self.leader_state: Optional[RaftLeaderState] = None

        # Timing (in secondi)
        self.election_timeout_min = 3.0
        self.election_timeout_max = 6.0
        self.heartbeat_interval = 1.0

        # Timestamp ultimo heartbeat ricevuto
        self.last_heartbeat_time = time.time()

        # Callback per applicare operazioni committate
        self.apply_operation_callback: Optional[Callable] = None

        # Task asyncio
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.election_timer_task: Optional[asyncio.Task] = None

        logging.info(f"👑 RaftManager inizializzato per nodo {node_id[:8]}...")
        logging.info(f"   Validator set: {len(validator_set)} validatori")

    def is_validator(self) -> bool:
        """Verifica se questo nodo è parte del validator set"""
        return self.node_id in self.validator_set

    def update_validator_set(self, new_validator_set: List[str]):
        """
        Aggiorna il validator set quando cambiano le reputazioni.

        Se questo nodo non è più un validatore, si demota a follower.
        Se il leader corrente non è più nel validator set, trigger elezione.
        """
        old_is_validator = self.is_validator()
        self.validator_set = new_validator_set
        new_is_validator = self.is_validator()

        if old_is_validator and not new_is_validator:
            logging.warning(f"⚠️  Questo nodo non è più un validatore. Demozione a follower.")
            self.volatile.state = RaftState.FOLLOWER
            self.leader_state = None

        if self.volatile.leader_id and self.volatile.leader_id not in new_validator_set:
            logging.warning(f"⚠️  Leader corrente {self.volatile.leader_id[:8]}... non è più un validatore. Trigger elezione.")
            self.volatile.leader_id = None
            # TODO: Trigger election

    def set_apply_operation_callback(self, callback: Callable):
        """
        Imposta la callback che verrà chiamata quando un'operazione viene committata.

        La callback dovrebbe avere la firma:
            async def callback(operation: str, params: dict, proposal_id: str) -> bool
        """
        self.apply_operation_callback = callback

    async def start(self):
        """Avvia il RaftManager (solo se validatore)"""
        if not self.is_validator():
            logging.info(f"📝 Questo nodo non è un validatore. Raft inattivo.")
            return

        logging.info(f"👑 Avvio Raft come {self.volatile.state.value}")

        # Resetta a follower all'avvio
        self.volatile.state = RaftState.FOLLOWER
        self.volatile.leader_id = None

        # Avvia timer per elezione
        self.election_timer_task = asyncio.create_task(self._election_timer())

        # Se siamo leader, avvia heartbeat
        if self.volatile.state == RaftState.LEADER:
            self.heartbeat_task = asyncio.create_task(self._send_heartbeats())

    async def stop(self):
        """Ferma il RaftManager"""
        if self.election_timer_task:
            self.election_timer_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        logging.info(f"👑 RaftManager arrestato")

    # --- Placeholder per funzioni Raft ---

    async def request_vote(self, candidate_id: str, term: int, last_log_index: int, last_log_term: int) -> dict:
        """
        RPC RequestVote - chiamata da un candidato per richiedere voti.

        TODO: Implementare logica completa
        """
        logging.debug(f"👑 RequestVote ricevuto da {candidate_id[:8]}... per term {term}")
        return {
            "term": self.persistent.current_term,
            "vote_granted": False
        }

    async def append_entries(
        self,
        leader_id: str,
        term: int,
        prev_log_index: int,
        prev_log_term: int,
        entries: List[RaftLogEntry],
        leader_commit: int
    ) -> dict:
        """
        RPC AppendEntries - chiamata dal leader per replicare log entries (o heartbeat).

        TODO: Implementare logica completa
        """
        logging.debug(f"👑 AppendEntries ricevuto da leader {leader_id[:8]}... (term {term}, {len(entries)} entries)")

        # Aggiorna ultimo heartbeat
        self.last_heartbeat_time = time.time()
        self.volatile.leader_id = leader_id

        return {
            "term": self.persistent.current_term,
            "success": True
        }

    async def propose_operation(self, operation: str, params: dict, proposal_id: str) -> bool:
        """
        Propone una network operation per la ratifica del consiglio.

        Se questo nodo è il leader, aggiunge l'operazione al log e inizia la replicazione.
        Se non è il leader, rifiuta (il client deve contattare il leader).

        Returns:
            True se l'operazione è stata accettata dal leader, False altrimenti
        """
        if not self.is_validator():
            logging.warning(f"⚠️  Questo nodo non è un validatore. Impossibile proporre operazioni.")
            return False

        if self.volatile.state != RaftState.LEADER:
            logging.warning(f"⚠️  Questo nodo non è il leader. Redirigere al leader: {self.volatile.leader_id}")
            return False

        # TODO: Aggiungi entry al log e replica
        logging.info(f"👑 Leader: Propongo operazione '{operation}' (proposta {proposal_id[:8]}...)")
        logging.info(f"   Parametri: {params}")

        # Placeholder: aggiungi entry al log
        new_entry = RaftLogEntry(
            term=self.persistent.current_term,
            index=len(self.persistent.log),
            operation=operation,
            params=params,
            proposal_id=proposal_id
        )
        self.persistent.log.append(new_entry)

        # TODO: Avvia replicazione agli altri validatori
        # TODO: Quando committed, applica via callback

        return True

    # --- Placeholder per timer e heartbeat ---

    async def _election_timer(self):
        """
        Timer per l'elezione. Se scade senza ricevere heartbeat, diventa candidato.
        """
        import random
        
        while True:
            try:
                # Timeout randomizzato
                timeout = random.uniform(self.election_timeout_min, self.election_timeout_max)
                await asyncio.sleep(timeout)

                # Verifica se abbiamo ricevuto heartbeat recente
                time_since_heartbeat = time.time() - self.last_heartbeat_time

                # Se siamo follower e non abbiamo ricevuto heartbeat, diventa candidato
                if self.volatile.state == RaftState.FOLLOWER and time_since_heartbeat >= timeout:
                    logging.info(f"⏰ Election timeout scaduto. Divento candidato.")
                    await self._become_candidate()

                # Se siamo candidato, retry elezione
                elif self.volatile.state == RaftState.CANDIDATE:
                    logging.info(f"⏰ Election timeout come candidato. Retry elezione.")
                    await self._become_candidate()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"❌ Errore election timer: {e}")
                await asyncio.sleep(1)

    async def _become_candidate(self):
        """
        Diventa candidato e inizia un'elezione.
        """
        self.volatile.state = RaftState.CANDIDATE
        self.persistent.current_term += 1
        self.persistent.voted_for = self.node_id
        
        logging.info(f"🗳️  Divento candidato per term {self.persistent.current_term}")

        # Vota per sé stesso
        votes_received = 1

        # Richiedi voti agli altri validatori
        # TODO: Implementare chiamate HTTP agli altri validatori
        # Per ora, semplicemente logga
        logging.info(f"🗳️  Richiedo voti agli altri {len(self.validator_set) - 1} validatori")

        # Placeholder: Se siamo l'unico validatore, diventa leader
        if len(self.validator_set) == 1:
            await self._become_leader()

    async def _become_leader(self):
        """
        Diventa leader del cluster Raft.
        """
        logging.info(f"👑✨ SONO IL LEADER del consiglio per term {self.persistent.current_term}!")
        
        self.volatile.state = RaftState.LEADER
        self.volatile.leader_id = self.node_id

        # Inizializza leader state
        self.leader_state = RaftLeaderState()
        for validator_id in self.validator_set:
            if validator_id != self.node_id:
                self.leader_state.next_index[validator_id] = len(self.persistent.log)
                self.leader_state.match_index[validator_id] = -1

        # Avvia heartbeat task
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        self.heartbeat_task = asyncio.create_task(self._send_heartbeats())

    async def _send_heartbeats(self):
        """
        Invia heartbeat periodici ai follower (AppendEntries vuoti).
        """
        while self.volatile.state == RaftState.LEADER:
            try:
                logging.debug(f"💓 Invio heartbeat ai follower")
                
                # TODO: Invia AppendEntries (vuoto) a tutti i follower
                # Per ora, solo logga
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"❌ Errore invio heartbeat: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _apply_committed_entries(self):
        """
        Applica le entry committate alla state machine (esecuzione operazioni).
        """
        while self.volatile.last_applied < self.volatile.commit_index:
            self.volatile.last_applied += 1
            entry = self.persistent.log[self.volatile.last_applied]

            logging.info(f"⚙️  Applico operazione committata: {entry.operation} (proposta {entry.proposal_id[:8]}...)")

            # Chiama callback se impostato
            if self.apply_operation_callback:
                try:
                    await self.apply_operation_callback(entry.operation, entry.params, entry.proposal_id)
                except Exception as e:
                    logging.error(f"❌ Errore applicazione operazione: {e}")
