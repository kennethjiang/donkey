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
    
    def __init__(self,
            steering_left_pwm=1000,
            steering_neutral_pwm=1500,
            steering_right_pwm=2000,
            throttle_forward_pwm=1000,
            throttle_stopped_pwm=1500,
            throttle_reverse_pwm=2000
            ):

        self.steering_left_pwm=steering_left_pwm
        self.steering_neutral_pwm=steering_neutral_pwm
        self.steering_right_pwm=steering_right_pwm
        self.throttle_forward_pwm=throttle_forward_pwm
        self.throttle_stopped_pwm=throttle_stopped_pwm
        self.throttle_reverse_pwm=throttle_reverse_pwm

        self.lock = threading.RLock()
        #self.serial_bus = serial.Serial('/dev/ttyACM0', 115200, timeout = 0.05)

        self.steering_pwm_in = self.steering_neutral_pwm
        self.throttle_pwm_in = self.throttle_stopped_pwm
        self.max_throttle = 0.25
        self.drive_mode = 'user'
        self.recording = False

		#Critical sections that should be guarded by lock
        with self.lock:
            self.steering_pwm_out = self.steering_neutral_pwm
            self.throttle_pwm_out = self.throttle_stopped_pwm

    def set_angle(self, angle):
        if self.drive_mode == 'user':  # Ignore predicted value when in user mode
            return;

        with self.lock:
            self.steering_pwm_out = self.angle_to_pwm(angle)

    def angle_to_pwm(self, angle):
        if angle >= 0:
            return utils.map_range(angle, 0, 1, self.steering_neutral_pwm, self.steering_right_pwm)
        else:
            return utils.map_range(angle, 0, -1, self.steering_neutral_pwm, self.steering_left_pwm)

    def pwm_to_value(self, pwm, pwm_min, pwm_neutral, pwm_max):
        if (pwm-pwm_neutral) * (pwm_min-pwm_neutral) > 0: #pwm is between min and neutral
            return utils.map_range(pwm, pwm_neutral, pwm_min, 0, -1)
        else:
            return utils.map_range(pwm, pwm_neutral, pwm_max, 0, 1)

    def update(self):
        msg_in_thread = threading.Thread(target=self.message_in_loop)
        msg_in_thread.daemon = True
        msg_in_thread.start()

        msg_out_thread = threading.Thread(target=self.message_out_loop)
        msg_out_thread.daemon = True
        msg_out_thread.start()

        TeensyWebServer(self).start()


    def run_threaded(self, img_in):
        with self.lock:
            steering = self.pwm_to_value(self.steering_pwm_out, self.steering_left_pwm, self.steering_neutral_pwm, self.steering_right_pwm)
            throttle = self.pwm_to_value(self.throttle_pwm_out, self.throttle_reverse_pwm, self.throttle_stopped_pwm, self.throttle_forward_pwm)

        return steering, throttle, self.drive_mode, self.recording

    def message_in_loop(self):
        while True:
            line = self.serial_bus.readline().strip()

            if line.startswith(b'S'):
                self.steering_pwm_in = int(line[1:])
            if line.startswith(b'T'):
                self.throttle_pwm_in = int(line[1:])

            with self.lock:
                throttle_pwm_cap = utils.map_range(self.max_throttle, 0, 1, self.throttle_stopped_pwm, self.throttle_forward_pwm)
                self.throttle_pwm_out = max(self.throttle_pwm_in, throttle_pwm_cap)
                if self.mode == 'user':
                    self.steering_pwm_out = self.steering_pwm_in

    def message_out_loop(self):
        while True:
            with self.lock:
                steering_pwm = self.steering_pwm_out
                throttle_pwm = self.throttle_pwm_out

            a = 'S' + str(steering_pwm) + '\n'; 
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

