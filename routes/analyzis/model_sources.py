# управление подключениями модели к внешним ресурсам
import json
import os
from urllib.parse import quote_plus

import requests
from dotenv import load_dotenv
from flask import Blueprint, render_template, url_for, current_app, request, jsonify, flash, redirect
from sqlalchemy import create_engine, text

import forms.connect_model as modelforms
from utils.decorators import has_permission
from utils.taskmanager import get_scheduler
from utils.tasks import Tasks
from utils.utils import delete_task

model_source_bp = Blueprint('model_source', __name__, url_prefix='/model/source')


@model_source_bp.route('/', methods=['GET'])
@has_permission(['source'])
def index(payload):
    # return '1'
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sources = data['sources']
    return render_template('analysis/model/source/index.html', sources=sources)


@model_source_bp.route('/select', methods=['GET'])
@has_permission(['source.select'])
def select(payload):
    task = request.args.get('task')
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    source = data['sources'][task]
    return render_template('analysis/model/source/select.html', source=source, task=task)


@model_source_bp.route('/create', methods=['GET', 'POST'])
@has_permission(['source.create'])
def create(payload):
    load_dotenv()
    # print(f'{os.path.exists(os.path.join(current_app.root_path, "data", "json", "models.json"))}')
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(data['models'])

    models = []
    for k, d in data['models'].items():
        try:
            models.append((k, d['title']))
        except Exception as e:
            models.append((k, k))
            print(f'Не удалось извлечь имя модель: нет title')
    print(models)
    form = modelforms.CreateModelConnect()
    form.list_models(models)
    # form.model_cmc.сhoices = [('', 'Выберите модели:')]

    source_id = None

    if request.args.get('source_id'):
        source_id = request.args.get('source_id')
        connection = data['sources'][source_id]
        print(f'source_id: {source_id}, data: {connection}')
        form.title_cmc.data = connection['title']
        form.model_cmc.data = connection['model']

        form.type_cmc.data = connection['source']['type']

        if form.delete_cmc.data:
            delete_task(source_id)
            flash(f'Задача #{source_id} удалена и снята с потока', 'success')
            return redirect(url_for('model_source.index'))

    if form.submit_cmc.data:
        source_id = request.args.get('source_id')
        print(f'edited connection id: {source_id}')

        data = request.form.to_dict()
        models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
        with open(models_config, 'r', encoding='utf-8') as f:
            models_json = json.load(f)
        if not 'sources' in models_json:
            models_json['sources'] = {}

        print(f'form: {data}')

        assoc = {k.replace('column_', ''): v for k, v in data.items() if k.startswith('column_')}

        source = {}

        if data['type_cmc'] == 'form':
            source = {
                "type": data['type_cmc']
            }
        elif data['type_cmc'] == 'json':
            freq = int(data['json_settings_cmc-frequency_jsd'])
            source = {
                "type": data['type_cmc'],
                "host": data['json_settings_cmc-host_jsd'],
                "freq": freq
            }
        elif data['type_cmc'] == 'sql':
            freq = data['sql_settings_cmc-frequency_ssd']
            source = {
                "type": data['type_cmc'],
                "db": {
                    "driver": data['sql_settings_cmc-db_type_ssd'],
                    "host": data['sql_settings_cmc-host_ssd'],
                    "port": data['sql_settings_cmc-port_ssd'],
                    "dbname": data['sql_settings_cmc-database_ssd'],
                    "user": data['sql_settings_cmc-user_ssd'],
                    "password": data['sql_settings_cmc-password_ssd'],
                    "query": data['sql_settings_cmc-query_ssd'],
                    "freq": int(freq)
                }
            }

        con_obj = {
            "title": data['title_cmc'],
            "model": data['model_cmc'],
            "fields": assoc,
            "source": source
        }

        keys = models_json['sources'].keys()
        key = source_id or max([int(i) for i in keys])+1
        models_json['sources'][key] = con_obj
        with open(models_config, 'w', encoding='utf-8') as f:
            json.dump(models_json, f, ensure_ascii=False, indent=4)

        if data['type_cmc'] in ['sql', 'json']:
            get_scheduler().add_task(key, con_obj)

        if source_id:
            flash(f'Задача #{source_id} успешно обновлена', 'success')
        else:
            flash('Задача успешно создана и добавлена в очередь', 'success')
        return redirect(url_for('model_source.index'))

    return render_template('analysis/model/source/create.html', form=form, task=source_id)


