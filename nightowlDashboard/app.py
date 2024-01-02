#!/usr/bin/env python3

from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request
import time

# import temp/hum sensor driver
from drv.aht20driver import AHT20
aht20sens = AHT20()

# import LED driver
from drv.LEDdriver import IReyes
redeyes = IReyes()

# import camera driver
if os.environ.get('CAMERA'):
    Camera = import_module('livecamera.camera_' + os.environ['CAMERA']).Camera
else:
    from livecamera.camera_dummy import Camera

# Raspberry Pi camera module (requires picamera package)
# from camera_pi import Camera

app = Flask(__name__)


@app.route('/')
def index():
    """Start page."""
    aht20sens.measure()
    templateData = {
        'nowtime': time.ctime(),
        'temp': round(aht20sens.temperature, 1),
        'hum': round(aht20sens.humidity, 1)
    }
    return render_template('index.html', content = 'landing.html', **templateData)

@app.route('/livepage')
def livepage():
    """Video streaming page."""
    if redeyes.status:
        irstate = True
    else:
        irstate = False
    templateData = {
        'nowtime': time.ctime(),
        'IRstate': irstate
    }
    return render_template('index.html', content = 'livepage.html', **templateData)

@app.route('/timelapse')
def tlpage():
    """Timelapse configuration page."""
    return return redirect('/')

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Link this URL in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/toggle_lights/", methods=['POST'])
def toggle_lights():
    redeyes.toggle()
    return redirect(request.referrer)



if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80, debug = True, threaded = True)
