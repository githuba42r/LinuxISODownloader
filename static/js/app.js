// Global state
let checkInProgress = false;
let autoRefreshInterval = null;
let statusCheckInterval = null;
let eventHistory = []; // Store last 200 events
const MAX_EVENTS = 200;
let eventSource = null; // SSE connection

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    loadDistros();
    updateStatus();
    startAutoRefresh();
    connectEventStream();
    
    // Set up event listeners
    document.getElementById('select-all-btn').addEventListener('click', selectAllDistros);
    document.getElementById('check-updates-btn').addEventListener('click', checkForUpdates);
    
    // Settings modal listeners
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    document.getElementById('close-modal').addEventListener('click', closeSettings);
    document.getElementById('cancel-settings').addEventListener('click', closeSettings);
    document.getElementById('save-settings').addEventListener('click', saveSettings);
    document.getElementById('auto-check-toggle').addEventListener('change', toggleFrequencyGroup);
    
    // Close modal when clicking outside
    document.getElementById('settings-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeSettings();
        }
    });
});

// Connect to Server-Sent Events stream
function connectEventStream() {
    if (eventSource) {
        eventSource.close();
    }
    
    eventSource = new EventSource('/api/events');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
    };
    
    eventSource.onerror = function(error) {
        console.error('EventSource error:', error);
        // Attempt reconnection after 5 seconds
        setTimeout(() => {
            if (eventSource.readyState === EventSource.CLOSED) {
                connectEventStream();
            }
        }, 5000);
    };
}

// Handle events from server
function handleServerEvent(event) {
    const { type, message, data } = event;
    
    switch (type) {
        case 'connected':
            console.log('Connected to event stream');
            break;
            
        case 'check_start':
            // Distro check starting
            console.log(`Check starting: ${message}`);
            break;
            
        case 'check_result':
            // Individual distro result
            const result = data.result;
            const distro = data.distro;
            
            let eventType = 'info';
            if (result.status === 'error') {
                eventType = 'error';
            } else if (result.status === 'update_available' || result.status === 'new') {
                eventType = 'success';
            }
            
            addEvent(`${formatDistroName(distro)}: ${message}`, eventType);
            renderEvents();
            break;
            
        case 'check_complete':
            // All checks complete
            checkInProgress = false;
            resetCheckButton();
            updateStatus();
            break;
    }
}

// Load configuration and set up Transmission button
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // Set Transmission button URL
        const transmissionBtn = document.getElementById('transmission-btn');
        if (transmissionBtn && config.transmission_url) {
            transmissionBtn.href = config.transmission_url;
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Load available distributions
async function loadDistros() {
    try {
        const response = await fetch('/api/distros');
        const data = await response.json();
        
        const container = document.getElementById('distros-container');
        container.innerHTML = '';
        
        data.distros.forEach(distro => {
            const badge = document.createElement('div');
            badge.className = 'distro-badge';
            badge.dataset.distro = distro.id;
            
            // Set selected state from backend default
            if (distro.selected) {
                badge.classList.add('selected');
            }
            
            // Set custom color
            badge.style.setProperty('--distro-color', distro.color);
            
            badge.innerHTML = `
                <img src="${distro.logo}" alt="${distro.name}" class="distro-logo" onerror="this.style.display='none'">
                <div class="distro-name">${distro.name}</div>
            `;
            
            // Toggle selection on click
            badge.addEventListener('click', function() {
                this.classList.toggle('selected');
            });
            
            container.appendChild(badge);
        });
    } catch (error) {
        console.error('Error loading distros:', error);
        showMessage('error', 'Failed to load distributions');
    }
}

// Format distro name for display (kept for backwards compatibility)
function formatDistroName(distro) {
    const names = {
        'centos': 'CentOS Stream',
        'debian': 'Debian',
        'ubuntu': 'Ubuntu',
        'arch': 'Arch Linux',
        'raspberrypi': 'Raspberry Pi OS'
    };
    return names[distro] || distro;
}

// Select all distros
function selectAllDistros() {
    const badges = document.querySelectorAll('.distro-badge');
    const allSelected = Array.from(badges).every(badge => badge.classList.contains('selected'));
    
    badges.forEach(badge => {
        if (allSelected) {
            badge.classList.remove('selected');
        } else {
            badge.classList.add('selected');
        }
    });
    
    // Update button text
    const btn = document.getElementById('select-all-btn');
    btn.textContent = allSelected ? 'Select All' : 'Deselect All';
}

// Update status display
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Update manager status with enhanced information
        const statusElement = document.getElementById('manager-status');
        const statusText = data.status_text || capitalizeFirst(data.status);
        const scheduleInfo = data.schedule_info || '';
        
        statusElement.innerHTML = `
            <div class="status-line">
                <span class="status status-${data.status}">${statusText}</span>
            </div>
            ${scheduleInfo !== 'Disabled' ? `
                <div class="status-schedule">
                    ${scheduleInfo}
                </div>
            ` : `
                <div class="status-schedule status-disabled">
                    Automatic checks: Disabled
                </div>
            `}
        `;
        
        // Update torrents list
        updateTorrentsList(data.torrents);
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Update torrents list
function updateTorrentsList(torrents) {
    const container = document.getElementById('torrents-list');
    
    if (!torrents || torrents.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No torrents found</p></div>';
        return;
    }
    
    container.innerHTML = '';
    
    torrents.forEach(torrent => {
        const item = document.createElement('div');
        item.className = 'torrent-item';
        
        const progress = torrent.percentDone * 100;
        const status = getTorrentStatus(torrent);
        
        item.innerHTML = `
            <h3>${torrent.name}</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
                <div class="progress-text">${progress.toFixed(1)}%</div>
            </div>
            <div class="torrent-info">
                <div class="torrent-info-item">
                    <strong>Status:</strong> ${status}
                </div>
                <div class="torrent-info-item">
                    <strong>Size:</strong> ${formatBytes(torrent.totalSize)}
                </div>
                <div class="torrent-info-item">
                    <strong>Downloaded:</strong> ${formatBytes(torrent.downloadedEver)}
                </div>
                <div class="torrent-info-item">
                    <strong>Down Speed:</strong> ${formatSpeed(torrent.rateDownload)}
                </div>
                <div class="torrent-info-item">
                    <strong>Up Speed:</strong> ${formatSpeed(torrent.rateUpload)}
                </div>
                <div class="torrent-info-item">
                    <strong>Ratio:</strong> ${torrent.uploadRatio.toFixed(2)}
                </div>
            </div>
        `;
        
        container.appendChild(item);
    });
}

// Get torrent status text
function getTorrentStatus(torrent) {
    const statusMap = {
        0: 'Stopped',
        1: 'Verify Queue',
        2: 'Verifying',
        3: 'Download Queue',
        4: 'Downloading',
        5: 'Seed Queue',
        6: 'Seeding'
    };
    return statusMap[torrent.status] || 'Unknown';
}

// Check for updates
async function checkForUpdates() {
    if (checkInProgress) {
        showMessage('info', 'Check already in progress');
        return;
    }
    
    const selectedDistros = Array.from(document.querySelectorAll('.distro-badge.selected'))
        .map(badge => badge.dataset.distro);
    
    if (selectedDistros.length === 0) {
        showMessage('error', 'Please select at least one distribution');
        return;
    }
    
    // Add event for check start
    const distroNames = selectedDistros.map(id => formatDistroName(id)).join(', ');
    addEvent(`Checking for updates: ${distroNames}`, 'info');
    renderEvents();
    
    // Disable button and show spinner
    const btn = document.getElementById('check-updates-btn');
    btn.disabled = true;
    btn.innerHTML = 'Checking<span class="spinner"></span>';
    
    checkInProgress = true;
    
    try {
        const response = await fetch('/api/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                distros: selectedDistros
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showMessage('error', data.error);
            checkInProgress = false;
            resetCheckButton();
            return;
        }
        
        // SSE will handle real-time updates, no need to poll
        
    } catch (error) {
        console.error('Error checking for updates:', error);
        showMessage('error', 'Failed to start update check');
        checkInProgress = false;
        resetCheckButton();
    }
}

// Reset check button
function resetCheckButton() {
    const btn = document.getElementById('check-updates-btn');
    btn.disabled = false;
    btn.textContent = 'Check for Updates';
}

// Show message
function showMessage(type, text) {
    const container = document.getElementById('message-container');
    
    const message = document.createElement('div');
    message.className = `message message-${type}`;
    message.textContent = text;
    
    container.appendChild(message);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        message.remove();
    }, 5000);
}

