import os
from flask import Blueprint

#no_prefix=True
bp = Blueprint('templates',
                __name__, 
                url_prefix='/', 
                template_folder="templates", 
                static_folder="static",
                )


