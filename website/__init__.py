from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from os import path
from datetime import timedelta
from flask_migrate import Migrate # type: ignore
from sqlalchemy.sql import func



db = SQLAlchemy()
DB_name = "database.db"


def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY']  = 'secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_name}"
    app.config['SESSION_PERMANENT'] = False
    db.init_app(app)
    
    migrate = Migrate(app, db)


    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')    

    from .models import Cities, WeatherForecast
    
    create_database(app)
    

    # Print URL map to debug routes
    print(app.url_map)
    
    return app

def create_database(app):
    if not path.exists('website/' + DB_name):
        with app.app_context():
            db.create_all()
        print('Created Database!')
