from flask import g, current_app, session
import datetime

class Theme:
    def __init__(self):
        pass
        
    @staticmethod
    def get_all_themes():
        """Get all available themes from database"""
        db = current_app.db
        query = "SELECT id, name, description, menu_location, wide, dark_mode, search, show_icons FROM _themes"
        return db.fetch_all(query)
    
    @staticmethod
    def get_user_preference(user_id):
        """Get user's theme preference"""
        db = current_app.db
        query = "SELECT TOP 1 t.* \
                FROM jadvdata.dbo._themes AS t \
                LEFT JOIN jadvdata.dbo._user_theme_preferences AS u  \
                    ON u.theme_id = t.id AND u.user_id = ? \
                ORDER BY CASE WHEN u.user_id IS NOT NULL THEN 1 ELSE 2 END"

        return db.fetch(query, [user_id])
    
    @staticmethod
    def getadmin_id(user_id):
        """Get user's theme preference"""
        db = current_app.db
        query= "select t.system_id from jadvdata.dbo._user_theme_preferences as p \
                join jadvdata.dbo._themes t on t.id=p.theme_id \
                where user_id= ?"
        return db.fetch(query, [user_id])

    @staticmethod
    def save_user_preference(user_id, theme_id):
        """Save user's theme preference"""
        db = current_app.db
        
        query = """
        MERGE INTO jadvdata.dbo._user_theme_preferences AS target
        USING (SELECT ? AS user_id, ? AS theme_id) AS source
        ON target.user_id = source.user_id
        WHEN MATCHED THEN 
            UPDATE SET theme_id = source.theme_id
        WHEN NOT MATCHED THEN 
            INSERT (user_id, theme_id) VALUES (source.user_id, source.theme_id);
        """
        
        return db.execute(query, [user_id, theme_id])

    @staticmethod
    def update_session(user_id):
        # Initialize theme model
        theme = Theme()
        # Get data from model
        user_preferences = Theme.get_user_preference(user_id)
        if user_preferences:
            session['theme']=user_preferences
        else:
            session['theme']=None