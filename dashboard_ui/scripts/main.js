/**
 * main.js - Main application orchestrator
 * 
 * Initializes all monitors and handles UI interactions
 */

// Global instances
let healthMonitor;
let governanceMonitor;
let evolutionMonitor;
let voteSimulator;

/**
 * Initialize the dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Dashboard] Initializing Organism Consciousness Dashboard...');

    // Initialize monitors
    healthMonitor = new HealthMonitor(synapseAPI);
    governanceMonitor = new GovernanceMonitor(synapseAPI);
    evolutionMonitor = new EvolutionMonitor(synapseAPI);
    voteSimulator = new VoteSimulator(synapseAPI);

    // Make vote simulator globally accessible
    window.voteSimulator = voteSimulator;

    // Initialize all
    healthMonitor.init();
    governanceMonitor.init();
    evolutionMonitor.init();
    voteSimulator.init();

    // Setup connection controls
    setupConnectionControls();

    // Setup modals
    setupModals();

    // Setup API event listeners
    setupAPIListeners();

    // Attempt initial connection
    const endpoint = document.getElementById('nodeEndpoint').value;
    connect(endpoint);

    console.log('[Dashboard] ✓ Initialization complete');
});

/**
 * Setup connection controls
 */
function setupConnectionControls() {
    const connectBtn = document.getElementById('connectBtn');
    const endpointInput = document.getElementById('nodeEndpoint');

    if (connectBtn) {
        connectBtn.onclick = () => {
            const endpoint = endpointInput.value.trim();
            connect(endpoint);
        };
    }

    if (endpointInput) {
        endpointInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                connect(endpointInput.value.trim());
            }
        });
    }
}

/**
 * Connect to node
 */
async function connect(endpoint) {
    const statusIndicator = document.getElementById('connectionStatus');
    const nodeIdDisplay = document.getElementById('nodeId');
    const connectBtn = document.getElementById('connectBtn');

    // Show loading
    if (statusIndicator) {
        statusIndicator.classList.remove('connected', 'disconnected');
    }
    if (nodeIdDisplay) {
        nodeIdDisplay.textContent = 'Connecting...';
    }
    if (connectBtn) {
        connectBtn.disabled = true;
        connectBtn.textContent = 'Connecting...';
    }

    // Attempt connection
    const success = await synapseAPI.setEndpoint(endpoint);

    // Update UI
    if (connectBtn) {
        connectBtn.disabled = false;
        connectBtn.textContent = 'Connect';
    }

    if (success) {
        const nodeId = synapseAPI.getNodeId();
        if (statusIndicator) {
            statusIndicator.classList.add('connected');
        }
        if (nodeIdDisplay) {
            nodeIdDisplay.textContent = `Node: ${nodeId}`;
        }
        
        // Initial update
        updateAllPanels();
        
        showNotification('success', `Connected to ${nodeId}`);
    } else {
        if (statusIndicator) {
            statusIndicator.classList.add('disconnected');
        }
        if (nodeIdDisplay) {
            nodeIdDisplay.textContent = 'Connection Failed';
        }
        
        showNotification('error', 'Failed to connect to node');
    }
}

/**
 * Setup API event listeners
 */
function setupAPIListeners() {
    synapseAPI.on('connected', (state) => {
        console.log('[Dashboard] Connected to node');
        updateAllPanels();
    });

    synapseAPI.on('disconnected', (error) => {
        console.log('[Dashboard] Disconnected from node');
        const statusIndicator = document.getElementById('connectionStatus');
        const nodeIdDisplay = document.getElementById('nodeId');
        
        if (statusIndicator) {
            statusIndicator.classList.remove('connected');
            statusIndicator.classList.add('disconnected');
        }
        if (nodeIdDisplay) {
            nodeIdDisplay.textContent = 'Disconnected';
        }
    });

    synapseAPI.on('state-updated', (state) => {
        updateLastUpdate();
    });
}

/**
 * Update all panels
 */
function updateAllPanels() {
    if (healthMonitor) healthMonitor.update();
    if (governanceMonitor) governanceMonitor.update();
    if (evolutionMonitor) evolutionMonitor.update();
    updateLastUpdate();
}

/**
 * Update last update timestamp
 */
function updateLastUpdate() {
    const lastUpdate = synapseAPI.getLastUpdate();
    const display = document.getElementById('lastUpdate');
    
    if (display && lastUpdate) {
        const formatted = formatTimestamp(lastUpdate);
        display.textContent = formatted;
    }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleString();
}

/**
 * Setup modal controls
 */
function setupModals() {
    // Proposal details modal
    const proposalModal = document.getElementById('proposalModal');
    const closeProposal = document.getElementById('closeModal');

    if (closeProposal) {
        closeProposal.onclick = () => closeModal('proposalModal');
    }
    if (proposalModal) {
        proposalModal.onclick = (e) => {
            if (e.target === proposalModal) closeModal('proposalModal');
        };
    }

    // Code viewer modal
    const codeViewerModal = document.getElementById('codeViewerModal');
    const closeCodeViewer = document.getElementById('closeCodeViewer');

    if (closeCodeViewer) {
        closeCodeViewer.onclick = () => closeModal('codeViewerModal');
    }
    if (codeViewerModal) {
        codeViewerModal.onclick = (e) => {
            if (e.target === codeViewerModal) closeModal('codeViewerModal');
        };
    }
}

/**
 * Show modal
 */
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * Close modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Show proposal details
 */
