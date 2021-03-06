#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 20:35:17 2017

@author: krishna
"""

import numpy as np
import cv2
import socket
import time
import math






class DistanceToCamera(object):

    def __init__(self):
        # camera params
        self.alpha = 8.0 * math.pi / 180
        self.v0 = 119.865631204
        self.ay = 332.262498472

    def calculate(self, v, h,x_shift,y_shift, image):
        # compute and return the distance from the target point to the camera
        d = h*5 / math.tan(self.alpha + math.atan((v - self.v0) / self.ay))
        if d > 0:
            cv2.putText(image, "%.1fcm" % d,
                ( x_shift,y_shift), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return d

class CollectTrainingData(object):
    
    def __init__(self):

        self.server_socket = socket.socket()
        self.server_socket.bind(('192.168.43.204', 3000))
        print("server started")
        self.server_socket.listen(0)

        # accept a single connection
        self.connection = self.server_socket.accept()[0].makefile('rb')
        print("connected with client")
        self.send_inst = True

        self.collect_image()



    def collect_image(self):

        # collect images for training
        print ('Start collecting images...')
        # h1: stop sign
        h1 = 15.5 - 10  # cm
        # h2: traffic light
        h2 = 15.5 - 10

        # light_cascade = cv2.CascadeClassifier('xml/traffic_light.xml')

        r = 0
        d_to_camera = DistanceToCamera()
        print(d_to_camera)
        try:
#            start=time.time()
            stream_bytes = ' '
            frame = 1
            stream_bytes=stream_bytes.encode('utf-8')

            print(type(stream_bytes))
            time.sleep(5)
            while self.send_inst:
                stream_bytes += self.connection.read(1024)
                #print(stream_bytes)
                first = stream_bytes.find(b'\xff\xd8')
                last = stream_bytes.find(b'\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last + 2]
#                    print(jpg)
                    stream_bytes = stream_bytes[last + 2:]
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),1)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

                    # .......detection of stop sign
                    cascade_classifier = cv2.CascadeClassifier("xml/stop_sign.xml")

                    cascade_obj = cascade_classifier.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(30, 30),
                        flags=0
                    )

                    # draw a rectangle around the objects
                    for (x_pos, y_pos, width, height) in cascade_obj:
                        cv2.rectangle(image, (x_pos + 5, y_pos + 5), (x_pos + width - 5, y_pos + height - 5),
                                      (255, 255, 255), 2)
                        v = y_pos + height - 5

                        # print(x_pos+5, y_pos+5, x_pos+width-5, y_pos+height-5, width, height)

                        # stop sign
                        if width / height == 1:
                            cv2.putText(image, 'STOP', (x_pos, y_pos - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),
                                        2)
                            d_to_camera.calculate(v, h1, x_pos + 100, y_pos - 10, image)
                            print("stop")
                            r = 1
                        else:
                            r = 0

                            # .....detectio of traffic light......#

                    #hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

                    # ....Green color....#
                    lower_green = np.array([45, 50, 60])
                    upper_green = np.array([75, 255, 255])

                    mask_green = cv2.inRange(hsv, lower_green, upper_green)
                    mask_green = cv2.erode(mask_green, None, iterations=6)
                    mask_green = cv2.dilate(mask_green, None, iterations=6)

                    # ....yellow color.....#
                    lower_yellow = np.array([20, 100, 100])
                    upper_yellow = np.array([35, 255, 255])

                    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
                    mask_yellow = cv2.erode(mask_yellow, None, iterations=4)
                    mask_yellow = cv2.dilate(mask_yellow, None, iterations=4)

                    #  For red.....#
                    lower_red = np.array([100, 65, 65])
                    upper_red = np.array([180, 255, 255])

                    mask_red = cv2.inRange(hsv, lower_red, upper_red)
                    mask_red = cv2.erode(mask_red, None, iterations=6)
                    mask_red = cv2.dilate(mask_red, None, iterations=6)

                    '''for (x_pos, y_pos, width, height) in :
                        cv2.rectangle(image, (x_pos+5, y_pos+5), (x_pos+width-5, y_pos+height-5), (255, 255, 255), 2)
                        v = y_pos + height - 5'''

                    # ...contour for green....#
                    _, contours, hierarchy = cv2.findContours(mask_green.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in contours:
                        bx, by, bw, bh = cv2.boundingRect(cnt)
                        im = cv2.rectangle(image, (bx, by), (bx + bw, by + bh), (0, 0, 0), 3)
                        cv2.putText(im, 'green', (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                        print("Green light")
                    # ..contour for red...#
                    if r == 0:
                        _, contours1, hierarchy1 = cv2.findContours(mask_red.copy(), cv2.RETR_TREE,
                                                                    cv2.CHAIN_APPROX_SIMPLE)
                        for cnt in contours1:
                            bx, by, bw, bh = cv2.boundingRect(cnt)
                            v = by + bh - 5
                            im = cv2.rectangle(image, (bx, by), (bx + bw, by + bh), (0, 0, 0), 3)
                            cv2.putText(im, 'red', (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                                        cv2.LINE_AA)
                            d_to_camera.calculate(v, h2, bx + 20, by + 20, im)
                            print("Red light")
                    else:
                        r = 0


                        # .....contours for yellow...#
                    _, contours2, hierarchy2 = cv2.findContours(mask_yellow.copy(), cv2.RETR_TREE,
                                                                cv2.CHAIN_APPROX_SIMPLE)
                    for cnt in contours2:
                        bx, by, bw, bh = cv2.boundingRect(cnt)
                        im = cv2.rectangle(image, (bx, by), (bx + bw, by + bh), (0, 0, 0), 3)
                        cv2.putText(im, 'Yellow', (bx, by), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2,
                                    cv2.LINE_AA)
                        print("Yellow light")

                    cv2.imshow('image', image)

                    if cv2.waitKey(1) & 0xff==ord('q'):
                        break

        finally:
            self.connection.close()
            self.server_socket.close()

if __name__ == '__main__':
    CollectTrainingData()