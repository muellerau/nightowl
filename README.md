# Nightowl

A small, lightweight infrared camera for wildlife and plant surveillance.
I built this for a family member so they can observe plant growth at night and detect pests.

## Materials

 - Raspberry Pi Zero W (or better Zero 2 W)
 - microSD card (64 GB or greater ! double check !)
 - Camera with IR LEDs (! need to look up exact model !)
 - Adafruit AHT20 temperature and humidity sensor
 - power bank (>10 Ah recommended)
 - 3D printed models

## Dashboard Dependencies
 - Python modules: ```flask``` (and dependencies) ```picamera``` (or camera specific module, see M. Grinberg's driver below) ```smbus2```
 - Miguel Grinberg's camera live streaming driver
https://github.com/miguelgrinberg/flask-video-streaming/



## Usage notes
- Copy the nightowlDashboard folder to the Pi Zero
- Set environment variable ```CAMERA = pi```
- Start the dashboard as root with environment preservation: ```sudo -E python3 app.py```
