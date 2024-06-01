#!/usr/bin/env python3

from importlib import import_module
import os
from flask import Flask, render_template, Response, redirect, request, url_for, send_from_directory
import time
from datetime import datetime, timedelta
from threading import Thread

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
app.config['MOV_FOLDER'] = 'static/mov/'
#app.config['TMP_FOLDER'] = 'static/tmp/'
app.config['AHT20_FOLDER'] = 'static/aht20/'

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

# Timelapse
@app.route('/timelapse', methods = ['GET', 'POST'])
def tlpage():
    """Timelapse configuration page."""
    lapse_thread = Thread(target=timelapse_c.start, args=[])
    lapse_interval = timelapse_c.current_interval
    templateData = {
        'nowtime': time.ctime(),
        'camsettings': timelapse_c.cam_settings,
        'lapse_interval': (lapse_interval[0].strftime('%y-%m-%dT%H:%M'), lapse_interval[1], lapse_interval[2]),
        'lapse_interval_text': ('Start', 'Aufnahmedauer (in Stunden)', 'Zeitkompressionsfaktor'),
        'camstatus': timelapse_c.status,
        'preview_img': None,
        'camresolution_options': {'1920x1080 (FullHD 16:9)':'1920x1080',
                                    '1440x1080 (4:3)':'1440x1080',
                                    '1366x768 (WXGA 16:9)':'1366x768',
                                    '1024x768 (XGA 4:3)':'1024x768',
                                    '1280x720 (HD 16:9)':'1280x720',
                                    '960x720 (4:3)':'960x720',
                                    '1024x600 (WSVGA 16:9)':'1024x600',
                                    '800x600 (SVGA 4:3)':'800x600',
                                    '854x480 (FWVGA 16:9)':'854x480',
                                    '640x480 (VGA 4:3)':'640x480',
                                    '480x320 (HVGA 3:2)':'480x320',
                                    '320x240 (QVGA 4:3)':'320x240'
                                 },
        'camiso_options': (0,50,100,200,300,400,500,600,800,1000) # these are not in use
    }
    if request.method == 'POST':
        # handle form input
        if 'camsetter' in request.form:
            # new cam settings
            timelapse_c.set_cam_params(camresolution = request.form.get('camresolution'),
                camiso = int(request.form.get('camiso')),
                ir_light = (request.form.get('ir_light') == 'True'),
                tmp_dir = request.form.get('tmp_dir'),
                mov_dir = request.form.get('mov_dir')
                )
            #new_cam_settings = {k:request.form.get(k) for k in timelapse_c.cam_settings}
            #timelapse_c.set_cam_params(**new_cam_settings)
            templateData['camsettings'] = timelapse_c.cam_settings
            
            # check user input
            try:
                newduration = float(request.form.get('duration'))
                if newduration > 24:
                    raise
            except:
                newduration = 1.0
            
            try:
                newstart = datetime.strptime(request.form.get('t_start'), '%Y-%m-%dT%H:%M')
                if (newstart + timedelta(hours=newduration)) < datetime.now():
                    raise
            except:
                newstart = datetime.now()
            
            try:
                newfacc = float(request.form.get('f_acc'))
                if newfacc < 1:
                    raise
            except:
                newfacc = 240.0
            
            # new interval parameters
            timelapse_c.set_interval(newstart, newduration, newfacc)
            lapse_interval = timelapse_c.current_interval
            templateData['lapse_interval'] = (lapse_interval[0].strftime('%Y-%m-%dT%H:%M'), lapse_interval[1], lapse_interval[2])
        elif 'preview' in request.form:
            # capture preview
            templateData['preview_img'] = url_for('static', filename = timelapse_c.capture_preview())
            #try:
            #    templateData['preview_img'] = sorted(os.listdir(app.config['TMP_FOLDER']))[:-1]
            #except:
            #    templateData['preview_img'] = None
        elif 'abort' in request.form:
            # abort timelapse
            timelapse_c.stop()
            time.sleep(1)
            templateData['camstatus'] = timelapse_c.status
            #lapse_thread.join(timeout=10)
        elif 'lapse_start' in request.form:
            # start timelapse
            lapse_thread.start()
            time.sleep(1)
            templateData['camstatus'] = timelapse_c.status
            #lapse_thread.join(timeout=1)
    else:
        # whatever
        pass
    return render_template('index.html', content = 'timelapse.html', **templateData)

