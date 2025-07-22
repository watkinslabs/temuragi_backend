// Sidebar state management
const SIDEBAR_STATE_KEY = 'sidebar_state';
const SIDEBAR_SECTIONS_BASE_KEY = 'sidebar_expanded_sections';

function get_menu_id() {
    const sidebar = document.querySelector('.sidebar[data_menu_id], #sidebar[data_menu_id]');
    return sidebar ? sidebar.getAttribute('data_menu_id') : null;
}

function get_sections_key() {
    const menu_id = get_menu_id();
    return menu_id ? `${SIDEBAR_SECTIONS_BASE_KEY}_${menu_id}` : null;
}

function toggle_sidebar() {
    const content_area = document.querySelector('.content_area');
    const sidebar_toggle = document.querySelector('.sidebar_toggle i');
    
    content_area.classList.toggle('collapsed');
    
    // Update the icon direction
    if (content_area.classList.contains('collapsed')) {
        sidebar_toggle.className = 'fas fa-chevron-right';
    } else {
        sidebar_toggle.className = 'fas fa-chevron-left';
    }
    
    // Save state
    localStorage.setItem(SIDEBAR_STATE_KEY, content_area.classList.contains('collapsed') ? 'collapsed' : 'expanded');
}

function toggle_nav_item(element) {
    if (!element.classList.contains('has_children')) {
        return;
    }
    
    event.stopPropagation();
    element.classList.toggle('expanded');
    
    // Save expanded sections state
    save_sidebar_sections();
}

function save_sidebar_sections() {
    const sections_key = get_sections_key();
    
    // If no menu_id, don't save state
    if (!sections_key) {
        return;
    }
    
    const expanded_sections = [];
    document.querySelectorAll('.nav_item.expanded[data-section]').forEach(item => {
        const section = item.getAttribute('data-section');
        if (section) {
            expanded_sections.push(section);
        }
    });
    
    localStorage.setItem(sections_key, JSON.stringify(expanded_sections));
}

function restore_sidebar_state() {
    // Restore sidebar collapsed state (shared across all menus)
    const sidebar_state = localStorage.getItem(SIDEBAR_STATE_KEY);
    if (sidebar_state === 'collapsed') {
        const content_area = document.querySelector('.content_area');
        if (content_area) {
            content_area.classList.add('collapsed');
        }
        // Also update the icon
        const sidebar_toggle = document.querySelector('.sidebar_toggle i');
        if (sidebar_toggle) {
            sidebar_toggle.className = 'fas fa-chevron-right';
        }
    }
    
    // Handle expanded sections based on menu_id
    const menu_id = get_menu_id();
    
    if (!menu_id) {
        // No menu_id - expand all sections
        document.querySelectorAll('.nav_item.has_children').forEach(item => {
            item.classList.add('expanded');
        });
    } else {
        // Restore expanded sections for this specific menu
        const sections_key = get_sections_key();
        const expanded_sections = JSON.parse(localStorage.getItem(sections_key) || '[]');
        
        expanded_sections.forEach(section => {
            const element = document.querySelector(`.nav_item[data-section="${section}"]`);
            if (element) {
                element.classList.add('expanded');
            }
        });
    }
    
    // Set active item based on current URL
    const current_path = window.location.pathname;
    document.querySelectorAll('.nav_item').forEach(item => {
        const onclick = item.getAttribute('onclick');
        if (onclick && onclick.includes('window.location.href') && onclick.includes(current_path)) {
            item.classList.add('active');
            
            // Expand parent sections
            let parent = item.closest('.nav_children');
            while (parent) {
                const parent_item = parent.previousElementSibling;
                if (parent_item && parent_item.classList.contains('has_children')) {
                    parent_item.classList.add('expanded');
                }
                parent = parent.parentElement.closest('.nav_children');
            }
        }
    });
    
    // Save state after setting active items (only if we have a menu_id)
    if (menu_id) {
        save_sidebar_sections();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', restore_sidebar_state);