from flask import current_app, g, session

class Menu:
    def __init__(self):
        self.database = "VirtualReports"
        self.schema = "dbo"
        self.user_id = session.get('user_id')
        self.is_admin = session.get('is_admin')
        self.quick_links = []
        self.menu_links = []
    
    @property
    def db(self):
        # Get db from current_app if not provided in init
        if hasattr(g, 'db'):
            return g.db
        return current_app.db
    
    @property
    def logger(self):
        # Get logger from app or current_app
        return current_app.logger
    
    def get_quick_links(self):
        """Fetch user's quick links from database"""
        query = f"""
            SELECT m.[user_menu_id], m.[menu_id], m.[order]
            FROM [{self.database}].[{self.schema}].[user_menu] m
            JOIN [{self.database}].[{self.schema}].[menu_items] mi on mi.menu_id=m.user_menu_id
            WHERE [user_id] = :user_id
            ORDER BY mi.display asc
        """
        self.quick_links = self.db.fetch_all(query, {'user_id':self.user_id})
        self.logger.debug(f"Retrieved {len(self.quick_links)} quick links")
        return self.quick_links
    
    def get_menu(self):
        """Fetch menu permissions based on user ID"""
        # Special case for certain user IDs
        if self.is_admin:
            query = f"""
                SELECT [menu_id],[name],[display],[link],[icon],[is_category]
                        ,[is_visible],[is_active],[is_development],[is_new_tab]
                        ,[menu_order],[parent_id]
                FROM [{self.database}].[{self.schema}].[menu_items] mi
                WHERE (is_category = 1 OR is_active = 1) 
                ORDER BY parent_id, menu_order, display
            """
            self.menu_links = self.db.fetch_all(query)
        else:
            query = f"""
                SELECT * FROM (
                    SELECT 
                        [menu_id],[name],[display],[link],[icon],[is_category]
                        ,[is_visible],[is_active],[is_development],[is_new_tab]
                        ,[menu_order],[parent_id]
                    FROM [{self.database}].[{self.schema}].[menu_items] mi
                    JOIN [{self.database}].[{self.schema}].[menu_permissions] mp 
                    ON mp.user_id = :user_id AND mp.menu_id = mi.id
                    WHERE is_visible = 1
                    UNION
                    SELECT 
                        [menu_id],[name],[display],[link],[icon],[is_category]
                        ,[is_visible],[is_active],[is_development],[is_new_tab]
                        ,[menu_order],[parent_id]

                    FROM [{self.database}].[{self.schema}].[menu_items] mi
                    WHERE is_category = 1 AND is_development = 0
                ) AS mi
                ORDER BY parent_id, menu_order, display
            """
            self.menu_links = self.db.fetch_all(query, {'user_id':self.user_id})
        self.logger.debug(f"Retrieved {len(self.menu_links)} menu items for user {self.user_id}")
        return self.menu_links