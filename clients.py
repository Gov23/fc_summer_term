import threading
import socket
import time
import zmq
import imutils
import cv2
import os
import json

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream

from random import choice
from datetime import datetime, timedelta

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

def get_co2value(sec):
    return co2[sec]

class Client(threading.Thread):
    ''' Represents an example client. '''
    def __init__(self, identity, ip='localhost', port=5001, timeout=10):
        threading.Thread.__init__(self)
        self.identity = identity
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.zmq_context = zmq.Context()
        
        '''
        messages in queue are for reliability checking
        is a list of dictionaries containing keys
        1. uid: a unique id of the certain message
        2. body: the content of the message
        3. isAcked: whether the messages is acked or not
        4. timestamp: the time when the message was sent
        '''
        self.queue = []

    def run(self):
        ''' Connects to server. Send compute request, poll for and print result to standard out. '''

        socket = self.get_connection()
        
        # Poller is used to check for availability of data before reading from a socket.
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        # Infinitely poll for the result. 
        # Polling is used to check for sockets with data before reading because socket.recv() is blocking.
        uid = 0
        while True:

            if not isConnected(self.ip, self.port):
                time.sleep(10)

            if self.msginQueue():
                for msg in self.queue:
                    try:
                        if msg["timestamp"]+timedelta(0,self.timeout) >= datetime.now() and not msg["isAckd"]:
                            print("msg sent from queue")
                            self.send(socket, f'{msg["uid"]};{msg["body"]}')
                    except:
                        break
                    
            # don't need to run calculation constantly
            time.sleep(2)
            
            # air quality sensor
            if self.identity == '1':
                
                print("Camera")
                
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
                print(f"send message with uid:{uid}")
                self.send(socket, f"{uid};{isMask}")
                self.queue.append({
                    "uid":uid, 
                    "timestamp": datetime.now(),
                    "body": isMask,
                    "isAcked": False
                    })
                cv2.imshow("Frame", frame)
                key = cv2.waitKey(1) & 0xFF
                # if the `q` key was pressed, break from the loop
                if key == ord("q"):
                    break

            # air quality sensor
            elif self.identity == '2':
                print("Air Quality")
                #idea:
                #have a starting value of 750, have it increase by 10 or 20 every second
                #once it reaches 850, we start air conditioning, which then decreases number 
                #once it goes down to 600, stop air conditioning to save electricity
                #goes back up
                co2 = get_co2value(datetime.now().second)
                self.send(socket, f'{uid};{co2}')
                self.queue.append({
                    "uid":uid, 
                    "timestamp": datetime.now(),
                    "body": co2,
                    "isAcked": False
                    })
            #door opener
            elif self.identity == '3':
                print("Door")
                continue
            #air conditioning unit
            elif self.identity == '4':
                print("Air Conditioning")
                continue

            sockets = dict(poller.poll(1000))
            # If socket has data to be read.
            if socket in sockets and sockets[socket] == zmq.POLLIN:
                result_ = self.receive(socket).decode('utf-8')
                uuid, result = result_.split(';')[0], result_.split(';')[1]
                for i, msg in enumerate(self.queue):
                    if msg["uid"] == uuid:
                        self.queue.pop(i)
                        
                if self.identity == '1':
                    print('Client ID - %s. Recieved Time is %s' % (self.identity, result))
                else:
                    print('Client ID - %s. Received result: We should %s the air Conditioner.' % (self.identity, result))
            #     break
            uid += 1

        cv2.destroyAllWindows()
        vs.stop()    
        socket.close()
        self.zmq_context.term()

    def msginQueue(self):
        if len(self.queue) != 0:
            return True
        return False

    def send(self, socket, data):
        ''' Send data through provided socket. '''
        socket.send_string(data)

    def receive(self, socket):
        ''' Recieve and return data through provided socket. '''
        return socket.recv()

    def get_connection(self):
        ''' 
            Create a zeromq socket of type DEALER; 
            set it's identity, connect to server and return socket.
        '''
        # Socket type DEALER is used in asynchronous request/reply patterns.
        # It prepends identity of the socket with each message.
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect(f'tcp://{self.ip}:{self.port}')
        return socket

if __name__ == '__main__':
    # Instantiate three clients with different ID's.
    vs, faceNet, maskNet = videostream()
    vs = vs.start()
    time.sleep(2)
    f = open('config.json')
    data = json.load(f)
    ip = data["ip_local"]
    ip2 = data["ip_cloud"]
    port = data["port"]

    with open("co2.txt") as f:
        co2 = f.readline()
    co2 = co2.split(', ')

    for client in data['clients']:
        print(client['id'])
        client = Client(client['id'], ip, port)
        client.start()
    f.close()