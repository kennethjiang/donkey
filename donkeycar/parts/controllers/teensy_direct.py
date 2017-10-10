#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time

import requests

import tornado.ioloop
import tornado.web
import tornado.gen

from ... import utils


class TeensyDirectController():
    import threading
    
    def __init__(self, angle_pwm_neutral=1500, throttle_pwm_neutral=1500):

        self.lock = threading.RLock()
        self.serial_bus = = serial.Serial('/dev/ttyACM0', 115200, timeout = 0.05)

        self.angle_pwm_out = angle_pwm_neutral
        self.throttle_pwm_out = throttle_pwm_neutral
        self.mode = 'user'
        self.recording = False

        
    def update(self):
        msg_in_thread = threading.Thread(target=self.message_in_loop)
        msg_in_thread.daemon = True
        msg_in_thread.start()

        msg_out_thread = threading.Thread(target=self.message_out_loop)
        msg_out_thread.daemon = True
        msg_out_thread.start()


    def run_threaded(self):
        ''' 
        Return the last state given from the remote server.
        '''
        
        #return last returned last remote response.
        return self.angle, self.throttle, self.mode, self.recording

    def message_in_loop(self):
        while True:
            line = self.serial_bus.readline().strip()

            with self.lock:
                if line.startswith('S'):
                    self.angle_pwm_in = int(line[1:])
                if line.startswith('T'):
                    self.throttle_pwm_in = int(line[1:])
                if self.mode == 'user':
                    self.angle_pwm_out = self.angle_pwm_in
                    self.throttle_pwm_out = self.throttle_pwm_in

    def message_out_loop(self):
        while True:
            with self.lock:
                angle_pwm = self.angle_pwm_out
                throttle_pwm = self.throttle_pwm_out
            self.serial_bus.write(('S' + str(angle_pwm) + '\n').encode())
            self.serial_bus.write(('T' + str(throttle_pwm) + '\n').encode())


class TeensyWebServer(tornado.web.Application):

    def __init__(self):
        print('Starting Donkey Server...')

        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.static_file_path = os.path.join(this_dir, 'templates', 'static')
        
        self.angle = 0.0
        self.throttle = 0.0
        self.mode = 'user'
        self.recording = False

        handlers = [
            (r"/", tornado.web.RedirectHandler, dict(url="/drive")),
            (r"/drive", DriveAPI),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.static_file_path}),
            ]

        settings = {'debug': True}

        super().__init__(handlers, **settings)

    def update(self, port=8887):
        ''' Start the tornado webserver. '''
        print(port)
        self.port = int(port)
        self.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def run_threaded(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording
        
    def run(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording


class DriveAPI(tornado.web.RequestHandler):

    def get(self):
        data = {}
        self.render("templates/vehicle.html", **data)
    
    
    def post(self):
        '''
        Receive post requests as user changes the angle
        and throttle of the vehicle on a the index webpage
        '''
        data = tornado.escape.json_decode(self.request.body)
        self.application.angle = data['angle']
        self.application.throttle = data['throttle']
        self.application.mode = data['drive_mode']
        self.application.recording = data['recording']

