# Nightowl

A small, lightweight infrared camera for wildlife and plant surveillance.
I built this for a family member so they can observe plant growth at night and detect pests.

## Materials

 - Raspberry Pi Zero W (or better Zero 2 W)
 - microSD card (32 GB or greater recommended)
 - Camera with IR LEDs (! need to look up exact model !)
 - Adafruit AHT20 temperature and humidity sensor
 - power bank (>10 Ah recommended)
 - 3D printed models

## Dashboard Dependencies
 - Python modules: ```flask``` (and dependencies) ```picamera``` (or camera specific module, see M. Grinberg's driver below) ```smbus2```


The dashboard incorporates Miguel Grinberg's camera live streaming driver (https://github.com/miguelgrinberg/flask-video-streaming/) with minor adjustments.



## Usage notes
- Copy the nightowlDashboard folder to the Pi Zero
- Set environment variable ```CAMERA = pi```
- Start the dashboard as root with environment preservation: ```sudo -E python3 app.py```

## Use as service
Establishing the flask webserver as a server will enable
- start on boot
- automatic restarts upon crash/failure
- journal logging

Create a file ```/etc/systemd/system/nightowl.service``` with content
```[Unit]
Description=Nightowl Web Application
After=network.target
StartLimitBurst=10
StartLimitIntervalSec=300

[Service]
User=root
WorkingDirectory=/home/nachteule/nightowlDashboard
Environment=CAMERA=pi
ExecStart=/bin/env python3 /home/nachteule/nightowlDashboard/app.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target```

Execute ```sudo systemctl daemon-reload```
Check if it executes fine by ```sudo systemctl start nightowl```
Status checks can be performed with ```sudo systemctl status nightowl```
The journal can be accessed through ```journatctl -u nightowl```
