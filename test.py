from core.socket import Socket

socket = Socket("tcp://127.0.0.1:5556")

@socket.emitter.on("angle")
def handle_angle_payload(payload):
    print(f"angle handler: {payload.angle}")

def main():
    print(f"Connecting to {socket.address} with type {socket.SOCKET_TYPE}")

    # Start the receiver thread
    socket.start()
    
if __name__ == '__main__':
    main()
