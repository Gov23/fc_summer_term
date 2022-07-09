import threading

import zmq

class Server(object):
    ''' Front facing server. '''

    def __init__(self):
        self.zmq_context = zmq.Context()

    def start(self):
        ''' Main execution. 
            Instantiate workers, Accept client connections, 
            distribute computation requests among workers and route computed results back to clients. '''

        # Front facing socket to accept client connections.
        socket_front = self.zmq_context.socket(zmq.ROUTER)
        socket_front.bind('tcp://*:5001')

        # Backend socket to distribute work.
        socket_back = self.zmq_context.socket(zmq.DEALER)
        socket_back.bind('inproc://backend')

        # Start three workers.
        for i in range(1,3):
            worker = Worker(self.zmq_context, i)
            worker.start()

        # Use built in queue device to distribute requests among workers.
        # What queue device does internally is,
        #   1. Read a client's socket ID and request.
        #   2. Send socket ID and request to a worker.
        #   3. Read a client's socket ID and result from a worker.
        #   4. Route result back to the client using socket ID. 
        zmq.device(zmq.QUEUE, socket_front, socket_back)

class Worker(threading.Thread):
    ''' Workers accept computation requests from front facing server.
        Does computations and return results back to server. '''

    def __init__(self, zmq_context, _id):
        threading.Thread.__init__(self)
        self.zmq_context = zmq_context
        self.worker_id = _id
        print('this is id')
        print(self.worker_id)
        print(type(self.worker_id))

    def run(self):
        ''' Main execution. '''
        # Socket to communicate with front facing server.
        socket = self.zmq_context.socket(zmq.DEALER)
        socket.connect('inproc://backend')

        while True:
            # First string recieved is socket ID of client
            client_id = socket.recv()
            _ci = client_id.decode('utf-8')
            request_ = socket.recv().decode('utf-8')
            uid, request = request_.split(';')[0], request_.split(';')[1]

            # print(f'this is client id {_ci}')

            if _ci == '1':
                print('Worker ID - %s has detected %s.' % (self.worker_id, request))
                if request == 'No Mask':
                    result = "Please wear a mask"
                else:
                    result = "Welcome"
            else:
                print('Worker ID - %s. Received CO2 level of %s.' % (self.worker_id, request))
                result = 'Open' if int(request) > 750 else 'Close'

            # For successful routing of result to correct client, the socket ID of client should be sent first.
            socket.send(client_id, zmq.SNDMORE)
            socket.send_string(f'{uid};{result}')

if __name__ == '__main__':
    server = Server().start()