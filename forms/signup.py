from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired


class SignupForm(FlaskForm):
    lastname_sf = StringField('Фамилия', validators=[DataRequired()])
    firstname_sf = StringField('Имя', validators=[DataRequired()])
    patronymic_sf = StringField('Отчество', validators=[DataRequired()])
    emp_num_sf = StringField('Номер сотрудника', validators=[DataRequired()])
    submit_sf = SubmitField('Регистрация')


class ExcelSignupForm(FlaskForm):
    excel_file_esf = FileField('Выберите cvs с пользователями', validators=[
        DataRequired(),
        FileAllowed(['xls', 'xlsx'], message='Допустимы только файлы .xls и .xlsx')
    ])
    submit_esf = SubmitField('Регистрация')


class ExcelMappingForm(FlaskForm):
    lastname_emf = SelectField('Фамилия', validators=[DataRequired()])
    firstname_emf = SelectField('Имя', validators=[DataRequired()])
    patronymic_emf = SelectField('Отчество', validators=[DataRequired()])
    emp_num_emf = SelectField('Номер сотрудника', validators=[DataRequired()])
    submit_emf = SubmitField('Импорт')

    def set_choices(self, columns):
        self.lastname_emf.choices = [(col, col) for col in columns]
        self.firstname_emf.choices = [(col, col) for col in columns]
        self.patronymic_emf.choices = [(col, col) for col in columns]
        self.emp_num_emf.choices = [(col, col) for col in columns]


class ExportExcelUsers(FlaskForm):
    submit_e = SubmitField('Скачать пароли')


class ExportTxtUser(FlaskForm):
    submit_etu = SubmitField('Скачать учётную запись')
