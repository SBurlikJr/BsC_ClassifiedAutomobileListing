import os

from uuid import uuid4
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

DB_PATH = os.path.join(os.path.abspath('flaskr'), 'db\\data.sqlite')
db_dir = os.path.dirname(DB_PATH)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    print('Database folder created')
if os.path.exists(DB_PATH):
    print('Database already exists')

app = Flask(__name__, instance_relative_config=True)

app.secret_key = str(uuid4())

app.config.from_mapping(
    SECRET_KEY='dev',
    FLASK_DEBUG=True,
    SQLALCHEMY_DATABASE_URI='sqlite:///' + DB_PATH,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_EXTENSIONS=[".jpg", ".jpeg", ".png", ".heif"],
    UPLOAD_PATH=['/static/images']
)


bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

if os.path.isfile("config.py"):
    test_config = app.config.from_pyfile('config.py', silent=True)
else:
    app.config.from_mapping()

try:
    os.makedirs(app.instance_path)
except OSError:
    pass


from . import main
from . import auth
from . import listing
from . import user
from . import assistant


app.register_blueprint(main.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(listing.bp)
app.register_blueprint(user.bp)
app.register_blueprint(assistant.bp)
