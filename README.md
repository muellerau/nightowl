# Nightowl

A small, lightweight infrared timelapse camera for wildlife and plant surveillance.
I built this for a family member so they can observe plant growth at night and detect pests.

## Materials

| line  | item                                                    | supplier        | cat-no      | quantity | $/item | $total | remarks                               |
| :---: | ------------------------------------------------------- | --------------- | ----------- | :------: | :----: | :----: | ------------------------------------- |
| 1     | Raspberry Pi Zero W                                     | PiShopUS        | #808        | 1        | 15.00  | 15.00  | or better now, use Pi Zero 2W         |
| 2     | microSD card 32GB or greater                            | any             | any         | 1        | ???    | ???    | I used a SanDisk 32GB Extreme Pro     |
| 3     | DORHEA Camera Manual Focus 5MP OV5647 with 2x3W IR LED  | Amazon          | B07JXZ93SK  | 1        | 15.99  | 15.99  |                                       |
| 4     | Pi Zero Ribbon Cable Adapter 15CM 15 Pin to 22 Pin      | Amazon          | B0716TB6X3  | 1        | 5.99   | 5.99   |                                       |
| 5     | R330 resistor                                           | any             | any         | 2        | 0.00   | 0.00   | still had a few lying around          |
| 6     | NPN BJT                                                 | onsemi/digikey  | PN2222      | 2        | 0.40   | 0.80   |                                       |
| 7     | AHT20                                                   | Adafruit        | #4566       | 1        | 4.50   | 4.50   |                                       |
| 8     | 3D printed housing                                      | any             | any         | x        | ???    | ???    | see below                             |
| 9     | 30 Ah USB power bank                                    | any             | any         | 1        | ???    | ???    | any generic power bank with 2A or greater output will do |

Regarding the housing/case in line 8: models for 3D printing are located in the 'case' folder; my design was loosely based on
https://www.thingiverse.com/thing:4741526
and the stand is identical (or use other mounts depending on application)

## Wiring

circuit sketch
BJT = onsemi PN2222


            LED(-) ------ BJT-C > BJT-B > BJT-E ----- 
             |||                   ^                |
            LED(+)                R330              |
              ^                    ^                |
            CAM(+)              GPIO pin7           |
    CSI------|||                                    |
            CAM(-)                                  |
              |                                     |
              ---------------------------------------

This was the test setup. In the end, I used GPIO pins 13 and 15 (physical numbering; BCM numbering is GPIO 27 and 22).


I did some measurements using a generic amp-meter (no guarantees for accuracy)
| routing                    | max current (mA) |
| -------------------------- | ---------------- |
| GPIO pin7 -> R330 -> BJT-B | 9                |
| CAM(+) -> LED(+)           | 140 (varies with photoresistor and potentiometer on LED) |

If the LED power consumption is too high, adjust the variable resistor on the LEDs.


## Dashboard Dependencies
 - Python modules: `flask` `picamera` `smbus2`

The dashboard incorporates Miguel Grinberg's camera live streaming driver (https://github.com/miguelgrinberg/flask-video-streaming/) with minor adjustments.

## Usage notes
- Copy the nightowlDashboard folder to the Pi Zero
- Set environment variable `CAMERA = pi`
- Start the dashboard as root with environment preservation: `sudo -E python3 app.py`

## Use as service
Establishing the flask webserver as a server will enable
- start on boot
- automatic restarts upon crash/failure
- journal logging

To do so,
- create a file `/etc/systemd/system/nightowl.service` with content
```
[Unit]
Description=Nightowl Web Application
After=network.target
StartLimitBurst=10
StartLimitIntervalSec=300

[Service]
User=root
WorkingDirectory=/home/nightowl/nightowlDashboard
Environment=CAMERA=pi
ExecStart=/bin/env python3 /home/nightowl/nightowlDashboard/app.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

- execute `sudo systemctl daemon-reload`
- check if it executes fine by `sudo systemctl start nightowl`
- status checks can be performed with `sudo systemctl status nightowl`
- the journal/log can be accessed through `journatctl -u nightowl`



