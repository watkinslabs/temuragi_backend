function toggle_nine_dot_dropdown() {
    const dropdown = document.getElementById('nine_dot_dropdown');
    dropdown.classList.toggle('show');
}

function toggle_theme() {
    const toggle = document.getElementById('dark_mode_toggle');
    const html = document.documentElement;

    if (toggle.checked) {
        html.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme_preference', 'dark');
    } else {
        html.setAttribute('data-theme', 'light');
        localStorage.setItem('theme_preference', 'light');
    }
}

function get_theme_preference() {
    const saved_preference = localStorage.getItem('theme_preference');
    if (saved_preference !== null) {
        return saved_preference;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function apply_theme(theme) {
    const html = document.documentElement;
    const toggle = document.getElementById('dark_mode_toggle');
    
    html.setAttribute('data-theme', theme);
    if (toggle) {
        toggle.checked = theme === 'dark';
    }
    localStorage.setItem('theme_preference', theme);
}

function reset_theme_to_auto() {
    localStorage.removeItem('theme_preference');
    const system_theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    apply_theme(system_theme);
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    const preferred_theme = get_theme_preference();
    apply_theme(preferred_theme);
});

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const menu = document.querySelector('.nine_dot_menu');
    const dropdown = document.getElementById('nine_dot_dropdown');

    if (!menu.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

