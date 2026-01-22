from flask import Blueprint
from app.controllers.snap_controller import snap

snap_bp = Blueprint('snap', __name__)
snap_bp.route('/snap', methods=['POST', 'GET'])(snap)