import io
import os
import uuid
from datetime import datetime, timedelta

import jwt
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, current_app, make_response, session, request, \
    send_file, send_from_directory, flash

import forms.auth as authform
import forms.signup as signupform
import utils.sqlite as sql
from utils.decorators import has_permission, only_via_ui

users_bp = Blueprint('users', __name__, url_prefix='/users')
UPLOAD_FOLDER = 'temp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@users_bp.route('/')
@only_via_ui
@has_permission(None)
def index(payload):
    return redirect(url_for('users.select'))


@users_bp.route('/signin', methods=['GET', 'POST'])
# @only_via_ui
def signin():
    form = authform.AuthForm()
    if form.validate_on_submit():
        try:
            login = form.login.data
            password = form.password.data
            user = sql.get_user(login, password)
            payload = {
                'exp': datetime.utcnow() + timedelta(hours=1),
                'login': login
            }
            session.permanent = True

            token = jwt.encode(payload=payload, key=current_app.config['SECRET_KEY'], algorithm="HS256")
            # perms = sql.get_permissions(login)
            user_perms = sql.get_permissions(login)
            session['user_perms'] = [p['title'] for _, p in user_perms.iterrows()]

            this_user_roles = sql.get_user_roles(user['user_id'])
            tur_list = [r['title'] for _, r in this_user_roles.iterrows()]

            perms_list = []
            for r in tur_list:
                role_perms = sql.permissions_children(r)
                role_perms_list = [rp['title'] for _, rp in role_perms.iterrows()]
                perms_list = list(set(perms_list + role_perms_list))
            session['user_perms'] = perms_list
            # print(f'full perms: {perms_list}')
            # full_user_perms = sql.permissions_children()

            # print(f'login: {login} | roles: {roles} | permissions: {perms["title"].to_list()}')
            flash('Добро пожаловать!', 'success')
            response = make_response(redirect(url_for('index')))
            response.set_cookie('user_token', token)

            return response
        except Exception as e:
            flash('Неверный логин и/или пароль', 'error')
            print(str(e))  #TODO сообщение "неверный логин и/или пароль" - вывести на форму
    # if request.cookies.get('user_token'):
    #     return redirect(url_for('users.select'))
    return render_template('users/signin.html', form=form)


@users_bp.route('/do_signin', methods=['GET', 'POST'])
def do_signin():
    login = request.args.get('login')
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=1),
        'login': login
    }
    session.permanent = True
    token = jwt.encode(payload=payload, key=current_app.config['SECRET_KEY'], algorithm="HS256")
    response = make_response(redirect(url_for('index')))
    response.set_cookie('user_token', token)
    return response


@users_bp.route('/select')
@only_via_ui
@has_permission(['users.select'])
def select(payload):
    users = sql.get_users(payload['login'])
    # table = pd.DataFrame.
    titles = {
        'user_id': 'ID в системе',
        'lastname': 'Фамилия',
        'firstname': 'Имя',
        'patronymic': 'Отчество',
        'emp_num': 'Номер сотрудника',
        'login': 'Логин',
        'password': 'Пароль'
    }
    return render_template('users/index.html', users=users.to_dict('records'), titles=titles)


