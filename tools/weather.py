#!/usr/bin/env python3
import sys
import requests
from PIL import Image, ImageDraw, ImageFont

# --- INKY SETUP ---
try:
    from inky.phat import InkyPHAT_SSD1608
    inky_display = InkyPHAT_SSD1608("red")
except ImportError:
    print("Error: InkyPHAT_SSD1608 not found. Are you in the venv?")
    sys.exit(1)

inky_display.set_border(inky_display.WHITE)

# --- CONFIG ---
# Springfield, IL Coordinates
LAT = "39.7817"
LON = "-89.6501"
USER_AGENT = "(my-weather-app, contact@example.com)" # NWS requires a User-Agent

# --- FONTS ---
try:
    from font_hanken_grotesk import HankenGroteskBold
    font_header = ImageFont.truetype(HankenGroteskBold, 14)
    font_text = ImageFont.truetype(HankenGroteskBold, 12)
    font_small = ImageFont.truetype(HankenGroteskBold, 10)
except ImportError:
    font_header = ImageFont.load_default()
    font_text = ImageFont.load_default()
    font_small = ImageFont.load_default()

def get_forecast():
    headers = {"User-Agent": USER_AGENT}
    try:
        # 1. Get Grid Point
        point_url = f"https://api.weather.gov/points/{LAT},{LON}"
        r = requests.get(point_url, headers=headers)
        r.raise_for_status()
        grid_data = r.json()
        forecast_url = grid_data['properties']['forecast']

        # 2. Get Forecast
        r = requests.get(forecast_url, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data['properties']['periods']
    except Exception as e:
        print(f"API Error: {e}")
        return None

def draw_weather(periods):
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    
    # Colors
    c_white = inky_display.WHITE
    c_black = inky_display.BLACK
    c_red = inky_display.RED

    # Clear background
    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

    # Filter for Daytime periods (only show highs/days)
    day_periods = [p for p in periods if p['isDaytime']]
    # Take top 3
    days_to_show = day_periods[:3]

    # Layout Calculations
    col_width = inky_display.WIDTH // 3
    
    # Draw Data
    for i, p in enumerate(days_to_show):
        x_offset = i * col_width
        
        # Period Name (e.g., "This Afternoon", "Friday")
        # Shorten names for space
        name = p['name'].replace("This Afternoon", "Today").replace("Afternoon", "P.M.")
        name = name[:9] # Truncate long names
        
        temp = f"{p['temperature']}F"
        short_forecast = p['shortForecast'].split("then")[0].strip() # Take first part of complex forecasts
        
        # Header Box for Day
        draw.rectangle((x_offset, 0, x_offset + col_width - 2, 20), fill=c_black)
        draw.text((x_offset + 5, 4), name, fill=c_white, font=font_small)

        # Temp
        draw.text((x_offset + 5, 30), temp, fill=c_red, font=font_header)

        # Wrap Forecast Text (Simple logic)
        words = short_forecast.split()
        line1 = " ".join(words[:2])
        line2 = " ".join(words[2:4])
        
        draw.text((x_offset + 5, 55), line1, fill=c_black, font=font_small)
        draw.text((x_offset + 5, 70), line2, fill=c_black, font=font_small)

        # Divider Line (except last)
        if i < 2:
             draw.line((x_offset + col_width - 1, 0, x_offset + col_width - 1, inky_display.HEIGHT), fill=c_black)

    inky_display.set_image(img)
    inky_display.show()

if __name__ == "__main__":
    print("Fetching weather...")
    forecast = get_forecast()
    if forecast:
        print("Drawing...")
        draw_weather(forecast)
        print("Done.")
    else:
        print("Failed to get forecast.")