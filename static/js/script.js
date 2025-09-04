// Basic JavaScript utilities for the POS system

// Format numbers for display
function formatNumber(n) {
    return Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// Show alerts/messages
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    // Insert at top of content
    const content = document.querySelector('.content') || document.body;
    content.insertBefore(alertDiv, content.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Confirm actions
function confirmAction(message) {
    return confirm(message);
}

// Handle form submissions with loading states
function handleFormSubmit(form, callback) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
        submitBtn.disabled = true;

        callback().finally(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        });
    } else {
        callback();
    }
}

// Navigation and UI functionality
let sidebarCollapsed = false;

// Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    const overlay = document.getElementById('sidebarOverlay');

    if (window.innerWidth <= 768) {
        // Mobile behavior
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
    } else {
        // Desktop behavior
        sidebarCollapsed = !sidebarCollapsed;
        sidebar.classList.toggle('collapsed', sidebarCollapsed);
        mainContent.style.marginLeft = sidebarCollapsed ? '0' : '280px';
    }
}

// Close sidebar on mobile
function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');

    sidebar.classList.remove('show');
    overlay.classList.remove('show');
}

// Toggle user dropdown - Updated to match current template structure
function toggleUserMenu() {
    const menu = document.getElementById('userMenu');
    const trigger = document.querySelector('.user-profile-trigger');
    const arrow = document.getElementById('dropdownArrow');

    if (!menu || !trigger) {
        console.error('User menu elements not found');
        return;
    }

    const isExpanded = menu.classList.contains('show');

    if (isExpanded) {
        closeUserMenu();
    } else {
        openUserMenu();
    }
}

// Helper functions for user menu
function openUserMenu() {
    const menu = document.getElementById('userMenu');
    const trigger = document.querySelector('.user-profile-trigger');
    const arrow = document.getElementById('dropdownArrow');

    if (menu && trigger) {
        menu.classList.add('show');
        menu.style.display = 'block';
        trigger.setAttribute('aria-expanded', 'true');
        menu.setAttribute('aria-hidden', 'false');
        if (arrow) arrow.textContent = '▲';

        // Add animation class
        setTimeout(() => {
            menu.classList.add('animate-in');
        }, 10);
    }
}

function closeUserMenu() {
    const menu = document.getElementById('userMenu');
    const trigger = document.querySelector('.user-profile-trigger');
    const arrow = document.getElementById('dropdownArrow');

    if (menu && trigger) {
        menu.classList.remove('animate-in');
        menu.classList.remove('show');
        trigger.setAttribute('aria-expanded', 'false');
        menu.setAttribute('aria-hidden', 'true');
        if (arrow) arrow.textContent = '▼';

        // Hide after animation
        setTimeout(() => {
            menu.style.display = 'none';
        }, 200);
    }
}

// Simple Logout Function
function handleLogout() {
    // Close the user menu first
    closeUserMenu();

    // Simple confirmation
    if (confirm('Are you sure you want to logout?')) {
        // Find the logout form and submit it
        const logoutForm = document.querySelector('.logout-form');
        if (logoutForm) {
            logoutForm.submit();
        }
    }
}

// Toggle notifications
function toggleNotifications() {
    // Placeholder for notifications functionality
    console.log('Notifications clicked');
}

// Modal functionality for change password
function openChangePasswordModal() {
    closeUserMenu();
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeChangePasswordModal() {
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Modal functionality for secret question
function openSecretQuestionModal() {
    closeUserMenu();
    const modal = document.getElementById('secretQuestionModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeSecretQuestionModal() {
    const modal = document.getElementById('secretQuestionModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Modal functionality for profile
function openProfileModal() {
    closeUserMenu();
    const modal = document.getElementById('profileModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeProfileModal() {
    const modal = document.getElementById('profileModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    // Close user menu dropdown
    const userMenu = document.getElementById('userMenu');
    const userTrigger = document.querySelector('.user-profile-trigger');

    if (userMenu && userTrigger && !userTrigger.contains(event.target) && !userMenu.contains(event.target)) {
        closeUserMenu();
    }

    // Close modal when clicking outside
    const modal = document.getElementById('changePasswordModal');
    if (modal && event.target === modal) {
        closeChangePasswordModal();
    }
});

// Close on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeUserMenu();
        closeChangePasswordModal();
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    if (window.innerWidth > 768) {
        const overlay = document.getElementById('sidebarOverlay');
        const sidebar = document.getElementById('sidebar');

        overlay.classList.remove('show');
        sidebar.classList.remove('show');
    }
});

// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            // Implement search functionality here
            console.log('Search query:', query);
        });
    }
});

// Navigation functions for dashboard buttons
function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    // Show the selected section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');

        // Update URL without page reload
        const newUrl = `/${sectionId}`;
        window.history.pushState({ section: sectionId }, '', newUrl);

        // Update sidebar active state if it exists
        const sidebarLinks = document.querySelectorAll('.nav-link, .sidebar button');
        sidebarLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `/${sectionId}` ||
                link.onclick?.toString().includes(sectionId)) {
                link.classList.add('active');
            }
        });
    } else {
        // If section doesn't exist on current page, navigate to it
        window.location.href = `/${sectionId}`;
    }
}

function generateReport() {
    // Open reports page in a new tab/window
    const reportWindow = window.open('/reports', '_blank', 'width=1200,height=800');

    // If popup is blocked, navigate to reports page
    if (!reportWindow || reportWindow.closed || typeof reportWindow.closed == 'undefined') {
        window.location.href = '/reports';
    }
}

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.section) {
        showSection(event.state.section);
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('POS System initialized');

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Processing...';
            }
        });
    });

    // Add modal close functionality
    const closeBtn = document.querySelector('.modal-close');
    if (closeBtn) {
        closeBtn.onclick = closeChangePasswordModal;
    }

    // Handle keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // ESC to close modal
        if (e.key === 'Escape') {
            closeChangePasswordModal();
        }

        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });

    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