@model_source_bp.route('/con_type_fields', methods=['POST'])
def con_type_fields():
    source_type = request.form.get('source_type')
    source_id = request.form.get('source_id')

    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if source_type:
        pass
    elif not source_type and source_id:
        source_type = data['sources'][source_id]['model']
    else:
        return jsonify({'Cant define fields'})

    # тут изменение fieldlist
    columns = data['models'][source_type]['fields']

    form = modelforms.CreateModelConnect(columns=columns, values=data['sources'][source_id]['fields']) if source_id else modelforms.CreateModelConnect(columns=columns)

    html = '<legend>Маппинг столбцов {модель: источник}</legend>'
    for i, field in enumerate(form.mapping_cmc):
        html += f'<div><label>{field.label}</label>{field()}</div>'
    return jsonify({'received_source': source_type, 'columns': columns, 'form': html}), 200


@model_source_bp.route('/source_type_fields', methods=['POST'])
def source_type_fields():
    source_type = request.form.get('source_type')
    source_id = request.form.get('source_id')

    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if source_type:
        pass
    elif not source_type and source_id:
        source_type = data['sources'][source_id]['source']['type']
    else:
        return jsonify({'Cant define fields'}), 403

    # if source_type == 'form':
    #     pass
    html = '<legend>Данные для подключения</legend>'
    form = modelforms.CreateModelConnect()
    test = 'no test'
    if source_type == 'sql':
        if source_id:
            con = data['sources'][source_id]['source']
            db = con['db']
            form.sql_settings_cmc.fill_data(db['driver'], db['host'], db['port'], db['dbname'], db['user'], db['password'], db['query'], db['freq'])
        html += f'<div>{form.sql_settings_cmc.db_type_ssd.label}{form.sql_settings_cmc.db_type_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.host_ssd.label}{form.sql_settings_cmc.host_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.port_ssd.label}{form.sql_settings_cmc.port_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.database_ssd.label}{form.sql_settings_cmc.database_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.user_ssd.label}{form.sql_settings_cmc.user_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.password_ssd.label}{form.sql_settings_cmc.password_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.query_ssd.label}{form.sql_settings_cmc.query_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.frequency_ssd.label}{form.sql_settings_cmc.frequency_ssd()}</div>'
        html += f'<div>{form.sql_settings_cmc.test_ssd()}</div>'

    elif source_type == 'json':
        if source_id:
            print('JSON EXISTS')
            con = data['sources'][source_id]['source']
            form.json_settings_cmc.fill_data(con['host'], con['freq'])

        html += f'<div>{form.json_settings_cmc.host_jsd.label}{form.json_settings_cmc.host_jsd()}</div>'
        html += f'<div>{form.json_settings_cmc.frequency_jsd.label}{form.json_settings_cmc.frequency_jsd()}</div>'
        html += f'<div>{form.json_settings_cmc.test_jsd()}</div>'
    return jsonify({'source': source_type, 'html': html, 'test': test}), 200


@model_source_bp.route('/sql_test', methods=['post'])
def sql_test():
    form = request.form.to_dict()
    print(f'form: {form}')
    return try_db(form['sql_settings_cmc-db_type_ssd'], form['sql_settings_cmc-host_ssd'], form['sql_settings_cmc'
                                                                                                '-port_ssd'],
                  form['sql_settings_cmc-user_ssd'], form['sql_settings_cmc-password_ssd'],
                  form['sql_settings_cmc-database_ssd'], form['sql_settings_cmc-query_ssd'])
    # return jsonify({'test': 'sql', 'form': request.form}), 200