#@app.route('/timelapse_process', methods = ['GET', 'POST'])
#def tlprocesspage():
#    lapse_thread = Thread(target=timelapse_c.start, args=[])
#    lapse_interval = timelapse_c.current_interval
#    if request.method == 'POST':
#        # handle form input
#        if 'camsetter' in request.form:
#            # new cam settings
#            timelapse_c.set_cam_params(camresolution = request.form.get('camresolution'),
#                camiso = int(request.form.get('camiso')),
#                ir_light = (request.form.get('ir_light') == 'True'),
#                tmp_dir = request.form.get('tmp_dir'),
#                mov_dir = request.form.get('mov_dir')
#                )
#            
#            # new interval parameters
#            timelapse_c.set_interval(datetime.strptime(request.form.get('t_start'), '%Y-%m-%dT%H:%M'), float(request.form.get('duration')), float(request.form.get('f_acc')))
#        elif 'preview' in request.form:
#            # capture preview
#            templateData['preview_img'] = url_for('static', filename = timelapse_c.capture_preview())
#        elif 'abort' in request.form:
#            # abort timelapse
#            timelapse_c.stop()
#            time.sleep(1)
#        elif 'lapse_start' in request.form:
#            # start timelapse
#            lapse_thread.start()
#            time.sleep(1)
#    else:
#        # whatever
#        pass
#    return redirect('/timelapse')

# Filebrowser
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['MOV_FOLDER'], filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    file_path = os.path.join(app.config['MOV_FOLDER'], filename)
    os.remove(file_path)
    return redirect(url_for('filebrowser'))

@app.route('/filebrowser', methods = ['GET', 'POST'])
def filebrowser():
    """File download page."""
    moviefiles = sorted(os.listdir(app.config['MOV_FOLDER']))
    sensorfiles = sorted(os.listdir(app.config['AHT20_FOLDER']))
    templateData = {
        'nowtime': time.ctime()
    }
    return render_template('index.html', content = 'filebrowser.html', moviefiles = moviefiles, sensorfiles = sensorfiles, **templateData)

# Live Video Feed
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

@app.route('/livepage', methods = ['GET', 'POST'])
def livepage():
    """Video streaming page."""
    templateData = {
        'nowtime': time.ctime(),
        'IRstate': bool(redeyes.status),
        'camstatus': timelapse_c.status
    }
    if request.method == 'POST':
        if request.form.get('IRled_state') == 'IRon':
            redeyes.turn_on()
            templateData['IRstate'] = bool(redeyes.status)
        elif request.form.get('IRled_state') == 'IRoff':
            redeyes.turn_off()
            templateData['IRstate'] = bool(redeyes.status)
    return render_template('index.html', content = 'livepage.html', **templateData)

#@app.route("/toggle_lights/", methods = ['POST'])
#def toggle_lights():
#    redeyes.toggle()
#    return redirect(request.referrer)

# shutdown
@app.route('/poweroff', methods = ['GET', 'POST'])
def poweroff():
    if request.method == 'POST':
        if request.form.get('poweroff') == 'poweroff_yes':
            os.system('sudo systemctl poweroff')
            return redirect('/goodnight')
        else:
            return redirect('/')
    return render_template('index.html', content = 'poweroff.html')

@app.route('/goodnight')
def goodnight():
    return render_template('goodnight.html')


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80, debug = True, threaded = True)
