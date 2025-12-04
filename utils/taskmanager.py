import json
import os

from apscheduler.schedulers.background import BackgroundScheduler
import utils.tasks as tasks


class Scheduler:
    def __init__(self, app):
        self.app = app

        self.scheduler = BackgroundScheduler({
            'apscheduler.job_defaults.max_instances': 10,
            'apscheduler.job_defaults.coalesce': False,
            'apscheduler.job_defaults.misfire_grace_time': 10
        })
        path = os.path.join(self.app.root_path, "data", "json", "models.json")
        self.config = self.get_config(path)
        self.set_tasks()
        self.scheduler.start()

    def get_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_task(self, id: int, obj: dict):
        try:
            t = tasks.Tasks(self.app.root_path)
            proc_id = f'task_{id}'
            type = obj['source']['type']

            freq = None
            if type == 'sql':
                freq = obj['source']['db']['freq']
                self.scheduler.add_job(
                    t.parse_sql,
                    trigger='interval',
                    seconds=freq,
                    args=[id, obj],
                    id=proc_id,
                    replace_existing=True
                )
            elif type == 'json':
                freq = obj['source']['freq']
                self.scheduler.add_job(
                    t.parse_web,
                    trigger='interval',
                    seconds=freq,
                    args=[id, obj],
                    id=proc_id,
                    replace_existing=True
                )
            return freq
        except:
            return False

    def pop_task(self, task_id):
        try:
            self.scheduler.remove_job(f'task_{task_id}')
            return True
        except:
            return False

    def set_tasks(self):
        sources = self.config['sources']
        self.scheduler.remove_all_jobs()

        for k, obj in sources.items():
            freq = self.add_task(k, obj)
            print(f'Задача: {k} запущена! Интервал {freq}')


scheduler = None


def get_scheduler(app=None):
    global scheduler
    if scheduler is None and app:
        scheduler = Scheduler(app)
    return scheduler
