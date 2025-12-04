import wtforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import StringField, PasswordField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired


class EditRoleForm(FlaskForm):
    title_erf = StringField('Наименование', validators=[DataRequired()])
    permissions_erf = SelectMultipleField('Разрешения', coerce=int,
                                          widget=wtforms.widgets.ListWidget(prefix_label=False))
    broadcast_erf = SelectMultipleField('Рассылки по', coerce=int,
                                          widget=wtforms.widgets.ListWidget(prefix_label=False))
    delete_erf = SubmitField('Удалить')
    submit_erf = SubmitField('Сохранить')

    def fill_form(self, role: dict):
        self.title_erf.data = role['title']

    def fill_perms(self, perms: list):
        self.permissions_erf.data = perms

    def fill_tasks(self, tasks: list):
        self.broadcast_erf.data = tasks

    def assoc_fields(self):
        return {
            'title': 'title_erf'
        }


class CreateRoleForm(FlaskForm):
    title_crf = StringField('Наименование', validators=[DataRequired()])
    permissions_crf = SelectMultipleField('Разрешения', coerce=int,
                                          widget=wtforms.widgets.ListWidget(prefix_label=False))
    broadcast_crf = SelectMultipleField('Рассылки по', coerce=int,
                                        widget=wtforms.widgets.ListWidget(prefix_label=False))
    submit_crf = SubmitField('Сохранить')

    def assoc_fields(self):
        return {
            'title': 'title_crf',
            'permission': 'permissions_crf',
            'broadcast': 'broadcast_crf'
        }
