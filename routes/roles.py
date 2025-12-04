import json
import os

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from wtforms.fields.simple import BooleanField

from utils.decorators import has_permission, only_via_ui
import utils.sqlite as sql
import forms.roles as roleforms

roles_bp = Blueprint('roles', __name__, url_prefix='/roles')


@roles_bp.route('/')
@only_via_ui
@has_permission(['roles'])
def index(payload):
    roles = sql.get_roles()
    print(roles)
    titles = {
        'role_id': 'ID',
        'title': 'Наименование'
    }
    return render_template('roles/index.html', roles=roles.to_dict('records'), titles=titles)


@roles_bp.route('/select', methods=['GET', 'POST'])
@has_permission(['roles.select'])
def select_role(payload):
    role_id = request.args.get('role')
    role = sql.get_role(role_id)
    print(f'role_id: {role_id}')

    perm = sql.get_role_permissions(role_id)

    bc = sql.get_broadcast_list(role_id)
    bc_list = [int(e['task_id']) for e in bc]
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        tasks = json.load(f)['sources']
    tasks_list = [f"[#{k}] {v['title']}" for k, v in tasks.items() if int(k) in bc_list]
    # print(f"bc_list: {bc_list}\ntasks: {tasks}")

    return render_template('roles/select.html', role=role, perm=list(perm['title']), bc=tasks_list)


@roles_bp.route('/edit', methods=['GET', 'POST'])
@only_via_ui
@has_permission(['roles.edit'])
def edit_role(payload):
    role_id = request.args.get('role')
    role = sql.get_role(role_id)
    form = roleforms.EditRoleForm()
    form.fill_form(role)

    perms = sql.get_permissions_list()
    choices = [(p['perm_id'], p['title']) for _, p in perms.iterrows()]
    form.permissions_erf.choices = choices

    this_role_perms = sql.get_role_permissions(role_id)
    perms_list = [int(p['perm_id']) for _, p in this_role_perms.iterrows()]
    print(f'permslist: {perms_list}')
    form.permissions_erf.data = perms_list

    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        tasks = json.load(f)['sources']
    tasks_list = [(int(k), f"[#{k}] {v['title']}") for k, v in tasks.items()]
    form.broadcast_erf.choices = tasks_list

    bc = sql.get_broadcast_list(role_id)
    bc_list = [int(e['task_id']) for e in bc]
    print(f'bclist: {bc_list}')
    # bc_list = []
    form.broadcast_erf.data = bc_list

    if form.validate_on_submit():
        if form.submit_erf.data:
            role_data = request.form.to_dict()
            permissions_list = [int(value) for value in request.form.getlist('permissions_erf')]
            print(f'role: {role_data} | new_perms: {permissions_list}')
            bc_list = [int(value) for value in request.form.getlist('broadcast_erf')]

            sql.update_role(int(role_id), role_data, permissions_list, bc_list, form.assoc_fields())
            flash('Роль успешно обновлена!', 'success')
        elif form.delete_erf.data:
            sql.delete_role(int(role_id))
            return redirect(url_for('roles.index'))
        return redirect(url_for('roles.edit_role', role=int(role_id)))

    return render_template('roles/edit.html', form=form, role=int(role_id))


@roles_bp.route('/create', methods=['GET', 'POST'])
@only_via_ui
@has_permission(['roles.create'])
def create_role(payload):
    form = roleforms.CreateRoleForm()
    perms = sql.get_permissions_list()
    choices = [(p['perm_id'], p['title']) for _, p in perms.iterrows()]
    form.permissions_crf.choices = choices

    bc = sql.get_broadcast_list()
    print(bc)
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        tasks = json.load(f)['sources']
    tasks_list = [(k, f"[#{k}] {v['title']}") for k, v in tasks.items()]
    form.broadcast_crf.choices = tasks_list
    # print(f'tasks_list: {tasks_list}')
    # bc_list = [(k, f'{v["title"]} [#{k}]') for k, v in bc.items()]
    # print(1)
    # print(f'bc_list: {bc_list}')

    if form.validate_on_submit():
        print(f'form: {form.data}')
        sql.create_role(form.data, form.assoc_fields())
        flash('Роль успешно создана!', 'success')
        return redirect(url_for('roles.index', role_id=id))
    return render_template('roles/create.html', form=form)
