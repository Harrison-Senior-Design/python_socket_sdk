import zmq
import threading
import datetime

from google.protobuf.any_pb2 import Any
from google.protobuf.empty_pb2 import Empty
from google.protobuf.timestamp_pb2 import Timestamp

from ..core.protobuf_files.generated import main_pb2 as main_proto
from ..core.protobuf_files.generated import hardwareMessages_pb2 as hardware_proto
from ..core.protobuf_files.generated import simulationMessages_pb2 as simulation_proto

class Emitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event=None, listener=None):
        def wrapper(listener):
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(listener)
            
            return listener

        if listener:
            return wrapper(listener)
        
        return wrapper
        
    def emit(self, event_name, *args):
        if event_name not in self._listeners:
            return

        for listener in self._listeners[event_name]:
            listener(*args)

class Socket:
    SOCKET_TYPE = zmq.DEALER

    def __init__(self, address, identity):
        self.context = zmq.Context()
        self.address = address;
        self.emitter = Emitter()
        self.running = False
        self.thread = None
        self.identity = identity;

        self.socket = self.context.socket(Socket.SOCKET_TYPE)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.setsockopt(zmq.HEARTBEAT_IVL, 1000)  # 1000ms interval
        self.socket.setsockopt(zmq.HEARTBEAT_TIMEOUT, 3000)  # 3000ms timeout
        self.socket.setsockopt(zmq.HEARTBEAT_TTL, 1750)  # 1750ms ttl
        self.socket.setsockopt(zmq.RECONNECT_IVL, 5000)  # 5000ms reconnect interval
        self.socket.setsockopt(zmq.RECONNECT_IVL_MAX, 60000)  # 60000ms maximum reconnect interval
        self.socket.setsockopt_string(zmq.IDENTITY, identity)

        self.socket.connect(address)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def identify(self):
        print("Identifying")
        self.send_message(main_proto.OperationCode.IDENTIFY)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._receive)
        self.thread.start()

    def stop(self):
        self.running = False
        print("Shutting down recv thread (takes up to 1000ms)")
        self.thread.join()

    def cleanup(self):
        self.stop()
        self.poller.unregister(self.socket)

        print("Closing socket")
        self.socket.close()
        self.context.term()

    def _receive(self):
        while self.running:
            socks = dict(self.poller.poll(1000))

            if not self.running:
                return

            if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                self._recv_handle()

    def _recv_handle(self):
        multipart_msg = self.socket.recv_multipart()

        if len(multipart_msg) < 2:
            return

        message = multipart_msg[1]

        wrapper = main_proto.Wrapper()
        wrapper.ParseFromString(message)
        
        if wrapper.opcode == main_proto.OperationCode.ANGLE_DATA:
            payload = simulation_proto.AnglePayload()
            wrapper.payload.Unpack(payload)
            self.emitter.emit("angle", payload)
        elif wrapper.opcode == main_proto.OperationCode.MOVE_STARTING_LOCATION:
            payload = hardware_proto.MoveStarterLocationPayload()
            wrapper.payload.Unpack(payload)
            self.emitter.emit("move_starter_location", payload)
        else:
            self.emitter.emit("unknown_payload", wrapper)
    
    def send_message(self, opcode, payload=None):
        if payload is None:
            payload = Empty()

        timestamp = Timestamp()
        now = datetime.datetime.now()
        timestamp.FromDatetime(now)

        payload = Any(value=payload.SerializeToString())

        wrapper = main_proto.Wrapper(
            opcode=opcode,
            timestamp=timestamp,
            payload=payload
        )

        serialized_wrapper = wrapper.SerializeToString()
        self.socket.send_multipart([b'', serialized_wrapper])
        
