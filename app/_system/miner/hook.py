
def register_miner(app):
    """Setup Miner Data API"""
    try:
        from app.services import Miner
        with app.app_context():
            app.extensions['Miner']=Miner(app)
        
        app.logger.info("Miner data api initialized")
    except ImportError:
        app.logger.info("Miner data api not available")
