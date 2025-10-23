/**
 * health-monitor.js - Homeostatic System (Panel 1) visualization
 * 
 * Displays vital signs, active diagnoses, and autonomous remedy proposals
 */

class HealthMonitor {
    constructor(api) {
        this.api = api;
        this.initialized = false;
    }

    /**
     * Initialize the health monitor
     */
    init() {
        if (this.initialized) return;

        // Listen for state updates
        this.api.on('state-updated', (state) => {
            this.update();
        });

        this.initialized = true;
        console.log('[HealthMonitor] Initialized');
    }

    /**
     * Update all health visualizations
     */
    update() {
        this.updateVitalSigns();
        this.updateDiagnoses();
        this.updateImmuneProposals();
    }

    /**
     * Update vital signs cards with traffic light indicators
     */
    updateVitalSigns() {
        const metrics = this.api.getHealthMetrics();
        
        if (!metrics) {
            console.warn('[HealthMonitor] No health metrics available');
            return;
        }

        // Latency
        this.updateVitalCard('latency', {
            value: metrics.latency,
            target: metrics.targets.max_latency_ms || 5000,
            unit: 'ms',
            lowerIsBetter: true
        });

        // Peers
        this.updateVitalCard('peers', {
            value: metrics.peers,
            target: metrics.targets.min_peers || 3,
            unit: '',
            lowerIsBetter: false
        });

        // Consensus
        this.updateVitalCard('consensus', {
            value: metrics.consensus,
            target: metrics.targets.max_consensus_time_ms || 10000,
            unit: 'ms',
            lowerIsBetter: true
        });

        // Messages
        this.updateVitalCard('messages', {
            value: metrics.messageSuccess * 100,
            target: (metrics.targets.min_message_success_rate || 0.95) * 100,
            unit: '%',
            lowerIsBetter: false
        });
    }

    /**
     * Update a single vital card with status indicator
     */
    updateVitalCard(metric, config) {
        const valueEl = document.getElementById(`${metric}Value`);
        const targetEl = document.getElementById(`${metric}Target`);
        const statusEl = document.getElementById(`${metric}Status`);
        const cardEl = document.querySelector(`.vital-card[data-metric="${metric}"]`);

        if (!valueEl || !targetEl || !statusEl || !cardEl) {
            console.warn(`[HealthMonitor] Elements not found for metric: ${metric}`);
            return;
        }

        // Update value
        const displayValue = config.unit === '%' 
            ? config.value.toFixed(1) 
            : Math.round(config.value);
        valueEl.textContent = `${displayValue} ${config.unit}`;

        // Update target
        const displayTarget = config.unit === '%'
            ? config.target.toFixed(0)
            : Math.round(config.target);
        targetEl.textContent = `Target: ${displayTarget} ${config.unit}`;

        // Calculate status (traffic light)
        const status = this.calculateStatus(config.value, config.target, config.lowerIsBetter);
        
        // Remove old status classes
        cardEl.classList.remove('status-healthy', 'status-warning', 'status-critical');
        
        // Add new status class
        cardEl.classList.add(`status-${status}`);
    }

    /**
     * Calculate traffic light status
     * Returns: 'healthy', 'warning', or 'critical'
     */
    calculateStatus(value, target, lowerIsBetter) {
        if (lowerIsBetter) {
            // For metrics where lower is better (latency, etc.)
            const ratio = value / target;
            if (ratio <= 1.0) return 'healthy';      // At or below target
            if (ratio <= 1.5) return 'warning';      // 50% above target
            return 'critical';                        // More than 50% above
        } else {
            // For metrics where higher is better (peers, message rate)
            const ratio = value / target;
            if (ratio >= 1.0) return 'healthy';      // At or above target
            if (ratio >= 0.7) return 'warning';      // 30% below target
            return 'critical';                        // More than 30% below
        }
    }

