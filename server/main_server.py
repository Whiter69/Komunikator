import socket
import threading
import json
from datetime import datetime
from database import ChatDatabase

class SecureRelayServer:
    """
    Główny serwer obsługujący połączenia wielu klientów asynchronicznie (TCP).
    Zbudowany w architekturze "Blind Relay" – przesyła wiadomości i pliki bez możliwości ich odczytania.
    """

    def __init__(self):
        self.clients = {}  # Mapuje obiekt gniazda na nazwę użytkownika (słownik)
        self.db = ChatDatabase()

    def broadcast_roster(self):
        """Aktualizuje i rozsyła listę aktywnych użytkowników do wszystkich klientów."""
        users_online = [{"name": name} for name in self.clients.values()]
        self.broadcast({"type": "roster_update", "list": users_online})

    def handle_client(self, conn, addr):
        """
        Funkcja obsługująca pojedynczego klienta. Każdy klient ma dedykowany wątek.
        Odpowiada za logowanie oraz routing nadchodzących paczek.
        """
        try:
            stream = conn.makefile("r", encoding="utf-8")
            auth_line = stream.readline()
            if not auth_line: return

            # 1. Logika autoryzacji
            auth_data = json.loads(auth_line.strip())
            action, user, pwd = auth_data.get("action"), auth_data.get("user"), auth_data.get("pass")

            if action == "register":
                success, msg = self.db.register_user(user, pwd)
            else:
                success, msg = self.db.login_user(user, pwd)

            conn.sendall((json.dumps({"status": "ok" if success else "fail", "message": msg}) + "\n").encode("utf-8"))
            if not success: return

            self.clients[conn] = user
            print(f"[AUTH] {user} zalogowany.")

            # Powiadomienie o dołączeniu
            time_now = datetime.now().strftime("%H:%M")
            self.broadcast({"type": "notif", "content": f"{user} dołączył.", "time": time_now}, sender_conn=conn)
            self.broadcast_roster()

            # 2. Główna pętla nasłuchująca wiadomości od klienta
            for line in stream:
                packet = json.loads(line.strip())

                # Czat globalny
                if packet.get("type") == "msg":
                    packet["author"] = user
                    packet["time"] = datetime.now().strftime("%H:%M")
                    self.broadcast(packet, sender_conn=conn)

                # Wiadomość prywatna (routing punkt-punkt)
                elif packet.get("type") == "private_msg":
                    target = packet.get("to")
                    packet["author"] = user
                    packet["time"] = datetime.now().strftime("%H:%M")
                    packet["type"] = "private"
                    self.send_to_user(target, packet)

                # Transfer plików
                elif packet.get("type") == "file":
                    packet["author"] = user
                    packet["time"] = datetime.now().strftime("%H:%M")
                    target = packet.get("to")
                    if target:
                        self.send_to_user(target, packet)
                    else:
                        self.broadcast(packet, sender_conn=conn)

        except:
            pass
        finally:
            # Czyszczenie i rozłączanie klienta po utracie połączenia
            user = self.clients.pop(conn, None)
            if user:
                time_exit = datetime.now().strftime("%H:%M")
                self.broadcast({"type": "notif", "content": f" {user} wyszedł.", "time": time_exit})
                self.broadcast_roster()
            conn.close()

    def broadcast(self, packet, sender_conn=None):
        """Rozsyła paczkę JSON do wszystkich zalogowanych użytkowników z pominięciem nadawcy."""
        data = (json.dumps(packet) + "\n").encode("utf-8")
        for client in list(self.clients.keys()):
            if client != sender_conn:
                try: client.sendall(data)
                except: pass

    def send_to_user(self, target_username, packet):
        """Wysyła paczkę JSON bezpośrednio do konkretnego gniazda odbiorcy."""
        data = (json.dumps(packet) + "\n").encode("utf-8")
        for conn, username in list(self.clients.items()):
            if username == target_username:
                try: conn.sendall(data)
                except: pass
                break

    def run(self):
        """Główna pętla serwera akceptująca nowe połączenia TCP."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", 5050))
        s.listen(50)
        print("SERWER URUCHOMIONY NA PORCIE 5050")
        while True:
            c, a = s.accept()
            threading.Thread(target=self.handle_client, args=(c, a), daemon=True).start()

if __name__ == "__main__":
    SecureRelayServer().run()