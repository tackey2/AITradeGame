// Enhanced Dashboard - Core Module
// Initialization, navigation, global state management

// ============================================
// GLOBAL STATE VARIABLES
// ============================================

let currentModelId = null;
let currentDecisionId = null;
let refreshInterval = null;
let trendingInterval = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Core initialization
    initializeApp();
    setupEventListeners();

    // Exchange credentials (from second listener)
    const modelSelect = document.getElementById('modelSelect');
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            if (typeof loadExchangeCredentials !== 'undefined') {
                loadExchangeCredentials();
            }
        });
    }
    if (typeof initExchangeCredentials !== 'undefined') {
        initExchangeCredentials();
    }

    // Initialize provider/model management (from second listener)
    if (typeof initProviderManagement !== 'undefined') {
        initProviderManagement();
    }
    if (typeof initModelManagement !== 'undefined') {
        initModelManagement();
    }
    if (typeof initTrendingData !== 'undefined') {
        initTrendingData();
    }
    if (typeof initPasswordToggles !== 'undefined') {
        initPasswordToggles();
    }

    // Chart initialization (from third listener)
    if (document.getElementById('assetAllocationChart')) {
        if (typeof initAssetAllocationChart !== 'undefined') {
            initAssetAllocationChart();
        }
    }

    // Analytics setup (from third listener)
    if (typeof setupAnalyticsRefresh !== 'undefined') {
        setupAnalyticsRefresh();
    }
    if (typeof setupConversationFilters !== 'undefined') {
        setupConversationFilters();
    }

    // Start auto-refresh last
    startAutoRefresh();
});

function initializeApp() {
    loadModels();
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (btn.hasAttribute('data-page')) {
                e.preventDefault();
                switchPage(btn.dataset.page);
            }
        });
    });

    // Model selector
    document.getElementById('modelSelect').addEventListener('change', (e) => {
        currentModelId = parseInt(e.target.value);
        if (currentModelId) {
            loadModelData();
        }
    });

    // Environment selection
    document.querySelectorAll('input[name="environment"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (currentModelId) {
                const newEnv = e.target.value;
                // Warn before switching to Live
                if (newEnv === 'live') {
                    showLiveWarning(() => {
                        setTradingEnvironment(newEnv);
                    }, () => {
                        // Cancelled - revert to simulation
                        document.getElementById('envSimulation').checked = true;
                    });
                } else {
                    setTradingEnvironment(newEnv);
                }
            }
        });
    });

    // Automation selection
    document.querySelectorAll('input[name="automation"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (currentModelId) {
                setAutomationLevel(e.target.value);
            }
        });
    });

    // Multi-model view toggle buttons
    const showAllBtn = document.getElementById('showAllModelsBtn');
    const showSingleBtn = document.getElementById('showSingleModelBtn');

    if (showAllBtn) {
        showAllBtn.addEventListener('click', () => {
            showAllModelsView();
            showAllBtn.style.display = 'none';
            showSingleBtn.style.display = 'inline-block';
        });
    }

    if (showSingleBtn) {
        showSingleBtn.addEventListener('click', () => {
            if (currentModelId) {
                loadModelData();
            }
            showSingleBtn.style.display = 'none';
            showAllBtn.style.display = 'inline-block';
        });
    }

    // Live warning modal
    document.getElementById('cancelLiveBtn').addEventListener('click', () => closeLiveWarning(false));
    document.getElementById('confirmLiveBtn').addEventListener('click', () => closeLiveWarning(true));

    // Action buttons
    document.getElementById('refreshBtn').addEventListener('click', () => refreshCurrentPage());
    document.getElementById('emergencyStopBtn').addEventListener('click', () => emergencyStopAll());
    document.getElementById('executeTradingBtn').addEventListener('click', () => executeTradingCycle());
    document.getElementById('pauseModelBtn').addEventListener('click', () => pauseModel());

    // Settings page
    document.getElementById('saveSettingsBtn').addEventListener('click', () => saveSettings());
    document.getElementById('resetSettingsBtn').addEventListener('click', () => loadSettings());
    document.getElementById('refreshIncidentsBtn').addEventListener('click', () => loadIncidents());

    // Modal
    document.getElementById('closeDecisionModal').addEventListener('click', () => closeModal());
    document.getElementById('approveDecisionBtn').addEventListener('click', () => approveDecision());
    document.getElementById('rejectDecisionBtn').addEventListener('click', () => rejectDecision());
    document.getElementById('modifyDecisionBtn').addEventListener('click', () => modifyDecision());
}

// ============================================
// PAGE NAVIGATION
// ============================================

function switchPage(pageName) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(`${pageName}Page`).classList.add('active');
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

    // Load page-specific data
    if (currentModelId) {
        switch(pageName) {
            case 'dashboard':
                loadDashboardData();
                break;
            case 'settings':
                loadSettings();
                break;
            case 'readiness':
                loadReadinessAssessment();
                break;
            case 'incidents':
                loadIncidents();
                break;
        }
    }

    // Load models page data when switched to
    if (pageName === 'models') {
        if (typeof loadModelsPage !== 'undefined') {
            loadModelsPage();
        }
    }

    // Dispatch page change event
    document.dispatchEvent(new CustomEvent('pageChange', { detail: pageName }));
}

function refreshCurrentPage() {
    const activePage = document.querySelector('.page.active');
    if (!activePage || !currentModelId) return;

    const pageName = activePage.id.replace('Page', '');
    switchPage(pageName);
    showToast('Refreshed');
}

// ============================================
// AUTO-REFRESH
// ============================================

function startAutoRefresh() {
    // Clear existing interval first to prevent duplicates
    stopAutoRefresh();

    refreshInterval = setInterval(() => {
        if (currentModelId) {
            const activePage = document.querySelector('.page.active');
            if (activePage && activePage.id === 'dashboardPage') {
                // Refresh all dashboard data like classic view
                loadPendingDecisions();
                loadRiskStatus();
                loadPortfolioChartData(currentTimeRange); // Match classic view's 10-second refresh
                loadPortfolioMetrics();
                loadPositionsTable();
                loadAssetAllocation();
            }
        }
    }, 10000); // Every 10 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

function disposeCharts() {
    // Dispose portfolio chart
    if (typeof portfolioChart !== 'undefined' && portfolioChart) {
        portfolioChart.dispose();
        portfolioChart = null;
    }

    // Dispose asset allocation chart
    if (typeof assetAllocationChart !== 'undefined' && assetAllocationChart) {
        assetAllocationChart.dispose();
        assetAllocationChart = null;
    }
}

// Pause auto-refresh when tab hidden
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Tab hidden, pausing auto-refresh');
    } else {
        console.log('Tab visible, resuming auto-refresh');
    }
});

console.log('✓ Enhanced Core Module Loaded');
