import zmq
import threading
import time

import core.protobuf_files.generated.main_pb2 as main_proto
import core.protobuf_files.generated.hardwareMessages_pb2 as hardware_proto
import core.protobuf_files.generated.simulationMessages_pb22 as simulation_proto

class Emitter:
    def __init__(self):
        self.listeners = {}
        
    def on(self, event, listener):
        if event not in self.listeners:
            self.listeners[event] = []
        self.listeners[event].append(listener)
        
    def emit(self, event_name, *args):
        if event_name not in self.handlers:
            return

        for handler in self.handlers[event_name]:
            handler(*args)

class Socket:
    SOCKET_TYPE = zmq.DEALER

    def __init__(self, address):
        self.context = zmq.Context()
        self.socket = self.context.socket(Socket.SOCKET_TYPE)
        self.socket.connect(address)
        self.emitter = EventEmitter()
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
        
