/**
 * evolution-monitor.js - Evolutionary Genome (Panel 3) visualization
 * 
 * Displays code upgrade timeline, evolution statistics, and generated solutions
 */

class EvolutionMonitor {
    constructor(api) {
        this.api = api;
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;

        this.api.on('state-updated', (state) => {
            this.update();
        });

        this.initialized = true;
        console.log('[EvolutionMonitor] Initialized');
    }

    update() {
        this.updateTimeline();
        this.updateStatistics();
        this.updateSolutions();
    }

    updateTimeline() {
        const codeUpgrades = this.api.getCodeUpgradeProposals();
        const container = document.getElementById('evolutionTimeline');

        if (!container) return;

        if (codeUpgrades.length === 0) {
            container.innerHTML = '<div class="empty-state">No code upgrades proposed yet</div>';
            return;
        }

        // Sort by date (newest first)
        codeUpgrades.sort((a, b) => {
            const dateA = new Date(a.created_at || 0);
            const dateB = new Date(b.created_at || 0);
            return dateB - dateA;
        });

        container.innerHTML = codeUpgrades.map(proposal => 
            this.createTimelineEvent(proposal)
        ).join('');
    }

    createTimelineEvent(proposal) {
        const title = proposal.title || 'Code Upgrade';
        const description = proposal.description || '';
        const status = proposal.status || 'open';
        const date = new Date(proposal.created_at || Date.now());
        
        // Extract improvement from params if available
        const improvement = proposal.params?.estimated_improvement || null;
        const component = proposal.params?.target_component || 'unknown';
        
        // Determine event status class
        const statusClass = this.getEventStatusClass(status);
        
        // Format date
        const formattedDate = this.formatDate(date);

        return `
            <div class="timeline-event event-${statusClass}">
                <div class="timeline-event-card" onclick="showCodeUpgradeDetails('${proposal.id}')">
                    <div class="timeline-event-header">
                        <div class="timeline-event-title">${this.escapeHtml(title)}</div>
                        <div class="timeline-event-date">${formattedDate}</div>
                    </div>
                    <div class="timeline-event-description">
                        <strong>Component:</strong> ${component}<br>
                        ${this.extractFirstLine(description)}
                    </div>
                    ${improvement ? this.renderImpact(improvement) : ''}
                </div>
            </div>
        `;
    }

    getEventStatusClass(status) {
        const mapping = {
            'executed': 'approved',
            'rejected': 'rejected',
            'open': 'pending',
            'voting': 'pending',
            'ratifying': 'pending'
        };
        return mapping[status] || 'pending';
    }

    renderImpact(improvement) {
        const isPositive = improvement > 0;
        const className = isPositive ? 'timeline-event-impact' : 'timeline-event-impact negative';
        const symbol = isPositive ? '↑' : '↓';
        
        return `
            <div class="${className}">
                ${symbol} ${Math.abs(improvement).toFixed(1)}% performance change
            </div>
        `;
    }

    updateStatistics() {
        const stats = this.api.getEvolutionStats();
        
        document.getElementById('totalGenerations').textContent = stats.total_generations || 0;
        document.getElementById('successfulCompilations').textContent = stats.successful_compilations || 0;
        
        const successRate = stats.total_generations > 0
            ? ((stats.successful_compilations / stats.total_generations) * 100).toFixed(1)
            : 0;
        document.getElementById('successRate').textContent = `${successRate}%`;
        
        // Count applied upgrades
        const codeUpgrades = this.api.getCodeUpgradeProposals();
        const applied = codeUpgrades.filter(p => p.status === 'executed').length;
        document.getElementById('appliedUpgrades').textContent = applied;
    }

    updateSolutions() {
        const codeUpgrades = this.api.getCodeUpgradeProposals();
        const container = document.getElementById('solutionsList');

        if (!container) return;

        // Filter for pending review (open/voting status)
        const pending = codeUpgrades.filter(p => 
            p.status === 'open' || p.status === 'voting'
        );

        if (pending.length === 0) {
            container.innerHTML = '<div class="empty-state">No generated solutions pending review</div>';
            return;
        }

        container.innerHTML = pending.map(proposal => 
            this.createSolutionCard(proposal)
        ).join('');
    }

    createSolutionCard(proposal) {
        const title = proposal.title || 'Generated Solution';
        const component = proposal.params?.target_component || 'unknown';
        const wasmSize = proposal.params?.wasm_size_bytes || 0;
        const wasmHash = proposal.params?.wasm_hash || 'N/A';
        const improvement = proposal.params?.estimated_improvement || 0;

        return `
            <div class="solution-card" onclick="showCodeViewer('${proposal.id}')">
                <div class="solution-card-header">
                    <div class="solution-card-title">${this.escapeHtml(title)}</div>
                    <div class="solution-card-component">${component}</div>
                </div>
                <div class="solution-card-description">
                    Proposed solution for chronic performance issue
                </div>
                <div class="solution-card-metrics">
                    <span>WASM Size: ${this.formatBytes(wasmSize)}</span>
                    <span>Hash: ${wasmHash.substring(0, 12)}...</span>
                    <span>Est. Improvement: ${improvement.toFixed(1)}%</span>
                </div>
                <div class="solution-card-action">
                    <button class="btn-secondary" onclick="event.stopPropagation(); showCodeViewer('${proposal.id}')">
                        View Code
                    </button>
                </div>
            </div>
        `;
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return `${seconds}s ago`;
    }

    extractFirstLine(text) {
        const lines = text.split('\n');
        const firstNonEmpty = lines.find(line => line.trim().length > 0);
        return this.escapeHtml(firstNonEmpty || '').substring(0, 150);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = EvolutionMonitor;
}
