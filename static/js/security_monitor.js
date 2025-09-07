// Enhanced Security Monitor JavaScript
class SecurityMonitor {
    constructor() {
        this.notifications = [];
        this.charts = {};
        this.alerts = [];
        this.init();
    }

    init() {
        this.setupRealTimeUpdates();
        this.setupCharts();
        this.setupNotifications();
        this.setupFilters();
        this.setupAlerts();
        this.loadSecurityData();
    }

    setupRealTimeUpdates() {
        // WebSocket connection for real-time updates (fallback to polling)
        this.setupWebSocket();
        this.startPolling();
    }

    setupWebSocket() {
        // Placeholder for WebSocket implementation
        // In a production environment, you'd connect to a WebSocket server
        console.log('WebSocket setup placeholder');
    }

    startPolling() {
        // Poll for updates every 30 seconds (more frequent than the current 5 minutes)
        setInterval(() => {
            this.checkForSecurityEvents();
        }, 30000);
    }

    async checkForSecurityEvents() {
        try {
            const response = await fetch('/api/security_events');
            const data = await response.json();

            if (data.new_events && data.new_events.length > 0) {
                this.handleNewSecurityEvents(data.new_events);
            }
        } catch (error) {
            console.error('Error checking for security events:', error);
        }
    }

    handleNewSecurityEvents(events) {
        events.forEach(event => {
            this.showNotification(event);
            this.updateDashboard(event);
        });
    }

    setupCharts() {
        // Initialize Chart.js for security metrics
        this.createLoginAttemptsChart();
        this.createThreatLevelChart();
        this.createGeolocationChart();
    }

