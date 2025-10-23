"""
Immune System - Sistema Immunitario Proattivo di Synapse-NG

Questo modulo implementa il primo ciclo omeostatico completo della rete:
1. Monitoraggio continuo delle metriche di salute
2. Diagnosi autonoma di inefficienze
3. Proposta automatica di rimedi tramite governance
4. Applicazione automatica delle cure approvate

Questo è il cuore pulsante della Network Singularity: la rete che si autocura.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class NetworkMetrics:
    """Snapshot delle metriche di salute della rete"""
    avg_propagation_latency_ms: float
    total_messages_propagated: int
    active_peers: int
    failed_messages: int
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthIssue:
    """Descrizione di un problema di salute rilevato"""
    issue_type: str  # "high_latency", "low_connectivity", "message_loss", etc.
    severity: str    # "low", "medium", "high", "critical"
    current_value: float
    target_value: float
    recommended_action: str
    description: str
    detected_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProposedRemedy:
    """Proposta di cura generata dal sistema immunitario"""
    issue_type: str
    proposal_title: str
    proposal_description: str
    config_changes: Dict[str, Any]
    expected_improvement: str
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# DEFAULT HEALTH TARGETS
# ============================================================================

DEFAULT_HEALTH_TARGETS = {
    "max_avg_propagation_latency_ms": 10000,  # 10 seconds
    "min_active_peers": 3,
    "max_failed_message_rate": 0.05,  # 5% failure rate
    "min_message_throughput": 10  # messages per minute
}


# ============================================================================
# IMMUNE SYSTEM MANAGER
# ============================================================================

class ImmuneSystemManager:
    """
    Gestore del sistema immunitario della rete.
    Monitora, diagnostica e propone rimedi in modo autonomo.
    """
    
    def __init__(self, node_id: str, network_state: Dict, pubsub_manager):
        self.node_id = node_id
        self.network_state = network_state
        self.pubsub_manager = pubsub_manager
        
        # Metrics tracking
        self.propagation_latencies: List[float] = []
        self.message_timestamps: List[float] = []
        self.failed_messages_count: int = 0
        self.total_messages_received: int = 0
        
        # Health targets (from config or defaults)
        self.health_targets = DEFAULT_HEALTH_TARGETS.copy()
        
        # Active issues and pending proposals
        self.active_issues: Dict[str, HealthIssue] = {}
        self.pending_remedy_proposals: Dict[str, str] = {}  # issue_type -> proposal_id
        
        # Loop control
        self.running = False
        self.loop_task: Optional[asyncio.Task] = None
        
        logger.info(f"[ImmuneSystem] Initialized for node {node_id}")
    
    
    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================
    
    async def start(self):
        """Avvia il loop del sistema immunitario"""
        if self.running:
            logger.warning("[ImmuneSystem] Already running")
            return
        
        self.running = True
        self._load_health_targets()
        self.loop_task = asyncio.create_task(self._immune_system_loop())
        logger.info("[ImmuneSystem] Started - monitoring every hour")
    
    
    async def stop(self):
        """Ferma il loop del sistema immunitario"""
        if not self.running:
            return
        
        self.running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[ImmuneSystem] Stopped")
    
    
    def _load_health_targets(self):
        """Carica i target di salute dalla configurazione globale"""
        global_config = self.network_state.get("global", {}).get("config", {})
        
        if "health_targets" in global_config:
            self.health_targets.update(global_config["health_targets"])
            logger.info(f"[ImmuneSystem] Loaded health targets from config: {self.health_targets}")
        else:
            # Inizializza la sezione nella config se non esiste
            if "global" in self.network_state:
                if "config" not in self.network_state["global"]:
                    self.network_state["global"]["config"] = {}
                self.network_state["global"]["config"]["health_targets"] = self.health_targets
                logger.info(f"[ImmuneSystem] Initialized default health targets in config")
    
    
    # ========================================================================
    # MAIN LOOP
    # ========================================================================
    
    async def _immune_system_loop(self):
        """
        Loop principale del sistema immunitario.
        Esegue ogni ora: raccolta metriche → diagnosi → proposta rimedi.
        """
        logger.info("[ImmuneSystem] Loop started - first check in 60 seconds")
        
        # Primo check dopo 1 minuto (per debug/testing, poi diventa 1 ora)
        await asyncio.sleep(60)
        
        while self.running:
            try:
                logger.info("[ImmuneSystem] ===== Starting health check cycle =====")
                
                # Step 1: Collect metrics
                metrics = self.collect_network_metrics()
                logger.info(f"[ImmuneSystem] Metrics: {metrics.to_dict()}")
                
                # Step 2: Diagnose issues
                issues = self.diagnose_health_issues(metrics)
                
                if issues:
                    logger.warning(f"[ImmuneSystem] Detected {len(issues)} health issue(s)")
                    for issue in issues:
                        logger.warning(f"  - {issue.issue_type}: {issue.description}")
                        
                    # Step 3: Propose remedies for new issues
                    for issue in issues:
                        await self.propose_remedy(issue)
                else:
                    logger.info("[ImmuneSystem] Network health is optimal ✓")
                
                # Step 4: Check if previous remedies were applied
                self._check_remedy_outcomes()
                
                logger.info("[ImmuneSystem] ===== Health check cycle complete =====")
                
            except Exception as e:
                logger.error(f"[ImmuneSystem] Error in loop: {e}", exc_info=True)
            
            # Wait 1 hour before next check (for production)
            # For testing, can use shorter interval like 5 minutes
            await asyncio.sleep(3600)  # 1 hour
    
    
    # ========================================================================
    # METRICS COLLECTION
    # ========================================================================
    
    def collect_network_metrics(self) -> NetworkMetrics:
        """
        Raccoglie e calcola le metriche di salute correnti della rete.
        
        Returns:
            NetworkMetrics con snapshot corrente della salute
        """
        now = time.time()
        
        # Calculate average propagation latency
        if self.propagation_latencies:
            avg_latency_ms = sum(self.propagation_latencies) / len(self.propagation_latencies)
        else:
            avg_latency_ms = 0.0
        
        # Count active peers
        active_peers = len(self.network_state.get("global", {}).get("nodes", {}))
        
        # Calculate failed message rate
        total_messages = self.total_messages_received
        failed_messages = self.failed_messages_count
        
        metrics = NetworkMetrics(
            avg_propagation_latency_ms=avg_latency_ms,
            total_messages_propagated=total_messages,
            active_peers=active_peers,
            failed_messages=failed_messages,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Reset accumulators for next cycle
        self.propagation_latencies = []
        self.failed_messages_count = 0
        self.total_messages_received = 0
        
        return metrics
    
    
    def record_message_propagation(self, message_created_at: float):
        """
        Registra la latenza di propagazione di un messaggio.
        Chiamata ogni volta che un messaggio viene ricevuto via gossip.
        
        Args:
            message_created_at: Timestamp di creazione del messaggio (Unix time)
        """
        now = time.time()
        latency_seconds = now - message_created_at
        latency_ms = latency_seconds * 1000
        
        self.propagation_latencies.append(latency_ms)
        self.total_messages_received += 1
        
        # Keep only last 1000 measurements to avoid memory bloat
        if len(self.propagation_latencies) > 1000:
            self.propagation_latencies = self.propagation_latencies[-1000:]
    
    
    def record_message_failure(self):
        """Registra un fallimento nella propagazione di un messaggio"""
        self.failed_messages_count += 1
    
    
    # ========================================================================
    # HEALTH DIAGNOSIS
    # ========================================================================
    
    def diagnose_health_issues(self, metrics: NetworkMetrics) -> List[HealthIssue]:
        """
        Analizza le metriche e identifica problemi di salute.
        
        Args:
            metrics: Snapshot delle metriche correnti
            
        Returns:
            Lista di HealthIssue rilevati
        """
        issues: List[HealthIssue] = []
        targets = self.health_targets
        
        # Check 1: High propagation latency
        if metrics.avg_propagation_latency_ms > targets["max_avg_propagation_latency_ms"]:
            severity = self._calculate_severity(
                metrics.avg_propagation_latency_ms,
                targets["max_avg_propagation_latency_ms"],
                multiplier=1.5
            )
            
            issue = HealthIssue(
                issue_type="high_latency",
                severity=severity,
                current_value=metrics.avg_propagation_latency_ms,
                target_value=targets["max_avg_propagation_latency_ms"],
                recommended_action="increase_gossip_peers",
                description=f"Average message propagation latency ({metrics.avg_propagation_latency_ms:.1f}ms) exceeds target ({targets['max_avg_propagation_latency_ms']}ms)",
                detected_at=datetime.now(timezone.utc).isoformat()
            )
            issues.append(issue)
            self.active_issues["high_latency"] = issue
        
        # Check 2: Low peer connectivity
        if metrics.active_peers < targets["min_active_peers"]:
            issue = HealthIssue(
                issue_type="low_connectivity",
                severity="high",
                current_value=float(metrics.active_peers),
                target_value=float(targets["min_active_peers"]),
                recommended_action="expand_discovery",
                description=f"Active peer count ({metrics.active_peers}) below minimum threshold ({targets['min_active_peers']})",
                detected_at=datetime.now(timezone.utc).isoformat()
            )
            issues.append(issue)
            self.active_issues["low_connectivity"] = issue
        
        # Check 3: High message failure rate
        if metrics.total_messages_propagated > 0:
            failure_rate = metrics.failed_messages / metrics.total_messages_propagated
            if failure_rate > targets["max_failed_message_rate"]:
                issue = HealthIssue(
                    issue_type="message_loss",
                    severity="medium",
                    current_value=failure_rate,
                    target_value=targets["max_failed_message_rate"],
                    recommended_action="increase_retry_attempts",
                    description=f"Message failure rate ({failure_rate:.2%}) exceeds target ({targets['max_failed_message_rate']:.2%})",
                    detected_at=datetime.now(timezone.utc).isoformat()
                )
                issues.append(issue)
                self.active_issues["message_loss"] = issue
        
        return issues
    
    
    def _calculate_severity(self, current: float, target: float, multiplier: float = 2.0) -> str:
        """
        Calcola la severità di un problema basandosi sulla deviazione dal target.
        
        Args:
            current: Valore corrente
            target: Valore target
            multiplier: Moltiplicatore per livelli di severità
            
        Returns:
            "low", "medium", "high", o "critical"
        """
        ratio = current / target
        
        if ratio < 1.2:
            return "low"
        elif ratio < 1.5:
            return "medium"
        elif ratio < 2.0:
            return "high"
        else:
            return "critical"
    
    
    # ========================================================================
    # REMEDY PROPOSAL
    # ========================================================================
    
    async def propose_remedy(self, issue: HealthIssue):
        """
        Genera e sottomette autonomamente una proposta di governance
        per risolvere un problema di salute.
        
        Args:
            issue: Il problema di salute rilevato
        """
        # Check if we already have a pending proposal for this issue type
        if issue.issue_type in self.pending_remedy_proposals:
            existing_proposal_id = self.pending_remedy_proposals[issue.issue_type]
            logger.info(f"[ImmuneSystem] Issue {issue.issue_type} already has pending proposal {existing_proposal_id}")
            return
        
        # Generate remedy based on recommended action
        remedy = self._generate_remedy(issue)
        
        if not remedy:
            logger.warning(f"[ImmuneSystem] Could not generate remedy for issue {issue.issue_type}")
            return
        
        # Create governance proposal
        proposal_id = await self._submit_governance_proposal(remedy)
        
        if proposal_id:
            self.pending_remedy_proposals[issue.issue_type] = proposal_id
            logger.info(f"[ImmuneSystem] Successfully proposed remedy: proposal_id={proposal_id}")
    
    
    def _generate_remedy(self, issue: HealthIssue) -> Optional[ProposedRemedy]:
        """
        Genera una proposta di rimedio basata sul tipo di problema.
        
        Args:
            issue: Il problema da risolvere
            
        Returns:
            ProposedRemedy o None se non può generare un rimedio
        """
        config_changes = {}
        expected_improvement = ""
        
        if issue.issue_type == "high_latency" and issue.recommended_action == "increase_gossip_peers":
            # Increase max gossip peers
            current_max = self.network_state.get("global", {}).get("config", {}).get("max_gossip_peers", 5)
            new_max = current_max + 2
            
            config_changes = {
                "max_gossip_peers": new_max
            }
            
            expected_improvement = f"Increasing gossip peer limit from {current_max} to {new_max} should reduce propagation latency by improving message redundancy and routing efficiency."
        
        elif issue.issue_type == "low_connectivity" and issue.recommended_action == "expand_discovery":
            # Increase discovery frequency
            current_interval = self.network_state.get("global", {}).get("config", {}).get("discovery_interval_seconds", 30)
            new_interval = max(10, current_interval - 10)
            
            config_changes = {
                "discovery_interval_seconds": new_interval
            }
            
            expected_improvement = f"Reducing discovery interval from {current_interval}s to {new_interval}s should help find and connect to more peers faster."
        
        elif issue.issue_type == "message_loss" and issue.recommended_action == "increase_retry_attempts":
            # Increase retry attempts
            current_retries = self.network_state.get("global", {}).get("config", {}).get("max_message_retries", 3)
            new_retries = current_retries + 2
            
            config_changes = {
                "max_message_retries": new_retries
            }
            
            expected_improvement = f"Increasing retry attempts from {current_retries} to {new_retries} should reduce message loss by providing more opportunities for successful delivery."
        
        else:
            logger.warning(f"[ImmuneSystem] Unknown remedy action: {issue.recommended_action}")
            return None
        
        # Generate proposal title and description
        title = f"[IMMUNE SYSTEM] Corrective Action: {issue.issue_type.replace('_', ' ').title()}"
        
        description = f"""**Automated Health Diagnosis**

