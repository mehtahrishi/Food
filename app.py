from flask import Flask, request, jsonify, render_template
import aiml
import requests

# Initialize Flask app
app = Flask(__name__)

# Initialize AIML kernel
kernel = aiml.Kernel()
kernel.learn("std-startup.xml")
kernel.respond("LOAD AIML B")

# Replace with your actual API keys
SPOONACULAR_API_KEY = 'your_spoonacular_api_key'
WEATHER_API_KEY = 'your_weather_api_key'

BASE_URL_SPOONACULAR = 'https://api.spoonacular.com/recipes'
BASE_URL_WEATHER = 'https://api.openweathermap.org/data/2.5/weather'

@app.route("/")
def index():
    return render_template("index.html")

def get_weather(city):
    try:
        response = requests.get(BASE_URL_WEATHER, params={
            'q': city,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        })
        data = response.json()
        if data.get('cod') == 200:
            temp = data['main']['temp']
            weather = data['weather'][0]['description']
            return temp, weather
        else:
            return None, "Sorry, I couldn't fetch the weather information."
    except Exception as e:
        return None, f"An error occurred: {e}"

def get_recipe(query):
    try:
        response = requests.get(f"{BASE_URL_SPOONACULAR}/search", params={
            'query': query,
            'apiKey': SPOONACULAR_API_KEY,
            'number': 1
        })
        data = response.json()
        
        # Check if the 'results' key exists and contains items
        if 'results' in data and data['results']:
            recipe = data['results'][0]
            recipe_id = recipe['id']
            recipe_details = get_recipe_details(recipe_id)
            return (f"Here's a recipe for {query}: {recipe['title']}. More details: {recipe['sourceUrl']}\n\n"
                    f"Ingredients:\n{recipe_details}")
        else:
            return "Sorry, I couldn't find any recipes for that query."
    except Exception as e:
        return f"An error occurred: {e}"

def get_recipe_details(recipe_id):
    try:
        response = requests.get(f"{BASE_URL_SPOONACULAR}/{recipe_id}/information", params={
            'apiKey': SPOONACULAR_API_KEY
        })
        data = response.json()
        ingredients = data.get('extendedIngredients', [])
        ingredient_list = [f"{ingredient['amount']} {ingredient['unit']} {ingredient['name']}" for ingredient in ingredients]
        ingredients_text = "\n".join(ingredient_list)
        return ingredients_text
    except Exception as e:
        return f"An error occurred: {e}"

def suggest_food_based_on_weather(temp):
    if temp < 15:
        return "It's quite cold! How about some hot soup or spicy food to warm you up?"
    elif 15 <= temp < 25:
        return "The weather is mild. A nice pasta or sandwich might be just right."
    elif 25 <= temp < 35:
        return "It's getting warm! Maybe a fresh salad or cold beverage would be refreshing."
    else:
        return "It's really hot outside! A cold dessert or something light would be perfect."

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip().lower()
    
    if user_message == "what should i eat":
        return jsonify({"response": "Hmm! Lemme see... Please provide your location."})
    
    # Handle location-based food suggestion
    elif user_message.startswith("location:"):
        city = user_message.replace("location:", "").strip()
        temp, weather = get_weather(city)
        if temp is not None:
            food_suggestion = suggest_food_based_on_weather(temp)
            response = f"In {city}, it's {temp}°C ({weather}). You might enjoy: {food_suggestion}"
        else:
            response = weather
        return jsonify({"response": response})
    
    # Handle recipe-related queries
    elif 'recipe' in user_message or 'how to cook' in user_message:
        query = user_message.replace('recipe', '').replace('how to cook', '').strip()
        recipe_info = get_recipe(query)
        return jsonify({"response": recipe_info})
    
    # Default to AIML responses for other queries
    else:
        response = kernel.respond(user_message)
        return jsonify({"response": response})

    # If the script is run directly (not imported), start the Flask app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)