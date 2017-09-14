#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from io import StringIO
from bluetooth import *


class BluetoothController:

    # The service UUID to advertise
    bt_uuid = "00001101-0000-1000-8000-00805F9B34FB"
    BT_SERVICE_NAME = "DonkeyRider"

    def __init__(self):
        self.angle = 0.
        self.throttle = 0.
        self.mode = 'user'
        self.recording = 'false'

    def update(self):

        # We need to wait until Bluetooth init is done
        time.sleep(5)

        # Make device visible
        print('Starting Donkey Bluetooth Server...')
        os.system("hciconfig hci0 piscan")

        # Create a new server socket using RFCOMM protocol
        server_sock = BluetoothSocket(RFCOMM)
        # Bind to any port
        server_sock.bind(("", PORT_ANY))
        # Start listening
        server_sock.listen(1)

        # Get the port the server socket is listening
        port = server_sock.getsockname()[1]

        # Start advertising the service
        advertise_service(server_sock, 
                           BluetoothController.BT_SERVICE_NAME,
                           service_id=BluetoothController.bt_uuid,
                           service_classes=[BluetoothController.bt_uuid, SERIAL_PORT_CLASS],
                           profiles=[SERIAL_PORT_PROFILE])

        while True:
            print("Waiting for connection on RFCOMM channel %d" % port)
            try:
                client_sock = None

                # This will block until we get a new connection
                client_sock, client_info = server_sock.accept()
                print("Connected from ", client_info)

                while True:
                    # Read the data sent by the client
                    data = client_sock.recv(1024)
                    #import pdb; pdb.set_trace()
                    buf = StringIO(data.decode('utf-8'))
                    (self.angle, self.throttle, self.mode, self.recording) = buf.readline().strip().split(',')

            except IOError:
                pass

            except KeyboardInterrupt:

                if client_sock is not None:
                    client_sock.close()

                server_sock.close()

                print("Server going down")
                break


    def run_threaded(self, img_arr=None):
        print("{0}, {1}, {2}, {3}".format(self.angle, self.throttle, self.mode, self.recording))
        return float(self.angle), float(self.throttle), self.mode, self.recording.lower() == 'true'