function showProposalDetails(proposalId) {
    const proposal = synapseAPI.getProposal(proposalId);
    
    if (!proposal) {
        console.error('[Dashboard] Proposal not found:', proposalId);
        return;
    }

    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');

    if (modalTitle) {
        modalTitle.textContent = proposal.title || 'Proposal Details';
    }

    if (modalBody) {
        modalBody.innerHTML = renderProposalDetails(proposal);
    }

    showModal('proposalModal');
}

/**
 * Render proposal details
 */
function renderProposalDetails(proposal) {
    const description = proposal.description || 'No description available';
    const proposer = proposal.proposer || 'Unknown';
    const type = proposal.proposal_type || 'config';
    const status = proposal.status || 'open';
    const votes = proposal.vote_count || 0;
    const quorum = proposal.quorum_required || 1;
    const tags = proposal.tags || [];

    return `
        <div class="proposal-details">
            <div class="proposal-detail-section">
                <h4>Metadata</h4>
                <div class="proposal-detail-meta">
                    <div class="proposal-detail-meta-item">
                        <div class="proposal-detail-meta-label">Proposer</div>
                        <div class="proposal-detail-meta-value">${proposer}</div>
                    </div>
                    <div class="proposal-detail-meta-item">
                        <div class="proposal-detail-meta-label">Type</div>
                        <div class="proposal-detail-meta-value">${type}</div>
                    </div>
                    <div class="proposal-detail-meta-item">
                        <div class="proposal-detail-meta-label">Status</div>
                        <div class="proposal-detail-meta-value">${status}</div>
                    </div>
                    <div class="proposal-detail-meta-item">
                        <div class="proposal-detail-meta-label">Votes</div>
                        <div class="proposal-detail-meta-value">${votes}/${quorum}</div>
                    </div>
                </div>
            </div>

            ${tags.length > 0 ? `
                <div class="proposal-detail-section">
                    <h4>Tags</h4>
                    <div class="proposal-tags-list">
                        ${tags.map(tag => `<span class="proposal-tag-item">${tag}</span>`).join('')}
                    </div>
                </div>
            ` : ''}

            <div class="proposal-detail-section">
                <h4>Description</h4>
                <div class="proposal-detail-content">${escapeHtml(description)}</div>
            </div>

            <div class="proposal-detail-section">
                <button class="btn-primary" onclick="openVoteSimulator('${proposal.id}'); closeModal('proposalModal');">
                    🗳️ Simulate My Vote Weight
                </button>
            </div>
        </div>
    `;
}

/**
 * Show code upgrade details (opens code viewer)
 */
function showCodeUpgradeDetails(proposalId) {
    showCodeViewer(proposalId);
}

/**
 * Show code viewer modal
 */
function showCodeViewer(proposalId) {
    const proposal = synapseAPI.getProposal(proposalId);
    
    if (!proposal) {
        console.error('[Dashboard] Proposal not found:', proposalId);
        return;
    }

    const codeInfo = document.getElementById('codeInfo');
    const codeContent = document.getElementById('codeContent');

    // Extract code and metadata
    const sourceCode = proposal.params?.source_code || 'Source code not available';
    const wasmSize = proposal.params?.wasm_size_bytes || 0;
    const wasmHash = proposal.params?.wasm_hash || 'N/A';
    const component = proposal.params?.target_component || 'unknown';
    const improvement = proposal.params?.estimated_improvement || 0;

    if (codeInfo) {
        codeInfo.innerHTML = `
            <div class="code-info-grid">
                <div class="code-info-item">
                    <div class="code-info-label">Component</div>
                    <div class="code-info-value">${component}</div>
                </div>
                <div class="code-info-item">
                    <div class="code-info-label">WASM Size</div>
                    <div class="code-info-value">${formatBytes(wasmSize)}</div>
                </div>
                <div class="code-info-item">
                    <div class="code-info-label">SHA256 Hash</div>
                    <div class="code-info-value">${wasmHash.substring(0, 16)}...</div>
                </div>
                <div class="code-info-item">
                    <div class="code-info-label">Est. Improvement</div>
                    <div class="code-info-value">${improvement.toFixed(1)}%</div>
                </div>
            </div>
        `;
    }

    if (codeContent) {
        codeContent.textContent = sourceCode;
        // Apply basic syntax highlighting
        highlightRustCode(codeContent);
    }

    showModal('codeViewerModal');
}

/**
 * Basic Rust syntax highlighting
 */
function highlightRustCode(element) {
    let code = element.textContent;
    
    // Keywords
    const keywords = ['fn', 'let', 'mut', 'pub', 'const', 'struct', 'enum', 'impl', 'trait', 'use', 'mod', 'return', 'if', 'else', 'match', 'for', 'while', 'loop'];
    keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'g');
        code = code.replace(regex, `<span class="keyword">${keyword}</span>`);
    });
    
    // Types
    const types = ['u8', 'u16', 'u32', 'u64', 'i8', 'i16', 'i32', 'i64', 'f32', 'f64', 'bool', 'String', 'Vec', 'Option', 'Result'];
    types.forEach(type => {
        const regex = new RegExp(`\\b${type}\\b`, 'g');
        code = code.replace(regex, `<span class="type">${type}</span>`);
    });
    
    element.innerHTML = code;
}

/**
 * Show notification
 */
function showNotification(type, message) {
    console.log(`[Dashboard] ${type.toUpperCase()}: ${message}`);
    // Could implement a toast notification system here
}

/**
 * Utility: Format bytes
 */
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally accessible
window.showProposalDetails = showProposalDetails;
window.showCodeUpgradeDetails = showCodeUpgradeDetails;
window.showCodeViewer = showCodeViewer;
window.closeModal = closeModal;
window.openVoteSimulator = openVoteSimulator;
