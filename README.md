# Weather Forecast Web App  <img src="website/static/img/weatherlogo.png" alt="Weather App Logo" width="50" height="50">

This project is a Flask-based web application that provides weather forecasts for various cities using data retrieved from the Meteomatics API.
Users can add cities to get forecasts, view the latest data, and see weather trends. The app is containerized using Docker, making it easy to run locally.

## Features

- Add cities and fetch their weather forecast, including temperature, wind speed, and precipitation.
- Store city data and weather forecasts using SQLAlchemy with a SQLite database.
- Dynamically display weather data for up to 3 cities in the app.
- Use the Meteomatics API for real-time weather data retrieval.

## Technologies Used

- Flask (Backend)
- SQLAlchemy (Database ORM)
- HTML, CSS, Bootstrap, JavaScript (Frontend)
- Docker (Containerization)
- Meteomatics API (Weather data)

## How to Run Locally Using Docker

To run this application locally, follow the steps below:

### Prerequisites

- Docker installed on your machine. You can download and install it from [Docker's official website](https://www.docker.com/get-started).

### Instructions

1. Pull the Docker image from Docker Hub:

   ```bash
   docker pull aggelos1/weather-app

2. Run the Docker container:

   ```bash
   docker run -d -p 5000:5000 aggelos1/weather-app

  This command will start the web app on port 5000. You can access the application by navigating to `http://localhost:5000` in your web browser.

3. The app is now running locally, and you can begin adding cities to fetch weather forecasts!

## Project Structure

- `main.py`: The main entry point of the application.
- `auth.py`: Handles user authentication and sessions.
- `__init__.py`: Initializes the Flask app and registers routes.
- `static/`: Contains static files such as CSS and JavaScript.
- `templates/`: Holds HTML templates for rendering the frontend.

## API Keys

To use the Meteomatics API, you'll need to set up your own API key.
Create an account at [Meteomatics](https://www.meteomatics.com/en/api/getting-started/) and obtain an API key, then add it
to your environment variables or config file as needed.
