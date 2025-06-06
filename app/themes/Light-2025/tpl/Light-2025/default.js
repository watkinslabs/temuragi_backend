<script>
    
    $(document).ready(function () {
        $('.toggle-favorite').bind('click', function () {
            var $button = $(this);
            var itemId = $button.attr('data-id');
            var action = $button.attr('data-action');
    
            $.ajax({
                url: '/menu/add_to_favorites',
                type: 'POST',
                contentType: 'application/json; charset=utf-8',
                data: JSON.stringify({ item_id: itemId, action: action }),
                success: function (data) {
                    if (data.status === 'success') {
                        // Toggle button icon and action
                        var $icon = $button.find('i');
                        if (action === 'add') {
                            $button.attr('data-action', 'remove');
                            $icon.removeClass('fa-plus-square').addClass('fa-minus-square'); // Change to minus icon
                        } else {
                            $button.attr('data-action', 'add');
                            $icon.removeClass('fa-minus-square').addClass('fa-plus-square'); // Change to plus icon
                        }
                    } else {
                        alert('Error: ' + data.message);
                    }
                },
                error: function (xhr, status, error) {
                    console.error('Error:', error);
                    alert('An error occurred while updating the quick link.');
                }
            });
        });
    
        {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        var flash_content = '';
        var modal_category = 'info'; // Default category
        var modal_title = 'Notification'; // Default title
        
        {% for category, message in messages %}
            flash_content += '<div class="alert alert-{{ category }}">' + 
                            '{{ message|safe }}' + 
                            '</div>';
            
            // Set the modal header style based on the first message category
            {% if loop.first %}
                modal_category = '{{ category }}';
                // Update title based on category
                if ('{{ category }}' === 'success') {
                    modal_title = 'Success';
                } else if ('{{ category }}' === 'error' || '{{ category }}' === 'danger') {
                    modal_title = 'Error';
                } else if ('{{ category }}' === 'warning') {
                    modal_title = 'Warning';
                } else if ('{{ category }}' === 'info') {
                    modal_title = 'Information';
                }
            {% endif %}
        {% endfor %}
        
        // Insert flash messages into modal
        $('#flash-modal-content').html(flash_content);
        
        // Update modal header style and title
        var modalHeader = $('#flashModal .modal-header');
        modalHeader.removeClass('modal-header-success modal-header-danger modal-header-warning modal-header-info');
        
        if (modal_category === 'success') {
            modalHeader.addClass('modal-header-success');
        } else if (modal_category === 'error' || modal_category === 'danger') {
            modalHeader.addClass('modal-header-danger');
        } else if (modal_category === 'warning') {
            modalHeader.addClass('modal-header-warning');
        } else {
            modalHeader.addClass('modal-header-info');
        }
        
        // Update modal title
        $('#flashModalLabel').text(modal_title);
        
        // Show the modal
        var flashModal = new bootstrap.Modal(document.getElementById('flashModal'));
        flashModal.show();
    {% endif %}
{% endwith %}
    
    
    });

</script>
