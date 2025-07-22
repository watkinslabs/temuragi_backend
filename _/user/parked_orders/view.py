from flask import Blueprint, request

# Create auth blueprint
bp = Blueprint('parked_orders', __name__, url_prefix='/parked_orders')

from app.register.database import db_registry


@bp.route('/manage', methods=['GET','POST'])
def login():
    from app.classes import TemplateRenderer
    renderer = TemplateRenderer()
     # Get database session
    data=request.get_json()
    #from pprint import pprint
    
    id=data['id']
    db_session = db_registry._routing_session()
    from app.services import ParkedOrderService
    service = ParkedOrderService(db_session, "GPACIFIC") 
    order=service.get_parked_order_details(id)
    #pprint(order)
    data={'order':order}

    return renderer.render_page("parked_orders/manage",**data)
    

