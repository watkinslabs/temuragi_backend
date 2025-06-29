from flask import Blueprint, request, jsonify, current_app

from app.classes import Miner

# Create blueprint
bp = Blueprint('miner', __name__, url_prefix='/api')

@bp.route('/data', methods=['POST'])
def data():
    """Route handler that delegates to Miner service"""
    
    miner=  current_app.extensions['Miner']
    
    return miner.data_endpoint()