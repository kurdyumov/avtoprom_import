import wtforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired


class ImportModelFile(FlaskForm):
    model_imf = FileField('Выберите .cbm модель', validators=[
        DataRequired()
    ])
    submit_imf = SubmitField('Импорт')


class ModelColumn(FlaskForm):
    column = StringField('Значение', validators=[DataRequired()])


class ImportModelForm(FlaskForm):
    title_imf = StringField('Наименование', validators=[DataRequired()])
    method_imf = SelectField('Метод модели', choices=[('', 'Выберите метод модели')]+[('classification', 'Классификация'), ('regression', 'Регрессия'), ('ranking', 'Ранжирование')])
    target_imf = StringField('Имя целевого пар.', validators=[DataRequired()])
    mapped_value = FieldList(StringField('Field'), validators=[DataRequired()], min_entries=0)
    submit_imf = SubmitField('Сохранить')
    delete_imf = SubmitField('Удалить')

    def __init__(self, columns, **kwargs):
        super().__init__(**kwargs)
        self.mapped_value.entries = []
        if isinstance(columns, list):
            for i, c in enumerate(columns):
                self.mapped_value.append_entry()
                self.mapped_value[i].name = f'column_{c}'
                self.mapped_value[i].label = c
        elif isinstance(columns, dict):
            for i, (k, v) in enumerate(columns.items()):
                self.mapped_value.append_entry()
                self.mapped_value[i].name = f'column_{k}'
                self.mapped_value[i].label = k
                self.mapped_value[i].data = v

    def set_title(self, title: str):
        self.title_imf.data = title

    def set_target(self, title: str):
        self.target_imf.data = title

    def set_method(self, title: str):
        self.method_imf.data = title





