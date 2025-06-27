  // Sidebar state management
  const SIDEBAR_STATE_KEY = 'sidebar_state';
  const SIDEBAR_SECTIONS_KEY = 'sidebar_expanded_sections';

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
      const expandedSections = [];
      document.querySelectorAll('.nav_item.expanded[data-section]').forEach(item => {
          const section = item.getAttribute('data-section');
          if (section) {
              expandedSections.push(section);
          }
      });
      localStorage.setItem(SIDEBAR_SECTIONS_KEY, JSON.stringify(expandedSections));
  }

  function restore_sidebar_state() {
     // Restore sidebar collapsed state
     const sidebarState = localStorage.getItem(SIDEBAR_STATE_KEY);
     if (sidebarState === 'collapsed') {
         document.querySelector('.content_area').classList.add('collapsed');
         // Also update the icon
         const sidebar_toggle = document.querySelector('.sidebar_toggle i');
         if (sidebar_toggle) {
             sidebar_toggle.className = 'fas fa-chevron-right';
         }
     }
     
     // Restore expanded sections
     const expandedSections = JSON.parse(localStorage.getItem(SIDEBAR_SECTIONS_KEY) || '[]');
     expandedSections.forEach(section => {
         const element = document.querySelector(`.nav_item[data-section="${section}"]`);
         if (element) {
             element.classList.add('expanded');
         }
     });
     
     // Set active item based on current URL
     const currentPath = window.location.pathname;
     document.querySelectorAll('.nav_item').forEach(item => {
         const onclick = item.getAttribute('onclick');
         if (onclick && onclick.includes('window.location.href') && onclick.includes(currentPath)) {
             item.classList.add('active');
             
             // Expand parent sections
             let parent = item.closest('.nav_children');
             while (parent) {
                 const parentItem = parent.previousElementSibling;
                 if (parentItem && parentItem.classList.contains('has_children')) {
                     parentItem.classList.add('expanded');
                 }
                 parent = parent.parentElement.closest('.nav_children');
             }
         }
     });
     
     // Save state after setting active items
     save_sidebar_sections();
   }
       
  // Initialize on page load
  document.addEventListener('DOMContentLoaded', restore_sidebar_state);