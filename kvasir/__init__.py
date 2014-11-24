import os
import sys
from flask import Flask

from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.mongoengine import MongoEngine
from flask.ext.mongoengine import MongoEngineSessionInterface
from flask.ext.security import Security, MongoEngineUserDatastore

from celery import Celery

from config import ADMINS, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, UPLOAD_FOLDER

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    return celery

app = Flask(__name__)
app.config.from_object('config')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["MONGODB_SETTINGS"] = {'DB': "kvasir"}

#Configure Celery Object
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)

celery = make_celery(app)

try:
    db = MongoEngine(app)
except:
    sys.stdout.write("Using docker environment variables to connect to linked MongoDB container\n")
    uri_string = "mongodb://%s:%s/kvasir" % (os.environ['DB_PORT_28017_TCP_ADDR'], os.environ['DB_PORT_27017_TCP_PORT'])
    app.config["MONGODB_SETTINGS"] = {'DB': "kvasir", "host": uri_string}
    db = MongoEngine(app)
    
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

mail = Mail(app)

# Setup Flask-Security
from models import User, Role
from forms import ExtendedRegisterForm

user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

app.session_interface = MongoEngineSessionInterface(db)

#Test: This can probably be changed to source_dir = os.path.dirname(os.path.dirname(__file__))
source_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
tmp = source_dir + "/tmp"
log = source_dir + "/tmp/kvasir.log"

def get_user_nickname(user_id):
    user = models.User(id = user_id)
    return user.nickname

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    
    from logging.handlers import SMTPHandler
    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'Kvasir server', credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
    
    file_handler = RotatingFileHandler(log, 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('Kvasir startup')

app.jinja_env.globals.update(get_user_nickname=get_user_nickname)

from kvasir import models
from kvasir.views import views, ngsviews, userviews, dataviews, editviews