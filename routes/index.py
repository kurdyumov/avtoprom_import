from flask import Blueprint, render_template, redirect, url_for, request, flash

from utils.decorators import has_permission
import utils.sqlite as sql

index_bp = Blueprint('index', __name__, '/')


@index_bp.route('/')
def entry_point():
    token = request.cookies.get('user_token')
    if token:
        return redirect(url_for('index.index'))
    else:
        flash('Для работы в ИС вам нужно авторизоваться', 'error')
        return redirect(url_for('users.signin'))


@index_bp.route('/index')
@has_permission(None)
def index(payload):
    profile = sql.get_user(payload['login'])
    print(profile)
    fio = f"{profile['lastname']} {profile['firstname']} {profile['patronymic']}"
    return render_template('menu.html', fio=fio)


@index_bp.route('/not_found')
def not_found():
    return render_template('utils4/error.html', error=str('Страница не найдена'))
