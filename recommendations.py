def get_temp_suggestion(difference: float) -> str:
    if difference < -5:
        return "Much cooler inside - keep windows closed"
    elif difference > 5:
        return "Warmer inside - consider ventilation"
    else:
        return "Temperature difference is normal"


def get_humidity_suggestion(humidity: int, location: str) -> str:
    location_name = "Indoor" if location == "indoor" else "Outdoor"
    if humidity < 40:
        if location_name == "Indoor":
            return f"Low humidity! Add water source"
        return f"{location_name} air is dry"
    elif humidity > 70:
        if location_name == "Indoor":
            return f"High humidity! Use dehumidifier"
        return f"{location_name} humidity is high"
    else:
        return f"{location_name} humidity is comfortable"


def get_rain_suggestion(main: str, temperature: int) -> str:
    if main == 'Rain':
        return f"Rain alert - close windows"
    elif main == 'Clear' and temperature > 28:
        return f"Strong sunshine - close curtains"
    elif main == 'Clouds':
        return "Collect the dried cloths"
    elif main == 'Mist':
        return "Wear reflective clothing"
    else:
        return "Conditions normal"

def get_activity_suggestion(weather_main: str, description: str, temperature: float, humidity: int) -> str:
    """Generate activity recommendations based on detailed weather conditions"""
    suggestions = {
        "Clouds": {
            "few clouds": "🌤️ Perfect for: Outdoor photography, rooftop dining, open-air markets",
            "scattered clouds": "⛅ Great for: Golf, tennis, cycling - clouds provide sun protection",
            "broken clouds": "☁️ Good for: Long walks, gardening, outdoor workouts",
            "overcast clouds": "🌥️ Ideal for: Marathon training, fishing, outdoor yoga"
        },
        "Mist": {
            "mist": "🌫️ Recommended: Spa visits, museum tours, indoor rock climbing (visibility low)",
            "fog": "⚠️ Avoid: Driving or cycling. Try: Board games, baking, indoor swimming"
        },
        "Rain": {
            "light rain": "🌧️ Suitable for: Cafe hopping, library visits, indoor climbing",
            "moderate rain": "☔ Try: Movie marathons, cooking classes, mall walking",
            "heavy intensity rain": "⛈️ Stay home with: Books, streaming shows, home workouts",
            "freezing rain": "🧊 Dangerous conditions! Indoor activities only: Puzzles, crafts"
        },
        "Clear": {
            "default": "☀️ Perfect for: Beach trips, hiking, outdoor sports" if temperature > 18 else "❄️ Best for: Skiing, ice skating, winter festivals"
        },
    }

    activity = (suggestions.get(weather_main, {}).get(description.lower())
                or suggestions.get(weather_main, {}).get("default")
                or f"Typical {weather_main.lower()} activities")

    if temperature > 35:
        activity += " 🥵 Avoid midday sun!"
    elif temperature < 15:
        activity += " 🧤 Dress warmly!"

    if humidity > 70:
        activity += " 💦 High humidity - stay hydrated"

    return activity


def get_dressing_suggestion_with_visuals(temperature: float,weather_main: str, description: str):
    """Enhanced version with visual elements"""
    suggestions = {
        "Clear": {
            "default": ("Wear light clothing and sunscreen", "☀️", "http://localhost:8000/static/images/sunny-outfit.png")
        },
        "Rain": {
            "light rain": ("Carry an umbrella and wear waterproof shoes", "🌧️", "http://localhost:8000/static/images/rainy-outfit.png"),
            "heavy rain": ("Full rain gear recommended - jacket, boots, umbrella", "⛈️",
                           "http://localhost:8000/static/images/heavy-rain-outfit.png"),
            "moderate rain": ("Full rain gear recommended - jacket, boots, umbrella", "🌧☔",
                              "http://localhost:8000/static/images/heavy-rain-outfit.png")
        },
        "Clouds": {
            "few clouds": ("Wear light clothing with sunglasses.", "🌤", "http://localhost:8000/static/images/few-cloud.png"),
            "broken clouds": ("Light layers recommended (t-shirt + light jacket)", "⛅",
                              "http://localhost:8000/static/images/few-cloud.png"),
            "overcast clouds": ("Wear comfortable clothing (jeans + long-sleeve shirt)", "☁️",
                                "http://localhost:8000/static/images/overcast.png"),
            "scattered clouds": ("Similar to broken clouds but prepare for sun breaks", "⛅",
                                 "http://localhost:8000/static/images/scattered.png"),
        },
        "Mist": {
            "mist": ("Misty conditions: Reduced visibility. Wear reflective clothing if walking near roads.", "🌫️",
                     "http://localhost:8000/static/images/mist.png")
        },
    }

    # Get specific recommendation or default
    weather_key = weather_main
    desc_key = description.lower()

    return (
        suggestions.get(weather_key, {}).get(desc_key, suggestions["Clear"]["default"])
        if weather_key in suggestions
        else suggestions["Clear"]["default"]
    )