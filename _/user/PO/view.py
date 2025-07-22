from flask import Blueprint, request

# Create auth blueprint
bp = Blueprint('purchase_order', __name__, url_prefix='/purchase-orders')

from app.register.database import db_registry

from pprint import pprint
from sqlalchemy.engine.row import Row
from sqlalchemy.inspection import inspect as sa_inspect

def _sa_to_builtin(obj):
    if isinstance(obj, Row):
        return dict(obj._mapping)

    try:
        mapper = sa_inspect(obj)
        if mapper and hasattr(mapper, "mapper"):
            out = {c.key: _sa_to_builtin(getattr(obj, c.key))
                   for c in mapper.mapper.column_attrs}
            for k, v in obj.__dict__.items():
                if k.startswith("_sa_"):
                    continue                # skip SQLAlchemy internals
                if k not in out:
                    out[k] = _sa_to_builtin(v)
            return out
    except Exception:
        pass

    if isinstance(obj, dict):
        return {k: _sa_to_builtin(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(_sa_to_builtin(v) for v in obj)
    return obj

def pprint_sa(obj, **pprint_kwargs):
    pprint(_sa_to_builtin(obj), **pprint_kwargs)



@bp.route('/manage', methods=['GET','POST'])
def manage():
    
    from pprint import pprint
    from app.classes import TemplateRenderer
    renderer = TemplateRenderer()
    id=0
    code=None
    try:
        
        data=request.form
        pprint(data)

        id=request.form.get['id'] #744433
        code=request.form.get['code']
    except:
        pass

    db_session = db_registry._routing_session()
    from app.services import PurchaseOrderService
    service = PurchaseOrderService(db_session)
    order=service.get_po("PACIFIC",id)
    #pprint_sa(order)

    data={'order':order,'company':'PACIFIC','id':id,'warehouse_code':code}

    return renderer.render_page("purchase_orders/manage",**data)
    

