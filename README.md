# Raspberry Pi 5 OLED System Monitor

A seamless, scrolling hardware monitor for the Raspberry Pi 5 using an I2C SSD1306 OLED display (128x32). It actively monitors and displays IP address, CPU temperature, RAM usage, Root Disk space, and real-time Network I/O.

## Hardware Requirements
* Raspberry Pi 5
* SSD1306 OLED Display (128x32 resolution) - The one I have: https://www.amazon.ca/dp/B07D3LPVLC
* I2C enabled via `raspi-config` (Address `0x3c` on Port 1)

## Setup & Installation

Due to PEP 668 restrictions in Raspberry Pi OS (Bookworm), this project requires a Python virtual environment.

### 1. Initialize the Environment
Navigate to the project directory and create the virtual environment:
```bash
python3 -m venv env
source env/bin/activate
```

### 2. Install Dependencies
Install the required Luma OLED drivers and Pillow for image processing:
```bash
pip install luma.oled pillow
```
*Note: Ensure the DejaVu TrueType font is installed on the OS (`sudo apt install fonts-dejavu`).*

## Running Manually
To test the script or run it manually, ensure the virtual environment is active:
```bash
source env/bin/activate
python stats_marquee_2line.py
```

## Running as a Systemd Service (Daemon)
To ensure the display starts automatically on boot and handles screen-clearing gracefully on shutdown, run it as a `systemd` service.

### Service Configuration (`/etc/systemd/system/oled_stats.service`)
```ini
[Unit]
Description=OLED System Stats Marquee
After=network.target

[Service]
Type=simple
User=tylebrim
WorkingDirectory=/home/tylebrim/oled_project
ExecStart=/home/tylebrim/oled_project/env/bin/python /home/tylebrim/oled_project/stats_marquee_2line.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Useful systemctl Commands
* **Start the monitor:** `sudo systemctl start oled_stats.service`
* **Stop the monitor:** `sudo systemctl stop oled_stats.service`
* **Restart the monitor:** `sudo systemctl restart oled_stats.service`
* **Check status:** `sudo systemctl status oled_stats.service`
* **Enable on boot:** `sudo systemctl enable oled_stats.service`

## Customization
* **Logo:** Replace `logo.png` in the root directory with any 128x32 image to change the boot splash screen. 
* **UI Margins:** Bounding boxes and horizontal separators are drawn dynamically via Pillow's `ImageDraw` module.
