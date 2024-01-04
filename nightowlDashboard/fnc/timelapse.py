#!/usr/bin/env python3

from time import sleep
from picamera import PiCamera
from datetime import datetime, timedelta
from drv.LEDdriver import IReyes

class Timelapse:
    def __init__(self) -> None:
        self._running = False
        self._movie_framerate = 24
        # initialize defaults
        self.set_interval()
        self.set_cam_params()
    
    def set_cam_params(self, camresolution: tuple = (1280, 720), camiso: int = 0, ir_light: bool = False, tmp_dir: str = 'tmp', mov_dir: str = 'mov') -> None:
        # collect parameters
        self._cam_settings = {
            'camresolution': camresolution,
            #'camframerate': camframerate, # not in use
            'camiso': camiso,
            'ir_light': ir_light,
            'tmp_dir': tmp_dir,
            'mov_dir': mov_dir
        }
    
    def capture_preview(self) -> str:
        if not self._running:
            # Initialize/reset camera variables for fixed exposure settings
            self._cam_shut_speed = None
            self._cam_awb_gains = None
            
            prev_img = self._cam_settings['tmp_dir']+'/preview_{timestamp:%Y-%m-%d-%H-%M}.jpg'
            
            if self._cam_settings['irlight']:
                self._cameyes = IReyes()
                self._cameyes.turn_on()
            
            with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
                if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                    self._fix_cam_exp(camera)
                else:
                    sleep(1)
                camera.capture(prev_img, format = 'jpeg', thumbnail = None, bayer = True)
                
            if self._cam_settings['irlight']:
                self._cameyes.turn_off()
                self._cameyes.cleanup()
            return prev_img
    
    def start(self) -> None:
    #def start(self, camresolution: tuple = (1280, 720), camframerate: int = 30, camiso: int = 0, ir_light: bool = False) -> None:
        self._running = True
        #if camframerate < self._movie_framerate or camframerate > 60:
        #    print("WARNING: camera framerate may not be lower than 24 or greater than 60. Using default of 30.")
        #    camframerate = self._movie_framerate
        
        # Wait for start
        while self._running and (self._tinterval[0] - datetime.now()).total_seconds() > 0:
            sleep(1)
        
        # Initialize/reset camera variables for fixed exposure settings
        self._cam_shut_speed = None
        self._cam_awb_gains = None
        
        if self._cam_settings['irlight']:
            self._cameyes = IReyes()
        # main working area
        if self._tinterval[3] >= 120:
            self._slow_capture() # handle large capture intervals individually
        else:
            self._fast_capture() # intervals less than 5s can be handled by continuous capture
        # make timelapse movie
        self._combine_shots_to_movie()
        # cleanup GPIO resources
        if self._cam_settings['irlight']:
            self.cameyes.cleanup()
    
    def _fix_cam_exp(self, camera):
        if camera:
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
            return camera
    
    def _slow_capture(self) -> None:
        counter = 0
        # loop capture until stopped
        while self._running:
            if self._cam_settings['ir_light']:
                self._cameyes.turn_on()
                sleep(1)
            with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
                if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                    self._fix_cam_exp(camera)
                # Capture image
                camera.capture(self._cam_settings['tmp_dir']+'/img_{timestamp:%Y-%m-%d-%H-%M}_'+str(counter).zfill(6)+'.jpg', format = 'jpeg', thumbnail = None, bayer = False)
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
                self._fix_cam_exp(camera)
            # Capture images continuously with small delays
            for image in camera.capture_continous(self._cam_settings['tmp_dir']+'/img_{timestamp:%Y-%m-%d-%H-%M}_{counter:06d}.jpg', format = 'jpeg', thumbnail = None, bayer = False):
                self._wait()
        if self._cam_settings['ir_light']:
            self._cameyes.turn_off()
    
    def _combine_shots_to_movie(self) -> None:
        # combine image captures to movie
        pass
    
    def stop(self) -> None:
        self._running = False
    
    def set_interval(self, t_start: float = float(datetime.now().hour + datetime.now().minute / 60 + datetime.now().second / 60),
            duration: float = 1.0, f_acc: float = 240.0) -> None:
        # t_start hour of 24h scale
        # duration in hours
        # f_acc time acceleration factor; default of 240 translates to one capture every 10s in a 24fps movie
        if t_start < 24 and t_start > 0 and duration > 0 and duration < 24 and f_acc > 1:
            today = datetime.now().date()
            t_start_dt = datetime(today.year, today.month, today.day, int(t_start), int((t_start%1)*60), int((((t_start%1)*60)%1)*60) )
            self._tinterval = (t_start_dt, duration, f_acc)
        else:
            print("Timelapse parameter error. Requirements: t_start 0 < x < 24; duration > 0; f_acc > 1")
    
    def _wait(self) -> None:
        if (self._tinterval[0] + timedelta(hours=self._tinterval[1])) < datetime.now():
            self._stop()
        sleep(self._tinterval[2] / self._movie_framerate)

    @property
    def current_interval(self) -> tuple:
        return self._tinterval
    
    @property
    def cam_settings(self):
        return self._cam_settings
    
    @property
    def status(self) -> bool:
        return self._running