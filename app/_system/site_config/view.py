from flask import Blueprint, request, jsonify, Response, current_app
#from app.auth import require_auth, get_current_user, require_build_token
from app.register.database import db_registry
from sqlalchemy import func
import json
import hashlib
import uuid 

from app.models import ComponentBundle, RouteMapping

bp = Blueprint('site_config', __name__, url_prefix="/api")

from app.register.database import db_registry


@bp.route('/site/config', methods=['POST','GET'])
def execute_report():

        #context: "layout"
        #include_sections: false
        #path: "/home"
        #@section:PR_MAIN"
        from app.models import SiteConfig
        db_session=db_registry._routing_session()
        from pprint import pprint 

        site = db_session.query(SiteConfig).filter_by(published=True).one()
        pprint(request)
        user_id = request.cookies.get('user_id')
        data={}
        try:
            data = request.get_json()
            pprint(data)
        except:
            pass


        menu_structure={}
        menus=[]
        menu_name='default'

        if user_id:

            user_id=uuid.UUID(user_id)
       
            from app.classes import MenuBuilder
            # Get menu structure
            
            menu_builder = MenuBuilder()
            menus=menu_builder.get_available_menus(user_id)

            menu_name=data.get('context') or 'default'
            
            if menus:
                if menu_name=="default":
                    menu_name=menus[0]['name']


                menu_structure = menu_builder.get_menu_structure(menu_name, user_id)
        

        return jsonify({'site':site.to_dict(),'menu':menu_structure,'contexts':menus,'current_context':menu_name})

        
