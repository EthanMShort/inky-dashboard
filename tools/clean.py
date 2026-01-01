import sys
from inky.phat import InkyPHAT_SSD1608
from PIL import Image

try:
    inky_display = InkyPHAT_SSD1608("red")
    inky_display.set_border(inky_display.WHITE)
    
    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT), color=inky_display.WHITE)
    
    inky_display.set_image(img)
    inky_display.show()
    print("Cleaned.")
except Exception as e:
    print(f"Error: {e}")
