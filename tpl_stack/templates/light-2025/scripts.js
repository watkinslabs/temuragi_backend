<script>
$(document).ready(function() {
    // Theme and page configuration
    const config = {
        theme: {
            enable_animations: {{ theme.enable_animations|lower }},
            enable_transitions: {{ theme.enable_transitions|lower }},
            transition_duration: '{{ theme.transition_duration }}'
        },
        page: {
            cache_duration: {{ page.cache_duration }},
            requires_auth: {{ page.requires_auth|lower }},
            published: {{ page.published|lower }}
        }
    };

    // Flash message handling
    {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        let flash_content = '';
        let modal_title = 'Notification';
        
        {% for category, message in messages %}
            flash_content += `<div class="alert alert-{{ category }}" role="alert">{{ message|safe }}</div>`;
            
            {% if loop.first %}
                switch('{{ category }}') {
                    case 'success': modal_title = 'Success'; break;
                    case 'error':
                    case 'danger': modal_title = 'Error'; break;
                    case 'warning': modal_title = 'Warning'; break;
                    default: modal_title = 'Information';
                }
            {% endif %}
        {% endfor %}

        $('#flash-modal-content').html(flash_content);
        $('#flashModalLabel').text(modal_title);
        
        const flash_modal = new bootstrap.Modal('#flashModal');
        flash_modal.show();
    {% endif %}
    {% endwith %}

    // Page cache headers
    {% if page.cache_duration and page.cache_duration > 0 %}
    $('head').append('<meta http-equiv="Cache-Control" content="max-age={{ page.cache_duration }}">');
    {% endif %}

    // Page expiration check
    {% if page.expire_date %}
    const expire_date = new Date('{{ page.expire_date }}');
    if (new Date() > expire_date) {
        console.warn('Page expired on {{ page.expire_date }}');
    }
    {% endif %}

    // Enhanced form handling
    $('form').on('submit', function() {
        const $btn = $(this).find('button[type="submit"]');
        if ($btn.length) {
            $btn.prop('disabled', true).append(' <i class="fas fa-spinner fa-spin"></i>');
        }
    });

    // Auto-dismiss alerts
    $('.alert:not(.alert-permanent)').delay(5000).fadeOut();

    // Enhanced tooltips and popovers
    if (typeof bootstrap !== 'undefined') {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(el => new bootstrap.Tooltip(el));
        
        const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
        popovers.forEach(el => new bootstrap.Popover(el));
    }
});
</script>