from functools import wraps

import jwt
from flask import request, current_app, redirect, url_for, abort, session, flash
import utils.sqlite as sql
from utils.exceptions import *


def has_permission(perms):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # print(perms)
            token = request.cookies.get('user_token')
            try:
                payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                kwargs['payload'] = payload

                if perms is None or 'admin' in list(session['user_perms']) and perms:
                    pass
                elif type(perms) is list and 'user_perms' in session:
                    # print('admin' not in list(session['user_perms']) and perms)
                    if not 'all_permissions' in session:
                        existing_perms = sql.get_permissions_list()
                        session['all_permissions'] = [p['title'] for _, p in existing_perms.iterrows()]
                    if perms:
                        user_perms_set = set(session['user_perms'])
                        # all_perms_set = set(session['all_permissions'])
                        print(f'{user_perms_set & set(perms)}')
                        if not bool(user_perms_set & set(perms)):
                            raise NotEnoughPermissions('У вас недостаточно прав')
                        print(f'Ваши привилегии: {session["user_perms"]}')
                    # else:
                    #     raise NotEnoughPermissions('Только административный доступ')

                    # print(f'{session["all_permissions"]}')
                else:
                    raise NotEnoughPermissions(f'Некорректная аннотация прав')
            except jwt.ExpiredSignatureError or jwt.InvalidTokenError as e:
                flash('Авторизация истекла', 'error')
                return redirect(url_for('users.logout'))
            except Exception as e:
                flash(f'У вас недостаточно прав', 'error')
                return redirect(request.referrer)
            return f(*args, **kwargs)

        return wrapper
    return decorator


def has_permission_disp(perms):
    token = request.cookies.get('user_token')
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])

        user_perms_set = set(session['user_perms'])
        # if not perms is None and user_perms_set:
        #     return redirect('users.logout')

        if perms is None or 'admin' in list(session['user_perms']) and perms:
            pass
        elif type(perms) is list and 'user_perms' in session:
            if not 'all_permissions' in session:
                existing_perms = sql.get_permissions_list()
                session['all_permissions'] = [p['title'] for _, p in existing_perms.iterrows()]
            if perms:
                # all_perms_set = set(session['all_permissions'])
                print(f'{user_perms_set & set(perms)}')
                if not bool(user_perms_set & set(perms)):
                    return False
        else:
            return False
        return True
    except Exception as e:
        return False


def only_via_ui(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        referrer = request.referrer
        if not referrer or not referrer.startswith(request.host_url):
            print(f"Прямой доступ запрещен")
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
