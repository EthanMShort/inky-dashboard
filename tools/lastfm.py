#!/usr/bin/env python3
import sys
import io
import os
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- INKY SETUP ---
try:
    from inky.phat import InkyPHAT_SSD1608
    inky_display = InkyPHAT_SSD1608("red")
except ImportError:
    print("Error: InkyPHAT_SSD1608 not found.")
    sys.exit(1)

inky_display.set_border(inky_display.WHITE)

# --- CONFIG ---
LASTFM_API_KEY = "7e38dcd7a4d3453493c1c9d8b6499acd"
LASTFM_USER = "emusic05"
API_URL = "http://ws.audioscrobbler.com/2.0/"

# --- FONTS ---
try:
    from font_fredoka_one import FredokaOne
    from font_hanken_grotesk import HankenGroteskBold
    # Larger fonts for the new layout
    font_title = ImageFont.truetype(FredokaOne, 22)   # Big & Bold
    font_artist = ImageFont.truetype(HankenGroteskBold, 16) # Clean & Readable
    font_icon = ImageFont.truetype(FredokaOne, 40)    # For the music note icon
except ImportError:
    font_title = ImageFont.load_default()
    font_artist = ImageFont.load_default()
    font_icon = ImageFont.load_default()

def get_now_playing():
    params = {
        'method': 'user.getrecenttracks',
        'user': LASTFM_USER,
        'api_key': LASTFM_API_KEY,
        'format': 'json',
        'limit': 1
    }
    try:
        r = requests.get(API_URL, params=params, timeout=5)
        data = r.json()
        if 'recenttracks' not in data: return None

        track = data['recenttracks']['track'][0]
        
        is_playing = False
        if '@attr' in track and track['@attr'].get('nowplaying') == 'true':
            is_playing = True
            
        art_url = track['image'][3]['#text'] if len(track['image']) > 3 else None

        return {
            "title": track['name'],
            "artist": track['artist']['#text'],
            "art_url": art_url,
            "is_playing": is_playing
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_art(url, size=(122, 122)):
    """Downloads art and converts to HIGH CONTRAST (No dots/dithering)"""
    if not url: return None
    try:
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))
        
        # 1. Resize nicely (LANCZOS keeps it smooth before we cut it)
        img = ImageOps.fit(img, size, method=Image.LANCZOS)
        
        # 2. Convert to Grayscale
        img = img.convert("L")
        
        # 3. THRESHOLD: Force every pixel to be either fully Black or fully White
        # This removes the "dots". Adjust '128' up or down to change darkness sensitivity.
        img = img.point(lambda p: 0 if p < 128 else 255, '1')
        
        return img
    except:
        return None

def draw_screen(track):
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)
    
    c_white = inky_display.WHITE
    c_black = inky_display.BLACK
    c_red = inky_display.RED

    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

    # --- IDLE SCREEN ---
    if not track or not track['is_playing']:
        draw.text((20, 20), "Not Playing", fill=c_red, font=font_title)
        draw.text((20, 50), "Put on some tunes!", fill=c_black, font=font_artist)
        inky_display.set_image(img)
        inky_display.show()
        return

    # --- 1. ALBUM ART (Full Height Split) ---
    # We make it 122x122 to fill the left side completely
    art_size = 122
    art_img = process_art(track['art_url'], size=(art_size, art_size))
    
    if art_img:
        # Create mask for transparency
        mask = art_img.convert("L")
        mask = ImageOps.invert(mask)
        # Paste Black ink
        img.paste(c_black, (0, 0), mask)
        # Draw a thin divider line
        draw.line((art_size, 0, art_size, 122), fill=c_black, width=2)
    else:
        # Fallback Icon if no art
        draw.rectangle((0, 0, art_size, 122), fill=c_black)
        draw.text((40, 35), "♫", fill=c_white, font=font_icon)

    # --- 2. TEXT (Right Side) ---
    # We have about 128px of width remaining (250 - 122)
    text_x = art_size + 8
    text_w = inky_display.WIDTH - text_x - 2
    
    # WRAPPING LOGIC
    # Wrap title to max 2 lines. approx 11 chars per line at this font size
    wrapper = textwrap.TextWrapper(width=11) 
    title_lines = wrapper.wrap(track['title'])[:2] # Limit to 2 lines
    
    cursor_y = 15 # Start Y position
    
    # Draw Title (Red)
    for line in title_lines:
        draw.text((text_x, cursor_y), line, fill=c_red, font=font_title)
        cursor_y += 24 # Move down for next line
        
    # Draw Artist (Black) - Add a little padding
    cursor_y += 5 
    artist = track['artist']
    # Truncate artist if it's super long
    if len(artist) > 15: 
        artist = artist[:14] + "..."
        
    draw.text((text_x, cursor_y), artist, fill=c_black, font=font_artist)

    inky_display.set_image(img)
    inky_display.show()

if __name__ == "__main__":
    print("Checking Last.fm...")
    track = get_now_playing()
    if track:
        print(f"Playing: {track['title']}")
    else:
        print("Nothing playing.")
    draw_screen(track)
