from flask import request
from app.services.user_service import UserService
from app.utils.response import success, error

def get_user(user_id):
    user = UserService.get_by_id(user_id)
    if not user:
        return error('用户不存在')
    return success(user.to_dict())

def create_user():
    data = request.json or {}
    if not data.get('username'):
        return error('username required')
    user = UserService.create(data['username'], data.get('email'))
    return success(user.to_dict())
