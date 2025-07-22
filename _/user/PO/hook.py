
def register_miner(app):
    """PO Data API"""
    try:
        from app.services import PurchaseOrderHandler
        with app.app_context():

            app.extensions['Miner'].register_data_handler("PurchaseOrder", PurchaseOrderHandler)
        
        app.logger.info("PO api initialized")
    except ImportError as i:
        print(i)
        app.logger.info("PO api not available")
