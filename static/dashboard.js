// Dashboard JavaScript functionality
class Dashboard {
    constructor() {
        this.isTracking = false;
        this.statsUpdateInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.startStatsUpdate();
    }

    bindEvents() {
        // Start/Stop tracking buttons
        const startBtn = document.getElementById('start-tracking');
        const stopBtn = document.getElementById('stop-tracking');

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startTracking());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopTracking());
        }

        // Refresh stats button
        const refreshBtn = document.getElementById('refresh-stats');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.updateStats());
        }
    }

    async startTracking() {
        try {
            const response = await fetch('/api/start-tracking', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.isTracking = true;
                this.updateTrackingStatus();
                this.showNotification('Tracking started successfully', 'success');
            } else {
                this.showNotification('Failed to start tracking', 'error');
            }
        } catch (error) {
            console.error('Error starting tracking:', error);
            this.showNotification('Error starting tracking', 'error');
        }
    }

    async stopTracking() {
        try {
            const response = await fetch('/api/stop-tracking', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                this.isTracking = false;
                this.updateTrackingStatus();
                this.showNotification('Tracking stopped successfully', 'success');
            } else {
                this.showNotification('Failed to stop tracking', 'error');
            }
        } catch (error) {
            console.error('Error stopping tracking:', error);
            this.showNotification('Error stopping tracking', 'error');
        }
    }

    updateTrackingStatus() {
        const statusElement = document.getElementById('tracking-status');
        const startBtn = document.getElementById('start-tracking');
        const stopBtn = document.getElementById('stop-tracking');

        if (statusElement) {
            if (this.isTracking) {
                statusElement.innerHTML = `
                    <span class="status-indicator status-active"></span>
                    <span class="text-green-600 font-semibold">Active</span>
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="status-indicator status-inactive"></span>
                    <span class="text-red-600 font-semibold">Inactive</span>
                `;
            }
        }

        if (startBtn && stopBtn) {
            startBtn.disabled = this.isTracking;
            stopBtn.disabled = !this.isTracking;
            
            if (this.isTracking) {
                startBtn.classList.add('opacity-50', 'cursor-not-allowed');
                stopBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                stopBtn.classList.add('opacity-50', 'cursor-not-allowed');
            }
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                this.displayStats(stats);
            }
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    displayStats(stats) {
        // Update current people count
        const currentCountElement = document.getElementById('current-count');
        if (currentCountElement) {
            currentCountElement.textContent = stats.current_people || 0;
        }

        // Update total people count
        const totalCountElement = document.getElementById('total-count');
        if (totalCountElement) {
            totalCountElement.textContent = stats.total_people || 0;
        }

        // Update session duration
        const durationElement = document.getElementById('session-duration');
        if (durationElement) {
            durationElement.textContent = stats.duration || '0s';
        }

        // Update session status
        const sessionStatusElement = document.getElementById('session-status');
        if (sessionStatusElement) {
            sessionStatusElement.textContent = stats.status || 'Unknown';
        }
    }

    startStatsUpdate() {
        // Update stats every 2 seconds
        this.statsUpdateInterval = setInterval(() => {
            this.updateStats();
        }, 2000);
    }

    stopStatsUpdate() {
        if (this.statsUpdateInterval) {
            clearInterval(this.statsUpdateInterval);
            this.statsUpdateInterval = null;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            'bg-blue-500'
        } text-white`;
        
        notification.textContent = message;
        document.body.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
