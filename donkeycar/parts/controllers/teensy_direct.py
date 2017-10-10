#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import threading
import serial

import requests

import tornado.ioloop
import tornado.web
import tornado.gen

from ... import utils


class TeensyDirectController():
    
    def __init__(self, angle_pwm_neutral=1500, throttle_pwm_neutral=1500):

        self.lock = threading.RLock()
        #self.serial_bus = serial.Serial('/dev/ttyACM0', 115200, timeout = 0.05)

        self.angle_pwm_in = angle_pwm_neutral
        self.throttle_pwm_in = throttle_pwm_neutral
        self.max_throttle = 0.25
        self.drive_mode = 'user'
        self.recording = False

		#Critical sections that should be guarded by lock
        self.angle_pwm_out = angle_pwm_neutral
        self.throttle_pwm_out = throttle_pwm_neutral

        
    def update(self):
        msg_in_thread = threading.Thread(target=self.message_in_loop)
        msg_in_thread.daemon = True
        msg_in_thread.start()

        msg_out_thread = threading.Thread(target=self.message_out_loop)
        msg_out_thread.daemon = True
        msg_out_thread.start()

        TeensyWebServer(self).start()


    def run_threaded(self, what):
        ''' 
        Return the last state given from the remote server.
        '''
        
        #return last returned last remote response.
        #return self.angle, self.throttle, self.mode, self.recording
        return 0, 0, 'user', False

    def message_in_loop(self):
        while True:
            line = self.serial_bus.readline().strip()

            with self.lock:
                if line.startswith(b'S'):
                    self.angle_pwm_in = int(line[1:])
                if line.startswith(b'T'):
                    self.throttle_pwm_in = int(line[1:])

                if self.mode == 'user':
                    self.angle_pwm_out = self.angle_pwm_in
                    self.throttle_pwm_out = self.throttle_pwm_in

    def message_out_loop(self):
        while True:
            with self.lock:
                angle_pwm = self.angle_pwm_out
                throttle_pwm = self.throttle_pwm_out

            a = 'S' + str(angle_pwm) + '\n'; 
            print("OUT: " + a)
            t = 'T' + str(throttle_pwm) + '\n'
            print("OUT: " + t)
            self.serial_bus.write(a.encode())
            self.serial_bus.write(t.encode())


class TeensyWebServer(tornado.web.Application):

    def __init__(self, controller):

        this_dir = os.path.dirname(os.path.realpath(__file__))
        self.static_file_path = os.path.join(this_dir, 'templates', 'static')
        
        self.angle = 0.0
        self.throttle = 0.0
        self.mode = 'user'
        self.recording = False

        handlers = [
            (r"/", tornado.web.RedirectHandler, dict(url="/drive")),
            (r"/drive", DriveHandler),
			(r"/api/drive", DriveApi, dict(controller=controller)),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": self.static_file_path}),
            ]

        settings = {'debug': True}

        super().__init__(handlers, **settings)

    def start(self, port=8887):
        print('Starting Donkey Server on part {0}...'.format(port))
        self.port = int(port)
        self.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def run_threaded(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording
        
    def run(self, img_arr=None):
        self.img_arr = img_arr
        return self.angle, self.throttle, self.mode, self.recording


class DriveHandler(tornado.web.RequestHandler):

    def get(self):
        data = {}
        self.render("templates/drive.html", **data)


class DriveApi(tornado.web.RequestHandler):

    def initialize(self, controller):
        self.controller = controller

    def respond_with_json(self):
        self.write(json.dumps({
            'max_throttle': str(self.controller.max_throttle),
            'recording': self.controller.recording,
            'drive_mode': self.controller.drive_mode
            }))

    def get(self):
        self.respond_with_json()

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        self.controller.drive_mode = data['drive_mode']
        self.controller.max_throttle = data['max_throttle']
        self.controller.recording = data['recording']
        self.respond_with_json()

