from flask import Flask, request, jsonify, render_template, url_for
import requests
import config

app = Flask(__name__, static_folder='static', template_folder='templates')
colab_url = config.colab_url

# IBM Cloud credentials
API_KEY = config.API_KEY
TOKEN_URL = config.TOKEN_URL
IBM_API_URL = config.IBM_API_URL

# Function to get IAM token using API key
def get_iam_token(api_key):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = f"apikey={api_key}&grant_type=urn:ibm:params:oauth:grant-type:apikey"
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Error obtaining IAM token: {response.status_code} {response.text}")

@app.route('/', methods=['GET'])
def home():
    return  render_template('main.html')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return  render_template('dashboard.html')




# Endpoint to trigger the simulation and call Colab URL
@app.route('/simulate', methods=['POST'])
def simulate():
    if colab_url:
        try:
            # Extract simulation data from request
            simulation_data = request.json

            # Custom header
            headers = {
                'Content-Type': 'application/json',
                'bypass-tunnel-reminder': 'any_value' 
            }

            # Make the request to the Colab URL with the custom header
            response_text = requests.post(colab_url+'/predict', json=simulation_data, headers=headers)
            response_text = response_text.json()
            response_text = response_text['response']
            
            predicted_energy = response_text.split('### Response:')[1].strip()
            print(predicted_energy)
            return jsonify({'predicted_energy': predicted_energy})
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'error': 'Colab URL not set yet'}), 400

# Add your OpenWeatherMap API key
OPENWEATHER_API_KEY = config.OPENWEATHER_API_KEY

# Underserved locations with latitude and longitude
locations = [
    {"name": "Turkana, Kenya", "lat": 3.475, "lon": 35.985},
    {"name": "Dhaka, Bangladesh", "lat": 23.8103, "lon": 90.4125},
    {"name": "Udaipur, India", "lat": 24.5854, "lon": 73.7125},
    {"name": "Sindhupalchok, Nepal", "lat": 27.8571, "lon": 85.7278},
    {"name": "Chad", "lat": 15.4542, "lon": 18.7322},
    {"name": "Afghanistan", "lat": 33.9391, "lon": 67.71},
    {"name": "Haiti", "lat": 18.9712, "lon": -72.2852},
    {"name": "Papua New Guinea", "lat": -6.314993, "lon": 143.95555}
]

@app.route('/get_weather', methods=['GET'])
def get_weather():
    location_name = request.args.get('location')
    location_data = next((loc for loc in locations if loc["name"] == location_name), None)

    if not location_data:
        return jsonify({"error": "Location not found"}), 404

    lat = location_data['lat']
    lon = location_data['lon']

    # Make API request
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data"}), 500

    # Extract useful information from the API response
    weather_info = {
        "location": location_name,
        "temperature": f"{data['main']['temp']} Degree Celsius",
        "feels_like": f"{data['main']['feels_like']} Degree Celsius",
        "pressure": f"{data['main']['pressure']} hPa",
        "humidity": f"{data['main']['humidity']} %",
        "wind_speed": f"{data['wind']['speed']} meters per second",
        "wind_direction": f"{data['wind']['deg']} degree",
        "cloudiness": f"{data['clouds']['all']} %",
        "rain_1h": f"{data['rain']['1h']} millimeters per hour" if "rain" in data else "0 millimeters per hour"
    }

    return jsonify(weather_info)