@users_bp.route('/signup', methods=['GET', 'POST'])
@has_permission(['users.signup'])
def signup(payload):
    # print(f'файл для скачивания: {request.args.get("file_path")}')
    form = signupform.SignupForm()
    csvform = signupform.ExcelSignupForm()
    mapform = signupform.ExcelMappingForm()

    file_path = request.args.get('file_path')
    # upload_txt = request.args.get('upload_txt')
    if file_path:
        exportform = signupform.ExportExcelUsers()
        if exportform.validate_on_submit():
            file_name = request.args.get('file_name')
            response = send_file(
                file_path,
                as_attachment=True,
                download_name=file_name,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            print(f'file_path: {file_path}\nfile_name: {file_name}')
            return response
        return render_template('users/signup.html', form=form, csvform=csvform, exportform=exportform,
                               file_path=file_path, single=False)
    # if upload_txt:
    #     print('Ожидаем кнопку txt экспорта')
    #     print(file_path)
    #     exportform = signupform.ExportTxtUser()
    #     if exportform.validate_on_submit():
    #         response = send_file(
    #             io.BytesIO(upload_txt.encode()),
    #             as_attachment=True,
    #             download_name=request.args.get('file_name'),
    #             mimetype='text/plain'
    #         )
    #         return response
    #     return render_template('users/signup.html', form=form, csvform=csvform, exportform=exportform, file_path=file_path, single=True)

    # TODO форма "новый сотрудник"
    if form.submit_sf.data:
        if form.validate_on_submit():
            print(f'импорт формой. {form.data}')
            try:
                user = {
                    'lastname': form.lastname_sf.data,
                    'firstname': form.firstname_sf.data,
                    'patronymic': form.patronymic_sf.data,
                    'emp_num': form.emp_num_sf.data
                }
                data = sql.do_signup(user)

                buffer = io.StringIO()
                for k, v in data.items():
                    buffer.write(f"{k}: {v}\n")
                buffer.seek(0)
                file_name = f'{data["login"]}.txt'
                # file_path = os.path.join(UPLOAD_FOLDER, file_name)
                # with open(file_path, 'w', encoding='utf-8') as f:
                #     f.write(buffer.getvalue())
                # buffer.close()

                flash(f'Пользователь {data["login"]} зарегистрирован. Вы получите txt с учётными данными', 'success')
                # return redirect(url_for('users.signup', upload_txt=buffer.getvalue(), file_name=file_name))
                # return send_file(
                #     io.BytesIO(buffer.getvalue().encode()),
                #     as_attachment=True,
                #     download_name=f'{data["login"]}.txt',
                #     mimetype='text/plain'
                # )
                # session['form_buffer'] = buffer
                # session['form_data'] = data

                response = make_response(send_file(
                    io.BytesIO(buffer.getvalue().encode()),
                    as_attachment=True,
                    download_name=f'{data["login"]}.txt',
                    mimetype='text/plain'
                ))
                response.headers['X-Redirect-After-Download'] = url_for('users.index')
                return response
            except Exception as e:
                flash(f'Регистрация не удалась: {e}', 'error')
            # return redirect(url_for('users.select'))
    #TODO импорт таблицей
    elif csvform.submit_esf.data and csvform.validate_on_submit():
        try:
            file = csvform.excel_file_esf.data
            table = pd.read_excel(file, sheet_name=0)
            fields = table.columns.tolist()

            session['users_excel'] = table.to_dict()
            session['fields'] = fields
            return redirect(url_for('users.map_excel', mapform=mapform))
        except Exception as e:
            flash(f'Импорт пользователей не удался: {e}', 'error')
            return redirect(request.referrer)
    return render_template('users/signup.html', form=form, csvform=csvform)


@users_bp.route('/map_excel', methods=['GET', 'POST'])
@only_via_ui
@has_permission(['users.signup'])
def map_excel(payload):
    mapform = signupform.ExcelMappingForm()
    mapform.set_choices(session['fields'])
    if mapform.validate_on_submit():
        print(mapform.data)
        try:
            excel = pd.DataFrame.from_dict(session['users_excel'])
            form_db_map = {
                'lastname': mapform.lastname_emf.data,
                'firstname': mapform.firstname_emf.data,
                'patronymic': mapform.patronymic_emf.data,
                'emp_num': mapform.emp_num_emf.data
            }
            users = sql.do_signup_many(excel, form_db_map)
            if type(users) is pd.DataFrame:
                print(f'users: {users}')
                file_name = f"export_{uuid.uuid4().hex}.xlsx"
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                users.to_excel(file_path, index=False, sheet_name='avtoprom_users')
                flash('Пользователи успешно импортированы. Скачайте файл с учётными данными', 'success')
                return redirect(url_for('users.signup', file_path=file_path, file_name=file_name))
        except Exception as e:
            flash(f'Импорт пользователей не удался: {e}', 'error')
            return redirect(url_for('users.signup'))
    return render_template('users/mapform.html', mapform=mapform)


@users_bp.route('/export')
@has_permission(['users.signup'])
def export_users(payload):
    file_path = request.args.get('file_path')
    if file_path:
        print('exported')
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=request.args.get('file_name'),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        return response
    return redirect(url_for('users.signup'))


@users_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('users.signin')))
    response.set_cookie('user_token', '', expires=0)
    session.pop('all_permission', None)
    session.pop('csrf_token', None)
    session.pop('user_perms', None)
    session.pop('temp_file_path', None)
    return response
