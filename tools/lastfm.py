#!/usr/bin/env python3
import sys
import io
import os
import time
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
LASTFM_API_KEY = "YOUR_API_KEY_HERE"
LASTFM_USER = "YOUR_USERNAME_HERE"
API_URL = "http://ws.audioscrobbler.com/2.0/"

# SETTINGS
SKIP_BUFFER_SECONDS = 20  
POLL_INTERVAL = 10        

# --- FONTS ---
try:
    from font_fredoka_one import FredokaOne
    from font_hanken_grotesk import HankenGroteskBold
    # UPDATED: Smaller sizes to fit more text
    font_title = ImageFont.truetype(FredokaOne, 18)       # Was 22
    font_artist = ImageFont.truetype(HankenGroteskBold, 14) # Was 16
    font_icon = ImageFont.truetype(FredokaOne, 40)
except ImportError:
    font_title = ImageFont.load_default()
    font_artist = ImageFont.load_default()
    font_icon = ImageFont.load_default()

def get_now_playing():
    """Fetches current track from Last.fm"""
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
    """Downloads art and converts to Dithered B&W (The 'In-Between' look)"""
    if not url: return None
    try:
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))
        
        # 1. Resize nicely first (LANCZOS keeps details sharp)
        img = ImageOps.fit(img, size, method=Image.LANCZOS)
        
        # 2. Convert to Dithered 1-bit (Standard "Old Version" look)
        # This uses Floyd-Steinberg dithering to simulate grays with dots
        img = img.convert("1")
        
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

    if not track or not track['is_playing']:
        # Idle Screen
        draw.text((20, 20), "Not Playing", fill=c_red, font=font_title)
        draw.text((20, 50), "Waiting for music...", fill=c_black, font=font_artist)
        inky_display.set_image(img)
        inky_display.show()
        return

    # 1. Art (Left Side - Full Height)
    art_size = 122
    art_img = process_art(track['art_url'], size=(art_size, art_size))
    
    if art_img:
        # For dithered images, we can't simple mask. 
        # We need to paste the dithered pixels directly.
        # Since the image is mode "1", we can convert to "P" or use it as a mask for Black ink.
        
        # Create mask: Black pixels in art -> Opaque in mask
        mask = art_img.convert("L")
        mask = ImageOps.invert(mask)
        img.paste(c_black, (0, 0), mask)
        
        draw.line((art_size, 0, art_size, 122), fill=c_black, width=2)
    else:
        draw.rectangle((0, 0, art_size, 122), fill=c_black)
        draw.text((40, 35), "♫", fill=c_white, font=font_icon)

    # 2. Text (Right Side)
    text_x = art_size + 6
    
    # UPDATED WRAPPING LOGIC
    # Smaller font = more chars per line (~14 instead of 11)
    wrapper = textwrap.TextWrapper(width=14) 
    
    # Allow up to 3 lines now
    title_lines = wrapper.wrap(track['title'])[:3]
    
    # Start slightly higher to accommodate potentially 3 lines
    cursor_y = 8
    
    for line in title_lines:
        draw.text((text_x, cursor_y), line, fill=c_red, font=font_title)
        cursor_y += 20 # Line spacing for title
        
    # Add a little gap before Artist
    cursor_y += 4
    
    artist = track['artist']
    # Truncate artist if it's still too long for one line
    if len(artist) > 16: artist = artist[:15] + "..."
    
    draw.text((text_x, cursor_y), artist, fill=c_black, font=font_artist)

    inky_display.set_image(img)
    inky_display.show()

def is_active_dashboard():
    """Checks if this script should still be running"""
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state.txt")
    try:
        if not os.path.exists(state_path): return False
        with open(state_path, "r") as f:
            # Check if "Music" (or "music") is in the file
            return f.read().strip().lower() == "music"
    except:
        return False

# --- MAIN LOOP ---
if __name__ == "__main__":
    print("Starting Music Monitor...")
    last_displayed_title = None
    
    while True:
        # 1. Check if we should exit (User clicked Weather/Stocks)
        if not is_active_dashboard():
            print("Music is no longer active. Exiting.")
            sys.exit(0)

        # 2. Get Current Track
        current_track = get_now_playing()
        
        # 3. Logic: Did the song change?
        current_title = current_track['title'] if current_track and current_track['is_playing'] else "IDLE"
        
        if current_title != last_displayed_title:
            print(f"Detected change: {current_title}. Waiting {SKIP_BUFFER_SECONDS}s buffer...")
            
            # WAIT BUFFER (Skip Detection)
            slept = 0
            while slept < SKIP_BUFFER_SECONDS:
                time.sleep(1)
                slept += 1
                if not is_active_dashboard(): 
                    sys.exit(0)

            # Re-Check after buffer
            check_again = get_now_playing()
            check_title = check_again['title'] if check_again and check_again['is_playing'] else "IDLE"

            if check_title == current_title:
                print(f"Song stable. Updating display to: {current_title}")
                draw_screen(check_again)
                last_displayed_title = current_title
            else:
                print("Song changed during buffer (User skipped). Ignoring.")
        
        # 4. Sleep before next poll
        time.sleep(POLL_INTERVAL)
