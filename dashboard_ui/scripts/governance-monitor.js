/**
 * governance-monitor.js - Nervous System (Panel 2) visualization
 * 
 * Displays governance proposals in kanban format and treasury status
 */

class GovernanceMonitor {
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
        console.log('[GovernanceMonitor] Initialized');
    }

    update() {
        this.updateKanban();
        this.updateTreasury();
    }

    updateKanban() {
        const statuses = ['open', 'voting', 'ratifying', 'executed', 'rejected'];
        
        statuses.forEach(status => {
            let proposals;
            if (status === 'executed' || status === 'rejected') {
                proposals = this.api.getProposalsByStatus(status);
                this.updateKanbanColumn('closed', proposals, status);
            } else {
                proposals = this.api.getProposalsByStatus(status);
                this.updateKanbanColumn(status, proposals);
            }
        });
    }

    updateKanbanColumn(columnId, proposals, secondaryStatus = null) {
        const container = document.getElementById(`${columnId}Proposals`);
        const countEl = document.getElementById(`${columnId}Count`);

        if (!container) return;

        // Handle closed column (executed + rejected)
        if (columnId === 'closed') {
            const executed = this.api.getProposalsByStatus('executed');
            const rejected = this.api.getProposalsByStatus('rejected');
            proposals = [...executed, ...rejected];
        }

        if (countEl) {
            countEl.textContent = proposals.length;
        }

        if (proposals.length === 0) {
            container.innerHTML = '<div class="empty-state" style="padding: var(--spacing-md); font-size: 12px;">No proposals</div>';
            return;
        }

        container.innerHTML = proposals.map(p => this.createProposalCard(p)).join('');
    }

    createProposalCard(proposal) {
        const title = proposal.title || 'Unnamed Proposal';
        const type = proposal.proposal_type || 'config';
        const votes = proposal.vote_count || 0;
        const quorum = proposal.quorum_required || 1;
        const voteProgress = (votes / quorum) * 100;
        
        // Tags
        const tags = proposal.tags || [];
        const tagsHtml = tags.slice(0, 3).map(tag => 
            `<span class="proposal-tag">${tag}</span>`
        ).join('');

        return `
            <div class="proposal-card" onclick="showProposalDetails('${proposal.id}')">
                <div class="proposal-card-header">
                    <div class="proposal-card-title">${this.escapeHtml(title)}</div>
                    <div class="proposal-card-type type-${type}">${type}</div>
                </div>
                <div class="proposal-card-meta">
                    Proposer: ${proposal.proposer || 'Unknown'}
                </div>
                <div class="proposal-card-votes">
                    <div class="vote-bar">
                        <div class="vote-bar-fill" style="width: ${Math.min(voteProgress, 100)}%"></div>
                    </div>
                    <span>${votes}/${quorum} votes</span>
                </div>
                ${tags.length > 0 ? `<div class="proposal-card-tags">${tagsHtml}</div>` : ''}
            </div>
        `;
    }

    updateTreasury() {
        const treasury = this.api.getTreasury();
        const container = document.getElementById('treasuryChannels');

        if (!container) return;

        const channels = Object.keys(treasury);

        if (channels.length === 0) {
            container.innerHTML = '<div class="empty-state">No treasury data available</div>';
            return;
        }

        container.innerHTML = channels.map(channel => {
            const balance = treasury[channel] || 0;
            return `
                <div class="treasury-channel">
                    <div class="treasury-channel-name">${channel}</div>
                    <div class="treasury-channel-balance">${balance.toFixed(2)}</div>
                    <div class="treasury-channel-label">SYNAPSE</div>
                </div>
            `;
        }).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = GovernanceMonitor;
}
