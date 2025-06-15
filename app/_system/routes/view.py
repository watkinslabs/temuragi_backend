from flask import Blueprint, jsonify, request, current_app

bp = Blueprint('routes', __name__, url_prefix='/api')


