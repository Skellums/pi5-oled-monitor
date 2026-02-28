import time
import subprocess
import os
import signal
import sys
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

device = None
last_rx = 0
last_tx = 0
last_net_time = 0

def graceful_exit(signum, frame):
    print("\nReceived termination signal. Clearing screen...")
    if device:
        device.clear()
    sys.exit(0)

def get_system_stat(command):
    try:
        return subprocess.check_output(command, shell=True).decode("utf-8").strip()
    except Exception:
        return "Err"

def get_net_bytes():
    rx, tx = 0, 0
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:] 
            for line in lines:
                parts = line.split()
                iface = parts[0].strip(":")
                if iface != "lo": 
                    rx += int(parts[1])
                    tx += int(parts[9])
    except Exception:
        pass
    return rx, tx

def format_speed(speed_kbps):
    if speed_kbps >= 1000.0:
        return f"{speed_kbps / 1024.0:.1f}MB/s"
    return f"{speed_kbps:.1f}KB/s"

def get_net_speed():
    global last_rx, last_tx, last_net_time
    
    current_rx, current_tx = get_net_bytes()
    current_time = time.time()
    
    if last_net_time == 0:
        last_rx, last_tx, last_net_time = current_rx, current_tx, current_time
        return "DL: 0.0KB/s  UP: 0.0KB/s"
        
    elapsed = current_time - last_net_time
    rx_speed = (current_rx - last_rx) / elapsed / 1024.0
    tx_speed = (current_tx - last_tx) / elapsed / 1024.0
    
    last_rx, last_tx, last_net_time = current_rx, current_tx, current_time
    return f"DL: {format_speed(rx_speed)}  UP: {format_speed(tx_speed)}"

def get_stats():
    ip = get_system_stat("hostname -I | cut -d' ' -f1")
    raw_temp = get_system_stat("cat /sys/class/thermal/thermal_zone0/temp")
    cpu_temp = f"{int(raw_temp) / 1000.0:.1f}C" if raw_temp.isdigit() else "N/A"
    ram = get_system_stat("free -m | awk 'NR==2{printf \"%s/%sMB\", $3,$2}'")
    
    disk = get_system_stat("df -h / | awk 'NR==2{print $4}'")
    net_speed = get_net_speed()

    line1 = f"IP: {ip}  |  Temp: {cpu_temp}  |  RAM: {ram}"
    line2 = f"Disk: {disk}  |  Net: {net_speed}"
    return line1, line2

def main():
    global device
    
    signal.signal(signal.SIGTERM, graceful_exit)

    serial = i2c(port=1, address=0x3C)
    device = ssd1306(serial, width=128, height=32)
    
    # Dropped font size to 12 to fit cleanly inside the UI borders
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_size = 12
    if not os.path.exists(font_path):
        font = ImageFont.load_default()
    else:
        font = ImageFont.truetype(font_path, font_size)

# --- BOOT SPLASH SCREEN WITH LOGO ---
    try:
        # Dynamically get the absolute path to the directory this script lives in
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "logo.png")
        print(f"Logo path: {logo_path}")
        
        # Load, convert to 1-bit monochrome, resize to fit exactly, and display
        logo = Image.open(logo_path).convert("1").resize((128, 32))
        device.display(logo)
        time.sleep(3.0) 
        
    except Exception as e:
        # Fallback to text if the image is missing or corrupted
        print(f"Failed to load logo: {e}")
        splash = Image.new("1", (device.width, device.height))
        splash_draw = ImageDraw.Draw(splash)
        splash_draw.rectangle((0, 0, device.width - 1, device.height - 1), outline=255)
        splash_draw.text((12, 9), "System Booting...", font=font, fill=255)
        device.display(splash)
        time.sleep(3.0) 
    # ------------------------------------
    # --- BOOT SPLASH SCREEN WITH BORDER ---
    splash = Image.new("1", (device.width, device.height))
    splash_draw = ImageDraw.Draw(splash)
    splash_draw.rectangle((0, 0, device.width - 1, device.height - 1), outline=255)
    splash_draw.text((12, 9), "System Booting...", font=font, fill=255)
    device.display(splash)
    time.sleep(3.0) 
    # --------------------------------------

    last_update_time = 0
    line1, line2 = "", ""
    max_text_width = 0

    x_pos = 0 
    padding = 40 

    print("Starting Bordered Network Stats Marquee...")

    try:
        while True:
            current_time = time.time()
            if current_time - last_update_time > 5.0:
                line1, line2 = get_stats()
                
                left1, top1, right1, bottom1 = font.getbbox(line1)
                left2, top2, right2, bottom2 = font.getbbox(line2)
                
                max_text_width = max(right1 - left1, right2 - left2)
                last_update_time = current_time

            segment_width = max_text_width + padding

            image = Image.new("1", (device.width, device.height))
            draw = ImageDraw.Draw(image)
            
            # 1. Draw the scrolling text
            draw_x = x_pos
            while draw_x < device.width:
                draw.text((draw_x, 1), line1, font=font, fill=255)
                draw.text((draw_x, 17), line2, font=font, fill=255)
                draw_x += segment_width
            
            # 2. Draw black masks on the extreme left/right edges so text doesn't smear into the border
            draw.line((1, 1, 1, 30), fill=0)
            draw.line((126, 1, 126, 30), fill=0)

            # 3. Draw the static UI elements on top
            # Outer Bounding Box
            draw.rectangle((0, 0, device.width - 1, device.height - 1), outline=255)
            # Horizontal Separator (Y=15 is roughly the center point)
            draw.line((0, 15, device.width - 1, 15), fill=255)
            
            device.display(image)
            
            x_pos -= 2
            
            if x_pos <= -segment_width:
                x_pos += segment_width
                
            time.sleep(0.02)
                
    except KeyboardInterrupt:
        graceful_exit(None, None)

if __name__ == "__main__":
    main()
