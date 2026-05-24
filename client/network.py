import socket
import threading
import json
import queue
from crypto import AESCipher

class SecureNetwork:
    """
    Silnik sieciowy aplikacji klienckiej.
    Zarządza gniazdem TCP, wielowątkowością oraz buforowaniem odbieranych paczek w kolejce.
    """

    def __init__(self):
        self.socket = None
        self.queue = queue.Queue()  # Bezpieczna kolejka dla wątku GUI
        self.crypto = AESCipher()
        self.current_user = ""

    def connect_and_auth(self, ip, action, user, pwd):
        """
        Łączy się z serwerem i przeprowadza proces logowania lub rejestracji.
        Odpala wątek nasłuchujący po udanym logowaniu.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, 5050))

        auth_pkt = {"action": action, "user": user, "pass": pwd}
        self.socket.sendall((json.dumps(auth_pkt) + "\n").encode("utf-8"))

        resp = json.loads(self.socket.makefile("r", encoding="utf-8").readline())
        if resp["status"] == "ok":
            self.current_user = user
            threading.Thread(target=self.recv_loop, daemon=True).start()
            return True, resp["message"]
        return False, resp["message"]

    def send_secure_msg(self, text, to=None):
        """Szyfruje i wysyła wiadomość tekstową (publiczną lub prywatną)."""
        encrypted_body = self.crypto.encrypt(text)
        packet = {"type": "private_msg", "to": to, "body": encrypted_body} if to else {"type": "msg", "body": encrypted_body}
        self.socket.sendall((json.dumps(packet) + "\n").encode("utf-8"))

    def send_secure_file(self, filename, file_data_b64, to=None):
        """Szyfruje i wysyła plik zamieniony na format Base64."""
        encrypted_data = self.crypto.encrypt(file_data_b64)
        packet = {"type": "file", "filename": filename, "data": encrypted_data}
        if to:
            packet["to"] = to
        self.socket.sendall((json.dumps(packet) + "\n").encode("utf-8"))

    def recv_loop(self):
        """
        Pętla działająca w tle. Nasłuchuje, odbiera paczki JSON,
        odszyfrowuje ich zawartość i wrzuca do kolejki do wyświetlenia.
        """
        stream = self.socket.makefile("r", encoding="utf-8")
        for line in stream:
            packet = json.loads(line.strip())

            if "body" in packet and packet.get("type") in ["msg", "private"]:
                packet["body"] = self.crypto.decrypt(packet["body"])
            elif packet.get("type") == "file" and "data" in packet:
                packet["data"] = self.crypto.decrypt(packet["data"])

            self.queue.put(packet)