from flask import Blueprint, request, jsonify

from app.classes import Miner

# Create blueprint
bp = Blueprint('miner', __name__, url_prefix='/api')

@bp.route('/data', methods=['POST'])
def data_endpoint():
    """Route handler that delegates to Miner service"""
    miner = Miner()
    return miner.data_endpoint()