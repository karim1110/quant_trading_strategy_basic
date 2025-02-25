#!/usr/bin/env python3
import socket
import threading
import csv
import json
import argparse
import sys
import time
import datetime

def handle_csv_client(client, files, interval):
    """
    Streams CSV data to the connected client.
    Each row is sent as a JSON message with a timestamp.
    """
    csv_data = []
    # Read all CSV files and accumulate rows
    for f in files:
        try:
            with open(f, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    csv_data.append(row)
        except Exception as e:
            print(f"Error reading file {f}: {e}")
    # Stream each row to the client
    for row in csv_data:
        # Optionally add a timestamp or other processing here
        row['date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            client.send((json.dumps(row) + "\n").encode("utf-8"))
            time.sleep(interval)
        except Exception as e:
            print(f"Error sending to CSV client: {e}")
            break
    client.close()

def csv_stream_server(host, port, files, interval):
    """
    Listens for incoming CSV stream clients.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    print(f"CSV Stream Server listening on {host}:{port}")
    while True:
        client, addr = s.accept()
        print(f"CSV Client connected from {addr}")
        threading.Thread(target=handle_csv_client, args=(client, files, interval)).start()

def handle_order_client(client):
    """
    Receives order messages from a client.
    Expects newline-delimited JSON messages.
    """
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode("utf-8")
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    order = json.loads(line.strip())
                    print("Received order:", order)
                    # Here you could add further processing for the order.
                except json.JSONDecodeError:
                    print("Received invalid JSON order:", line)
        except Exception as e:
            print(f"Error receiving order: {e}")
            break
    client.close()

def order_server(host, port):
    """
    Listens for incoming order connections.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    print(f"Order Server listening on {host}:{port}")
    while True:
        client, addr = s.accept()
        print(f"Order Client connected from {addr}")
        threading.Thread(target=handle_order_client, args=(client,)).start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage='Usage: unified_server.py --csv-port PORT --order-port PORT --files file1.csv file2.csv [--interval seconds]')
    parser.add_argument("--csv-port", type=int, default=9995, help="Port for CSV streaming")
    parser.add_argument("--order-port", type=int, default=9999, help="Port for receiving orders")
    parser.add_argument("--files", nargs='+', required=True, help="CSV file(s) to stream")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--interval", type=int, default=0.1, help="Time interval between messages")
    args = parser.parse_args()

    # Start CSV stream server in one thread.
    csv_thread = threading.Thread(target=csv_stream_server, args=(args.host, args.csv_port, args.files, args.interval))
    csv_thread.daemon = True
    csv_thread.start()

    # Start Order server in another thread.
    order_thread = threading.Thread(target=order_server, args=(args.host, args.order_port))
    order_thread.daemon = True
    order_thread.start()

    print("Unified server running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down.")
        sys.exit(0)

# python3 tcp_server.py --csv-port 9995 --order-port 9999 --files finance/finance.csv
