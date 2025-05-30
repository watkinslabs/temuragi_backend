# routes/menu_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .model import Menu

bp = Blueprint('menu', __name__, url_prefix='/menu', template_folder="templates")



'''
# Available icons for menu items
AVAILABLE_ICONS = [
    {'value': 'fa-folder', 'label': 'folder'},
    {'value': 'fa-home', 'label': 'home'},
    {'value': 'fa-user', 'label': 'user'},
    {'value': 'fa-cog', 'label': 'cog'},
    {'value': 'fa-chart-bar', 'label': 'chart-bar'},
    {'value': 'fa-file-alt', 'label': 'file-alt'},
    {'value': 'fa-users', 'label': 'users'},
    {'value': 'fa-box', 'label': 'box'},
    {'value': 'fa-link', 'label': 'link'},
    {'value': 'fa-list', 'label': 'list'},
    {'value': 'fa-plus-circle', 'label': 'plus-circle'},
]

@bp.route('/editor')
def editor():
    """Main menu editor view"""
    # Create menu model instance
    menu_model = MenuModel(db=request.db)
    
    # Get selected item ID from query param
    selected_item_id = request.args.get('item_id', type=int)
    selected_item = None
    
    if selected_item_id:
        selected_item = menu_model.get_item_by_id(selected_item_id)
        if selected_item:
            # Add children count for warnings in deletion
            selected_item.children_count = menu_model.get_children_count(selected_item_id)
    
    # Get menu structure and parent options
    menu_items = menu_model.get_menu_tree()
    parent_options = menu_model.get_parent_options()
    
    return render_template(
        'menu/editor.html',
        menu_items=menu_items,
        selected_item=selected_item,
        selected_item_id=selected_item_id,
        parent_options=parent_options,
        available_icons=AVAILABLE_ICONS
    )

@bp.route('/add_category', methods=['POST'])
def add_category():
    """Add a new category"""
    menu_model = MenuModel(db=request.db)
    
    # Get form data
    name = request.form.get('name', '').lower().replace(' ', '_')
    display = request.form.get('display')
    icon = request.form.get('icon')
    link = request.form.get('link', '')  # Optional for categories
    parent_id = request.form.get('parent_id', type=int)
    parent_id = parent_id if parent_id != 0 else None  # Convert 0 to None
    
    # Basic validation
    if not name or not display:
        flash('Category name and display text are required', 'danger')
        return redirect(url_for('menu.editor'))
    
    # Add the category
    success, result = menu_model.add_menu_item(
        name=name,
        display=display,
        link=link,
        icon=icon,
        is_category=True,
        is_visible=True,
        is_active=True,
        is_development=False,
        is_new_tab=False,
        parent_id=parent_id
    )
    
    if success:
        flash('Category added successfully', 'success')
        return redirect(url_for('menu.editor', item_id=result))
    else:
        flash(result, 'danger')
        return redirect(url_for('menu.editor'))

@bp.route('/add_item', methods=['POST'])
def add_item():
    """Add a new menu item"""
    menu_model = MenuModel(db=request.db)
    
    # Get form data
    name = request.form.get('name', '').lower().replace(' ', '_')
    display = request.form.get('display')
    icon = request.form.get('icon')
    link = request.form.get('link')
    parent_id = request.form.get('parent_id', type=int)
    parent_id = parent_id if parent_id != 0 else None  # Convert 0 to None
    is_new_tab = request.form.get('is_new_tab', '') == 'on'
    
    # Basic validation
    if not name or not display or not link:
        flash('Name, display text, and link are required for menu items', 'danger')
        return redirect(url_for('menu.editor'))
    
    # Add the menu item
    success, result = menu_model.add_menu_item(
        name=name,
        display=display,
        link=link,
        icon=icon,
        is_category=False,
        is_visible=True,
        is_active=True,
        is_development=False,
        is_new_tab=is_new_tab,
        parent_id=parent_id
    )
    
    if success:
        flash('Menu item added successfully', 'success')
        return redirect(url_for('menu.editor', item_id=result))
    else:
        flash(result, 'danger')
        return redirect(url_for('menu.editor'))

@bp.route('/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    """Update an existing menu item"""
    menu_model = MenuModel(db=request.db)
    
    # Get current item to check if it exists
    current_item = menu_model.get_item_by_id(item_id)
    if not current_item:
        flash('Menu item not found', 'danger')
        return redirect(url_for('menu.editor'))
    
    # Get form data
    name = request.form.get('name', '').lower().replace(' ', '_')
    display = request.form.get('display')
    icon = request.form.get('icon')
    link = request.form.get('link', '')
    is_visible = request.form.get('is_visible', '') == 'on'
    is_active = request.form.get('is_active', '') == 'on'
    is_development = request.form.get('is_development', '') == 'on'
    is_new_tab = request.form.get('is_new_tab', '') == 'on'
    order = request.form.get('order', type=int) or 0
    
    # We don't allow changing parent from the update form to avoid
    # creating loops in the hierarchy - that should be done via drag-drop
    
    # Basic validation
    if not name or not display:
        flash('Name and display text are required', 'danger')
        return redirect(url_for('menu.editor', item_id=item_id))
    
    # Update the item
    success, message = menu_model.update_menu_item(
        item_id=item_id,
        name=name,
        display=display,
        link=link,
        icon=icon,
        is_visible=is_visible,
        is_active=is_active,
        is_development=is_development,
        is_new_tab=is_new_tab,
        menu_order=order,
        parent_id=current_item.parent_id  # Keep the same parent
    )
    
    if success:
        flash('Menu item updated successfully', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('menu.editor', item_id=item_id))

@bp.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    """Delete a menu item and its children"""
    menu_model = MenuModel(db=request.db)
    
    # Get item to be deleted
    item = menu_model.get_item_by_id(item_id)
    if not item:
        flash('Menu item not found', 'danger')
        return redirect(url_for('menu.editor'))
    
    # Delete the item
    success, message = menu_model.delete_menu_item(item_id)
    
    if success:
        flash(f'Menu item "{item.display}" deleted successfully', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('menu.editor'))

@bp.route('/reorder', methods=['POST'])
def reorder_items():
    """Reorder menu items via AJAX"""
    # This endpoint receives JSON data
    menu_model = MenuModel(db=request.db)
    
    # Example request data:
    # { items: [{id: 1, parent_id: null, order: 0}, {id: 2, parent_id: 1, order: 0}] }
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'success': False, 'message': 'Invalid data format'})
    
    # Process the reordering
    success, message = menu_model.reorder_menu_items(data['items'])
    
    return jsonify({'success': success, 'message': message})

@bp.route('/get_menu', methods=['GET'])
def get_menu():
    """API endpoint to get the current menu structure"""
    menu_model = MenuModel(db=request.db)
    menu_items = menu_model.get_menu_tree()
    
    # Filter only visible and active items if requested
    visible_only = request.args.get('visible_only', '').lower() == 'true'
    active_only = request.args.get('active_only', '').lower() == 'true'
    hide_dev = request.args.get('hide_dev', '').lower() == 'true'
    
    if visible_only or active_only or hide_dev:
        # Filter recursively
        filtered_items = []
        for item in menu_items:
            include = True
            
            if visible_only and not item.get('is_visible', False):
                include = False
            if active_only and not item.get('is_active', False):
                include = False
            if hide_dev and item.get('is_development', False):
                include = False
                
            if include:
                # Filter children using the same criteria
                if 'children' in item:
                    filtered_children = []
                    for child in item['children']:
                        include_child = True
                        if visible_only and not child.get('is_visible', False):
                            include_child = False
                        if active_only and not child.get('is_active', False):
                            include_child = False
                        if hide_dev and child.get('is_development', False):
                            include_child = False
                            
                        if include_child:
                            filtered_children.append(child)
                    
                    item['children'] = filtered_children
                
                filtered_items.append(item)
        
        menu_items = filtered_items
    
    return jsonify({'menu': menu_items})


    '''