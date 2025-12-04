import json
import os

from apscheduler.schedulers.background import BackgroundScheduler
import utils3.tasks as tasks


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
        set_tasks(self.scheduler, self.config, self.app.root_path)
        self.scheduler.start()

    def get_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_task(self, type: str, id: int, obj: dict, freq):
        try:
            t = tasks.Tasks(self.app.app_path)
            proc_id = f'task_{k}'

            if type == 'sql':
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
            return True
        except:
            return False

    def set_tasks(self):
        sources = self.config['sources']
        self.scheduler.remove_all_jobs()

        for k, obj in sources.items():
            type = obj['source']['type']
            freq = obj['source']['freq']

            add_task(self.app.app_path, self.scheduler, type, k, obj, freq)
            print(f'Задача: {k} запущена! Интервал {freq}')


def get_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def add_task(app_path, scheduler: BackgroundScheduler, type: str, k: int, obj, freq):
    t = tasks.Tasks(app_path)
    proc_id = f'task_{k}'

    if type == 'sql':
        # freq = obj['source']['freq']
        scheduler.add_job(
            t.parse_sql,
            trigger='interval',
            seconds=freq,
            args=[k, obj],
            id=proc_id,
            replace_existing=True
        )
    elif type == 'json':
        freq = obj['source']['freq']
        scheduler.add_job(
            t.parse_web,
            trigger='interval',
            seconds=freq,
            args=[k, obj],
            id=proc_id,
            replace_existing=True
        )
    pass


def set_tasks(scheduler: BackgroundScheduler, config, app_path):
    sources = config['sources']
    scheduler.remove_all_jobs()
    t = tasks.Tasks(app_path)

    for k, obj in sources.items():
        type = obj['source']['type']
        # proc_id = f'task_{k}'
        freq = obj['source']['freq']

        add_task(app_path, scheduler, type, k, obj, freq)
        # if type == 'sql':
        #     freq = obj['source']['freq']
        #     scheduler.add_job(
        #         t.parse_sql,
        #         trigger='interval',
        #         seconds=freq,
        #         args=[k, obj],
        #         id=proc_id,
        #         replace_existing=True
        #     )
        # elif type == 'json':
        #     freq = obj['source']['freq']
        #     scheduler.add_job(
        #         t.parse_web,
        #         trigger='interval',
        #         seconds=freq,
        #         args=[k, obj],
        #         id=proc_id,
        #         replace_existing=True
        #     )
        print(f'Задача: {k} запущена! Интервал {freq}')


# def update_scheduler(scheduler: BackgroundScheduler, config):
#     set_tasks(scheduler, config)


def start_scheduler(app):
    scheduler = BackgroundScheduler({
        'apscheduler.job_defaults.max_instances': 10,  # Разрешить до 2 параллельных задач
        'apscheduler.job_defaults.coalesce': False,  # Объединять пропущенные запуски
        'apscheduler.job_defaults.misfire_grace_time': 10  # Допуск 30 секунд на задержку
    })
    path = os.path.join(app.root_path, "data", "json", "models.json")
    config = get_config(path)
    set_tasks(scheduler, config, app.root_path)
    # scheduler.add_job(
    #     update_scheduler,
    #     trigger='interval',
    #     minutes=5,
    #     args=[scheduler, config],
    #     id='update_scheduler',
    #     replace_existing=True
    # )
    scheduler.start()
