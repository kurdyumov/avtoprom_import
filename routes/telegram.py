import json
import os

import requests
import telebot
from flask import Blueprint, render_template, current_app, flash, redirect, url_for

from utils.decorators import has_permission
import forms.telegram as tgforms
from utils.tg import CustomTGBot

telegram_bp = Blueprint('telegram', __name__, url_prefix='/telegram')


@telegram_bp.route('/', methods=['GET', 'POST'])
@has_permission(['telegram'])
def index(payload):
    token_form = tgforms.BotID()
    config = os.path.join(current_app.root_path, "data", "json", "config.json")
    with open(config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    read_bot = None
    if 'telegram_bot_token' in data:
        bot_token = data['telegram_bot_token']
        if not bot_token is None:
            token_form.token_bid.data = data['telegram_bot_token']
            read_bot = CustomTGBot.check_bot(data['telegram_bot_token'])
    if token_form.validate_on_submit():
        if token_form.submit_bid.data:
            token = token_form.token_bid.data
            token_res = CustomTGBot.check_bot(token)

            print(token_res)
            if token_res:
                data['telegram_bot_token'] = token_form.token_bid.data
                with open(config, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(token)
            else:
                flash('Некорректный токен', 'error')

        if token_form.remove_bid.data:
            print('Токен отвязан')
            data['telegram_bot_token'] = None
            with open(config, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            flash('Токен отвязан', 'success')

        return redirect(url_for('telegram.index'))

    return render_template('telegram/index.html', token_form=token_form, read_bot=read_bot)
