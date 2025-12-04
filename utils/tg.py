import json
import os
from pathlib import Path

import bcrypt
import requests
import telebot
import sqlite3
import time
import utils.sqlite as sql

root = Path(__file__).resolve().parent.parent

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), 'avtoprom.db'), check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

ADMIN_ID = None


def read_conf():
    config = os.path.join(root, "data", "json", "config.json")
    with open(config, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def write_conf(data):
    config = os.path.join(root, "data", "json", "config.json")
    with open(config, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class CustomTGBot:
    @staticmethod
    def check_bot(token):
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        token = response.json()
        if token['ok']:
            return token
        else:
            data = read_conf()
            data['telegram_bot_token'] = None
            write_conf(data)
            # raise Exception('Некорректный токен')
            return False

    def __init__(self):
        data = read_conf()

        if 'telegram_bot_token' not in data:
            raise Exception('Не удалось найти токен чат-бота')

        self.token = data['telegram_bot_token']
        token = CustomTGBot.check_bot(self.token)
        if not token:
            raise Exception('Некорректный токен')
        self.bot = telebot.TeleBot(self.token)
        self.init_handlers()

    def broadcast_report(self, path_to_doc, task_id, message='Задайте текст'):
        tg = sql.get_all_tg()
        if os.path.isfile(path_to_doc):
            for chat_id in list(tg['chat_id']):
                bc_list = sql.get_emp_subscriptions(chat_id)
                # print(f'tg: {chat_id}, tasks: {list(bc_list["task_id"])}')
                if int(task_id) in list(bc_list["task_id"]):
                    print(f'{chat_id} ждёт статус задачи {task_id}')
                    with open(path_to_doc, 'rb') as pdf_file:
                        self.bot.send_document(chat_id, pdf_file, caption=message)
                else:
                    print(f'{chat_id} не подписан на #{task_id}')

    def add_user(self, chat_id):
        cursor.execute('INSERT OR IGNORE INTO tg (chat_id) VALUES (?)', (chat_id,))
        conn.commit()

    def get_subscribers(self):
        conn.row_factory = sqlite3.Row
        cursor.execute('SELECT chat_id FROM users WHERE subscribed = 1')
        return [row[0] for row in cursor.fetchall()]

    def broadcast_message(self, message_text):
        subscribers = self.get_subscribers()
        for chat_id in subscribers:
            try:
                self.bot.send_message(chat_id, message_text)
                time.sleep(0.05)
            except Exception as e:
                print(f"Ошибка отправки в {chat_id}: {e}")
                # Опционально: отключить неактивных
                cursor.execute('UPDATE users SET subscribed = 0 WHERE chat_id = ?', (chat_id,))
                conn.commit()

    def init_handlers(self):
        bot = self.bot

        @bot.message_handler(commands=['start'])
        def start(message):
            self.add_user(message.chat.id)
            self.bot.reply_to(message, "Привет! Ты добавлен в список уведомлений. Используй /help для справки.")

        @bot.message_handler(commands=['help'])
        def help_command(message):
            bot.reply_to(message,
                         "Это бот-рассылка производственных показаний\n/binduser <ваш_логин_в_ИС> - привязать тг к "
                         "сотруднику\n/me - текущие настройки\n/resetpassword <новый_пароль> - сбросить старый пароль")

        @bot.message_handler(commands=['me'])
        def me(message):
            conn.row_factory = sqlite3.Row
            query = 'select * from tg where chat_id=?'
            res = cursor.execute(query, (message.from_user.id,))
            info = ''
            tguser = res.fetchone()
            if tguser:
                info += 'Вы зарегистрированы в ИС'
                query = 'select * from users where tg=?'
                res = cursor.execute(query, (message.from_user.id,))
                user = res.fetchone()
                if user:
                    print(user)
                    info += f'\nВаш логин: {user["login"]}'
                else:
                    info += f'\nПривязка к сотруднику: /binduser <логин_в_ИС>'
            else:
                info = 'Введите /start для регистрации'

            bot.reply_to(message, info)

        @bot.message_handler(commands=['resetpassword'])
        def resetpassword(message):
            conn.row_factory = sqlite3.Row
            command_text = message.text[len('/resetpassword '):].strip() if message.text.startswith(
                '/resetpassword ') else ''
            params = command_text.split()

            if len(params) == 1:
                query = 'select * from users where tg=?'
                res = cursor.execute(query, (message.from_user.id,))
                user = res.fetchone()
                if user:
                    hashed = bcrypt.hashpw(params[0].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    query = 'update users set password=? where tg=?'
                    cursor.execute(query, (hashed, message.from_user.id))
                    conn.commit()
                    bot.reply_to(message, 'Ваш пароль успешно изменён!')
                else:
                    bot.reply_to(message, f'Вы не привязаны к сотруднику. Выполните /binduser <логин_в_ИС>')
            else:
                bot.reply_to(message, 'Синтаксис: /resetpassword <новый_пароль>')

        @bot.message_handler(commands=['broadcast'])
        def broadcast_start(message):
            if message.from_user.id != ADMIN_ID:
                bot.reply_to(message, "У вас нет прав на эту команду.")
                return
            msg = bot.reply_to(message, "Введите текст для рассылки:")
            bot.register_next_step_handler(msg, self.process_broadcast_text)

        @bot.message_handler(commands=['binduser'])
        def bind_user(message):
            # if message.from_user.id != ADMIN_ID:
            #     bot.reply_to(message, "У вас нет прав на эту команду.")
            #     return
            command_text = message.text[len('/binduser '):].strip() if message.text.startswith('/binduser ') else ''
            params = command_text.split()

            if len(params) == 1:
                # conn.row_factory = sqlite3.Row
                query = 'select * from users where login=? and tg is null'
                try:
                    res = cursor.execute(query, (command_text,))
                    user = res.fetchall()
                    query = 'update users set tg=? where login=?'
                    cursor.execute(query, (message.from_user.id, params[0]))
                    conn.commit()
                    bot.reply_to(message, f'Добро пожаловать, {user[0][1]} {user[0][2]} {user[0][3]}!')
                except Exception as e:
                    bot.reply_to(message, f'Такого логина нет, либо он уже имеет тг привязку')
                    bot.reply_to(message, str(e))
                    # bot.reply_to(message, 'Пользователя не существует, либо tg уже привязан')
            else:
                bot.reply_to(message, 'Ожидается 1 параметр - номер сотрудника на предприятии (узнайте у руководства)')

    def process_broadcast_text(self, message):
        if message.from_user.id != ADMIN_ID:
            return
        self.broadcast_message(message.text)
        self.bot.reply_to(message,
                          f"Рассылка '{message.text}' завершена для {len(self.get_subscribers())} пользователей.")


global_bot = None


def tg_bot():
    global global_bot
    if global_bot is None:
        global_bot = CustomTGBot()
    return global_bot


if __name__ == '__main__':
    print("Бот запущен...")
    tg_bot().bot.infinity_polling()
