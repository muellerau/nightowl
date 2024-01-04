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

# import timelapse module
from fnc.timelapse import Timelapse
timelapse_c = Timelapse()

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

@app.route('/livepage', methods = ['GET', 'POST'])
def livepage():
    """Video streaming page."""
    templateData = {
        'nowtime': time.ctime(),
        'IRstate': bool(redeyes.status),
        'camstatus': timelapse_c.status
    }
    if request.method == 'POST':
        redeyes = IReyes()
        if request.form.get('IRled_state') == 'IRon':
            redeyes.turn_on()
        elif request.form.get('IRled_state') == 'IRoff':
            redeyes.turn_off()
        redeyes.cleanup()
    return render_template('index.html', content = 'livepage.html', **templateData)

@app.route('/timelapse', methods = ['GET', 'POST'])
def tlpage():
    """Timelapse configuration page."""
    templateData = {
        'camsettings': timelapse_c.cam_settings,
        'camstatus': timelapse_c.status,
        'preview_img': None
    }
    if request.method == 'POST':
        # handle form input
        if 'camsetter' in request.form:
            # new cam settings
            new_cam_settings = {k:request.form.get(k) for k in timelapse_c.cam_settings}
            timelapse_c.set_cam_params(**new_cam_settings)
            templateData['camsettings'] = timelapse_c.cam_settings
        elif 'preview' in request.form:
            # capture preview
            templateData['preview_img'] = timelapse_c.capture_preview()
        elif 'abort' in request.form:
            # abort timelapse
            timelapse_c.stop()
    else:
        # whatever
        pass
    return render_template('index.html', content = 'timelapse.html', **templateData)

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Link this URL in the src attribute of an img tag."""
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/toggle_lights/", methods = ['POST'])
def toggle_lights():
    redeyes.toggle()
    return redirect(request.referrer)



if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80, debug = True, threaded = True)
