# Nightowl

A small, lightweight infrared timelapse camera for wildlife and plant surveillance with temperature/humidity recording.
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
| 9     | M2 stand-offs (10mm male-female, 25mm female-female) + screws | Amazon    | B0BXT4FG1T  | 1        | 9.99   | 9.99   |                                       |
| 10    | 30 Ah USB power bank                                    | any             | any         | 1        | ???    | ???    | any generic power bank with 2A or greater output will do |
| 11    | tesa Sugru                                              | any             | any         | x        | ???    |        | used to isolate open wires, fix AHT20 and camera |

Regarding the housing/case in line 8: models for 3D printing are located in the 'case' folder; my design was loosely based on
https://www.thingiverse.com/thing:4741526
and the stand is identical (or use other mounts depending on application)
Note that I had some difficulty to fit the camera/LED module through the holes in the casing. Maybe the 3D print was a bit deformed or I made a mistake when calculating the dimensions, but a little bit of sanding resolved the issue.

## Wiring

The IR LEDs require a lot of power, but I wanted to be able to power the device with a battery/power bank. To minimize energy consumption, I included a small circuit to enable manual switching of the IR LEDs.

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


## Assembly

Before assembly, the switching circuit for the IR LEDs should be soldered. Any open wires can be isolated using a moldable plastic glue (e.g., I used Sugru).

To mount the camera and Pi Zero in the case, stand-offs are needed (line 9 above):
- 4x 6mm female-female in the cam body to support camera (glue onto plastic pins around camera hole)
- place LEDs, place 2 washers over each mount hole, place camera on top, screw everything onto stand-off (this part is rather finicky)
- 4x 15mm female-female in the cam body to support the Pi Zero body (glue onto raised plastic pins)
- 4x 6mm male-female for the Pi Zero body to support the lid
- the lid is simply screwed on

The AHT20 (with header soldered on) can be mounted with small blobs of moldable plastic glue.

The case leaves space for a small heatsinks to be added to the camera/LEDs and the Pi Zero (max 5mm). However, I only used a heatsink on the Pi Zero.



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



