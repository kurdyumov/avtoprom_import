import wtforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired


class EditProfileRef(FlaskForm):
    submit_epr = SubmitField('...')


class UserProfileEdit(FlaskForm):
    login_up = StringField('Логин', validators=[DataRequired()])
    lastname_up = StringField('Фамилия', validators=[DataRequired()])
    firstname_up = StringField('Имя', validators=[DataRequired()])
    patronymic_up = StringField('Отчество', validators=[DataRequired()])
    emp_num_up = StringField('Номер сотрудника', validators=[DataRequired()])
    password_old_up = PasswordField('Текущий пароль')
    password_up = PasswordField('Новый пароль')
    repassword_up = PasswordField('Повторите пароль')
    submit_up = SubmitField('Сохранить', validators=[DataRequired()])
    delete_up = SubmitField('Удалить', validators=[DataRequired()])

    roles_up = SelectMultipleField('Роли', coerce=int,
                                          widget=wtforms.widgets.ListWidget(prefix_label=False))

    def fill_profile(self, profile: dict):
        try:
            self.login_up.data = profile['login']
            self.lastname_up.data = profile['lastname']
            self.firstname_up.data = profile['firstname']
            self.patronymic_up.data = profile['patronymic']
            self.emp_num_up.data = profile['emp_num']
        except:
            print(f'profile: {profile}')
            raise Exception('Некорректный профиль')

    def assoc_fields(self):
        return {
            'login': 'login_up',
            'lastname': 'lastname_up',
            'firstname': 'firstname_up',
            'patronymic': 'patronymic_up',
            'emp_num': 'emp_num_up',
            'password_old': 'password_old_up',
            'password': 'password_up',
            'permission': 'permissions_up'
        }