    createLoginAttemptsChart() {
        const ctx = document.getElementById('loginAttemptsChart');
        if (!ctx) return;

        this.charts.loginAttempts = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Successful Logins',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Failed Attempts',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Login Attempts Over Time'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    createThreatLevelChart() {
        const ctx = document.getElementById('threatLevelChart');
        if (!ctx) return;

        this.charts.threatLevel = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Low', 'Medium', 'High', 'Critical'],
                datasets: [{
                    data: [60, 25, 10, 5],
                    backgroundColor: [
                        '#10b981',
                        '#f59e0b',
                        '#ef4444',
                        '#7c2d12'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Current Threat Level Distribution'
                    }
                }
            }
        });
    }

    createGeolocationChart() {
        const ctx = document.getElementById('geolocationChart');
        if (!ctx) return;

        this.charts.geolocation = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Login Attempts by Country',
                    data: [],
                    backgroundColor: '#6366f1'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Geographic Distribution of Login Attempts'
                    }
                }
            }
        });
    }

    setupNotifications() {
        // Create notification container
        const container = document.createElement('div');
        container.id = 'securityNotifications';
        container.className = 'security-notifications';
        document.body.appendChild(container);

        // Setup notification styles
        this.addNotificationStyles();
    }

    addNotificationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .security-notifications {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            }

            .security-notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                margin-bottom: 10px;
                padding: 16px;
                border-left: 4px solid #6366f1;
                animation: slideIn 0.3s ease-out;
            }

            .security-notification.success { border-left-color: #10b981; }
            .security-notification.warning { border-left-color: #f59e0b; }
            .security-notification.error { border-left-color: #ef4444; }
            .security-notification.critical { border-left-color: #7c2d12; }

            .security-notification-header {
                display: flex;
                justify-content: between;
                align-items: center;
                margin-bottom: 8px;
            }

            .security-notification-title {
                font-weight: 600;
                margin: 0;
            }

            .security-notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #6b7280;
            }

            .security-notification-message {
                color: #374151;
                font-size: 14px;
                margin: 0;
            }

            .security-notification-time {
                color: #9ca3af;
                font-size: 12px;
                margin-top: 4px;
            }

            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    showNotification(event) {
        const notification = document.createElement('div');
        notification.className = `security-notification ${event.severity || 'info'}`;

        const severityColors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'error',
            'critical': 'critical'
        };

        notification.className = `security-notification ${severityColors[event.severity] || 'info'}`;

        notification.innerHTML = `
            <div class="security-notification-header">
                <h4 class="security-notification-title">${event.title || 'Security Event'}</h4>
                <button class="security-notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            <p class="security-notification-message">${event.message}</p>
            <div class="security-notification-time">${new Date().toLocaleTimeString()}</div>
        `;

        document.getElementById('securityNotifications').appendChild(notification);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }

    setupFilters() {
        // Setup advanced filtering
        const filterForm = document.getElementById('securityFilters');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.applyFilters();
            });
        }

        // Setup date range picker
        this.setupDateRangePicker();
    }

    setupDateRangePicker() {
        // Placeholder for date range picker implementation
        console.log('Date range picker setup');
    }

    applyFilters() {
        const filters = {
            dateFrom: document.getElementById('dateFrom')?.value,
            dateTo: document.getElementById('dateTo')?.value,
            severity: document.getElementById('severityFilter')?.value,
            ipAddress: document.getElementById('ipFilter')?.value,
            username: document.getElementById('usernameFilter')?.value
        };

        this.loadFilteredData(filters);
    }

    async loadFilteredData(filters) {
        try {
            const queryString = new URLSearchParams(filters).toString();
            const response = await fetch(`/api/security_data?${queryString}`);
            const data = await response.json();

            this.updateSecurityDisplay(data);
        } catch (error) {
            console.error('Error loading filtered data:', error);
        }
    }

    setupAlerts() {
        // Setup security alerts configuration
        this.loadAlertSettings();
        this.setupAlertForm();
    }

    async loadAlertSettings() {
        try {
            const response = await fetch('/api/security_alerts');
            const alerts = await response.json();
            this.alerts = alerts;
            this.renderAlertSettings();
        } catch (error) {
            console.error('Error loading alert settings:', error);
        }
    }

    setupAlertForm() {
        const form = document.getElementById('alertSettingsForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveAlertSettings();
            });
        }
    }

    async saveAlertSettings() {
        const settings = {
            failedLoginThreshold: document.getElementById('failedLoginThreshold')?.value,
            suspiciousIPThreshold: document.getElementById('suspiciousIPThreshold')?.value,
            enableEmailAlerts: document.getElementById('enableEmailAlerts')?.checked,
            enableRealTimeAlerts: document.getElementById('enableRealTimeAlerts')?.checked
        };

        try {
            const response = await fetch('/api/security_alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            if (response.ok) {
                this.showNotification({
                    title: 'Alert Settings Updated',
                    message: 'Security alert settings have been saved successfully.',
                    severity: 'success'
                });
            }
        } catch (error) {
            console.error('Error saving alert settings:', error);
        }
    }

    renderAlertSettings() {
        // Render alert settings UI
        console.log('Rendering alert settings');
    }

    async loadSecurityData() {
        try {
            // Show loading state for charts
            this.showChartLoadingStates();

            const response = await fetch('/api/security_dashboard_data');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Update charts and dashboard
            this.updateCharts(data);
            this.updateDashboard(data);

            // Hide loading states
            this.hideChartLoadingStates();

            console.log('Security data loaded successfully');
        } catch (error) {
            console.error('Error loading security data:', error);
            this.hideChartLoadingStates();
            this.showChartErrorStates(error);
        }
    }

    updateCharts(data) {
        // Update login attempts chart
        if (this.charts.loginAttempts && data.loginAttempts) {
            this.charts.loginAttempts.data.labels = data.loginAttempts.labels;
            this.charts.loginAttempts.data.datasets[0].data = data.loginAttempts.successful;
            this.charts.loginAttempts.data.datasets[1].data = data.loginAttempts.failed;
            this.charts.loginAttempts.update();
        }

        // Update geolocation chart
        if (this.charts.geolocation && data.geolocation) {
            this.charts.geolocation.data.labels = data.geolocation.countries;
            this.charts.geolocation.data.datasets[0].data = data.geolocation.counts;
            this.charts.geolocation.update();
        }
    }

    updateDashboard(data) {
        // Update dashboard metrics
        if (data.metrics) {
            Object.keys(data.metrics).forEach(key => {
                const element = document.getElementById(`${key}Metric`);
                if (element) {
                    element.textContent = data.metrics[key];
                }
            });
        }
    }

    // Chart loading and error handling methods
    showChartLoadingStates() {
        const chartIds = ['loginAttemptsChart', 'threatLevelChart', 'geolocationChart'];

        chartIds.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                const container = canvas.parentElement;
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'chart-loading';
                loadingDiv.id = `${id}Loading`;
                loadingDiv.innerHTML = `
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading chart...</span>
                    </div>
                    <p class="mt-2">Loading chart data...</p>
                `;

                // Hide canvas and show loading
                canvas.style.display = 'none';
                container.appendChild(loadingDiv);
            }
        });
    }

    hideChartLoadingStates() {
        const chartIds = ['loginAttemptsChart', 'threatLevelChart', 'geolocationChart'];

        chartIds.forEach(id => {
            const canvas = document.getElementById(id);
            const loadingDiv = document.getElementById(`${id}Loading`);

            if (canvas) {
                canvas.style.display = 'block';
            }

            if (loadingDiv) {
                loadingDiv.remove();
            }
        });
    }

    showChartErrorStates(error) {
        const chartIds = ['loginAttemptsChart', 'threatLevelChart', 'geolocationChart'];

        chartIds.forEach(id => {
            const canvas = document.getElementById(id);
            if (canvas) {
                const container = canvas.parentElement;
                const errorDiv = document.createElement('div');
                errorDiv.className = 'chart-error';
                errorDiv.id = `${id}Error`;
                errorDiv.innerHTML = `
                    <div class="text-center text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                        <p>Failed to load chart data</p>
                        <small class="text-muted">${error.message || 'Unknown error'}</small>
                    </div>
                `;

                // Hide canvas and show error
                canvas.style.display = 'none';
                container.appendChild(errorDiv);
            }
        });
    }

    updateSecurityDisplay(data) {
        // Update table data
        if (data.attempts) {
            this.updateAttemptsTable(data.attempts);
        }

        // Update charts with filtered data
        if (data.loginAttempts) {
            this.updateCharts({ loginAttempts: data.loginAttempts });
        }

        // Update metrics
        if (data.total_count !== undefined) {
            const totalElement = document.getElementById('totalAttemptsMetric');
            if (totalElement) {
                totalElement.textContent = data.total_count;
            }
        }
    }

    updateAttemptsTable(attempts) {
        const tbody = document.querySelector('#attemptsTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        attempts.forEach(attempt => {
            const row = document.createElement('tr');
            row.className = attempt.success ? 'table-success' : 'table-danger';

            row.innerHTML = `
                <td>${new Date(attempt.attempt_time).toLocaleTimeString()}</td>
                <td>${attempt.username}</td>
                <td>${attempt.ip_address}</td>
                <td>
                    ${attempt.success ?
                        '<span class="badge badge-success">Success</span>' :
                        '<span class="badge badge-danger">Failed</span>'}
                </td>
                <td>
                    ${attempt.captcha_required ?
                        (attempt.captcha_solved ?
                            '<span class="badge badge-success">Solved</span>' :
                            '<span class="badge badge-warning">Required</span>') :
                        '<span class="text-muted">-</span>'}
                </td>
                <td class="text-truncate" style="max-width: 200px;" title="${attempt.user_agent || 'N/A'}">
                    ${attempt.user_agent ? attempt.user_agent.substring(0, 50) : 'N/A'}
                </td>
            `;

            tbody.appendChild(row);
        });
    }

    // Utility methods
    formatDate(date) {
        return new Date(date).toLocaleString();
    }

    getSeverityColor(severity) {
        const colors = {
            'low': '#10b981',
            'medium': '#f59e0b',
            'high': '#ef4444',
            'critical': '#7c2d12'
        };
        return colors[severity] || '#6366f1';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('securityMonitorContainer')) {
        try {
            window.securityMonitor = new SecurityMonitor();
            console.log('Security Monitor initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Security Monitor:', error);
            showInitializationError();
        }
    }
});

// Show initialization error
function showInitializationError() {
    const container = document.getElementById('securityMonitorContainer');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">
                    <i class="fas fa-exclamation-triangle"></i> Security Monitor Error
                </h4>
                <p>Failed to initialize the Security Monitor. Please refresh the page or contact your administrator.</p>
                <hr>
                <p class="mb-0">If this problem persists, check the browser console for more details.</p>
            </div>
        `;
    }
}

// Export for global access
window.SecurityMonitor = SecurityMonitor;
