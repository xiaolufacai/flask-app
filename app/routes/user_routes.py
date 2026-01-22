from flask import Blueprint
from app.controllers.user_controller import get_user, create_user

user_bp = Blueprint('user', __name__)
user_bp.route('/<int:user_id>', methods=['GET'])(get_user)
user_bp.route('/', methods=['POST'])(create_user)
