import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'I like pineapple on my pizza'
    UPLOAD_FOLDER = 'uploads'
    MODELS_FOLDER = 'data/catboost'
