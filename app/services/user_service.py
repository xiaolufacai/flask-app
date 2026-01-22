from app.models.user import User
from app.extensions import db

class UserService:
    @staticmethod
    def get_by_id(uid):
        return User.query.get(uid)

    @staticmethod
    def create(username, email=None):
        u = User(username=username, email=email)
        db.session.add(u)
        db.session.commit()
        return u
