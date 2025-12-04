# управление моделями в ИС
import json
import os
import shutil
from pathlib import Path

import catboost
from catboost import CatBoostError
from flask import Blueprint, render_template, url_for, current_app, request, session, redirect, flash

import forms.import_model as imodelforms
from utils.decorators import has_permission
from utils.utils import delete_task

model_bp = Blueprint('model', __name__, url_prefix='/model/models')


@model_bp.route('/', methods=['GET', 'POST'])
@has_permission(['model'])
def index(payload):
    model_id = request.args.get('model_id')
    print(model_id)
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    model = data['models'][model_id]
    type = {
        'classification': 'Классификация',
        'regression': 'Регрессия',
        'ranking': 'Ранжирование'
    }[model['type']]
    model['type'] = type
    return render_template('analysis/model/index.html', model=model, title=model_id)


@model_bp.route('/edit', methods=['GET', 'POST'])
@has_permission(['model.edit'])
def edit(payload):
    try:
        os.remove(session["temp_file_path"])
        session.pop('temp_file_name')
    except:
        pass

    model_id = request.args.get('model_id')
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(models_config)
    assoc = dict(data['models'][model_id]['fields'])
    fields = [k for k, v in assoc.items()]
    form = imodelforms.ImportModelForm(assoc)
    form.set_title(data['models'][model_id]['title'])
    form.set_target(data['models'][model_id]['target'])
    form.set_method(data['models'][model_id]['type'])

    file_name = model_id
    if form.validate_on_submit():
        if form.submit_imf.data:
            formdata = request.form.to_dict()
            assoc = {k[7:]: v for k, v in formdata.items() if k.startswith('column_')}
            print(formdata)
            model_obj = {"title": request.form.to_dict()['title_imf'], "target": formdata['target_imf'], "type": formdata['method_imf'], "fields": assoc}

            path = os.path.join(current_app.root_path, "data", "json", "models.json")

            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_name = file_name.replace('.cbm', '')
                    data['models'][file_name] = model_obj
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            return redirect(url_for('analysis.index'))
        elif form.delete_imf.data:
            try:
                models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
                with open(models_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # снос задач, основанных на удаляемой модели
                tasks = [k for k, v in data['sources'].items() if v['model'] == model_id]
                print(f'deleted tasks: {tasks}')
                for t in tasks:
                    delete_task(t)

                # снос самой модели
                with open(models_config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['models'].pop(model_id)
                with open(models_config, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                model_path = os.path.join(current_app.root_path, 'data', 'catboost', f'{model_id}.cbm')
                os.remove(model_path)

                flash(f'Модель {model_id} и связанные с ней задачи удалены', 'success')
                return redirect(url_for('analysis.index'))
            except Exception as e:
                flash(f'Не удалось удалить модель {model_id}.cbm: {str(e)}', 'error')
                return redirect(request.referrer)
    return render_template('analysis/model/create.html', form=form, model_cols=fields, model_id=model_id)


@model_bp.route('/create', methods=['GET', 'POST'])
@has_permission(['model.create'])
def create(payload):
    print('create: True')
    try:
        model = catboost.CatBoost().load_model(session["temp_file_path"])
        # print(model.feature_names_)
        fields = model.feature_names_
        form = imodelforms.ImportModelForm(fields)

        file_name = str(session["temp_file_name"])
        file_path = os.path.join('data', 'catboost', f'{file_name}')
        file = Path(file_path)

        print(file)
        if file.exists():
            raise Exception(f'Модель с именем файла {file_name} уже существует')
    except CatBoostError as e:
        flash(str(e), 'error')
        return redirect(url_for('analysis.index'))
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('analysis.index'))

    print(f'Удачный импорт')

        # print(f'regression: {isinstance(model, CatBoostRegressor)}\nclassif: {isinstance(model, CatBoostClassifier)}\nranking: {isinstance(model, CatBoostRanker)}')
    if form.validate_on_submit() or form.submit_imf.data:
        print('validated')
        print(f'form: {request.form.to_dict()}')
        formdata = request.form.to_dict()
        assoc = {k[7:]: v for k, v in formdata.items() if k.startswith('column_')}
        model_obj = {"title": request.form.to_dict()['title_imf'], "target": formdata['target_imf'], "type": formdata['method_imf'], "fields": assoc}
        print(f'Модель: {model_obj}')

        path = os.path.join(current_app.root_path, "data", "json", "models.json")

        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                file_name = file_name.replace('.cbm', '')
                data['models'][file_name] = model_obj
                print(f'temp_file_path: {session["temp_file_path"]}')
                if 'temp_file_path' in session:
                    shutil.move(session['temp_file_path'], os.path.join('data', 'catboost', f'{file_name}.cbm'))
                if 'temp_file_name' in session:
                    session.pop('temp_file_name')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        if 'temp_file_path' in session:
            session.pop('temp_file_path')
        return redirect(url_for('analysis.index'))
    return render_template('analysis/model/create.html', form=form, model_cols=fields)

    # form.mapped_value.min_entries = len(fields)
    # form.mapped_value.max_entries = len(fields)
    # print(fields)
    # for name in fields:
    #     form.mapped_value.append_entry(name)
    # print(form.mapped_value.)

    # if form.validate_on_submit():
