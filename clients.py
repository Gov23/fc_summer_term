''' zeromq client example.
    Three clients are instantiated.
    Each client would generate a pair of numbers and send them to a server to be computed. 
    The computation is adding the two numbers together.
    Once the computed result is recieved from the server it would be printed to standard out. 
    Demonstrables:
        Multiple clients connecting to same server.
        Clients receiving correct response. '''

# Author - Kasun Herath <kasunh01 at gmail.com>
# Source - https://github.com/kasun/zeromq-client-server.git

import threading
from random import choice
import datetime
import zmq

class Client(threading.Thread):
    ''' Represents an example client. '''
    def __init__(self, identity):
        threading.Thread.__init__(self)
        self.identity = identity

    def run(self):
        ''' Connects to server. Send compute request, poll for and print result to standard out. '''
        socket = self.get_connection()
        poller = zmq.Poller()
        poller.register(socket,zmq.POLLIN)
        #Send new data from client
        while True:
            #air quality sensor
            if self.identity == "1":
                self.send(socket, "Init from client")
                current = datetime.datetime.now()
                print("Waiting for response from server as client "+ self.identity)
                sockets = poller.poll(1000)
                if socket in sockets and sockets[socket] == zmq.POLLIN:
                    reply = socket.recv()
            #camera data
            else:
                self.send(socket, "Init from client")
                current = datetime.datetime.now()
                print("Waiting for response from server as client "+ self.identity)
                sockets = poller.poll(1000)
                if socket in sockets and sockets[socket] == zmq.POLLIN:
                    reply = socket.recv()
      

    def send(self, socket, data):
        ''' Send data through provided socket. '''
        print(data)
        socket.send_string(data)

    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()
        
    def receive(self, socket):
        ''' Recieve and return data through provided socket. '''
        return socket.recv()

    def get_connection(self):
        ''' Create a zeromq socket of type DEALER; set it's identity, connect to server and return socket. '''

        # Socket type DEALER is used in asynchronous request/reply patterns.
        # It prepends identity of the socket with each message.
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.identity)
        socket.connect("tcp://localhost:5591")
        return socket

if __name__ == '__main__':
    # Instantiate three clients with different ID's.
    for i in range(1,3):
        client = Client(str(i))
        client.start()