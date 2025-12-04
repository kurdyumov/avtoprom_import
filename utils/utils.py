import json
import os

from flask import current_app

import utils.sqlite as sql
from utils.taskmanager import get_scheduler


def clear_temp():
    temp = os.path.join(current_app.root_path, "temp")
    for f in os.listdir(temp):
        file_path = os.path.join(temp, f)
        os.remove(file_path)


def delete_task(source_id):
    models_config = os.path.join(current_app.root_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sql.clear_broadcast(int(source_id))
    data['sources'].pop(source_id)
    with open(models_config, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    get_scheduler().pop_task(source_id)