The Immune System has detected a network health issue requiring attention:

**Issue Type**: {issue.issue_type}
**Severity**: {issue.severity}
**Current Value**: {issue.current_value:.2f}
**Target Value**: {issue.target_value:.2f}

**Problem Description**:
{issue.description}

**Proposed Solution**:
{expected_improvement}

**Configuration Changes**:
```json
{config_changes}
```

This is an automated configuration proposal generated by the network's immune system to maintain optimal health and performance.

**Detected At**: {issue.detected_at}
**Proposed By**: Node {self.node_id} (Immune System)
"""
        
        remedy = ProposedRemedy(
            issue_type=issue.issue_type,
            proposal_title=title,
            proposal_description=description,
            config_changes=config_changes,
            expected_improvement=expected_improvement,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        return remedy
    
    
    async def _submit_governance_proposal(self, remedy: ProposedRemedy) -> Optional[str]:
        """
        Sottomette una proposta di governance per applicare il rimedio.
        
        Args:
            remedy: Il rimedio proposto
            
        Returns:
            proposal_id se successo, None altrimenti
        """
        try:
            import uuid
            
            proposal_id = str(uuid.uuid4())
            
            # Construct proposal object
            proposal = {
                "id": proposal_id,
                "title": remedy.proposal_title,
                "description": remedy.proposal_description,
                "proposal_type": "config_change",
                "params": {
                    "config_changes": remedy.config_changes
                },
                "tags": ["immune_system", "automated", remedy.issue_type],
                "author": self.node_id,
                "created_at": remedy.created_at,
                "votes": {},
                "status": "open",
                "closes_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                "vote_count": {"yes": 0, "no": 0, "abstain": 0},
                "result": None
            }
            
            # Add to network state
            if "global" not in self.network_state:
                self.network_state["global"] = {}
            if "proposals" not in self.network_state["global"]:
                self.network_state["global"]["proposals"] = {}
            
            self.network_state["global"]["proposals"][proposal_id] = proposal
            
            # Broadcast proposal via gossip
            if self.pubsub_manager:
                message_payload = {
                    "action": "proposal_created",
                    "proposal": proposal
                }
                await self.pubsub_manager.publish("global", message_payload)
            
            logger.info(f"[ImmuneSystem] Proposal {proposal_id} submitted successfully")
            return proposal_id
            
        except Exception as e:
            logger.error(f"[ImmuneSystem] Failed to submit proposal: {e}", exc_info=True)
            return None
    
    
    def _check_remedy_outcomes(self):
        """
        Verifica se i rimedi proposti in precedenza sono stati applicati
        e se hanno migliorato la situazione.
        """
        for issue_type, proposal_id in list(self.pending_remedy_proposals.items()):
            proposal = self.network_state.get("global", {}).get("proposals", {}).get(proposal_id)
            
            if not proposal:
                # Proposal not found, remove from pending
                del self.pending_remedy_proposals[issue_type]
                continue
            
            status = proposal.get("status")
            
            if status == "approved":
                # Proposal was approved and executed
                logger.info(f"[ImmuneSystem] Remedy for {issue_type} was approved (proposal {proposal_id})")
                
                # Clear the issue and pending proposal
                if issue_type in self.active_issues:
                    del self.active_issues[issue_type]
                del self.pending_remedy_proposals[issue_type]
                
            elif status == "rejected":
                # Proposal was rejected
                logger.warning(f"[ImmuneSystem] Remedy for {issue_type} was rejected (proposal {proposal_id})")
                
                # Clear pending but keep issue active for potential re-proposal
                del self.pending_remedy_proposals[issue_type]


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_immune_system_manager: Optional[ImmuneSystemManager] = None


def initialize_immune_system(node_id: str, network_state: Dict, pubsub_manager) -> ImmuneSystemManager:
    """
    Inizializza il sistema immunitario globale.
    
    Args:
        node_id: ID del nodo corrente
        network_state: Riferimento al network state globale
        pubsub_manager: Manager PubSub per broadcasting proposte
        
    Returns:
        ImmuneSystemManager inizializzato
    """
    global _immune_system_manager
    
    if _immune_system_manager is None:
        _immune_system_manager = ImmuneSystemManager(node_id, network_state, pubsub_manager)
        logger.info(f"[ImmuneSystem] Global instance initialized for node {node_id}")
    
    return _immune_system_manager


def get_immune_system() -> Optional[ImmuneSystemManager]:
    """Ottiene l'istanza globale del sistema immunitario"""
    return _immune_system_manager


def is_immune_system_enabled() -> bool:
    """Verifica se il sistema immunitario è abilitato e disponibile"""
    return _immune_system_manager is not None and _immune_system_manager.running
