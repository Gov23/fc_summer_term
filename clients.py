import threading
import socket
import time
import zmq
import imutils
import cv2
import os

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream

from random import choice
from datetime import datetime

from detect_mask_video import videostream, detect_and_predict_mask

def isConnected(host, port, timeout_second=1):
    # test connectivity
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_second)
    result = sock.connect_ex((host, int(port)))
    if result == 0:
        return True
    else:
        return False

class Client(threading.Thread):
    ''' Represents an example client. '''
    def __init__(self, identity, ip='localhost', port=5001):
        threading.Thread.__init__(self)
        self.identity = identity
        self.ip = ip
        self.port = port
        self.zmq_context = zmq.Context()

    def run(self):
        ''' Connects to server. Send compute request, poll for and print result to standard out. '''
        # num1, num2 = self.generate_numbers()
        # print('Client ID - %s. Numbers to be added - %s and %s.' % (self.identity, num1, num2))
        socket = self.get_connection()
        
        # Poller is used to check for availability of data before reading from a socket.
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        # self.send(socket, '%s:%s' % (num1, num2))

        # Infinitely poll for the result. 
        # Polling is used to check for sockets with data before reading because socket.recv() is blocking.
        count = 0
        while True:
            # Poll for 5 seconds. Return any sockets with data to be read.
            count+=1
            # air quality sensor
            if self.identity == '1':
                print("inside id 1")
                
                # grab the frame from the threaded video stream and resize it
                # to have a maximum width of 400 pixels

                frame = vs.read()
                frame = imutils.resize(frame, width=400)

                isMask = "No Mask"

                # detect faces in the frame and determine if they are wearing a
                # face mask or not
                (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

                # loop over the detected face locations and their corresponding
                # locations
                for (box, pred) in zip(locs, preds):
                    # unpack the bounding box and predictions
                    (startX, startY, endX, endY) = box
                    (mask, withoutMask) = pred

                    # determine the class label and color we'll use to draw
                    # the bounding box and text
                    isMask = "Mask" if mask > withoutMask else "No Mask"
                    color = (0, 255, 0) if isMask == "Mask" else (0, 0, 255)

                    # include the probability in the label
                    label = "{}: {:.2f}%".format(isMask, max(mask, withoutMask) * 100)

                    # display the label and bounding box rectangle on the output
                    # frame
                    cv2.putText(frame, label, (startX, startY - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                    cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

                # show the output frame
                self.send(socket, isMask)
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break
                
        

            # camera
            elif self.identity == '2':
                print("inside id 2")
                num1, num2 = self.generate_numbers()
                self.send(socket, '%s:%s' % (num1, num2))


            sockets = dict(poller.poll(5000))
            # If socket has data to be read.
            if socket in sockets and sockets[socket] == zmq.POLLIN:
                result = self.receive(socket)
                if self.identity == '1':
                    print('Client ID - %s. Recieved Time is %s' % (self.identity, result))
                else:
                    print('Client ID - %s. Received result - %s.' % (self.identity, result))
            #     break

            # if count>5:
            #     break

        cv2.destroyAllWindows()
        vs.stop()    
        socket.close()
        self.zmq_context.term()

    def send(self, socket, data):
        ''' Send data through provided socket. '''
        socket.send_string(data)

    def receive(self, socket):
        ''' Recieve and return data through provided socket. '''
        return socket.recv()

    def get_connection(self):
        ''' Create a zeromq socket of type DEALER; set it's identity, connect to server and return socket. '''

        # Socket type DEALER is used in asynchronous request/reply patterns.
        # It prepends identity of the socket with each message.
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(f'tcp://{self.ip}:{self.port}')
        return socket

    def generate_numbers(self):
        ''' Generate and return a pair of numbers. '''
        number_list = range(0,10)
        num1 = choice(number_list)
        num2 = choice(number_list)
        return num1, num2

if __name__ == '__main__':
    # Instantiate three clients with different ID's.
    ip = '34.159.53.31'
    ip2 = '35.207.94.238'
    vs, faceNet, maskNet = videostream()
    vs = vs.start()
    time.sleep(2)

    # for i in range(1,2):
    #     client = Client(str(i))
    #     # client = Client(str(i), ip=ip2)
    #     client.start()