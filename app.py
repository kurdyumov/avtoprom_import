import json
import os

from flask import Flask, redirect, request, url_for, render_template, session, g
from jinja2 import TemplateNotFound
from apscheduler.schedulers.background import BackgroundScheduler

from routes.users import users_bp
from routes.roles import roles_bp
from routes.index import index_bp
from routes.profile import profile_bp
from routes.analysis import analysis_bp
from routes.analyzis.model_sources import model_source_bp
from routes.analyzis.model import model_bp
from routes.analyzis.reports import reports_bp
from routes.telegram import telegram_bp

from config import Config
import utils.sqlite as sql
from utils.exceptions import *
from utils.taskmanager import get_scheduler
import locale
from utils.decorators import has_permission_disp, has_permission
from utils.utils import clear_temp

# from utils4.tg import tg_bot

locale.setlocale(
    category=locale.LC_ALL,
    locale="Russian"  # Note: do not use "de_DE" as it doesn't work
)

app = Flask(__name__,
            static_folder='static/',
            template_folder='views/')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.jinja_env.globals['has_permission'] = has_permission_disp

app.config.from_object(Config)

app.register_blueprint(users_bp)
app.register_blueprint(roles_bp)
app.register_blueprint(index_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(model_source_bp)
app.register_blueprint(model_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(telegram_bp)

sql.signup_root()


@app.route('/')
def index():
    return redirect(url_for('users.signin'))


# @app.before_request
# def before_request():
#     # print(f'path: {request.referrer}, endpoint: {request.endpoint}')
#     if request.endpoint == 'users.signin' and request.cookies.get('user_token'):
#         return redirect(url_for('index'))
#     # if request.referrer is None:
#     #     return redirect(url_for('index'))

# @app.before_request
# def before_request():
#     print(request)
#     user = request.cookies.get('user_token')
#     if not user:
#         return redirect(url_for('users.signin'))
#     pass


@app.errorhandler(TemplateNotFound)
def handle_tnf(error):
    print(f'Не нашёлся шаблон: {error}')


@app.errorhandler(NotEnoughPermissions)
def handle_nep(error):
    return render_template('utils4/error.html', error=str(error))


@app.errorhandler(404)
def handle_notfound(error):
    return redirect(url_for('index.not_found'))


if __name__ == '__main__':
    # tg_bot().bot.infinity_polling()
    # with app.app_context():
    get_scheduler(app)
    with app.app_context():
        clear_temp()

    # tg_bot().bot.infinity_polling()
    app.run(debug=True, load_dotenv=False, use_reloader=False)
