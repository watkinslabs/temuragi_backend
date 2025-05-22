from flask import g, current_app, request

class MenuBuilder:
    CLASSNAMES = {
        'ACCORDION_ITEM': 'accordion-item',
        'ACCORDION_HEADER': 'accordion-header',
        'ACCORDION_BUTTON': 'accordion-button',
        'ACCORDION_COLLAPSE': 'accordion-collapse',
        'ACCORDION_BODY': 'accordion-body',
        'LIST_GROUP_ITEM': 'list-group-item',
        'LIST_GROUP_ACTION': 'list-group-item-action',
        'LEVEL_2': 'level-2',
        'LEVEL_3': 'level-3',
        'ICON': 'icon',
        'COLLAPSED': 'collapsed',
        'COLLAPSE': 'collapse'
    }

    def __init__(self, controller, page, user_id, current_menu_id, mega_menu=False, show_icons=True,quick_links=None,menu_links=None):
        self.controller = controller
        self.page = page
        self.mega_menu = mega_menu
        self.prefix = 'mega' if mega_menu else 'sidebar'
        self.user_id = user_id
        self.current_menu_id = current_menu_id
        self.show_icons = show_icons
        self.id = None
        self.parent_id = None
        self.title = None
        self.menu_links = None
        self.menu = None
        self.html = ""
        self.breadcrumb_path = []
        self.breadcrumbs = ""
        self.is_quicklink = False
        self.ITEMS_PER_COLUMN =24  # Maximum items before creating a new column
        self.COLUMNS_PER_SECTION = 5  # Number of columns to split sections into
        self.quick_links=quick_links
        self.menu_links=menu_links

        # Define specific icons for the menu items
        self.icons = {
            'Accounting': 'fa-coins',
            'Catalog': 'fa-book',
            'Customer Account': 'fa-user',
            'Inventory': 'fa-boxes',
            'Marketing': 'fa-bullhorn',
            'Operations': 'fa-cogs',
            'Settings': 'fa-cog',
            'Support': 'fa-headset',
            'T$html_fragment .=ps': 'fa-tools',
            'Warehouse': 'fa-warehouse',
            'Sales': 'fa-chart-line',
            'Action': 'fa-bolt',
            'Actions': 'fa-bolt',
            'Report': 'fa-file-alt',
            'Reports': 'fa-file-alt',
            'Data Base Tools': 'fa-database',
            'Technical Details': 'fa-code',
            'Administrative': 'fa-user-shield',
            'My Account': 'fa-user-circle',
            'Customer': 'fa-users',
            'DocCenter': 'fa-folder-open'
        }
        
        self.generate_tree()
        
        self.search_breadcrumb(self.menu_tree[0], self.page, self.controller, [])
        self.breadcrumbs = self.generate_breadcrumb_html()

        if mega_menu:
            self.html = self.generate_mega_menu(self.menu_tree)
        else:
            self.html = self.build_sidebar(self.menu_tree)

    def get_link_by_id(self, id):
        """Find a specific link by its ID"""
        for quick_link in self.menu_links:
            if quick_link['id'] == id:
                return quick_link
        return None  # Return None if no link with the given ID is found

    def prune_menu(self, menu, depth=0):
        """Remove menu items without children at depth 0 or 1"""
        keys_to_unset = []  # Store keys to unset after the iteration
        
        for idx, item in enumerate(menu):
            # Recursively prune children first
            if 'children' in item:
                self.prune_menu(item['children'], depth + 1)
                
                # Recount children after pruning
                item['childrenCount'] = len(item['children'])
                if item['childrenCount'] == 0:
                    del item['children']
            
            # Mark items at depth 0 or 1 for removal if they have no children
            if (depth == 0 or depth == 1) and ('children' not in item or item['childrenCount'] == 0):
                keys_to_unset.append(idx)
        
        # Remove marked items outside of the loop (in reverse order to maintain indices)
        for idx in sorted(keys_to_unset, reverse=True):
            del menu[idx]

    def add_node(self, item, array, depth):
        """Recursively add nodes to the menu tree"""
        # Skip menu items that aren't menu links
        if 'menu_link' in item and item['menu_link'] == '0':
            return

        # Get the ID with a default of 0
        id = item.get('id', 0)
        
        # If this ID doesn't exist in the array yet, add it
        if id not in array:
            array[id] = {
                'parent_id': item.get('parent_id', 0),
                'id': id,
                'depth': depth,
                'item': item,
                'children': []  # Initialize as a list, not a dictionary
            }

        # Process child items
        for sub_item_id, sub_item in self.menu.items():
            # Check if this is a child of the current item
            if sub_item.get('parent_id') == id:
                depth += 1
                # Pass the correct array location
                child_array = {}  # Temporary dictionary for this child
                self.add_node(sub_item, child_array, depth)
                # If child has been added to the temporary array, add it to the children list
                if sub_item_id in child_array:
                    array[id]['children'].append(child_array[sub_item_id])
                depth -= 1
        
        # Calculate number of children
        array[id]['childrenCount'] = len(array[id]['children'])
        # Remove children key if empty
        if array[id]['childrenCount'] == 0:
            del array[id]['children']

    def generate_tree(self):
        """Generate the complete menu tree structure"""
        # Process quick_links if any
        quick_links_tree = {}
        if self.quick_links:
            quick_links_tree = {
                'parent_id': 0,
                'id': -1,  # Unique ID for quick_links section
                'open': True,
                'depth': 0,
                'item': {'title': 'Quick Links'},
                'children': []
            }
            
            if self.mega_menu:
                quick_links_tree['children'] = [
                    {
                        'parent_id': -1,
                        'id': -2,  # Unique ID for quick_links section
                        'open': True,
                        'depth': 0,
                        'item': {'title': 'User Links'},
                        'children': []
                    }
                ]
                
                for quick_link in self.quick_links:
                    quick_links_tree['children'][0]['children'].append({
                        'parent_id': 0,
                        'id': quick_link['permission_id'],
                        'depth': 0,
                        'open': False,
                        'item': self.get_link_by_id(quick_link['permission_id']),
                        'children': []
                    })
            else:
                for quick_link in self.quick_links:
                    quick_links_tree['children'].append({
                        'parent_id': 0,
                        'id': quick_link['permission_id'],
                        'depth': 0,
                        'open': False,
                        'item': self.get_link_by_id(quick_link['permission_id']),
                        'children': []
                    })
                    
            quick_links_tree['childrenCount'] = len(quick_links_tree['children'])
            quick_links_tree['isQuicklinks'] = True
        
        # Generate menu tree
        item_index = {}
        quicklink_pages = [link['permission_id'] for link in self.quick_links]
        
        # Get current request URI from Flask instead of using environment variables
        current_uri = request.path
        
        for item in self.menu_links:
            # Safely get and strip values, checking for None or missing keys
            folder = item.get('folder', '')
            folder = folder.strip() if folder is not None else ''
            
            controller = item.get('controller', '')
            controller = controller.strip() if controller is not None else ''
            
            page = item.get('page', '')
            page = page.strip() if page is not None else ''
            
            uri = "/" + folder + "/" + controller + "/" + page
            uri = uri.replace("//", "/")
            
            # Check if this is the current URI
            if current_uri == uri:
                self.title = item.get('title')
                self.id = item.get('id')
                self.parent_id = item.get('parent_id')
                self.is_quicklink = self.id in quicklink_pages
                
            item_index[item['id']] = item
            
        self.menu = item_index
        root_id = 0
        tree = {}
        depth = 0
        tree[root_id] = {
            'parent_id': 0,
            'id': 0,
            'depth': 0,
            'open': True,
            'item': {'title': 'root'},
            'children': []
        }
        
        self.add_node({'id': 0}, tree, depth)
        #print(tree)
        self.prune_menu(tree[root_id]['children'], depth)
        
        # Append quick_links at the top if any exist
        if quick_links_tree:
            if 'children' not in tree[root_id]:
                tree[root_id]['children'] = []
                
            # Insert at the beginning
            tree[root_id]['children'].insert(0, quick_links_tree)
            tree[root_id]['childrenCount'] = len(tree[root_id]['children'])
            
        self.menu_tree = tree

    def get_class(self, class_name, additional=''):
        """Get CSS class name with prefix"""
        class_str = f"{self.prefix}-{self.CLASSNAMES[class_name].lower()}"
        return f"{class_str} {additional}" if additional else class_str

    def render_icon(self, title, level=0):
        """Render an icon based on the menu title and level"""
        if not self.show_icons:
            return ''
        
        if title in self.icons:
            icon_class = self.icons[title]
        elif level == 0:
            icon_class = 'fa-folder'
        elif level == 1:
            icon_class = 'fa-layer-group'
        else:
            icon_class = 'fa-dot-circle'
        
        return f"<i class='fas {icon_class} sidebar_icon'></i>"

    def build_sidebar(self, tree, parent_id="accordionSidebar", level=0, has_siblings=False):
        """Build HTML for sidebar menu"""
        html_fragment = ""
        
        if level == 0 and 0 in tree and tree[0]['id'] == 0:
            tree = tree[0]['children']
        
        has_siblings = len(tree) > 1
        
        for key, item in enumerate(tree):
            if 'item' in item:
                # Safely get title and path components
                title = item['item'].get('title', '')
                
                # Safely get and strip path components
                folder = item['item'].get('folder', '')
                folder = folder.strip() if folder is not None else ''
                
                controller = item['item'].get('controller', '')
                controller = controller.strip() if controller is not None else ''
                
                page = item['item'].get('page', '')
                page = page.strip() if page is not None else ''
                
                item_uri = "/" + folder + "/" + controller + "/" + page
                item_uri = item_uri.replace("//", "/")
                
                has_children = 'children' in item and len(item['children']) > 0
                collapsed_class = "collapsed"
                collapse_class = "collapse"
                
                if not has_siblings:
                    collapsed_class = ""
                    collapse_class = ""
                    
                if item.get('open', False) == True:
                    collapsed_class = ""
                    collapse_class = ""
                
                if has_children:
                    # Safely get ID
                    item_id = item['item'].get('id', 'unknown')
                    collapse_id = f"collapse-{item_id}"
                    
                    html_fragment += "<div class='accordion-item sidebar_accordion_item'>"
                    
                    # Main Menu Items
                    if level == 0:
                        icon_class = self.icons.get(title, 'fa-folder')
                        html_fragment += f"<h2 class='accordion-header sidebar_accordion_header' id='heading-{collapse_id}'>"
                        html_fragment += f"<button class='accordion-button sidebar_accordion_button {collapsed_class}' type='button' data-bs-toggle='collapse' data-bs-target='#{collapse_id}' aria-expanded='false' aria-controls='{collapse_id}'>"
                        html_fragment += f"<i class='fas {icon_class} sidebar_icon'></i>"
                        html_fragment += f"{title}"
                        html_fragment += "</button>"
                        html_fragment += "</h2>"
                    
                    # Submenu Items
                    elif level == 1:
                        icon_class = self.icons.get(title, 'fa-layer-group')
                        html_fragment += f"<h2 class='accordion-header sidebar_accordion_header' id='heading-{collapse_id}'>"
                        html_fragment += f"<button class='accordion-button sidebar_accordion_button {collapsed_class} sidebar_level_2' type='button' data-bs-toggle='collapse' data-bs-target='#{collapse_id}' aria-expanded='false' aria-controls='{collapse_id}'>"
                        html_fragment += f"<i class='text-secondary fas {icon_class} sidebar_icon'></i>"
                        html_fragment += f"{title}"
                        html_fragment += "</button>"
                        html_fragment += "</h2>"
                    
                    # Collapsible Submenu
                    html_fragment += f"<div id='{collapse_id}' class='accordion-collapse sidebar_accordion_collapse {collapse_class}' aria-labelledby='heading-{collapse_id}' data-bs-parent='#{parent_id}'>"
                    html_fragment += "<div class='accordion-body sidebar_accordion_body'>"
                    
                    # Recursive call for generating children
                    html_fragment += self.build_sidebar(item['children'], collapse_id, level + 1)
                    
                    html_fragment += "</div>"
                    html_fragment += "</div>"
                    html_fragment += "</div>"
                else:
                    # Leaf Items (No Children)
                    icon_class = self.icons.get(title, 'fa-dot-circle')
                    html_fragment += f"<a href='{item_uri}' class='list-group-item list-group-item-action sidebar_list_group_item sidebar_list_group_item_action sidebar_level_3'>"
                    html_fragment += f"{title}"
                    html_fragment += "</a>"
        
        return html_fragment

    def generate_mega_menu(self, tree):
        """Generate HTML for mega menu"""
        html_fragment = "<div class='mega-menu-container'>"
        html_fragment += "<nav class='mega-menu'><div class='container-fluid'><ul class='mega-menu-list'>"
        
        # Store content panes to be appended after the menu
        content_panes = ""
        
        if 0 in tree and 'children' in tree[0]:
            for item in tree[0]['children']:
                if 'item' in item:
                    title = item['item'].get('title', '')
                    has_children = 'children' in item and len(item['children']) > 0
                    
                    if has_children:
                        menu_id = f"mega-menu-{title.lower().replace(' ', '-')}"
                        menu_id = ''.join(c for c in menu_id if c.isalnum() or c == '-')
                        
                        # Menu item
                        html_fragment += "<li class='mega-menu-item'>"
                        icon_class = self.icons.get(title, 'fa-folder')
                        active = ""
                        
                        # Check if this is the active item
                        if (self.breadcrumb_path and 
                            len(self.breadcrumb_path) > 0 and 
                            'id' in self.breadcrumb_path[0] and 
                            self.breadcrumb_path[0]['id'] == item['id']):
                            active = " active"
                        
                        html_fragment += f"<a href='#' class='mega-menu-link{active}' data-target='{menu_id}'>"
                        if self.show_icons:
                            html_fragment += f"<i class='fas {icon_class} mega-menu-icon'></i>"
                        html_fragment += f"{title}"
                        html_fragment += "</a>"
                        html_fragment += "</li>"
                        
                        # Content pane
                        content_panes += f"<div id='{menu_id}' class='mega-menu-content'>"
                        content_panes += "<div class='container-fluid'><div class='row'>"
                        
                        # Calculate number of columns needed
                        num_of_columns = 0
                        for child in item['children']:
                            if 'children' in child:
                                num_of_columns += (len(child['children']) + 24) // 25

                        
                        col_width =  12 // max(4, num_of_columns)
                        
                        # Group children into specified number of columns
                        columns = []
                        chunk_size = max(1, (len(item['children']) + self.COLUMNS_PER_SECTION - 1) // self.COLUMNS_PER_SECTION)
                        for i in range(0, len(item['children']), chunk_size):
                            columns.append(item['children'][i:i + chunk_size])
                        
                        for column in columns:
                            if col_width<=2:
                                content_panes += f"<div class='col'>"
                            else:
                                content_panes += f"<div class='col-md-{col_width}'>"
                            
                            for child in column:
                                if 'item' in child:
                                    child_title = child['item'].get('title', '')
                                    
                                    # Safely get and strip path components
                                    folder = child['item'].get('folder', '')
                                    folder = folder.strip() if folder is not None else ''
                                    
                                    controller = child['item'].get('controller', '')
                                    controller = controller.strip() if controller is not None else ''
                                    
                                    page = child['item'].get('page', '')
                                    page = page.strip() if page is not None else ''
                                    
                                    child_uri = "/" + folder + "/" + controller + "/" + page
                                    child_uri = child_uri.replace("//", "/")
                                    
                                    if 'children' in child and len(child['children']) > 0:
                                        # Subgroup header
                                        content_panes += "<h6 class='mega-menu-group'>"
                                        child_icon_class = self.icons.get(child_title, 'fa-layer-group')
                                        if self.show_icons:
                                            content_panes += f"<i class='fas {child_icon_class}'></i> "
                                        
                                        content_panes += f"{child_title}</h6>"
                                        content_panes += "<ul class='mega-menu-sub-list'>"
                                        
                                        item_count = 0
                                        for sub_child in child['children']:
                                            if 'item' in sub_child:
                                                # Check if we need to start a new column
                                                if item_count == self.ITEMS_PER_COLUMN:
                                                    content_panes += f"</ul></div><div class='col-md-{col_width}'>"
                                                    # Repeat the header for the new column
                                                    content_panes += "<h6 class='mega-menu-group'>"
                                                    if self.show_icons:
                                                        content_panes += f"<i class='fas {child_icon_class}'></i> "
                                                    content_panes += f"{child_title} (cont.)</h6>"
                                                    content_panes += "<ul class='mega-menu-sub-list'>"
                                                    item_count = 0
                                                
                                                sub_child_title = sub_child['item'].get('title', '')
                                                
                                                # Safely get and strip path components
                                                folder = sub_child['item'].get('folder', '')
                                                folder = folder.strip() if folder is not None else ''
                                                
                                                controller = sub_child['item'].get('controller', '')
                                                controller = controller.strip() if controller is not None else ''
                                                
                                                page = sub_child['item'].get('page', '')
                                                page = page.strip() if page is not None else ''
                                                
                                                sub_child_uri = "/" + folder + "/" + controller + "/" + page
                                                sub_child_uri = sub_child_uri.replace("//", "/")
                                                
                                                content_panes += f"<li><a href='{sub_child_uri}'>{sub_child_title}</a></li>"
                                                item_count += 1
                                        
                                        content_panes += "</ul>"
                            
                            content_panes += "</div>"  # End column
                        
                        content_panes += "</div></div><div class='mega_menu_bottom'></div></div>"  # End row, container-fluid, and mega-menu-content
        
        html_fragment += "</ul></div></nav>"
        html_fragment += content_panes
        html_fragment += "</div>"
        
        # Add JavaScript for menu interaction
        html_fragment += """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
                const menuLinks = document.querySelectorAll('.mega-menu-link');
                const contentPanes = document.querySelectorAll('.mega-menu-content');
                
                function deactivateAll() {
                    menuLinks.forEach(link => link.classList.remove('active'));
                    contentPanes.forEach(pane => pane.classList.remove('active'));
                }
                
                menuLinks.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const targetId = this.getAttribute('data-target');
                        
                        // If clicking active link, close it
                        if (this.classList.contains('active')) {
                            deactivateAll();
                            return;
                        }
                        
                        // Deactivate all, then activate clicked item
                        deactivateAll();
                        this.classList.add('active');
                        document.getElementById(targetId)?.classList.add('active');
                    });
                });
                
                // Close when clicking outside
                document.addEventListener('click', e => {
                    if (!e.target.closest('.mega-menu-container')) {
                        deactivateAll();
                    }
                });
            });
        </script>"""
        
        return html_fragment
    
    def search_breadcrumb(self, node, target_page, target_controller, current_path):
        """Recursively search for the page in the menu to build breadcrumbs"""
        # Skip if we've already found the path or if this is the quicklinks section
        if self.breadcrumb_path or (isinstance(node, dict) and node.get('id') == -1):
            return
        
        # Add current node to path if it's not the root
        if 'item' in node and node.get('id') != 0:
            current_path.append(node['item'])
        
        # Check if current node matches our target
        if ('item' in node and 
            'page' in node['item'] and 
            'controller' in node['item'] and 
            node['item']['page'] == target_page and 
            node['item']['controller'] == target_controller):
            self.breadcrumb_path = current_path.copy()
            return
        
        # Recurse through children if they exist
        if 'children' in node and isinstance(node['children'], (list, dict)):
            children = node['children'].values() if isinstance(node['children'], dict) else node['children']
            for child in children:
                self.search_breadcrumb(child, target_page, target_controller, current_path)

    def generate_breadcrumb_html(self):
        """Generate HTML for breadcrumb navigation"""
        html = '<nav aria-label="breadcrumb">'
        html += '<ol class="breadcrumb">'
        
        # Add home link
        html += '<li class="breadcrumb-item"><a href="/v2/home"><i class="fas fa-home"></i></a></li>'
        
        # Process each breadcrumb item
        if self.breadcrumb_path:
            total = len(self.breadcrumb_path)
            for index, crumb in enumerate(self.breadcrumb_path):
                is_last = (index == total - 1)
                
                # Safely get and strip path components
                folder = crumb.get('folder', '')
                folder = folder.strip() if folder is not None else ''
                
                controller = crumb.get('controller', '')
                controller = controller.strip() if controller is not None else ''
                
                page = crumb.get('page', '')
                page = page.strip() if page is not None else ''
                
                url = "/" + folder + "/" + controller + "/" + page
                url = url.replace("//", "/")
                
                # Get title safely
                title = crumb.get('title', 'Untitled')
                
                # Add breadcrumb item
                if is_last:
                    html += f'<li class="breadcrumb-item active" aria-current="page">{title}</li>'
                else:
                    html += f'<li class="breadcrumb-item">{title}</li>'
        else:
            # If no breadcrumb path found, use controller name
            html += f'<li class="breadcrumb-item active" aria-current="page">{self.controller.capitalize()}</li>'

        # Add favorite/remove buttons
        if self.id is not None:
            if self.is_quicklink:
                html += '''<li><button class="toggle-favorite btn btn-sm text-grey" type="button" 
                        data-id="''' + str(self.id) + '''" data-action="remove" 
                        aria-controls="navbarNav" aria-expanded="false" aria-label="Remove from favorites">
                    <i class="fas fa-minus-square"></i> <!-- Minus icon -->
                </button>
                </li>
                '''
            else:
                html += '''<li>
            <button class="toggle-favorite btn btn-sm text-grey" type="button" 
                    data-id="''' + str(self.id) + '''" data-action="add" 
                    aria-controls="navbarNav" aria-expanded="false" aria-label="Add to favorites">
                <i class="fas fa-plus-square"></i> <!-- Plus icon -->
            </button></li>'''
        
        html += '</ol>'
        html += '</nav>'
        
        return html

  