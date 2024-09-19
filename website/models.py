from . import db
from sqlalchemy import func

class Cities(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Primary key column
    country = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(150), unique=True, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)

class WeatherForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=False)  # Foreign key to Cities
    date = db.Column(db.Date, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    precipitation = db.Column(db.Float, nullable=True)
    wind_speed = db.Column(db.Float, nullable=True)

    city = db.relationship('Cities', backref='forecasts')

