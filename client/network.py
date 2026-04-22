import socket
import threading
import json
import queue
from crypto import AESCipher


class SecureNetwork:
    def __init__(self):
        self.socket = None
        self.queue = queue.Queue()
        self.crypto = AESCipher()

    def connect_and_auth(self, ip, action, user, pwd):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, 5050))

        auth_pkt = {"action": action, "user": user, "pass": pwd}
        self.socket.sendall((json.dumps(auth_pkt) + "\n").encode("utf-8"))

        resp = json.loads(self.socket.makefile("r", encoding="utf-8").readline())
        if resp["status"] == "ok":
            threading.Thread(target=self.recv_loop, daemon=True).start()
            return True, resp["message"]
        return False, resp["message"]

    def send_secure_msg(self, text):
        encrypted_body = self.crypto.encrypt(text)
        packet = {"type": "msg", "body": encrypted_body}
        self.socket.sendall((json.dumps(packet) + "\n").encode("utf-8"))

    def recv_loop(self):
        stream = self.socket.makefile("r", encoding="utf-8")
        for line in stream:
            packet = json.loads(line.strip())
            if "body" in packet:
                packet["body"] = self.crypto.decrypt(packet["body"])
            self.queue.put(packet)