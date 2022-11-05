from core.socket import Socket

def main():
	socket = Socket("tcp://127.0.0.1:5556")

	print(f"Connecting to {socket.addr}")
	socket.connect()

	while True:
		print("Waiting for message")
		message = socket.socket.recv()
		print("message received: " + str(message))

if __name__ == "__main__":
	main()
