/**
 * vote-simulator.js - Contextual Vote Weight Calculator
 * 
 * Simulates how a node's vote weight is calculated based on their reputation
 * and specializations relative to a proposal's tags
 */

class VoteSimulator {
    constructor(api) {
        this.api = api;
        this.currentProposal = null;
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;

        // Setup modal controls
        const closeBtn = document.getElementById('closeVoteSimulator');
        const calculateBtn = document.getElementById('calculateVoteWeight');
        const modal = document.getElementById('voteSimulatorModal');

        if (closeBtn) {
            closeBtn.onclick = () => this.close();
        }

        if (calculateBtn) {
            calculateBtn.onclick = () => this.calculate();
        }

        if (modal) {
            modal.onclick = (e) => {
                if (e.target === modal) this.close();
            };
        }

        this.initialized = true;
        console.log('[VoteSimulator] Initialized');
    }

    /**
     * Open simulator for a specific proposal
     */
    open(proposalId) {
        const proposal = this.api.getProposal(proposalId);
        
        if (!proposal) {
            console.error('[VoteSimulator] Proposal not found:', proposalId);
            return;
        }

        this.currentProposal = proposal;
        
        const modal = document.getElementById('voteSimulatorModal');
        if (modal) {
            modal.classList.add('active');
        }

        // Clear previous results
        document.getElementById('simulatorResults').innerHTML = '';
        
        // Pre-fill with current node ID if available
        const nodeId = this.api.getNodeId();
        if (nodeId && nodeId !== 'unknown') {
            document.getElementById('voterNodeId').value = nodeId;
        }
    }

    /**
     * Close simulator
     */
    close() {
        const modal = document.getElementById('voteSimulatorModal');
        if (modal) {
            modal.classList.remove('active');
        }
        this.currentProposal = null;
    }

    /**
     * Calculate vote weight for entered node ID
     */
    calculate() {
        const nodeId = document.getElementById('voterNodeId').value.trim();
        const resultsContainer = document.getElementById('simulatorResults');

        if (!nodeId) {
            resultsContainer.innerHTML = `
                <div class="simulator-error">
                    Please enter a node ID
                </div>
            `;
            return;
        }

        if (!this.currentProposal) {
            resultsContainer.innerHTML = `
                <div class="simulator-error">
                    No proposal selected
                </div>
            `;
            return;
        }

        // Calculate weight
        const result = this.api.calculateVoteWeight(nodeId, this.currentProposal);

        if (result.error) {
            resultsContainer.innerHTML = `
                <div class="simulator-error">
                    ${result.message}
                </div>
            `;
            return;
        }

        // Render results
        resultsContainer.innerHTML = this.renderResults(result);
    }

    /**
     * Render calculation results
     */
    renderResults(result) {
        const { 
            nodeId, 
            totalReputation, 
            baseWeight, 
            bonusWeight, 
            totalWeight, 
            influenceIncrease,
            relevantSpecializations,
            allSpecializations
        } = result;

        // Build specializations HTML
        const specsHtml = relevantSpecializations.length > 0
            ? relevantSpecializations.map(spec => `
                <div class="simulator-specialization">
                    <div class="simulator-specialization-name">${spec.tag}</div>
                    <div class="simulator-specialization-value">+${spec.value.toFixed(2)}</div>
                </div>
            `).join('')
            : '<div class="empty-state" style="padding: var(--spacing-sm);">No relevant specializations</div>';

        // Build explanation text
        const explanationText = this.buildExplanation(result);

        return `
            <div class="simulator-result-card">
                <h4>Node: ${nodeId}</h4>
                
                <div class="simulator-stat-grid">
                    <div class="simulator-stat">
                        <div class="simulator-stat-label">Total Reputation</div>
                        <div class="simulator-stat-value">${totalReputation.toFixed(0)}</div>
                    </div>
                    <div class="simulator-stat">
                        <div class="simulator-stat-label">Base Weight</div>
                        <div class="simulator-stat-value">${baseWeight.toFixed(2)}</div>
                    </div>
                    <div class="simulator-stat">
                        <div class="simulator-stat-label">Bonus Weight</div>
                        <div class="simulator-stat-value">${bonusWeight.toFixed(2)}</div>
                    </div>
                    <div class="simulator-stat">
                        <div class="simulator-stat-label">Total Weight</div>
                        <div class="simulator-stat-value">${totalWeight.toFixed(2)}</div>
                    </div>
                </div>
                
                ${this.renderProgressBar(baseWeight, bonusWeight, totalWeight)}
                
                <div class="simulator-explanation">
                    <div class="simulator-explanation-text">
                        ${explanationText}
                    </div>
                </div>
            </div>

            <div class="simulator-result-card">
                <h4>Relevant Specializations</h4>
                <div class="simulator-specializations">
                    ${specsHtml}
                </div>
            </div>

            ${this.renderProposalTags()}
        `;
    }

    /**
     * Build human-readable explanation
     */
    buildExplanation(result) {
        const { bonusWeight, influenceIncrease, relevantSpecializations } = result;

        if (bonusWeight === 0) {
            return `
                Your vote has <span class="simulator-explanation-highlight">standard influence</span> 
                on this proposal because you don't have specialized reputation in the proposal's tags.
            `;
        }

        const topSpec = relevantSpecializations[0];
        const specCount = relevantSpecializations.length;

        if (specCount === 1) {
            return `
                Your experience in <span class="simulator-explanation-highlight">'${topSpec.tag}'</span> 
                gives your vote <span class="simulator-explanation-highlight">${influenceIncrease.toFixed(0)}% more influence</span> 
                on this decision.
            `;
        }

        return `
            Your expertise across <span class="simulator-explanation-highlight">${specCount} relevant areas</span> 
            (especially <span class="simulator-explanation-highlight">'${topSpec.tag}'</span>) 
            gives your vote <span class="simulator-explanation-highlight">${influenceIncrease.toFixed(0)}% more influence</span> 
            on this decision.
        `;
    }

    /**
     * Render weight breakdown progress bar
     */
    renderProgressBar(baseWeight, bonusWeight, totalWeight) {
        const basePercent = (baseWeight / totalWeight) * 100;
        const bonusPercent = (bonusWeight / totalWeight) * 100;

        return `
            <div style="margin: var(--spacing-md) 0;">
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">
                    Vote Weight Composition
                </div>
                <div class="progress-bar" style="height: 30px; display: flex;">
                    <div style="width: ${basePercent}%; background: var(--accent-cyan); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600;">
                        Base (${baseWeight.toFixed(2)})
                    </div>
                    <div style="width: ${bonusPercent}%; background: var(--accent-purple); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600;">
                        Bonus (${bonusWeight.toFixed(2)})
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render proposal tags
     */
    renderProposalTags() {
        if (!this.currentProposal.tags || this.currentProposal.tags.length === 0) {
            return '';
        }

        const tagsHtml = this.currentProposal.tags.map(tag => 
            `<span class="proposal-tag-item">${tag}</span>`
        ).join('');

        return `
            <div class="simulator-result-card">
                <h4>Proposal Tags</h4>
                <div class="proposal-tags-list">
                    ${tagsHtml}
                </div>
                <div style="margin-top: var(--spacing-sm); font-size: 12px; color: var(--text-muted);">
                    Your vote weight is boosted if you have reputation in any of these tags.
                </div>
            </div>
        `;
    }
}

// Global function to open vote simulator (called from proposal cards)
function openVoteSimulator(proposalId) {
    if (window.voteSimulator) {
        window.voteSimulator.open(proposalId);
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoteSimulator;
}
