from flask import Blueprint, request, redirect, render_template, url_for, flash
from utils.decorators import has_permission, only_via_ui
import utils.sqlite as sql
import forms.profile as profileforms

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


@profile_bp.route('/me')
@has_permission(None)
def get_my_profile(payload):
    login = payload['login']
    profile = sql.get_user(login)
    roles = sql.get_user_roles(int(profile['user_id']))
    tur_list = [f"{r['title']} [#{int(r['role_id'])}]" for _, r in roles.iterrows()]
    return render_template('profile/index.html', profile=profile, roles=tur_list, me=True)


@profile_bp.route('/me/edit', methods=['GET', 'POST'])
@has_permission(None)
def edit_my_profile(payload):
    login = payload['login']

    profile = sql.get_user(login)
    form = profileforms.UserProfileEdit()
    form.fill_profile(profile)

    roles = sql.get_roles()
    choices = [(r['role_id'], r['title']) for _, r in roles.iterrows()]
    form.roles_up.choices = choices
    # print(f'roles: {choices}')

    this_user_roles = sql.get_user_roles(int(profile['user_id']))
    tur_list = [int(r['role_id']) for _, r in this_user_roles.iterrows()]
    form.roles_up.data = tur_list

    if form.validate_on_submit():
        formdata = request.form.to_dict()
        login = formdata['login_up']
        try:
            # roles_list = [int(value) for value in request.form.getlist('roles_up')]
            sql.update_user(formdata, form.assoc_fields(), None, int(profile['user_id']))
            flash(f'Пользователь {profile["login"]} изменён!', 'success')
            profile = sql.get_user(login)
            return redirect(url_for('users.do_signin', login=login))
            # return redirect(url_for('profile.get_my_profile', login=profile['login']))
        except Exception as e:
            flash(f'Не удалось изменить пользователя: {e}', 'error')
            return redirect(request.referrer)
    return render_template('profile/edit.html', profile=profile, pform=form, me=True)


@profile_bp.route('/', methods=['GET', 'POST'])
@has_permission(['users.select'])
def get_profile(payload):
    login = request.args.get('login')
    profile = sql.get_user(login)
    roles = sql.get_user_roles(int(profile['user_id']))
    tur_list = [f"{r['title']} [#{int(r['role_id'])}]" for _, r in roles.iterrows()]
    return render_template('profile/index.html', profile=profile, roles=tur_list, me=False)


@profile_bp.route('/edit', methods=['GET', 'POST'])
@only_via_ui
@has_permission(['users.edit'])
def edit_profile(payload):
    login = request.args.get('login')

    profile = sql.get_user(login)
    form = profileforms.UserProfileEdit()
    form.fill_profile(profile)

    roles = sql.get_roles()
    choices = [(r['role_id'], r['title']) for _, r in roles.iterrows()]
    form.roles_up.choices = choices

    this_user_roles = sql.get_user_roles(int(profile['user_id']))
    tur_list = [int(r['role_id']) for _, r in this_user_roles.iterrows()]
    form.roles_up.data = tur_list

    if form.delete_up.data:
        try:
            user = sql.get_user(login)
            sql.delete_user(user['user_id'])
            flash(f'Пользователь {login} удалён', 'success')
            return redirect(url_for('users.index'))
        except Exception as e:
            flash(str(e), 'error')

    if form.validate_on_submit() or form.submit_up.data:
        formdata = request.form.to_dict()
        login = formdata['login_up']
        try:
            roles_list = [int(value) for value in request.form.getlist('roles_up')]
            sql.update_user(formdata, form.assoc_fields(), roles_list, int(profile['user_id']))
            flash(f'Пользователь {profile["login"]} изменён!', 'success')
            profile = sql.get_user(login)
            return redirect(url_for('profile.get_profile', login=profile['login']))
        except Exception as e:
            flash(f'Не удалось изменить пользователя: {e}', 'error')
            return redirect(request.referrer)

        # print(formdata)

    return render_template('profile/edit.html', profile=profile, pform=form, me=False)
