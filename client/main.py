import customtkinter as ctk
from network import NetworkCore


class MinimalClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Klient Testowy")
        self.geometry("600x400")

        self.network = NetworkCore()

        self.setup_ui()
        self.connect_to_server()

    def setup_ui(self):
        self.chat_box = ctk.CTkTextbox(self, state="disabled")
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry = ctk.CTkEntry(self, placeholder_text="Wyślij testową ramkę JSON...")
        self.entry.pack(fill="x", padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.send_message)

    def connect_to_server(self):
        try:
            self.network.connect("127.0.0.1", 5050)
            self.write_to_chat("[SYSTEM] Nawiązano stabilną sesję z serwerem.")
            self.poll_queue()
        except Exception as e:
            self.write_to_chat(f"[BŁĄD] Nie można się połączyć: {e}")

    def send_message(self, event=None):
        text = self.entry.get().strip()
        if text:
            packet = {"type": "msg", "body": text}
            self.network.send_packet(packet)

            self.write_to_chat(f"WYSŁANO: {text}")
            self.entry.delete(0, "end")

    def poll_queue(self):
        try:
            while True:
                packet = self.network.net_queue.get_nowait()
                if packet.get("type") == "msg":
                    self.write_to_chat(f"ODEBRANO: {packet.get('body')}")
                elif packet.get("type") == "error":
                    self.write_to_chat(f"[BŁĄD SIECI] {packet.get('message')}")
        except:
            pass  # Kolejka pusta

        self.after(50, self.poll_queue)

    def write_to_chat(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")


if __name__ == "__main__":
    app = MinimalClient()
    app.mainloop()