// Start auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(() => {
        if (!checkInProgress) {
            updateStatus();
        }
    }, 5000); // Refresh every 5 seconds
}

// Utility functions
function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatSpeed(bytesPerSecond) {
    if (bytesPerSecond === 0) return '0 B/s';
    return formatBytes(bytesPerSecond) + '/s';
}

// Settings Modal Functions
async function openSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.add('active');
    
    // Load current settings
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        const toggle = document.getElementById('auto-check-toggle');
        const frequencySelect = document.getElementById('check-frequency');
        const frequencyGroup = document.getElementById('frequency-group');
        
        toggle.checked = settings.enabled;
        frequencySelect.value = settings.frequency || '1d';
        
        if (settings.enabled) {
            frequencyGroup.classList.add('enabled');
        } else {
            frequencyGroup.classList.remove('enabled');
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        showMessage('error', 'Failed to load settings');
    }
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    modal.classList.remove('active');
}

function toggleFrequencyGroup() {
    const toggle = document.getElementById('auto-check-toggle');
    const frequencyGroup = document.getElementById('frequency-group');
    
    if (toggle.checked) {
        frequencyGroup.classList.add('enabled');
    } else {
        frequencyGroup.classList.remove('enabled');
    }
}

async function saveSettings() {
    const toggle = document.getElementById('auto-check-toggle');
    const frequencySelect = document.getElementById('check-frequency');
    
    const settings = {
        enabled: toggle.checked,
        frequency: frequencySelect.value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeSettings();
            // Display settings change in results container
            displaySettingsResult(settings);
            // Refresh status to show updated schedule info
            updateStatus();
        } else {
            showMessage('error', result.error || 'Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('error', 'Failed to save settings');
    }
}

// Display settings changes in results container
function displaySettingsResult(settings) {
    // Get friendly frequency name
    const frequencyNames = {
        '1h': 'Every 1 hour',
        '8h': 'Every 8 hours',
        '1d': 'Every 1 day',
        '7d': 'Every 7 days',
        '14d': 'Every 14 days',
        '30d': 'Every 30 days'
    };
    
    const frequencyText = frequencyNames[settings.frequency] || settings.frequency;
    
    if (settings.enabled) {
        addEvent(`Settings: Automatic checking enabled (${frequencyText})`, 'success');
    } else {
        addEvent('Settings: Automatic checking disabled', 'info');
    }
    
    renderEvents();
}

// Format timestamp for display
function formatTimestamp(date) {
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins}m ago`;
    }
    
    // Less than 1 day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }
    
    // More than 1 day - show date/time
    return date.toLocaleString();
}

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    if (eventSource) {
        eventSource.close();
    }
});
