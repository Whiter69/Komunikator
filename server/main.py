import socket
import threading
import json

class FoundationServer:
    def __init__(self):
        self.clients = []
        self.lock = threading.RLock()

    def broadcast(self, payload, sender_conn=None):
        data = (json.dumps(payload) + "\n").encode("utf-8")
        with self.lock:
            for client in self.clients:
                if client != sender_conn:
                    try:
                        client.sendall(data)
                    except:
                        pass

    def handle_client(self, conn, addr):
        print(f"[NOWE POŁĄCZENIE] {addr} dołączył do serwera.")
        with self.lock:
            self.clients.append(conn)

        try:
            stream = conn.makefile("r", encoding="utf-8")
            for line in stream:
                if not line.strip(): continue

                packet = json.loads(line.strip())
                print(f"[SERWER OTRZYMAŁ] {packet}")

                # Rozsyłamy surową ramkę dalej
                self.broadcast(packet, sender_conn=conn)
        except Exception as e:
            print(f"[BŁĄD] {addr}: {e}")
        finally:
            with self.lock:
                if conn in self.clients:
                    self.clients.remove(conn)
            conn.close()
            print(f"[ROZŁĄCZONO] {addr}")

    def run(self):

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 5050))
        server.listen(50)

        print("SERWER ONLINE na porcie 5050")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    FoundationServer().run()