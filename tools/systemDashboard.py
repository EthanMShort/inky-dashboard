#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import sys
from PIL import Image, ImageDraw, ImageFont

# --- THE FIX: USE SSD1608 DRIVER ---
try:
    from inky.phat import InkyPHAT_SSD1608
    # "red" is the colour, change to "black" or "yellow" if needed
    inky_display = InkyPHAT_SSD1608("red")
except ImportError:
    print("Error: Could not find InkyPHAT_SSD1608.")
    print("Make sure you are running this in the Pimoroni venv!")
    sys.exit(1)

inky_display.set_border(inky_display.WHITE)
# -----------------------------------

# Font Loading (Fail-safe)
try:
    from font_fredoka_one import FredokaOne
    from font_hanken_grotesk import HankenGroteskBold
    font_header = ImageFont.truetype(FredokaOne, 20)
    font_text = ImageFont.truetype(HankenGroteskBold, 12)
    font_small = ImageFont.truetype(HankenGroteskBold, 10)
except ImportError:
    # Fallback if fonts are missing
    print("Warning: Custom fonts not found. Using defaults.")
    font_header = ImageFont.load_default()
    font_text = ImageFont.load_default()
    font_small = ImageFont.load_default()

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No Wifi"

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return float(f.read()) / 1000.0
    except:
        return 0.0

def get_cpu_load():
    try:
        return os.getloadavg()[0]
    except:
        return 0.0

def get_ram_usage():
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        total = int([x for x in lines if 'MemTotal' in x][0].split()[1])
        avail = int([x for x in lines if 'MemAvailable' in x][0].split()[1])
        return ((total - avail) / total) * 100
    except:
        return 0

def get_disk_usage():
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        return ((total - free) / total) * 100
    except:
        return 0

def draw_progress_bar(draw, x, y, width, height, progress, color):
    # Outline
    draw.rectangle((x, y, x + width, y + height), outline=inky_display.BLACK, fill=None)
    # Fill
    fill_w = int((width - 2) * (max(0, min(100, progress)) / 100))
    if fill_w > 0:
        draw.rectangle((x + 1, y + 1, x + 1 + fill_w, y + height - 1), fill=color)

def create_dashboard():
    print("Generating dashboard...")
    
    # 1. Setup Canvas
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    c_black = inky_display.BLACK
    c_white = inky_display.WHITE
    c_red = inky_display.RED

    # Clear screen
    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

    # 2. Get Data
    ip = get_ip_address()
    host = socket.gethostname()
    temp = get_cpu_temp()
    load = get_cpu_load()
    ram = get_ram_usage()
    disk = get_disk_usage()

    # 3. Draw Header
    header_h = 28
    draw.rectangle((0, 0, inky_display.WIDTH, header_h), fill=c_red)
    draw.text((5, 2), host, fill=c_white, font=font_header)
    
    # Align IP to right
    try:
        ip_w = font_small.getlength(ip)
    except AttributeError:
        ip_w = font_small.getsize(ip)[0]
    draw.text((inky_display.WIDTH - ip_w - 5, 8), ip, fill=c_white, font=font_small)

    # 4. Draw Stats
    y = header_h + 5
    row_h = 24  # Increased slightly for readability
    bar_w = 90
    
    # CPU Row
    draw.text((5, y), "Load:", fill=c_black, font=font_text)
    draw.text((45, y), f"{load:.2f}", fill=c_black, font=font_text)
    temp_color = c_red if temp > 60 else c_black
    draw.text((inky_display.WIDTH - 65, y), f"{temp:.1f}C", fill=temp_color, font=font_text)
    y += row_h

    # RAM Row
    draw.text((5, y), "RAM:", fill=c_black, font=font_text)
    draw_progress_bar(draw, 45, y+2, bar_w, 10, ram, c_black)
    draw.text((50 + bar_w, y), f"{int(ram)}%", fill=c_black, font=font_small)
    y += row_h

    # Disk Row
    draw.text((5, y), "Disk:", fill=c_black, font=font_text)
    draw_progress_bar(draw, 45, y+2, bar_w, 10, disk, c_red)
    draw.text((50 + bar_w, y), f"{int(disk)}%", fill=c_black, font=font_small)

    # 5. Render
    print("Pushing to display...")
    inky_display.set_image(img)
    inky_display.show()
    print("Done!")

if __name__ == "__main__":
    create_dashboard()
