import threading

from random import choice
from datetime import datetime

import zmq

class Client(threading.Thread):
    ''' Represents an example client. '''
    def __init__(self, identity, ip):
        threading.Thread.__init__(self)
        self.identity = identity
        self.ip = ip
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
                current = datetime.now()
                dt = current.strftime("%m/%d/%Y %H:%M:%S")
                self.send(socket, dt)
            
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
                break

            if count>5:
                break

                
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
        socket.connect(f'tcp://{self.ip}:5001')
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
    for i in range(1,3):
        client = Client(str(i), ip=ip)
        client.start()