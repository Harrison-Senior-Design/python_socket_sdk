from core.socket import Socket
import asyncio

socket = Socket("tcp://127.0.0.1:5556")


@socket.emitter.on("angle")
def handle_angle_payload(payload):
    print(f"angle handler: {payload.angle}")


async def main():
    print(f"Connecting to {socket.addr} with type {socket.SOCKET_TYPE}")
    socket.connect()

    while True:
        await socket.recv_handler()


if __name__ == '__main__':
    asyncio.run(main())
