# Define some template examples as a class with template strings
class MenuTemplates:
    # Vertical sidebar menu
    SIDEBAR_MENU = """
    <nav class="sidebar-menu">
        {% for tier in menu.tiers %}
            <div class="menu-section">
                <h3 class="menu-section-title">
                    {% if tier.icon %}<i class="icon {{ tier.icon }}"></i>{% endif %}
                    {{ tier.display }}
                </h3>
                {% if tier.links %}
                    <ul class="menu-items">
                        {% for link in tier.links %}
                            <li class="menu-item {% if link.has_submenu %}has-submenu{% endif %}">
                                <a href="{{ link.url }}" class="menu-link" {% if link.new_tab %}target="_blank"{% endif %}>
                                    {% if link.icon %}<i class="icon {{ link.icon }}"></i>{% endif %}
                                    <span>{{ link.display }}</span>
                                </a>
                            </li>
                        {% endfor %}
                    </ul>
                {% endif %}
                
                {% if tier.children %}
                    {% for child in tier.children %}
                        <div class="submenu-section">
                            <h4 class="submenu-title">
                                {% if child.icon %}<i class="icon {{ child.icon }}"></i>{% endif %}
                                {{ child.display }}
                            </h4>
                            {% if child.links %}
                                <ul class="submenu-items">
                                    {% for link in child.links %}
                                        <li class="menu-item">
                                            <a href="{{ link.url }}" class="menu-link" {% if link.new_tab %}target="_blank"{% endif %}>
                                                {% if link.icon %}<i class="icon {{ link.icon }}"></i>{% endif %}
                                                <span>{{ link.display }}</span>
                                            </a>
                                        </li>
                                    {% endfor %}
                                </ul>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% endif %}
            </div>
        {% endfor %}
    </nav>
    """
    
    # Horizontal navigation bar
    NAVBAR_MENU = """
<div class="mega-menu-container">
  <nav class="mega-menu">
    <div class="container-fluid">
      <ul class="mega-menu-list">
        {% for tier in menu.tiers %}
          {% for menu_item in tier.children %}
            {% set title = menu_item.display %}
            {% set menu_id = 'mega-menu-' + title|lower|replace(' ', '-')|replace('&', 'and')|replace('!', '')|replace('?', '')|replace('#', '')|replace('%', '') %}
            
            {% set icon_class = menu_item.icon or 'fa-folder' %}
            {% set active = '' %}

            {% if breadcrumb_path and breadcrumb_path[0].display == title %}
              {% set active = ' active' %}
            {% endif %}

            <li class="mega-menu-item">
              <a href="#" class="mega-menu-link{{ active }}" data-target="{{ menu_id }}">
                {% if show_icons %}
                  <i class="fas {{ icon_class }} mega-menu-icon"></i>
                {% endif %}
                {{ title }}
              </a>
            </li>
          {% endfor %}
        {% endfor %}
      </ul>
    </div>
  </nav>

  {% for tier in menu.tiers %}
    {% for menu_item in tier.children %}
      {% set title = menu_item.display %}
      {% set menu_id = 'mega-menu-' + title|lower|replace(' ', '-')|replace('&', 'and')|replace('!', '')|replace('?', '')|replace('#', '')|replace('%', '') %}
      
      <div id="{{ menu_id }}" class="mega-menu-content">
        <div class="container-fluid">
          <div class="row">
            
            {% if menu_item.children %}
              <!-- Menu item has sub-categories (second level) -->
              {% set num_of_columns = menu_item.children | length %}
              {% if menu_item.links %}
                {% set num_of_columns = num_of_columns + 1 %}
              {% endif %}
              
              {% if num_of_columns > 4 %}
                {% set col_width = 3 %}
              {% else %}
                {% set col_width = 12 // num_of_columns %}
              {% endif %}
              
              {% for sub_item in menu_item.children %}
                <div class="col-md-{{ col_width }}">
                  <h6 class="mega-menu-group">
                    {% set sub_icon = sub_item.icon or 'fa-layer-group' %}
                    {% if show_icons %}
                      <i class="fas {{ sub_icon }}"></i>
                    {% endif %}
                    {{ sub_item.display }}
                  </h6>
                  <ul class="mega-menu-sub-list">
                    {% for link in sub_item.links %}
                      <li>
                        <a href="{{ link.url }}" {% if link.new_tab %}target="_blank"{% endif %}>
                          {% if link.icon and show_icons %}
                            <i class="fas {{ link.icon }}"></i>
                          {% endif %}
                          {{ link.display }}
                        </a>
                      </li>
                    {% endfor %}
                  </ul>
                </div>
              {% endfor %}
              
              <!-- Add menu item's direct links as a separate column if they exist -->
              {% if menu_item.links %}
                <div class="col-md-{{ col_width }}">
                  <h6 class="mega-menu-group">
                    {% if show_icons %}
                      <i class="fas {{ menu_item.icon or 'fa-link' }}"></i>
                    {% endif %}
                    Quick Links
                  </h6>
                  <ul class="mega-menu-sub-list">
                    {% for link in menu_item.links %}
                      <li>
                        <a href="{{ link.url }}" {% if link.new_tab %}target="_blank"{% endif %}>
                          {% if link.icon and show_icons %}
                            <i class="fas {{ link.icon }}"></i>
                          {% endif %}
                          {{ link.display }}
                        </a>
                      </li>
                    {% endfor %}
                  </ul>
                </div>
              {% endif %}
              
            {% elif menu_item.links %}
              <!-- Menu item has only direct links, no sub-categories -->
              <div class="col-md-12">
                <h6 class="mega-menu-group">
                  {% if show_icons %}
                    <i class="fas {{ menu_item.icon or 'fa-link' }}"></i>
                  {% endif %}
                  {{ menu_item.display }}
                </h6>
                <ul class="mega-menu-sub-list">
                  {% for link in menu_item.links %}
                    <li>
                      <a href="{{ link.url }}" {% if link.new_tab %}target="_blank"{% endif %}>
                        {% if link.icon and show_icons %}
                          <i class="fas {{ link.icon }}"></i>
                        {% endif %}
                        {{ link.display }}
                      </a>
                    </li>
                  {% endfor %}
                </ul>
              </div>
            {% endif %}
            
          </div>
        </div>
        <div class="mega_menu_bottom"></div>
      </div>
    {% endfor %}
  {% endfor %}
</div>
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
            
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.add('active');
            }
        });
    });
    
    // Close when clicking outside
    document.addEventListener('click', e => {
        if (!e.target.closest('.mega-menu-container')) {
            deactivateAll();
        }
    });
});
</script>
<style>
 
    .mega-menu-container {
        position: relative;
         width:100%
    }
    .mega_menu_bottom{
        background: #999;
        width: 100%;
        height: 10px;
    }

    .mega-menu {
        background: var(--bs-body-bg);
        
        width: 100%;
    }
    
    .mega-menu-list {
        display: flex;
        list-style: none;
        margin: 0;
        padding: 0;
    }
    
    .mega-menu-item {
        position: relative;
    }
    
    .mega-menu-link {
        color: grey;
        display: block;
        font-weight:bold;
        font-size:12px;
        padding: 1rem 1rem;
        text-decoration: none;
        white-space: nowrap;
        position: relative;
        transition: color 0.3s ease;
    }
    
    .mega-menu-link.active {
        color: black;
        background-color: rgba(var(--bs-primary-rgb), 0.1);
        border-bottom-style: solid;
        border-bottom-width: 4px;
        border-bottom-color:rgb(56, 71, 80);
        
        
    }

    .mega-menu-link.active::after {
        width: 100%;
    }            
    #.mega-menu-link:hover {
    #    color: var(--bs-primary);
    #    background-color: rgba(var(--bs-primary-rgb), 0.1);
    #}
    
    .mega-menu-icon {
        margin-right: 0.5rem;
        color: grey;
    }
    
    .mega-menu-content {
        position: absolute;
        left: 0;
        right: 0;
        top: 100%;
        background-color: #dfeef6;
        border: 1px solid var(--bs-border-color);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        padding-top: 1rem;
        z-index: 1000;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.6s ease;
    }

    .mega-menu-content.active {
        opacity: 1;
        transition: opacity 0.6s ease;
        pointer-events: auto;
    }
    
    .mega-menu-group {
        color: black;
        font-weight:bold;
        font-size: 0.8rem;
        margin-bottom: 0.20rem;
        text-transform: uppercase;
        border-bottom-color: #adadad;
        border-bottom-style: solid;
        border-bottom-width: 1px;                
    }
    
    .mega-menu-sub-list {
        list-style: none;
        margin: 0 0 1.5rem;
        padding: 0;
    }
        
    .mega-menu-content-column{
        border-left-style: solid;
        border-left-width: 1px;
        border-color: grey;
        }
    .mega-menu-sub-list li a {
        color: var(--bs-body-color);
        display: block;
        font-size: 0.8rem;
        padding: 0.1rem 0;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .mega-menu-sub-list li a:hover {
        color: var(--bs-primary);
        font-weight:bold;
    }
    
    .mega-menu-sublink {
        color: var(--bs-body-color);
        display: block;
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
        text-decoration: none;
    }
    
    .mega-menu-sublink:hover {
        color: var(--bs-primary);
    }
    </style>
    """
    
    # Quick links widget
    QUICK_LINKS = """
    <div class="quick-links-widget">
        <h3 class="widget-title">Quick Access</h3>
        <div class="quick-links-container">
            {% for link in quick_links %}
                <a href="{{ link.url }}" class="quick-link-card" {% if link.new_tab %}target="_blank"{% endif %}>
                    <div class="icon-container">
                        {% if link.icon %}
                            <i class="icon {{ link.icon }}"></i>
                        {% else %}
                            <i class="icon fa fa-link"></i>
                        {% endif %}
                    </div>
                    <div class="link-name">{{ link.display }}</div>
                </a>
            {% endfor %}
        </div>
    </div>
    """        