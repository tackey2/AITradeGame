// Enhanced Dashboard - Exchange Credentials Module
// Exchange credentials management, validation, environment switching

// ============================================
// EXCHANGE CREDENTIALS
// ============================================

async function loadExchangeCredentials() {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`);
        const data = await response.json();

        // Update status indicators
        const statusIndicator = document.getElementById('exchangeStatusIndicator');
        const statusText = document.getElementById('exchangeStatusText');
        const mainnetBadge = document.getElementById('mainnetStatusBadge');
        const testnetBadge = document.getElementById('testnetStatusBadge');
        const lastValidated = document.getElementById('lastValidatedText');

        if (data.configured) {
            statusIndicator.className = 'status-indicator status-ok';
            statusText.textContent = 'Configured';

            mainnetBadge.textContent = data.has_mainnet ? 'Configured' : 'Not Set';
            mainnetBadge.className = data.has_mainnet ? 'status-badge badge-ok' : 'status-badge badge-error';

            testnetBadge.textContent = data.has_testnet ? 'Configured' : 'Not Set';
            testnetBadge.className = data.has_testnet ? 'status-badge badge-ok' : 'status-badge badge-error';

            if (data.last_validated) {
                const date = new Date(data.last_validated);
                lastValidated.textContent = date.toLocaleString();
            } else {
                lastValidated.textContent = 'Never';
            }
        } else {
            statusIndicator.className = 'status-indicator status-inactive';
            statusText.textContent = 'Not Configured';
            mainnetBadge.textContent = 'Not Set';
            mainnetBadge.className = 'status-badge badge-error';
            testnetBadge.textContent = 'Not Set';
            testnetBadge.className = 'status-badge badge-error';
            lastValidated.textContent = 'Never';
        }

        // Load exchange environment
        const configResponse = await fetch(`/api/models/${currentModelId}/config`);
        const config = await configResponse.json();

        const exchangeEnv = config.exchange_environment || 'testnet';
        document.getElementById(`exchangeEnv${exchangeEnv.charAt(0).toUpperCase() + exchangeEnv.slice(1)}`).checked = true;

    } catch (error) {
        console.error('Failed to load exchange credentials:', error);
    }
}

async function saveExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    const mainnetApiKey = document.getElementById('mainnetApiKey').value.trim();
    const mainnetApiSecret = document.getElementById('mainnetApiSecret').value.trim();
    const testnetApiKey = document.getElementById('testnetApiKey').value.trim();
    const testnetApiSecret = document.getElementById('testnetApiSecret').value.trim();

    // At least one set of credentials must be provided
    if (!mainnetApiKey && !testnetApiKey) {
        showToast('Please enter at least testnet or mainnet credentials', 'error');
        return;
    }

    // Validate paired credentials
    if ((mainnetApiKey && !mainnetApiSecret) || (!mainnetApiKey && mainnetApiSecret)) {
        showToast('Both mainnet API key and secret are required', 'error');
        return;
    }

    if ((testnetApiKey && !testnetApiSecret) || (!testnetApiKey && testnetApiSecret)) {
        showToast('Both testnet API key and secret are required', 'error');
        return;
    }

    try {
        const payload = {
            exchange_type: 'binance'
        };

        // Add mainnet credentials if provided
        if (mainnetApiKey && mainnetApiSecret) {
            payload.api_key = mainnetApiKey;
            payload.api_secret = mainnetApiSecret;
        } else {
            // Use placeholder if not provided but testnet is
            payload.api_key = 'not_configured';
            payload.api_secret = 'not_configured';
        }

        // Add testnet credentials if provided
        if (testnetApiKey && testnetApiSecret) {
            payload.testnet_api_key = testnetApiKey;
            payload.testnet_api_secret = testnetApiSecret;
        }

        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (result.success) {
            showToast('✅ Exchange credentials saved successfully');

            // Clear sensitive input fields
            document.getElementById('mainnetApiKey').value = '';
            document.getElementById('mainnetApiSecret').value = '';
            document.getElementById('testnetApiKey').value = '';
            document.getElementById('testnetApiSecret').value = '';

            // Reload status
            loadExchangeCredentials();
        } else {
            showToast(`Failed to save credentials: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to save credentials:', error);
        showToast('Failed to save credentials', 'error');
    }
}

async function validateExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    const validateBtn = document.getElementById('validateCredentialsBtn');
    const originalText = validateBtn.innerHTML;

    validateBtn.disabled = true;
    validateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Validating...';

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/validate`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.valid) {
            showToast('✅ Credentials validated successfully!');
            loadExchangeCredentials(); // Reload to show updated validation time
        } else {
            showToast('❌ Credential validation failed. Please check your API keys.', 'error');
        }
    } catch (error) {
        console.error('Failed to validate credentials:', error);
        showToast('Failed to validate credentials', 'error');
    } finally {
        validateBtn.disabled = false;
        validateBtn.innerHTML = originalText;
    }
}

async function deleteExchangeCredentials() {
    if (!currentModelId) {
        showToast('Please select a model first', 'error');
        return;
    }

    if (!confirm('Are you sure you want to delete all exchange credentials for this model? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/credentials`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            showToast('🗑️ Exchange credentials deleted');

            // Clear input fields
            document.getElementById('mainnetApiKey').value = '';
            document.getElementById('mainnetApiSecret').value = '';
            document.getElementById('testnetApiKey').value = '';
            document.getElementById('testnetApiSecret').value = '';

            // Reload status
            loadExchangeCredentials();
        } else {
            showToast(`Failed to delete credentials: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to delete credentials:', error);
        showToast('Failed to delete credentials', 'error');
    }
}

async function setExchangeEnvironment(environment) {
    if (!currentModelId) return;

    try {
        const response = await fetch(`/api/models/${currentModelId}/exchange/environment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ exchange_environment: environment })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Exchange environment set to ${environment}`);
        } else {
            showToast(`Failed to set exchange environment: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to set exchange environment:', error);
        showToast('Failed to set exchange environment', 'error');
    }
}

// ============================================
// INITIALIZATION
// ============================================

function initExchangeCredentials() {
    // Save credentials button
    document.getElementById('saveCredentialsBtn')?.addEventListener('click', saveExchangeCredentials);

    // Validate credentials button
    document.getElementById('validateCredentialsBtn')?.addEventListener('click', validateExchangeCredentials);

    // Delete credentials button
    document.getElementById('deleteCredentialsBtn')?.addEventListener('click', deleteExchangeCredentials);

    // Exchange environment radio buttons
    document.querySelectorAll('input[name="exchangeEnv"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            setExchangeEnvironment(e.target.value);
        });
    });

    // Password visibility toggles
    document.querySelectorAll('.toggle-visibility').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            togglePasswordVisibility(targetId);
        });
    });

    // Load initial status
    loadExchangeCredentials();
}

console.log('✓ Enhanced Exchange Credentials Module Loaded');
