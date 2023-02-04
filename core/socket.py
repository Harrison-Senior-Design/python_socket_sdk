import zmq
import threading
import time

import core.protobuf_files.generated.main_pb2 as main_proto
import core.protobuf_files.generated.hardwareMessages_pb2 as hardware_proto
import core.protobuf_files.generated.simulationMessages_pb2 as simulation_proto

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

    def __init__(self, address):
        self.context = zmq.Context()
        self.socket = self.context.socket(Socket.SOCKET_TYPE)
        self.address = address;
        self.socket.connect(address)
        self.emitter = Emitter()
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._receive)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _receive(self):
        while self.running:
            msg = self.socket.recv_multipart()

            if len(msg) < 2:
                continue
            identity, message = msg[0], msg[1:]

            wrapper = main_proto.Wrapper()
            wrapper.ParseFromString(message[0])
            
            if wrapper.opcode == main_proto.OperationCode.ANGLE_DATA:
                payload = simulation_proto.AnglePayload()
                wrapper.payload.Unpack(payload)
                self.emitter.emit("angle", payload)
            elif wrapper.opcode == main_proto.OperationCode.MOVE_STARTING_LOCATION:
                payload = hardware_proto.MoveStarterLocationPayload()
                wrapper.payload.Unpack(payload)
                self.emitter.emit("move_starter_location", payload)
            else:
                self.emitter.emit("unknown_payload", wrapped_message)
    
    def send_message(self, opcode, payload):
        wrapper = Main.Wrapper(
            opcode=opcode,
            timestamp=0,
            payload=Any(value=payload.SerializeToString())
        )

        self.socket.send_multipart(wrapper.SerializeToString())
        
