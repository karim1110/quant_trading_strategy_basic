import socket
import json

def tcp_client(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
        print(f"Connected to {host}:{port}")
        while True:
            data = sock.recv(1024).decode()
            if not data:
                print("Server closed the connection")
                break
            try:
                message = json.loads(data)
                print("Received:", message)
            except json.JSONDecodeError:
                print("Invalid JSON:", data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
        print("Connection closed")

if __name__ == "__main__":
    tcp_client("127.0.0.1", 8080)


# python3 tcp_client.py