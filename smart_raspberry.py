#!/usr/bin/env python
import socket
import sys
import threading
import random
import os
import time
import struct
import serial


import cv
import cv2
import Image, StringIO
import numpy as np


from voice_engine.source import Source
from voice_engine.channel_picker import ChannelPicker
from voice_engine.doa_respeaker_4mic_array import DOA
from pixels import pixels

import datetime



port_serial="/dev/ttyACM0"
sl = serial.Serial(port_serial,9600)

HOST = "0.0.0.0"
PORT = 9004
SOCK_ADDR = (HOST, PORT)
exit_now = 0
distance = 0

moving = False
last_movement_timestamp = datetime.datetime.now()
doa_valid = True


def exit_signal_handle(sig,stack_frame):
    global exit_now
    print "EXIT sig"
    exit_now = 1

class serial_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        self.running = True
        while self.running:
            try:
                global distance
                data=sl.readline()
                #print "^^^^^^"
                #print data
                tmp = data.split("\r\n")[0]
                if (":" in tmp ) and (";" in tmp):
                    distance_str = (tmp.split(":")[1]).split(";")[0]
                    distance =  float(distance_str.decode("utf-8"))
                #print str(distance)
                #print "vvvvvv"
            except:
                print sys.exc_info()

    def stop(self):
        self.running = False

class doa_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        global moving,last_movement_timestamp,doa_valid
        src = Source(rate=16000, channels=4, frames_size=320)
        #ch1 = ChannelPicker(channels=4, pick=1)
        doa = DOA(rate=16000)
        #src.link(ch1)
        src.link(doa)
        src.recursive_start()



        self.running = True
        while self.running:
            try:
                time.sleep(1)
                current_timestamp = datetime.datetime.now()
                if doa_valid == True and ((current_timestamp - last_movement_timestamp).seconds > 2):
                    position, amplitute = doa.get_direction()
                    if amplitute > 2000:
                        pixels.wakeup(position)
                        print amplitute,position
                        if position > 0  and position < 180:
                            pivot_right()
                            time.sleep(position/200)
                            stop()
                        elif position >= 180 and position < 360:
                            pivot_left()
                            position = 360 - position
                            time.sleep(position/200)
                            stop()
                        time.sleep(2)
                    else:
                        pixels.speak()
                else:
                    pixels.think()
            except:
                print sys.exc_info()
         
        src.recursive_stop()

    def stop(self):
        self.running = False

class movement_thread(threading.Thread):
    def __init__(self, movement_type, quantity):
        threading.Thread.__init__(self)
        self.movement_type = movement_type
        self.quantity = quantity
    def run(self):
        global moving, last_movement_timestamp
        
        current_timestamp = datetime.datetime.now()
        if (current_timestamp - last_movement_timestamp).seconds > 0.5:
            moving = True
            if self.movement_type == 1:
                forward()
                time.sleep(self.quantity/200)
                stop()
            elif self.movement_type == 2:
                reverse()
                time.sleep(self.quantity/200)
                stop()
            elif self.movement_type == 3:
                pivot_left()
                time.sleep(self.quantity/200)
                stop()
            elif self.movement_type == 4:
                pivot_right()
                time.sleep(self.quantity/200)
                stop()
            moving = False
            last_movement_timestamp = datetime.datetime.now()
            
    




def forward():
    string="1"
    sl.write(string)

def reverse():
    string="2"
    sl.write(string)

def pivot_left():
    string="3"
    sl.write(string)

def pivot_right():
    string="4"
    sl.write(string)

def measure():
    string="6"
    sl.write(string)

def stop():
    string="0"
    sl.write(string)



def main():
    global moving,last_movement_timestamp,doa_valid,distance
    doa_th = doa_thread()
    doa_th.start()
    ser_th = serial_thread()
    ser_th.start()


    cap=cv2.VideoCapture(0)
    ret=cap.set(3,640)
    ret=cap.set(4,480)
    #resize = 2

    avg = None

    while exit_now == 0:
        ret, frame = cap.read()
        frame = cv2.resize(frame,None,fx=float(0.5),fy=float(0.5),interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame,-1)


        hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100,50,50])
        upper_blue = np.array([140,255,255])
        mask = cv2.inRange(hsv,lower_blue,upper_blue)
        
        if avg is None:
            avg = mask.copy().astype("float")
            continue

        cv2.accumulateWeighted(mask,avg,0.5)
        
        thresh = cv2.threshold(mask,25,255,cv2.THRESH_BINARY)[1]
        kernel = np.ones((4,4),np.uint8)
        thresh = cv2.erode(thresh,kernel, iterations = 1)
        kernel = np.ones((13,13),np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations = 1)
        
        (cnts,_) = cv2.findContours(thresh.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        rect_max = (0,0,0,0)
        for c in cnts:
            if cv2.contourArea(c) < 3000:
                continue
            
            if cv2.contourArea(c) > max_area:
                max_area = cv2.contourArea(c)
                rect_max = cv2.boundingRect(c)

        



        
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        #gray = cv2.equalizeHist(gray)

        if max_area !=0:
            doa_valid = False
            (x,y,w,h) = rect_max
            #cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
            x1 = x
            y1 = y
            x2 = x+w
            y2 = y+h

            

            x_mid = float((x1+x2)/2)
            y_mid = float((y1+y2)/2)

            print "cam middle x y", x_mid,y_mid
            if x_mid > (160 + 30) and np.abs(x2-x1) < 150 :
                print "cam detected on right turn right"
                mt = movement_thread(4,(np.abs(x_mid-160))/10)
                mt.start()       
            elif x_mid < (160 - 30) and np.abs(x2-x1) < 150 :
                print "cam detected on left turn left"
                mt = movement_thread(3,(np.abs(x_mid-160))/10)
                mt.start()
            else:
                print "DB for cam"
                #measure()                
                #if distance > 450:
                    #print "not detected by sonar"
                    #mt = movement_thread(1,np.abs(80))
                    #mt.start()
                #else:
                if distance < 450:
                    #print "target detected by sonar:",str(distance)                    
                    if distance > 50:
                        print "too far, move forward"
                        mt = movement_thread(1,np.abs(distance-50)*1)
                        mt.start()
                    elif distance < 30:
                        print "too close, move backward"
                        mt = movement_thread(2,np.abs(distance-50)*1)
                        mt.start()
                    else:
                        print "DB for sonar"
                
                    
              
                

        else:
            doa_valid = True
         
        
        
    doa_th.stop()
    doa_th.join()
    ser_th.stop()
    ser_th.join()


if __name__ == "__main__":
    main()