# Define the route for power distribution recommendation
@app.route('/power_distribution', methods=['POST'])
def power_distribution():
    try:
        # Get the IAM token
        iam_token = get_iam_token(API_KEY)
        
        # Extract weather data from the request body
        weather_data = request.json.get('weather_data')
        print(weather_data)
        # Prepare the input text for the IBM API
        input_text = f"""Analyze weather data to recommend power distribution among traditional and renewable energy sources (solar, wind, hydropower).
Input:
clouds: {weather_data.get('cloudiness')},
feels_like: {weather_data.get('feels_like')},
humidity: {weather_data.get('humidity')},
pressure: {weather_data.get('pressure')},
rain_1h: {weather_data.get('rain_1h')},
temperature: {weather_data.get('temperature')},
wind_direction: {weather_data.get('wind_direction')},
wind_speed: {weather_data.get('wind_speed')}

Output format (only percentages, no explanations):
traditional: %,
solar: %,
wind: %,
hydropower: %

Ensure 'traditional' is dominant and total equals 100%.

Output:"""

        # Define the request body for the IBM API
        body = {
            "input": input_text,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": 200,
                "repetition_penalty": 1
            },
            "model_id": "ibm/granite-13b-instruct-v2",
            "project_id": "5b2c4314-e133-441b-90ee-edbc6f77911b",
            "moderations": {
                "hap": {
                    "input": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    },
                    "output": {
                        "enabled": True,
                        "threshold": 0.5,
                        "mask": {
                            "remove_entity_value": True
                        }
                    }
                }
            }
        }

        # Define the headers for the IBM API request
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {iam_token}"
        }

        # Send a POST request to the IBM API
        response = requests.post(IBM_API_URL, headers=headers, json=body)

        # If the response is not successful, return an error message
        if response.status_code != 200:
            return jsonify({"error": "Non-200 response: " + str(response.text)}), response.status_code

        # Parse and return the API response
        data = response.json()
        print(data)

        try:
            import re
            data = response.json()
            generated_text = data["results"][0]["generated_text"]

            # Use regular expressions to extract the values for traditional, solar, wind, and hydropower
            traditional = re.search(r"traditional:\s*(\d+)", generated_text)
            solar = re.search(r"solar:\s*(\d+)", generated_text)
            wind = re.search(r"wind:\s*(\d+)", generated_text)
            hydropower = re.search(r"hydropower:\s*(\d+)", generated_text)

            # Extract the values or set them to 0 if not found
            traditional_val = int(traditional.group(1)) if traditional else 0
            solar_val = int(solar.group(1)) if solar else 0
            wind_val = int(wind.group(1)) if wind else 0
            hydropower_val = int(hydropower.group(1)) if hydropower else 0

            # Calculate the sum of the found percentages
            total_percentage = traditional_val + solar_val + wind_val + hydropower_val

            # Dynamically adjust the percentages if the total is less than 100%
            if total_percentage == 0:
                # If no values are detected, set traditional to 100%
                result = {
                    "traditional": 100,
                    "solar": 0,
                    "wind": 0,
                    "hydropower": 0
                }
            else:
                # Calculate remaining percentage
                remaining_percentage = 100 - total_percentage
                available_sources = {
                    "traditional": traditional_val,
                    "solar": solar_val,
                    "wind": wind_val,
                    "hydropower": hydropower_val
                }

                # Count the number of sources with 0% to distribute the remaining percentage
                zero_sources = [key for key, value in available_sources.items() if value == 0]

                if zero_sources:
                    # Distribute the remaining percentage equally among sources with 0%
                    per_source_increase = remaining_percentage // len(zero_sources)

                    for source in zero_sources:
                        available_sources[source] = per_source_increase

                # Adjust traditional energy to cover any rounding differences
                total_adjusted_percentage = sum(available_sources.values())
                if total_adjusted_percentage < 100:
                    available_sources["traditional"] += (100 - total_adjusted_percentage)

                # Construct the result JSON
                result = available_sources

            # Return the result as JSON
            return jsonify(result)

        except:
            return jsonify(data)
        return jsonify(result)

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    

@app.route('/simulationLocation', methods=['GET'])
def simulationLocation():
    # Get location from query parameters
    location_name = request.args.get('location')

    # Call the /get_weather endpoint to get weather information for the location
    weather_url = url_for('get_weather', location=location_name, _external=True)
    weather_response = requests.get(weather_url)

    if weather_response.status_code == 200:
        # Extract the weather data from the response
        weather_data = weather_response.json()
        print(weather_data)
        # Send the weather data to the /power_distribution endpoint
        power_distribution_url = url_for('power_distribution', _external=True)
        # print("dff")
        weather_datadic = dict()
        weather_datadic['weather_data'] = weather_data
        power_distribution_response = requests.post(
            power_distribution_url,
            json=weather_datadic  # Pass the weather data as the request body
        )
        print("dff")
        print(power_distribution_response)
        if power_distribution_response.status_code == 200:
            # Return the power distribution result
            return power_distribution_response.json()
        else:
            return {'error': 'Failed to calculate power distribution 3'}, 500
    else:
        return {'error': 'Failed to fetch weather data 4'}, 500


@app.route('/powerdistribution', methods=['POST'])
def powerdistribution():
        import json
        data ={
    "created_at": "2024-10-24T15:17:58.816Z",
    "model_id": "ibm/granite-13b-instruct-v2",
    "results": [
        {
            "generated_text": "{\n          \"traditional\": 50,\n          \"solar\": 30,\n          \"wind\": 10,\n          \"hydropower\": 10\n        }",
            "generated_token_count": 35,
            "input_token_count": 233,
            "seed": 0,
            "stop_reason": "eos_token"
        }
    ]
}
        generated_text = data["results"][0]["generated_text"]

        # Load the generated_text into another dictionary
        power_sources = json.loads(generated_text)

        # Create a new JSON structure with the extracted values
        result = {
            "traditional": power_sources["traditional"],
            "solar": power_sources["solar"],
            "wind": power_sources["wind"],
            "hydropower": power_sources["hydropower"]
        }

        # data = response.json()
        return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
