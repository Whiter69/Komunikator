import socket
import threading
import json
import queue


class NetworkCore:
    def __init__(self):
        self.socket = None
        self.net_queue = queue.Queue()

    def connect(self, ip, port):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def receive_loop(self):
        try:
            stream = self.socket.makefile("r", encoding="utf-8")
            for line in stream:
                if line.strip():
                    packet = json.loads(line.strip())
                    self.net_queue.put(packet)
        except Exception as e:
            self.net_queue.put({"type": "error", "message": str(e)})

    def send_packet(self, packet_dict):

        if self.socket:
            data = (json.dumps(packet_dict) + "\n").encode("utf-8")
            self.socket.sendall(data)