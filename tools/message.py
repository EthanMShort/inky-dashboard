import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
from inky.phat import InkyPHAT_SSD1608

# Setup Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--text", required=True, help="Text to display")
args = parser.parse_args()

# Setup Display
inky_display = InkyPHAT_SSD1608("red")
inky_display.set_border(inky_display.WHITE)

# Canvas
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Colors
c_white = inky_display.WHITE
c_black = inky_display.BLACK
c_red = inky_display.RED

draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

# Font
try:
    # Try using a bold font for impact
    from font_fredoka_one import FredokaOne
    font = ImageFont.truetype(FredokaOne, 24)
except ImportError:
    font = ImageFont.load_default()

# Wrap text logic (simple)
text = args.text
# Draw centered
w, h = 0, 0
try:
    w = font.getlength(text)
except:
    pass # Older PIL ignores this

x = (inky_display.WIDTH - w) // 2
y = (inky_display.HEIGHT - 30) // 2

# Draw text
draw.text((10, y), text, fill=c_black, font=font)

inky_display.set_image(img)
inky_display.show()import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
from inky.phat import InkyPHAT_SSD1608

# Setup Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--text", required=True, help="Text to display")
args = parser.parse_args()

# Setup Display
inky_display = InkyPHAT_SSD1608("red")
inky_display.set_border(inky_display.WHITE)

# Canvas
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)

# Colors
c_white = inky_display.WHITE
c_black = inky_display.BLACK
c_red = inky_display.RED

draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), fill=c_white)

# Font
try:
    # Try using a bold font for impact
    from font_fredoka_one import FredokaOne
    font = ImageFont.truetype(FredokaOne, 24)
except ImportError:
    font = ImageFont.load_default()

# Wrap text logic (simple)
text = args.text
# Draw centered
w, h = 0, 0
try:
    w = font.getlength(text)
except:
    pass # Older PIL ignores this

x = (inky_display.WIDTH - w) // 2
y = (inky_display.HEIGHT - 30) // 2

# Draw text
draw.text((10, y), text, fill=c_black, font=font)

inky_display.set_image(img)
inky_display.show()
