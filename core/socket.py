import zmq
from core.protobuf_files.generated import main_pb2, simulationMessages_pb2
from pyee import EventEmitter


class Socket:
    SOCKET_TYPE = zmq.ROUTER

    def __init__(self, addr):
        self.addr = addr
        self.emitter = EventEmitter()

        ctx = zmq.Context()
        self.socket = ctx.socket(Socket.SOCKET_TYPE)

    def connect(self):
        self.socket.bind(self.addr)

    async def recv_handler(self) -> main_pb2.Wrapper:
        data = self.socket.recv()

        wrapped_message = main_pb2.Wrapper()

        wrapped_message.ParseFromString(data)

        self.emitter.emit("message", wrapped_message)

        opcode = wrapped_message.opcode

        if opcode == main_pb2.OperationCode.ANGLE_DATA:
            payload = simulationMessages_pb2.AnglePayload()
            wrapped_message.payload.Unpack(payload)

            self.emitter.emit("angle", payload)
        elif opcode == main_pb2.OperationCode.MOVE_STARTING_LOCATION:
            payload = simulationMessages_pb2.AnglePayload()
            wrapped_message.payload.Unpack(payload)

            self.emitter.emit("move_starting_location", payload)
        else:
            self.emitter.emit("unknown_payload", wrapped_message)
