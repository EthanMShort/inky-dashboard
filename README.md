# Inky Dashboard

A modular e-Ink dashboard controller designed for the Raspberry Pi Zero 2 W and the Pimoroni Inky pHAT (SSD1608). This project utilizes a Flask web server to trigger various Python scripts that render system statistics, weather data, and media information to the display.

## Features

* **Web Control Panel:** A responsive mobile-friendly web interface to trigger display updates, manage power, and send custom text messages.
* **System Dashboard:** visualizes real-time CPU load, RAM usage, Disk usage, uptime, and network information.
* **Weather Forecast:** Fetches local forecast data via the NWS API, rendering custom weather icons and temperature highs/lows.
* **Music Tracker:** Integrates with the Last.fm API to display "Now Playing" track information and dithered album art.
* **Custom Messaging:** Send arbitrary text to the display directly from the browser.

## Hardware Requirements

* Raspberry Pi Zero 2 W (or similar)
* Pimoroni Inky pHAT (Specifically configured for the **SSD1608** driver)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/inky-dashboard.git](https://github.com/yourusername/inky-dashboard.git)
    cd inky-dashboard
    ```

2.  **Set up Virtual Environment:**
    It is recommended to use a virtual environment (e.g., `pimoroni`) to manage dependencies.
    ```bash
    python3 -m venv ~/.virtualenvs/pimoroni
    source ~/.virtualenvs/pimoroni/bin/activate
    ```

3.  **Install Dependencies:**
    Ensure you have the required libraries installed:
    ```bash
    pip install flask inky pillow requests psutil
    ```

## Configuration

Before running, you must configure the location and API keys in the tool scripts:

* **Weather:** Edit `tools/weather.py` and update the `LAT` and `LON` variables for your location.
* **Last.fm:** Edit `tools/lastfm.py` to add your `LASTFM_API_KEY` and `LASTFM_USER`.

## Usage

1.  **Start the Web Server:**
    ```bash
    python3 app.py
    ```

2.  **Access the Dashboard:**
    Open a browser and navigate to `http://<your-pi-ip>:5000`.

## Directory Structure

* `app.py`: Main Flask application entry point.
* `tools/`: Python scripts responsible for generating and rendering images.
* `web/templates/`: HTML templates for the UI.
* `examples/`: Reference scripts for Inky functionality.
