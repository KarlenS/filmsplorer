from flask import Flask
from flask_socketio import SocketIO

from ._const import KEY

socketio = SocketIO()

def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = KEY
    app.config["CACHE_TYPE"] = "null"

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)
    return app