    /**
     * Update active diagnoses list
     */
    updateDiagnoses() {
        const diagnoses = this.api.getDiagnoses();
        const container = document.getElementById('diagnosesContainer');

        if (!container) return;

        if (diagnoses.length === 0) {
            container.innerHTML = '<div class="empty-state">No health issues detected - Organism is healthy</div>';
            return;
        }

        container.innerHTML = diagnoses.map(issue => 
            this.createDiagnosisCard(issue)
        ).join('');
    }

    /**
     * Create a diagnosis card HTML
     */
    createDiagnosisCard(issue) {
        const severity = issue.severity || 'medium';
        const issueType = this.formatIssueType(issue.issue_type);
        const description = issue.description || 'No description available';
        
        // Calculate metrics display
        const current = issue.current_value?.toFixed?.(2) || issue.current_value || 'N/A';
        const target = issue.target_value?.toFixed?.(2) || issue.target_value || 'N/A';
        
        // Determine status text
        const statusText = this.getIssueStatus(issue);
        
        // Get affected component if available
        const component = issue.affected_component || 'unknown';
        const source = issue.issue_source || 'config';

        return `
            <div class="diagnosis-card severity-${severity}">
                <div class="diagnosis-header">
                    <div class="diagnosis-type">${issueType}</div>
                    <div class="diagnosis-severity severity-${severity}">${severity}</div>
                </div>
                <div class="diagnosis-description">${description}</div>
                <div class="diagnosis-metrics">
                    <div class="diagnosis-metric">
                        <span>Current:</span> <strong>${current}</strong>
                    </div>
                    <div class="diagnosis-metric">
                        <span>Target:</span> <strong>${target}</strong>
                    </div>
                    <div class="diagnosis-metric">
                        <span>Component:</span> <strong>${component}</strong>
                    </div>
                    <div class="diagnosis-metric">
                        <span>Source:</span> <strong>${source}</strong>
                    </div>
                </div>
                <div class="diagnosis-status">${statusText}</div>
            </div>
        `;
    }

    /**
     * Format issue type for display
     */
    formatIssueType(type) {
        return type
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Get issue status text
     */
    getIssueStatus(issue) {
        const action = issue.recommended_action || 'monitoring';
        
        const statusMap = {
            'adjust_config': 'Proposing config adjustment',
            'generate_optimized_code': '🧬 Generating algorithmic solution',
            'scale_resources': 'Proposing resource scaling',
            'monitoring': 'Under observation'
        };

        return statusMap[action] || 'Processing';
    }

    /**
     * Update immune system proposals
     */
    updateImmuneProposals() {
        const proposals = this.api.getImmuneProposals();
        const container = document.getElementById('immuneProposalsContainer');

        if (!container) return;

        if (proposals.length === 0) {
            container.innerHTML = '<div class="empty-state">No autonomous remedies proposed</div>';
            return;
        }

        container.innerHTML = proposals.map(proposal => 
            this.createImmuneProposalCard(proposal)
        ).join('');
    }

    /**
     * Create immune proposal card HTML
     */
    createImmuneProposalCard(proposal) {
        const title = proposal.title || 'Unnamed Remedy';
        const description = proposal.description || '';
        const status = proposal.status || 'open';
        const votes = proposal.vote_count || 0;
        const type = proposal.proposal_type || 'config';

        return `
            <div class="immune-proposal-card" onclick="showProposalDetails('${proposal.id}')">
                <div class="immune-proposal-header">
                    <div class="immune-proposal-title">${this.escapeHtml(title)}</div>
                    <div class="immune-proposal-badge">${status}</div>
                </div>
                <div class="immune-proposal-description">
                    ${this.escapeHtml(this.truncate(description, 150))}
                </div>
                <div class="immune-proposal-footer">
                    <span>Type: ${type}</span>
                    <span>Votes: ${votes}</span>
                </div>
            </div>
        `;
    }

    /**
     * Utility: Truncate text
     */
    truncate(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Utility: Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in main.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HealthMonitor;
}