@model_source_bp.route('/json_test', methods=['post'])
def json_test():
    form = request.form.to_dict()
    print(f'HOST {form["json_settings_cmc-host_jsd"]}')
    try:
        res = requests.get(form['json_settings_cmc-host_jsd'])
        if res.status_code == 200:
            data = res.json()  # Извлекаем JSON из ответа
            print(f'res: {data}')
            return jsonify({'json': 'success', 'res': data, 'answer': 'Web-запрос успешно выполнен!'}), 200
        else:
            return jsonify({'json': 'failed', 'res': f'HTTP {res.status_code}', 'answer': 'Не удалось выполнить web-запрос'}), res.status_code
    except Exception as e:
        return jsonify({'json': 'failed', 'res': e, 'answer': f'Не удалось выполнить web-запрос: {e}'}), 403


@model_source_bp.route('/passform', methods=['GET', 'POST'])
@has_permission(['source.use'])
def pass_form_type(payload):
    form_id = request.args.get('form_id')
    if not form_id:
        return redirect(url_for('model_source.index'))
    form = modelforms.InputRecordIntoModelForm(con_id=int(form_id))

    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if form.validate_on_submit():
        #TODO отправить в модель

        # model_name = data['sources'][form_id]['model']
        tasks = Tasks(current_app.root_path)
        try:
            params = {k.replace('column_', ''): v for k, v in request.form.to_dict().items() if k.startswith('column_')}
            tasks.pred_and_print(form_id, data['sources'][form_id], params, None)
            flash('Результат сохранён в PDF и отправлен в чат-бот', 'success')
        except Exception as e:
            err = f'Не удалось считать форму: {e}'
            tasks.pred_and_print(form_id, data['sources'], None, err)
            flash(err, 'error')

        # pred = do_forecast(model_name, params, current_app.root_path)
        # params = json.dumps(params, sort_keys=True, indent=4)
        #
        # header = {
        #     '{DATETIME}': datetime.datetime.now().strftime('%d %B %Y г. %H:%M:%S')
        # }
        # content = {
        #     '{TASK_NUM}': form_id,
        #     '{PROCESS}': data['sources'][form_id]['title'],
        #     '{MODEL}': f"{data['sources'][form_id]['model']}.cbm",
        #     '{TARGET}': data['models'][model_name]['target'],
        #     '{RESULT}': str(round(pred, 3)),
        #     '{PARAMS}': params
        # }
        # paragraph = {
        #     '{TASK_NAME}': data['sources'][form_id]['title'],
        #     '{TASK_NUM}': form_id,
        # }
        # doc = Tasks(current_app.root_path)
        # pdf = doc.prepare_doc(form_id, header_repl=header, table_repl=content, par_repl=paragraph)
        # base_name = f'{data["sources"][form_id]["title"]}_{form_id}_{datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")}.docx'
        # message, url = doc.write_pdf(pdf, base_name)

        # print(f'[passform] model: {model_name}, data: {request.form.to_dict()}')


    return render_template('analysis/model/source/passbyform.html', form=form, title=data["sources"][form_id]["title"])


def try_db(driver, host, port, user, password, database, query):
    if driver == 'mysql':
        driver = f'{driver}+pymysql'
    try:
        connection_path = f'{driver}://{user}:{quote_plus(password)}@{host}:{port}/{database}'
        engine = create_engine(connection_path, echo=False)
        with engine.connect() as c:
            data = c.execute(text(query)).fetchall()
            print(data)
        # flash(f'Успешное подключение к БД!', 'success')
        return jsonify({'Тест SQL': 'Пройден', 'answer': 'Успешное подключение к БД!'}), 200
    except Exception as e:
        # flash(f'Не удалось соединиться с БД: {e}', 'error')
        return jsonify({'Тест SQL': str(e), 'answer': f'Не удалось соединиться с БД: {e}'}), 403
