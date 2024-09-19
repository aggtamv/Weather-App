from flask import Blueprint, render_template, request, session, redirect, url_for, send_file
import requests
import datetime as dt
from datetime import datetime, timedelta
import meteomatics.api as api # type: ignore
from .models import Cities, WeatherForecast
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from . import db
from sqlalchemy import func, desc
import pandas as pd
import io
from sqlalchemy import cast, Date


auth = Blueprint('auth', __name__)

def get_coordinates(city):
    api_url = f'https://api.api-ninjas.com/v1/geocoding?city={city}'
    headers = {'X-Api-Key': 'CCoWazQWnXn7Uq9bW7nWZw==yeI9Z9WCgMxcmduf'}  # Replace with my API key

    response = requests.get(api_url, headers=headers)
    if response.status_code == requests.codes.ok:
        data = response.json()
        if data:
            return data[0]['latitude'], data[0]['longitude']
    return None, None

def capitalize_text(text):
    """Capitalize the first letter and make the rest lowercase."""
    return text.capitalize() if text else ''    

def add_city_data(cities):
    for city in cities:
        try:
            # Check if the city already exists
            existing_entry = Cities.query.filter_by(city=city['city']).first()
            if existing_entry is None:
                # Add new entry if it does not exist
                new_entry = Cities(
                    country=city['country'],
                    city=city['city'],
                    longitude=city['longitude'],
                    latitude=city['latitude']
                )
                db.session.add(new_entry)
                db.session.commit()
            else:
                print(f"City '{city['city']}' already exists in the database.")
        except IntegrityError as e:
            # Rollback the session in case of an integrity error
            db.session.rollback()
            print(f"IntegrityError: {e.orig}")
        except SQLAlchemyError as e:
            # Rollback the session in case of other SQLAlchemy errors
            db.session.rollback()
            print(f"SQLAlchemyError: {e}")
        except Exception as e:
            # Rollback the session in case of other exceptions
            db.session.rollback()
            print(f"Unexpected error: {e}")

@auth.route('/locations', methods=['GET', 'POST'])
def locations_info():
    if request.method == 'POST':
        if 'remove_city' in request.form:
            city_to_remove = request.form.get('remove_city')
            cities = session.get('cities', [])
            cities = [city for city in cities if city['city'] != city_to_remove]
            session['cities'] = cities
        else:
            country = request.form.get('country')
            city = request.form.get('city')

            latitude, longitude = get_coordinates(city)
            if latitude and longitude:
                city_data = {
                    'country': capitalize_text(country),
                    'city': capitalize_text(city),
                    'latitude': latitude,
                    'longitude': longitude
                }

                cities = session.get('cities', [])
                if len(cities) < 3:
                    cities.append(city_data)
                    session['cities'] = cities
                else:
                    message = "You can only select up to 3 cities."
                    return render_template('locations.html', message=message, cities=cities)
            else:
                message = f"Could not retrieve coordinates for {city}"
                return render_template('locations.html', message=message, cities=cities)

    cities = session.get('cities', [])
    add_city_data(cities)
    return render_template('locations.html', cities=cities)

