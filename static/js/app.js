/* ===== CRM Pro — Global JavaScript ===== */

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileToggle');
    const overlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            const main = document.querySelector('.main-content');
            if (sidebar.classList.contains('collapsed')) {
                sidebar.style.width = '64px';
                main.style.marginLeft = '64px';
                sidebar.querySelectorAll('.nav-item span, .sidebar-logo span, .user-details, .sidebar-footer').forEach(el => {
                    el.style.display = 'none';
                });
            } else {
                sidebar.style.width = '';
                main.style.marginLeft = '';
                sidebar.querySelectorAll('.nav-item span, .sidebar-logo span, .user-details, .sidebar-footer').forEach(el => {
                    el.style.display = '';
                });
            }
        });
    }

    // Mobile Sidebar
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }

    // Auto-dismiss flash messages
    document.querySelectorAll('.flash-message').forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
});
