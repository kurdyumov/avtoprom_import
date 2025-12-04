import json
import os

from flask import current_app
from flask_wtf import FlaskForm
from wtforms.fields.choices import SelectField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class SqlSourceData(FlaskForm):
    db_type_ssd = SelectField('СУБД', choices=[('', 'Выберите драйвер')]+[('mysql', 'MySQL'), ('postgresql', 'PostgreSQL')])
    host_ssd = StringField('Адрес подключения', validators=[DataRequired()])
    port_ssd = StringField('Порт подключения', validators=[DataRequired()])
    database_ssd = StringField('Имя БД', validators=[DataRequired()])
    user_ssd = StringField('Пользователь', validators=[DataRequired()])
    password_ssd = PasswordField('Пароль', validators=[DataRequired()])
    query_ssd = StringField('SQL-запрос', validators=[DataRequired()])
    frequency_ssd = IntegerField('Частота запроса (сек.)', validators=[NumberRange(min=0), DataRequired()])
    test_ssd = SubmitField('Тест')

    def fill_data(self, type: str, host: str, port: str, db: str, user: str, psw: str, query: str, freq: int):
        self.db_type_ssd.data = type
        self.host_ssd.data = host
        self.port_ssd.data = port
        self.database_ssd.data = db
        self.user_ssd.data = user
        self.password_ssd.data = psw
        self.query_ssd.data = query
        self.frequency_ssd.data = freq


class JsonSourceData(FlaskForm):
    host_jsd = StringField('Адрес запроса')
    frequency_jsd = IntegerField('Частота запроса (сек.)', validators=[NumberRange(min=0), DataRequired()])
    test_jsd = SubmitField('Тест')

    def fill_data(self, host: str, freq: int):
        self.host_jsd.data = host
        self.frequency_jsd.data = freq


class CreateModelConnect(FlaskForm):
    title_cmc = StringField('Название ресурса', validators=[DataRequired()])
    model_cmc = SelectField('Модель', validators=[DataRequired()], choices=[('', 'Выберите модель:')]+[], default='', coerce=str)
    type_cmc = SelectField('Источник данных', validators=[DataRequired()], choices=[('', 'Выберите тип:')]+[
        ('form', 'Вручную формой'),
        ('json', 'JSON из IoT-оборудования'),
        ('sql', 'SQL-запросом'),
    ], default='')
    sql_settings_cmc = FormField(SqlSourceData)
    json_settings_cmc = FormField(JsonSourceData)
    mapping_cmc = FieldList(StringField('Field', validators=[DataRequired()]), min_entries=0)
    submit_cmc = SubmitField('Сохранить')
    delete_cmc = SubmitField('Удалить')

    def list_models(self, models):
        self.model_cmc.choices = self.model_cmc.choices + models

    def gen_map_fields(self, model):
        return

    def __init__(self, columns=None, values=None, **kwargs):
        super().__init__(**kwargs)
        self.mapping_cmc.entries = []
        if isinstance(columns, dict):
            for i, (k, v) in enumerate(columns.items()):
                self.mapping_cmc.append_entry()
                self.mapping_cmc[i].name = f'column_{k}'
                self.mapping_cmc[i].label = v
                if isinstance(values, dict):
                    print(values[k])
                    self.mapping_cmc[i].data = values[k]


class InputRecordIntoModelForm(FlaskForm):
    values_irimf = FieldList(StringField('Column'))
    submit_irimf = SubmitField('Прогноз')

    def __init__(self, con_id: int, **kwargs):
        # print(f'fields: {fields}')
        super().__init__(**kwargs)
        models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
        with open(models_config, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f'con_id: {con_id}, data: {data["sources"][str(con_id)]["model"]}')
        fields = data["sources"][str(con_id)]["fields"]

        model_name = data["sources"][str(con_id)]["model"]

        for i, (k, v) in enumerate(fields.items()):
            self.values_irimf.append_entry()
            self.values_irimf[i].name = f'column_{k}'
            self.values_irimf[i].label = v
            self.values_irimf[i].render_kw = {'placeholder': data['models'][model_name]['fields'][k]}
