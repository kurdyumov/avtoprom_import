import wtforms
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms.fields.choices import SelectField, SelectMultipleField
from wtforms.fields.simple import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired


class BotID(FlaskForm):
    token_bid = StringField('Токен бота')
    submit_bid = SubmitField('Сохранить')
    remove_bid = SubmitField('Отвязать')
