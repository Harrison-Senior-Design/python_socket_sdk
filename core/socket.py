import zmq

class Socket:
    def __init__(self, addr):
        self.addr = addr

        ctx = zmq.Context()
        self.socket = ctx.socket(zmq.PULL)

    def connect(self):
        self.socket.bind(self.addr)

    def recv(self):
        return self.socket.recv()
