
__depends_on__ = ['Miner']

def register_parked_order_handler(app):
    """Parked Order Data API Registration"""
    try:
        from app.classes import ParkedOrderHandler
        
        with app.app_context():
            # Register the handler with Miner
            app.extensions['Miner'].register_data_handler("ParkedOrder", ParkedOrderHandler)
            
        app.logger.info("ParkedOrderHandler API initialized successfully")
        
    except ImportError as e:
        app.logger.error(f"Failed to import ParkedOrderDataHandler: {e}")
        app.logger.info("ParkedOrderHandler API not available - missing dependencies")
        
    except KeyError:
        app.logger.error("Miner extension not found in app.extensions")
        app.logger.info("ParkedOrderHandler API not available - Miner not initialized")
        
    except Exception as e:
        app.logger.error(f"Unexpected error registering ParkedOrderHandler: {e}")
        app.logger.info("ParkedOrderHandler API not available")