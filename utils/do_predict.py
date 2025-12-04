import json
import os

import pandas as pd
from catboost import CatBoostRegressor, CatBoostRanker, CatBoostClassifier
from sklearn.metrics import *
import matplotlib.pyplot as plt


def do_forecast(model_name: str, data: dict, app_path: str):
    models_config = os.path.join(app_path, "data", "json", "models.json")
    with open(models_config, 'r', encoding='utf-8') as f:
        conf = json.load(f)
    model_file = os.path.join(app_path, 'data', 'catboost', f'{model_name}.cbm')
    model_type = conf["models"][model_name]["type"]
    if model_type == 'classification':
        model = CatBoostClassifier()
        model.load_model(model_file)
        df = pd.DataFrame(data, index=[0])
        res = model.predict(df)[0]
        proba = model.predict_proba(df)[0][1]
        return f"{'Да' if res else 'Нет'} (вероятность: {round(proba, 4)})"
    elif model_type == 'regression':
        model = CatBoostRegressor()
        model.load_model(model_file)
        df = pd.DataFrame(data, index=[0])
        pred = model.predict(df)[0]
        return pred
    elif model_type == 'ranking':
        model = CatBoostRanker()
        model.load_model(model_file)
        df = pd.DataFrame(data, index=[0])
        pred = model.predict(df)[0]
        return pred
    else:
        raise Exception('Некорректный метод модели')
