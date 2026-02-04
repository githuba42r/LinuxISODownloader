// Global state
let checkInProgress = false;
let autoRefreshInterval = null;
let statusCheckInterval = null;

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadDistros();
    updateStatus();
    startAutoRefresh();
    
    // Set up event listeners
    document.getElementById('select-all-btn').addEventListener('click', selectAllDistros);
    document.getElementById('check-updates-btn').addEventListener('click', checkForUpdates);
});

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
                <div class="distro-logo">${distro.emoji}</div>
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
    
    // Clear previous results
    document.getElementById('results-container').innerHTML = '';
    
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
        
        // Start polling for status (status badge will show in-progress state)
        startStatusCheck();
        
    } catch (error) {
        console.error('Error checking for updates:', error);
        showMessage('error', 'Failed to start update check');
        checkInProgress = false;
        resetCheckButton();
    }
}

// Start polling for check status
function startStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/check/status');
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                checkInProgress = false;
                resetCheckButton();
                displayResults(data.results);
                showMessage('success', 'Update check completed');
            } else if (data.status === 'error') {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
                checkInProgress = false;
                resetCheckButton();
                showMessage('error', data.error || 'Update check failed');
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Display check results
function displayResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '<h3 style="margin-bottom: 15px;">Results:</h3>';
    
    if (!results || results.length === 0) {
        container.innerHTML += '<div class="empty-state"><p>No results</p></div>';
        return;
    }
    
    results.forEach(result => {
        const item = document.createElement('div');
        const hasUpdate = result.message.toLowerCase().includes('added') || 
                         result.message.toLowerCase().includes('found');
        const isError = result.message.toLowerCase().includes('error') || 
                       result.message.toLowerCase().includes('failed');
        
        item.className = 'result-item';
        if (isError) {
            item.classList.add('error');
        } else if (!hasUpdate) {
            item.classList.add('no-update');
        }
        
        item.innerHTML = `
            <strong>${formatDistroName(result.distro)}:</strong> ${result.message}
        `;
        
        container.appendChild(item);
    });
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

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
});
