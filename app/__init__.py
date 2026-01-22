from flask import Flask
from app.config import Config
from app.extensions import db, migrate
from app.routes.user_routes import user_bp
from app.routes.snap_routes import snap_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(snap_bp, url_prefix='/snap')
    return app

if __name__ == '__main__':
    create_app().run(debug=True)
