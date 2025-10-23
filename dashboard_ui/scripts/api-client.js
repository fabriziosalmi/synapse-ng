/**
 * api-client.js - API client for connecting to Synapse-NG node
 * 
 * This module handles all communication with the Synapse-NG /state endpoint
 * and provides a clean interface for other modules to access network data.
 */

class SynapseAPI {
    constructor() {
        this.endpoint = 'http://localhost:8000';
        this.connected = false;
        this.lastState = null;
        this.lastUpdate = null;
        this.updateInterval = null;
        this.pollingRate = 10000; // 10 seconds
        this.listeners = new Map();
    }

    /**
     * Set the node endpoint and attempt connection
     */
    setEndpoint(endpoint) {
        this.endpoint = endpoint.replace(/\/$/, ''); // Remove trailing slash
        return this.connect();
    }

    /**
     * Connect to the node and start polling
     */
    async connect() {
        console.log(`[API] Attempting to connect to ${this.endpoint}...`);
        
        try {
            const state = await this.fetchState();
            this.connected = true;
            this.lastState = state;
            this.lastUpdate = new Date();
            
            console.log('[API] ✓ Connected successfully');
            this.emit('connected', state);
            
            // Start polling
            this.startPolling();
            
            return true;
        } catch (error) {
            console.error('[API] ✗ Connection failed:', error);
            this.connected = false;
            this.emit('disconnected', error);
            return false;
        }
    }

    /**
     * Disconnect from the node and stop polling
     */
    disconnect() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        this.connected = false;
        console.log('[API] Disconnected');
        this.emit('disconnected');
    }

    /**
     * Start polling the /state endpoint
     */
    startPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(async () => {
            if (this.connected) {
                await this.update();
            }
        }, this.pollingRate);

        console.log(`[API] Polling started (every ${this.pollingRate}ms)`);
    }

    /**
     * Manually trigger an update
     */
    async update() {
        try {
            const state = await this.fetchState();
            this.lastState = state;
            this.lastUpdate = new Date();
            this.emit('state-updated', state);
            return state;
        } catch (error) {
            console.error('[API] Failed to update state:', error);
            this.connected = false;
            this.emit('disconnected', error);
            throw error;
        }
    }

    /**
     * Fetch the /state endpoint
     */
    async fetchState() {
        const response = await fetch(`${this.endpoint}/state`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data;
    }

    /**
     * Get current node ID
     */
    getNodeId() {
        return this.lastState?.node_id || 'unknown';
    }

    /**
     * Get health metrics
     */
    getHealthMetrics() {
        if (!this.lastState?.global?.immune_system) {
            return null;
        }

        const immune = this.lastState.global.immune_system;
        return {
            latency: immune.health_metrics?.avg_propagation_latency_ms || 0,
            peers: immune.health_metrics?.active_peers || 0,
            consensus: immune.health_metrics?.avg_consensus_time_ms || 0,
            messageSuccess: immune.health_metrics?.message_success_rate || 0,
            targets: immune.health_targets || {}
        };
    }

    /**
     * Get active diagnoses
     */
    getDiagnoses() {
        if (!this.lastState?.global?.immune_system?.active_issues) {
            return [];
        }

        return this.lastState.global.immune_system.active_issues;
    }

    /**
     * Get all governance proposals
     */
    getProposals() {
        if (!this.lastState?.global?.proposals) {
            return [];
        }

        return Object.values(this.lastState.global.proposals);
    }

    /**
     * Get proposals by status
     */
    getProposalsByStatus(status) {
        const proposals = this.getProposals();
        return proposals.filter(p => p.status === status);
    }

    /**
     * Get immune system proposals (autonomous remedies)
     */
    getImmuneProposals() {
        const proposals = this.getProposals();
        return proposals.filter(p => 
            p.title && (
                p.title.includes('Immune System') || 
                p.title.includes('Health') ||
                p.title.includes('Remedy')
            )
        );
    }

    /**
     * Get code upgrade proposals
     */
    getCodeUpgradeProposals() {
        const proposals = this.getProposals();
        return proposals.filter(p => p.proposal_type === 'code_upgrade');
    }

    /**
     * Get proposal by ID
     */
    getProposal(proposalId) {
        const proposals = this.getProposals();
        return proposals.find(p => p.id === proposalId);
    }

    /**
     * Get treasury balances
     */
    getTreasury() {
        if (!this.lastState?.global?.treasury) {
            return {};
        }

        return this.lastState.global.treasury;
    }

    /**
     * Get reputation for a node
     */
    getReputation(nodeId) {
        if (!this.lastState?.global?.reputation) {
            return null;
        }

        const rep = this.lastState.global.reputation[nodeId];
        if (!rep) {
            return null;
        }

        return {
            nodeId: nodeId,
            total: rep.total_reputation || 0,
            specializations: rep.specializations || {}
        };
    }

    /**
     * Get evolutionary engine statistics (if available)
     */
    getEvolutionStats() {
        if (!this.lastState?.global?.evolutionary_engine) {
            return {
                total_generations: 0,
                successful_compilations: 0,
                failed_compilations: 0,
                success_rate: 0
            };
        }

        return this.lastState.global.evolutionary_engine;
    }

    /**
     * Calculate contextual vote weight for a node on a proposal
     */
    calculateVoteWeight(nodeId, proposal) {
        const reputation = this.getReputation(nodeId);
        
        if (!reputation) {
            return {
                error: true,
                message: `Node ${nodeId} not found in reputation system`
            };
        }

        // Base weight (1.0 for any participant)
        const baseWeight = 1.0;

        // Calculate bonus weight from specializations
        let bonusWeight = 0;
        const relevantSpecializations = [];

        if (proposal.tags && proposal.tags.length > 0) {
            for (const tag of proposal.tags) {
                const specValue = reputation.specializations[tag] || 0;
                if (specValue > 0) {
                    bonusWeight += specValue;
                    relevantSpecializations.push({
                        tag: tag,
                        value: specValue
                    });
                }
            }
        }

        const totalWeight = baseWeight + bonusWeight;
        const influenceIncrease = bonusWeight > 0 ? (bonusWeight / baseWeight) * 100 : 0;

        return {
            error: false,
            nodeId: nodeId,
            totalReputation: reputation.total,
            baseWeight: baseWeight,
            bonusWeight: bonusWeight,
            totalWeight: totalWeight,
            influenceIncrease: influenceIncrease,
            relevantSpecializations: relevantSpecializations,
            allSpecializations: reputation.specializations
        };
    }

    /**
     * Event listener system
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    off(event, callback) {
        if (!this.listeners.has(event)) return;
        const callbacks = this.listeners.get(event);
        const index = callbacks.indexOf(callback);
        if (index > -1) {
            callbacks.splice(index, 1);
        }
    }

    emit(event, data) {
        if (!this.listeners.has(event)) return;
        const callbacks = this.listeners.get(event);
        callbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[API] Error in ${event} listener:`, error);
            }
        });
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.connected;
    }

    /**
     * Get last update time
     */
    getLastUpdate() {
        return this.lastUpdate;
    }

    /**
     * Get raw state (for debugging)
     */
    getRawState() {
        return this.lastState;
    }
}

// Create global instance
const synapseAPI = new SynapseAPI();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = synapseAPI;
}
