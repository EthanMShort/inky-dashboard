#!/usr/bin/env python3
import sys
import os
import textwrap
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- INKY SETUP ---
try:
    from inky.phat import InkyPHAT_SSD1608
    # "red" is the colour, change to "black" or "yellow" if needed
    inky_display = InkyPHAT_SSD1608("red")
except ImportError:
    print("Error: InkyPHAT_SSD1608 not found.")
    sys.exit(1)

inky_display.set_border(inky_display.WHITE)

# --- CONFIG ---
LAT = "39.7817" # Springfield, IL
LON = "-89.6501"
USER_AGENT = "(my-weather-app, contact@example.com)"

# System resources folder
ICON_DIR = "/opt/inky/examples/phat/resources"

# --- FONTS ---
try:
    from font_fredoka_one import FredokaOne
    from font_hanken_grotesk import HankenGroteskBold
    font_temp = ImageFont.truetype(FredokaOne, 20)
    font_header = ImageFont.truetype(HankenGroteskBold, 12)
    font_desc = ImageFont.truetype(HankenGroteskBold, 10)
    font_small = ImageFont.truetype(HankenGroteskBold, 9)
except ImportError:
    font_temp = ImageFont.load_default()
    font_header = ImageFont.load_default()
    font_desc = ImageFont.load_default()
    font_small = ImageFont.load_default()

def get_forecast():
    headers = {"User-Agent": USER_AGENT}
    try:
        point_url = f"https://api.weather.gov/points/{LAT},{LON}"
        r = requests.get(point_url, headers=headers)
        r.raise_for_status()
        grid_data = r.json()
        forecast_url = grid_data['properties']['forecast']

        r = requests.get(forecast_url, headers=headers)
        r.raise_for_status()
        data = r.json()
        return data['properties']['periods']
    except Exception as e:
        print(f"API Error: {e}")
        return None

def parse_forecast(periods):
    daily_data = []
    for i, p in enumerate(periods):
        if not p['isDaytime']:
            continue 
            
        if len(daily_data) >= 3:
            break

        dt = datetime.fromisoformat(p['startTime'])
        date_str = dt.strftime("%-m/%-d") 
        day_name = dt.strftime("%a")
        
        high = p['temperature']
        desc = p['shortForecast']
        
        short_desc = desc.lower()
        if "rain" in short_desc or "showers" in short_desc:
            icon_file = "icon-rain.png"
        elif "snow" in short_desc or "wintry" in short_desc:
            icon_file = "icon-snow.png"
        elif "storm" in short_desc or "thunder" in short_desc:
            icon_file = "icon-storm.png"
        elif "cloud" in short_desc or "overcast" in short_desc or "fog" in short_desc:
            icon_file = "icon-cloud.png"
        else:
            icon_file = "icon-sun.png"

        low = "--"
        if i + 1 < len(periods):
            next_p = periods[i+1]
            if not next_p['isDaytime']:
                low = next_p['temperature']

        daily_data.append({
            "header": f"{day_name} {date_str}",
            "high": high,
            "low": low,
            "desc": desc,
            "icon": icon_file
        })
        
    return daily_data

def process_icon(icon_path, size=(32, 32)):
    """
    Loads an icon, forces it to be RED, and cleans up fuzzy edges (thresholding).
    Returns (image, mask) ready for pasting.
    """
    try:
        # Load and convert to RGBA
        icon = Image.open(icon_path).convert("RGBA")
        
        # 1. Resize using NEAREST neighbor to keep lines sharp (avoid blur)
        icon = icon.resize(size, resample=Image.NEAREST)
        
        # 2. Extract the alpha mask
        # We create a new white image to use as the background for the icon content
        # But for Inky, we want the icon ITSELF to be the Ink color (Red/Black)
        
        # Split channels
        _, _, _, alpha = icon.split()
        
        # 3. THRESHOLD the mask
        # Any pixel that is partially transparent becomes fully opaque or fully transparent
        # This removes the "splat" look caused by fuzzy anti-aliasing
        mask = alpha.point(lambda p: 255 if p > 128 else 0)
        
        # 4. Create a solid RED block the size of the icon
        # We will use the mask to cut this block into the shape of the sun
        solid_color_block = Image.new("P", size, inky_display.RED)
        
        return solid_color_block, mask
        
    except Exception as e:
        print(f"Error processing icon {icon_path}: {e}")
        return None, None

def draw_weather(days):
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    
    c_white = inky_display.WHITE
    c_black = inky_display.BLACK
    c_red = inky_display.RED

    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

    col_w = inky_display.WIDTH // 3

    for i, data in enumerate(days):
        x = i * col_w
        center_x = x + (col_w // 2)

        # --- 1. HEADER ---
        draw.rectangle((x + 2, 2, x + col_w - 4, 18), fill=c_black)
        try:
            w = font_header.getlength(data['header'])
        except:
            w = font_header.getsize(data['header'])[0]
        draw.text((x + (col_w - w) // 2, 3), data['header'], fill=c_white, font=font_header)

        # --- 2. ICON (Cleaned) ---
        icon_path = os.path.join(ICON_DIR, data['icon'])
        if os.path.exists(icon_path):
            icon_img, mask = process_icon(icon_path)
            if icon_img:
                icon_x = center_x - 16
                icon_y = 20
                img.paste(icon_img, (icon_x, icon_y), mask)
            else:
                draw.text((center_x-5, 25), "?", fill=c_red, font=font_temp)
        else:
            draw.text((center_x-5, 25), "!", fill=c_red, font=font_temp)

        # --- 3. DESCRIPTION ---
        wrapper = textwrap.TextWrapper(width=10)
        desc_lines = wrapper.wrap(data['desc'])
        desc_lines = desc_lines[:2] 
        
        text_y = 55
        for line in desc_lines:
            try:
                lw = font_desc.getlength(line)
            except:
                lw = font_desc.getsize(line)[0]
            draw.text((x + (col_w - lw) // 2, text_y), line, fill=c_black, font=font_desc)
            text_y += 11

        # --- 4. TEMPS ---
        high_str = f"{data['high']}°"
        try:
            hw = font_temp.getlength(high_str)
        except:
            hw = font_temp.getsize(high_str)[0]
        draw.text((center_x - hw // 2, 78), high_str, fill=c_red, font=font_temp)

        low_str = f"L: {data['low']}°"
        try:
            low_w = font_small.getlength(low_str)
        except:
            low_w = font_small.getsize(low_str)[0]
        draw.text((center_x - low_w // 2, 98), low_str, fill=c_black, font=font_small)

        if i < 2:
             draw.line((x + col_w, 10, x + col_w, inky_display.HEIGHT - 10), fill=c_black, width=1)

    inky_display.set_image(img)
    inky_display.show()

if __name__ == "__main__":
    print("Fetching weather...")
    forecast_periods = get_forecast()
    if forecast_periods:
        clean_data = parse_forecast(forecast_periods)
        draw_weather(clean_data)
        print("Done.")
    else:
        print("Failed.")