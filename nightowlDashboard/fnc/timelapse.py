#!/usr/bin/env python3

from time import sleep
from picamera import PiCamera
from datetime import datetime, timedelta
from drv.LEDdriver import IReyes
import os
import glob
from threading import Thread
import subprocess

class Timelapse:
    def __init__(self) -> None:
        self._running = False
        self._conversion_running = False
        self._movie_framerate = 24
        # initialize defaults
        self.tl_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') # timestamp for current timelapse
        self.set_interval()
        self.set_cam_params()
        self._app_cwd = os.getcwd() + '/static/'
    
    def set_cam_params(self, camresolution: str = '1280x720', camiso: int = 0, ir_light: bool = False, tmp_dir: str = 'tmp', mov_dir: str = 'mov') -> None:
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
            
            tnow = datetime.now()
            prev_img = self._app_cwd + self._cam_settings['tmp_dir']+'/preview_'+ tnow.strftime('%y-%m-%d-%H-%M-%S') +'.jpg'
            
            if self._cam_settings['ir_light']:
                self._cameyes = IReyes()
                self._cameyes.turn_on()
            
            with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
                if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                    self._fix_cam_exp(camera)
                else:
                    camera.start_preview()
                    sleep(2)
                camera.capture(prev_img, format = 'jpeg', thumbnail = None, bayer = True)
            if self._cam_settings['ir_light']:
                self._cameyes.turn_off()
                #self._cameyes.cleanup() # will interfere with app.py calls...
            return prev_img.replace(self._app_cwd, '')
    
    def start(self) -> None:
        self._running = True
        #if camframerate < self._movie_framerate or camframerate > 60:
        #    print("WARNING: camera framerate may not be lower than 24 or greater than 60. Using default of 30.")
        #    camframerate = self._movie_framerate
        
        # Clear tmp files
        self.clear_tmp(prefix = 'timelapse')
        self.clear_tmp(prefix = 'preview')
        
        # Wait for start
        while self._running and (self._tinterval[0] - datetime.now()).total_seconds() > 0:
            print("waiting for start")
            sleep(1)
        
        if self._running:
            # Initialize/reset camera variables for fixed exposure settings
            self._cam_shut_speed = None
            self._cam_awb_gains = None
            
            if self._cam_settings['ir_light']:
                self._cameyes = IReyes()
            
            # update timestamp
            self.tl_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            
            # main working area
            if self._tinterval[2] >= 120:
                self._slow_capture() # handle large capture intervals individually
            else:
                self._fast_capture() # intervals less than 5s can be handled by continuous capture
            
            # make timelapse movie
            t_combine = Thread(target = self._combine_shots_to_movie, args = [])
            t_combine.start()
            #sleep(1)
            
            # cleanup GPIO resources
            #if self._cam_settings['ir_light']:
            #    self.cameyes.cleanup() # will interfere with app.py calls...
    
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
        #tl_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') # generated/updated for each run only; see self.start()
        # loop capture until stopped
        while self._running:
            if self._cam_settings['ir_light']:
                self._cameyes.turn_on()
                sleep(1)
            with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
                if self._cam_settings['camiso'] > 0: # if ISO is set, fix camera exposure
                    self._fix_cam_exp(camera)
                # Capture image
                camera.capture(self._app_cwd + self._cam_settings['tmp_dir']+'/timelapse_'+self.tl_timestamp+'_frame_'+str(counter).zfill(6)+'.jpg',
                                format = 'jpeg', thumbnail = None, bayer = False)
                counter += 1
            if self._cam_settings['ir_light']:
                self._cameyes.turn_off()
            self._wait()
    
    def _fast_capture(self) -> None:
        if self._cam_settings['ir_light']:
            self._cameyes.turn_on()
            sleep(1)
        #tl_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') # generated/updated for each run only; see self.start()
        with PiCamera(resolution = self._cam_settings['camresolution']) as camera:
            if self._cam_settings['camiso']: # if ISO is set, fix camera exposure
                self._fix_cam_exp(camera)
            # Capture images continuously with small delays
            for image in camera.capture_continuous(self._app_cwd + self._cam_settings['tmp_dir']+'/timelapse_'+self.tl_timestamp+'_frame_{counter:06d}.jpg',
                                                    format = 'jpeg', thumbnail = None, bayer = False):
                self._wait()
                if not self._running:
                    break
        if self._cam_settings['ir_light']:
            self._cameyes.turn_off()
    
    def _combine_shots_to_movie(self) -> None:
        # combine image captures to movie
        if not self._conversion_running:
            self._conversion_running = True
            #tl_timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') # generated/updated for each run only; see self.start()
            tmpfile = self._app_cwd + self._cam_settings['tmp_dir'] + '/ffmpeg_zeitraffer_' + self.tl_timestamp + '.mp4'
            outfile = self._app_cwd + self._cam_settings['mov_dir'] + '/zeitraffer_' + self.tl_timestamp + '.mp4'
            # construct command
            #ffmpeg_cmd = 'ffmpeg -framerate ' + str(self._movie_framerate) + ' -pattern_type glob -i "' + self._app_cwd+self._cam_settings['tmp_dir']+'/timelapse_*.jpg" -c:v libx264 ' + tmpfile
            ffmpeg_cmd = 'ffmpeg -framerate ' + str(self._movie_framerate) + ' -i "' + self._app_cwd+self._cam_settings['tmp_dir']+ '/timelapse_'+self.tl_timestamp+'_frame_%06d.jpg" -c:v libx264 -preset ultrafast ' + tmpfile
            epilogue_cmd = 'mv ' + tmpfile + ' ' + outfile
            final_cmd = ffmpeg_cmd + ' && ' + epilogue_cmd
            # run frame combination
            subprocess.run(final_cmd, shell = True)
            self._conversion_running = False
    
    def stop(self) -> None:
        self._running = False
    
    def clear_tmp(self, prefix: str = 'preview', quant: int = 0) -> None:
        # clear stale tmp images
        tmp_content = sorted(glob.glob(self._app_cwd + self._cam_settings['tmp_dir'] + '/' + prefix + '*'))
        if quant > 0:
            for f in tmp_content[:quant]:
                os.remove(f)
        else:
            for f in tmp_content:
                os.remove(f)
    
    def set_interval(self, t_start = datetime.now(), duration: float = 1.0, f_acc: float = 240.0) -> None:
        # duration in hours
        # f_acc time acceleration factor; default of 240 translates to one capture every 10s in a 24fps movie
        if duration > 0 and f_acc > 1:
            if type(t_start) is not type(datetime.now()):
                t_start = datetime.now()
            #today = datetime.now().date()
            #t_start_dt = datetime(today.year, today.month, today.day, int(t_start), int((t_start%1)*60), int((((t_start%1)*60)%1)*60) )
            self._tinterval = (t_start, duration, f_acc)
        else:
            print("Timelapse parameter error. Requirements: t_start 0 < x < 24; duration > 0; f_acc > 1")
    
    def _wait(self) -> None:
        if (self._tinterval[0] + timedelta(hours=self._tinterval[1])) < datetime.now():
            self.stop()
        sleep(self._tinterval[2] / self._movie_framerate)

    @property
    def current_interval(self) -> tuple:
        return self._tinterval
    
    @property
    def cam_settings(self):
        return self._cam_settings
    
    @property
    def status(self) -> bool:
        return any([self._running, self._conversion_running])