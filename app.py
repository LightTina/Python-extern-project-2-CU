import json

import requests
from flask import Flask, render_template, request
import random
import socket

app = Flask(__name__)
API_KEY = '4ih34htYfommSLwAlbcdfa3H24LYYJo3'


def check_bad_weather(conditions):
    if 0 <= conditions['temperature'] <= 35 and conditions['wind_speed'] <= 50 and conditions['probability_of_precipitation'] < 50:
        good_result = [
            'Неплохая погодка',
            'Можно выдвигаться',
            'На улице круто!',
            'Прогуляться точно стоит'
        ]
        return random.choice(good_result)
    else:
        bad_result = [
            'Плохенько с погодкой',
            'Выдвигаться нельзя, там ужасно',
            'На улице вообще не круто!',
            'Прогуляться явно не стоит'
        ]
        return random.choice(bad_result)


def check_internet_connection():
    try:
        socket.create_connection(("8.8.8.8", 53))
        return True
    except OSError:
        return False


def get_location_key(city):
    location_url = f'http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city}'
    try:
        location_response = requests.get(location_url)
        location_response.raise_for_status()
        location_data = location_response.json()
        return location_data[0]['Key'] if location_data else None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения данных для города '{city}': {e}")
        return None


def get_weather_data(location_key):
    weather_url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={API_KEY}&details=true'
    try:
        weather_response = requests.get(weather_url)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        return weather_data[0] if weather_data else None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения данных о погоде: {e}")
        return None


def get_forecast_data(location_key):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}?apikey={API_KEY}&details=true&metric=true"
    try:
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()
        data = forecast_response.json()
        return data['DailyForecasts'][0] if 'DailyForecasts' in data else None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка получения данных о прогнозе: {e}")
        return None


def get_conditions(city):
    location_key = get_location_key(city)
    if not location_key:
        return None
    weather_data = get_weather_data(location_key)
    forecast_data = get_forecast_data(location_key)
    if not weather_data or not forecast_data:
        return None
    probability_of_precipitation = forecast_data['Day'].get('PrecipitationProbability')

    return {
        'temperature': weather_data['Temperature']['Metric']['Value'],
        'wind_speed': weather_data['Wind']['Speed']['Metric']['Value'],
        'probability_of_precipitation': probability_of_precipitation,
        'humidity': weather_data['RelativeHumidity'],
        'weather_status': check_bad_weather({
            'temperature': weather_data['Temperature']['Metric']['Value'],
            'wind_speed': weather_data['Wind']['Speed']['Metric']['Value'],
            'probability_of_precipitation': probability_of_precipitation
        })
    }


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error_message = None
    if request.method == 'POST':
        city1 = request.form.get('city1')
        city2 = request.form.get('city2')
        if not city1 or not city2:
            error_message = "Пожалуйста, введите названия обоих городов."
        else:
            if not check_internet_connection():
                error_message = "Ууууупс, нет подключения к интернету(динозаврика не будет):("
            else:
                city_1_data = get_conditions(city1)
                city_2_data = get_conditions(city2)
                with open('data_city_1.json','w') as file: json.dump(city_1_data,file)
                with open('data_city_2.json','w') as file: json.dump(city_2_data,file)
                if city_1_data is None:
                    error_message = f"Не удалось получить данные для города: {city1}"
                elif city_2_data is None:
                    error_message = f"Не удалось получить данные для города: {city2}"
                else:
                    result = {
                        'city1': {'name': city1, **city_1_data},
                        'city2': {'name': city2, **city_2_data}
                    }
    return render_template('index.html', result=result, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)
