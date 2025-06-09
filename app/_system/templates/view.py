from flask import Blueprint

#no_prefix=True
bp = Blueprint('templates',
                __name__, 
                static_folder="static",
                )


