from flask import current_app, g, session

class Menu:
    def __init__(self):
        self.database = "jadvdata"
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
            SELECT m.[id], m.[permission_id], m.[order]
            FROM [{self.database}].[{self.schema}].[_custom_menu] m
            JOIN [{self.database}].[{self.schema}].[permissions] p on p.id=m.permission_id
            WHERE [user_id] = :user_id
            ORDER BY p.title asc
        """
        self.quick_links = self.db.fetch_all(query, {'user_id':self.user_id})
        self.logger.debug(f"Retrieved {len(self.quick_links)} quick links")
        return self.quick_links
    
    def get_menu(self):
        """Fetch menu permissions based on user ID"""
        # Special case for certain user IDs
        if self.is_admin:
            query = f"""
                SELECT p.* FROM [{self.database}].[{self.schema}].[permissions] p
                WHERE (grouper='1' OR validate='0') OR
                       (menu_link='1' AND title NOT LIKE '%::%' AND title!='---NAME---')
                ORDER BY order_number ASC, title ASC
            """
            self.menu_links = self.db.fetch_all(query)
        else:
            query = f"""
                SELECT * FROM (
                    SELECT p.* FROM [{self.database}].[{self.schema}].[permissions] p
                    JOIN [{self.database}].[{self.schema}].[permissions_rights] r 
                    ON r.user_id = :user_id AND r.permission_id = p.id
                    WHERE (title NOT LIKE '%::%' AND title!='---NAME---')
                    UNION
                    SELECT p.* FROM [{self.database}].[{self.schema}].[permissions] p
                    WHERE (grouper='1' OR validate='0') AND development='0'
                ) AS p 
                ORDER BY order_number ASC, grouper ASC, title ASC
            """
            self.menu_links = self.db.fetch_all(query, {'user_id':self.user_id})
        self.logger.debug(f"Retrieved {len(self.menu_links)} menu items for user {self.user_id}")
        return self.menu_links