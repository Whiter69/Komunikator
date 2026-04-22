import socket
import threading
import json
from database import ChatDatabase

class SecureRelayServer:
    def __init__(self):
        self.clients = {}
        self.db = ChatDatabase()

    def handle_client(self, conn, addr):
        try:
            stream = conn.makefile("r", encoding="utf-8")
            auth_line = stream.readline()
            if not auth_line: return

            auth_data = json.loads(auth_line.strip())
            action = auth_data.get("action")
            user = auth_data.get("user")
            pwd = auth_data.get("pass")

            if action == "register":
                success, msg = self.db.register_user(user, pwd)
            else:
                success, msg = self.db.login_user(user, pwd)

            conn.sendall((json.dumps({"status": "ok" if success else "fail", "message": msg}) + "\n").encode("utf-8"))
            if not success: return

            self.clients[conn] = user
            print(f"[AUTH] {user} zalogowany.")

            for line in stream:
                packet = json.loads(line.strip())
                self.broadcast(packet, sender_conn=conn)

        except:
            pass
        finally:
            self.clients.pop(conn, None)
            conn.close()

    def broadcast(self, packet, sender_conn):
        data = (json.dumps(packet) + "\n").encode("utf-8")
        for client in self.clients:
            if client != sender_conn:
                try:
                    client.sendall(data)
                except:
                    pass

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", 5050))
        s.listen()
        while True:
            c, a = s.accept()
            threading.Thread(target=self.handle_client, args=(c, a), daemon=True).start()


if __name__ == "__main__":
    SecureRelayServer().run()