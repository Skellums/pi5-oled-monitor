import argparse
import time
import os
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

def main():
    parser = argparse.ArgumentParser(description="Print dynamic text to an SSD1306 OLED.")
    parser.add_argument("--line1", "-l1", type=str, default="", help="Text for line 1")
    parser.add_argument("--line2", "-l2", type=str, default="", help="Text for line 2")
    parser.add_argument("--line3", "-l3", type=str, default="", help="Text for line 3")
    parser.add_argument("--line4", "-l4", type=str, default="", help="Text for line 4")
    parser.add_argument("--size", "-s", type=float, default=10, help="Font size")
    parser.add_argument("--time", "-t", type=int, default=3, help="Number of seconds to display message")
    args = parser.parse_args()

    # Safety check
    if not any([args.line1, args.line2, args.line3, args.line4]):
        print("Warning: No text provided! Display will be cleared.")

    serial = i2c(port=1, address=0x3C)
    
    # THE FIX IS HERE: persist=True tells the library NOT to clear the screen on exit
    device = ssd1306(serial, width=128, height=32, persist=True)
    
    image = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(image)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, args.size)

    lines = [args.line1, args.line2, args.line3, args.line4]
    timeout = args.time

    current_y = 0
    for line in lines:
        if line:  
            draw.text((0, current_y), line, font=font, fill=255)
            current_y += args.size 

    device.display(image)
    print(f"Text pushed to display. Display will persist for {timeout} seconds.")
    time.sleep(timeout)

if __name__ == "__main__":
    main()
