import os
import logging
from datetime import timedelta


basedir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

config={
    'SYSTEM_SCAN_PATHS'    : ['_system','admin','user'],
    'BASE_DIR'             : os.path.dirname(__file__),
    'DATABASE_URI'      :  ("postgresql+psycopg2://vr_web_user:"
                            "stronk_password_%24314X"
                            "@10.0.0.52:5432/virtual_reports"
                            ),                            
    'DB_CONN_ENC_KEY'   : 'lejookie',
    'CIPHER_KEY'        :  b'u1tOOtBW2ECTWXSMS_pZ9wwdn4dEZzg_-ihYJfbYbd8=',
    'SECRET_KEY'        : 'your_secret_key_here',
    'SESSION_LIFETIME'  :  timedelta(days=30),
    'DEBUG'             :  True ,
    'LOG_LEVEL'         : logging.DEBUG,
    'ROUTE_PREFIX'      : '/v2',
    'ADMIN_ROUTE_PREFIX': '/v2/admin',
    'APP_NAME'          : 'app1',
    'site_template' :{
        'SITE_NAME'         : 'Ahoy!',
        'SITE_AUTHOR'       : "Chris Watkins",
        'SITE_DESCRIPTION'  : "Performance Radiator Parts System",
    }
}
# dynamic
config['LOG_FILE']=  os.path.join(basedir, 'logs', config['APP_NAME']+'.log')