@auth.route('/forecast', methods=['GET', 'POST'])
def forecast_info():
    # Retrieve cities from session
    current_cities = session.get('cities', [])
    
    
    # Print the cities list for debugging purposes
    print(f"The current cities are:{current_cities}")  # Add this line to check the structure of cities
    
    # Check if the form was submitted
    if request.method == 'POST':
        selected_city_name = request.form.get('current_city')
        print(f"This is the selected city: {selected_city_name}") #Log the result to check if working
        # Find the selected city in the session cities list
        selected_city = [city for city in current_cities if city['city'] == selected_city_name][0]
        
        print(f"this is the selected city: {selected_city}") #Log for troubleshooting
        
        if not selected_city:
            return render_template('forecast.html', cities=current_cities, error="City not found.") #Error troubleshooting

        # Convert selected city to coordinates
        coordinates = [(selected_city['latitude'], selected_city['longitude'])]

        # Set up Meteomatics API parameters
        username = 'bakis_tamvakis_angelos'
        password = 'X0lyJj5k0D'
        parameters = ['t_2m:C', 'precip_1h:mm', 'wind_speed_10m:ms']
        model = 'mix'
        startdate = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
        enddate = startdate + dt.timedelta(days=7)
        interval = dt.timedelta(hours=1)

        # Query the Meteomatics API for the selected city
        try:
            df = api.query_time_series(coordinates, startdate, enddate, interval, parameters, username, password, model=model)
            print(f"This is the df: {df.columns}")
        except Exception as e:
            return render_template('forecast.html', cities=current_cities, error=f"Error fetching data: {e}")
        
        
        # Convert data to a more usable format
        forecast_data = df.reset_index().to_dict(orient='records')
        print(f"The forecast_data are: {forecast_data[:5]}")
        # Store data in the database
        city_record = Cities.query.filter_by(city=selected_city['city']).first()
        print(f"This is the city_record {city_record.city}") #Log for troubleshooting
        for index, row in enumerate(forecast_data):
            forecast = WeatherForecast(
                city_id=city_record.id,
                date=row['validdate'],
                temperature=row['t_2m:C'],
                precipitation=row['precip_1h:mm'],
                wind_speed=row['wind_speed_10m:ms']
            )
            db.session.add(forecast)
        db.session.commit()
        
        # List the average temperature of the last 3 forecasts for each city, grouped by date
        # Query to get the latest 7 distinct dates from the WeatherForecast table
        latest_dates_query = (
            db.session.query(WeatherForecast.date)
            .distinct(WeatherForecast.date)
            .order_by(WeatherForecast.date.desc())
            .limit(7)
        )
        # Fetch the result and extract the dates into a list
        latest_dates = [result.date for result in latest_dates_query.all()]

        # Subquery to get the row number for each temperature measurement
        subquery = (
            db.session.query(
                WeatherForecast.city_id,
                WeatherForecast.date,
                WeatherForecast.temperature,
                func.row_number().over(
                    partition_by=[WeatherForecast.city_id, WeatherForecast.date],
                    order_by=WeatherForecast.date.desc()
                ).label('row_number')
            )
            # Filter for only the latest 7 dates
            .filter(WeatherForecast.date.in_(latest_dates))
            .subquery()
        )

        # Main query to calculate the average temperature for the last 3 measurements per city per day
        query = (
            db.session.query(
                subquery.c.city_id,
                subquery.c.date,
                func.avg(subquery.c.temperature).label('average_temperature')
            )
            .filter(subquery.c.row_number <= 3)  # Keep only the last 3 measurements
            .group_by(subquery.c.city_id, subquery.c.date)
            .order_by(subquery.c.city_id, subquery.c.date)
        )

        avg_temperatures = query.all()

        avg_temperatures = [
            {
                'city_id': result.city_id,
                'date': result.date,
                'average_temperature': round(result.average_temperature, 2)
            }
            for result in avg_temperatures
            ]
        top_temps_query = (
            db.session.query(
                WeatherForecast.city_id,
                WeatherForecast.date,
                WeatherForecast.temperature
            )
            .group_by(WeatherForecast.date, WeatherForecast.city_id)
            .order_by(WeatherForecast.temperature.desc())
            .limit(5)
        )

        # Query for top 5 highest precipitations across all cities
        top_precip_query = (
            db.session.query(
                WeatherForecast.city_id,
                WeatherForecast.date,
                WeatherForecast.precipitation
            )
            .group_by(WeatherForecast.date, WeatherForecast.city_id)
            .order_by(WeatherForecast.precipitation.desc())
            .limit(5)
        )

        # Query for top 5 highest wind speeds across all cities
        top_wind_speed_query = (
            db.session.query(
                WeatherForecast.city_id,
                WeatherForecast.date,
                WeatherForecast.wind_speed
            )
            .group_by(WeatherForecast.date, WeatherForecast.city_id)
            .order_by(WeatherForecast.wind_speed.desc())
            .limit(5)
        )

        # Execute the queries for top 5 measurements
        top_temps = top_temps_query.all()
        top_precip = top_precip_query.all()
        top_wind_speeds = top_wind_speed_query.all()

        # Retrieve all cities for use in the template
        all_cities = Cities.query.all()

        last_forecast = []  # To store last_forecasts
        missing_forecasts = []  # To store cities with missing forecasts

        for city in current_cities:
            city_record = Cities.query.filter_by(city=city['city']).first()
            if city_record:
                temp_id = city_record.id
                temp_forecast = WeatherForecast.query.filter_by(city_id=temp_id).order_by(WeatherForecast.date.desc()).first()
                if temp_forecast:
                    last_forecast.append(temp_forecast)
                else:
                    missing_forecasts.append(city['city'])
            else:
                missing_forecasts.append(city['city'])  # City not found in Cities table

        return render_template('forecast.html', cities=current_cities, forecast_data=forecast_data,
                               last_forecast=last_forecast, missing_forecasts=missing_forecasts, 
                               avg_temperatures=avg_temperatures, all_cities=all_cities,
                               top_temps=top_temps, top_precip=top_precip, top_wind_speeds=top_wind_speeds)

    return render_template('forecast.html', cities=current_cities)

@auth.route('/export_cities_csv', methods=['GET'])
def export_cities_csv():
    # Export Cities table to CSV
    cities_data = db.session.query(Cities).all()
    cities_df = pd.DataFrame([{
        'id': city.id,
        'country': city.country,
        'city': city.city,
        'longitude': city.longitude,
        'latitude': city.latitude
    } for city in cities_data])

    # Use an in-memory buffer to create the CSV file
    output = io.StringIO()
    cities_df.to_csv(output, index=False)
    output.seek(0)

    # Send the file as a response
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='cities.csv')

@auth.route('/export_weather_csv', methods=['GET'])
def export_weather_csv():
    # Export WeatherForecast table to CSV
    weather_data = db.session.query(WeatherForecast).all()
    weather_df = pd.DataFrame([{
        'id': forecast.id,
        'city_id': forecast.city_id,
        'date': forecast.date,
        'temperature': forecast.temperature,
        'precipitation': forecast.precipitation,
        'wind_speed': forecast.wind_speed
    } for forecast in weather_data])

    # Use an in-memory buffer to create the CSV file
    output = io.StringIO()
    weather_df.to_csv(output, index=False)
    output.seek(0)

    # Send the file as a response
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='weather_forecast.csv')


