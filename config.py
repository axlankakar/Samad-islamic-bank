import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here_change_this' # CHANGE THIS!
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'bank.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # You can add other configurations here, e.g., for mail, etc. 