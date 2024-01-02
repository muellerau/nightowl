#!/usr/bin/env python3

from time import sleep
from picamera import PiCamera
from datetime import datetime, timedelta
from ..drv.LEDdriver import IReyes

class Timelapse:
    def __init__(self) -> None:
        self._movie_framerate = 24
        self._tinterval = ()
    
    def start(self, camresolution: tuple = (1280, 720), camiso: int = 0, ir_light: bool = False) -> None:
    #def start(self, camresolution: tuple = (1280, 720), camframerate: int = 30, camiso: int = 0, ir_light: bool = False) -> None:
        self._running = True
        if not self._tinterval:
            self.set_interval()
        #if camframerate < self._movie_framerate or camframerate > 60:
        #    print("WARNING: camera framerate may not be lower than 24 or greater than 60. Using default of 30.")
        #    camframerate = self._movie_framerate
        
        # Wait here for start
        while self._running and self._tinterval[0] < (datetime.now().hour + datetime.now().minute / 60):
            sleep(1)
        
        # Initialize camera variables for fixed exposure settings
        self._cam_shut_speed = None
        self._cam_awb_gains = None
        # collect parameters
        self._cam_settings = {
            'camresolution': camresolution,
            #'camframerate': camframerate,
            'camiso': camiso,
            'ir_light': ir_light
        }
        if ir_light:
            self._cameyes = IReyes()
        # main working area
        if self._tinterval[3] >= 120:
            self._slow_capture() # handle large capture intervals individually
        else:
            self._fast_capture() # intervals less than 5s can be handled by continuous capture
        # Cleanup
        if ir_light:
            #self.cameyes.cleanup() # will currently interfere with main app calls; requires reorganization
    
    def _slow_capture(self) -> None:
        counter = 0
        # loop capture until stopped
        while self._running: # and time window
            if self._cam_settings['ir_light']:
                self._cameyes.turn_on()
                sleep(1)
            with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
                if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                    # Set ISO to the desired value
                    camera.iso = self._cam_settings['camiso']
                    # Wait for the automatic gain control to settle
                    sleep(2)
                    # Now fix the values
                    if not self._cam_shut_speed:
                        self._cam_shut_speed = camera.exposure_speed
                    camera.shutter_speed = self._cam_shut_speed
                    camera.exposure_mode = 'off'
                    if not self._cam_awb_gains:
                        self._cam_awb_gains = camera.awb_gains
                    camera.awb_mode = 'off'
                    camera.awb_gains = self._cam_awb_gains
                # Capture image
                camera.capture(str('img_{timestamp:%Y-%m-%d-%H-%M}_'+str(counter).zfill(4)+'.jpg', format = 'jpeg', thumbnail = None, bayer = True)
                counter += 1
            if self._cam_settings['ir_light']:
                self._cameyes.turn_off()
            self._wait()
    
    def _fast_capture(self) -> None:
        if self._cam_settings['ir_light']:
            self._cameyes.turn_on()
            sleep(1)
        with PiCamera(resolution = camresolution) as camera:
            if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                # Set ISO to the desired value
                camera.iso = self._cam_settings['camiso']
                # Wait for the automatic gain control to settle
                sleep(2)
                # Now fix the values
                if not self._cam_shut_speed:
                    self._cam_shut_speed = camera.exposure_speed
                camera.shutter_speed = self._cam_shut_speed
                camera.exposure_mode = 'off'
                if not self._cam_awb_gains:
                    self._cam_awb_gains = camera.awb_gains
                camera.awb_mode = 'off'
                camera.awb_gains = self._cam_awb_gains
            # Capture images continuously with small delays
            for image in camera.capture_continous('img_{timestamp:%Y-%m-%d-%H-%M}_{counter:04d}.jpg', format = 'jpeg', thumbnail = None, bayer = True):
                self._wait()
        if self._cam_settings['ir_light']:
            self._cameyes.turn_off()
    
    def stop(self) -> None:
        self._running = False
    
    def set_interval(self, t_start: float = float(datetime.now().hour + datetime.now().minute / 60 + 1.0), duration: float = 1.0, f_acc: float = 240.0) -> None:
        # t_start hour of 24h scale
        # duration in hours
        # f_acc time acceleration factor; default of 240 translates to one capture every 10s
        if t_start < 24 and t_start > 0 and duration > 0 and f_acc > 1:
            self._tinterval = (t_start, duration, f_acc / self._movie_framerate)
        else:
            print("Timelapse parameter error. Requirements: t_start 0 < x < 24; duration > 0; f_acc > 1")
    
    def _wait(self) -> None:
        if (datetime.now() + timedelta(hours=duration)) < datetime.now():
            self._stop()
        sleep(self._tinterval[2])

    @property
    def current_interval(self) -> tuple:
        return self._tinterval
    
    @property
    def get_settings(self):
        if self._cam_settings:
            return self._cam_settings
        else:
            print("No settings defined.")
            return 1
    
    @property
    def status(self) -> bool:
        return self._running