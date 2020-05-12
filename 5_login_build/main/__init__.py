from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('main.config')

# flask-loginを設定
login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app)

import main.views
