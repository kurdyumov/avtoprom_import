import json
import os

from flask import Blueprint, render_template, flash
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from utils.decorators import *
import forms.import_model as importcbm

from catboost import CatBoostRanker, CatBoostRegressor, CatBoostClassifier

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')


@analysis_bp.route('/', methods=['GET', 'POST'])
@has_permission(['analysis'])
def index(payload):
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    form = importcbm.ImportModelFile()
    if form.validate_on_submit() and form.submit_imf.data:
        file = form.model_imf.data
        file_name = file.filename
        # print(request.files[form.model_imf.data].filename)

        if not file_name.lower().endswith('.cbm'):
            flash('Файл должен иметь расширение .cbm', 'error')
        else:
            file_path = os.path.join('temp', file_name)
            file.save(file_path)
            print(f'Модель {file_name} импортирована!')
            # session['model_file'] = file
            session['temp_file_path'] = file_path
            session['temp_file_name'] = file_name
            return redirect(url_for('model.create', file_path=file_path))
    return render_template('analysis/index.html', importcbm=form, models_json=data)
