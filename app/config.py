import os
import logging
from datetime import timedelta


basedir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

config={
    'SYSTEM_SCAN_PATHS'    : ['_system','admin','user'],
    'BASE_DIR'             : os.path.dirname(__file__),
    'DATABASE_URI'      :  ("postgresql+psycopg2://temuragi:"
                            "stronk_password_%24314X"
                            "@10.90.0.40:5432/temuragi"
                            ),
    'CIPHER_KEY'        :  b'u1tOOtBW2ECTWXSMS_pZ9wwdn4dEZzg_-ihYJfbYbd8=',
    'SECRET_KEY'        : 'your_secret_key_here',
    'SESSION_LIFETIME'  :  timedelta(days=30),
    'DEBUG'             :  True ,
    'LOG_LEVEL'         : logging.DEBUG,
    'ROUTE_PREFIX'      : '/v2',
    'ADMIN_ROUTE_PREFIX': '/v2/admin',
    'APP_NAME'          : 'app1',
    'site_template' :{
        'SITE_NAME'         : 'Temuragi',
        'SITE_AUTHOR'       : "Chris Watkins",
        'SITE_DESCRIPTION'  : "Modular Templating System for OPS and Reporting",
    }
}
# dynamic
config['LOG_FILE']=  os.path.join(basedir, 'logs', config['APP_NAME']+'.log')