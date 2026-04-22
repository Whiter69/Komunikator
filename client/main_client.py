import customtkinter as ctk
from network import SecureNetwork

class Sprint2Client(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Klient Testowy")
        self.geometry("600x500")

        self.network = SecureNetwork()
        self.setup_auth_ui()

    def setup_auth_ui(self):
        self.auth_frame = ctk.CTkFrame(self)
        self.auth_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.auth_frame, text="LOGOWANIE", font=("Arial", 18, "bold")).pack(pady=20)

        self.e_user = ctk.CTkEntry(self.auth_frame, placeholder_text="Login")
        self.e_user.pack(pady=10)

        self.e_pass = ctk.CTkEntry(self.auth_frame, placeholder_text="Hasło", show="*")
        self.e_pass.pack(pady=10)

        self.lbl_status = ctk.CTkLabel(self.auth_frame, text="", text_color="yellow")
        self.lbl_status.pack(pady=5)

        ctk.CTkButton(self.auth_frame, text="Zaloguj", command=lambda: self.authenticate("login")).pack(pady=5)
        ctk.CTkButton(self.auth_frame, text="Zarejestruj", command=lambda: self.authenticate("register")).pack(pady=5)

    def authenticate(self, action):
        user = self.e_user.get().strip()
        pwd = self.e_pass.get().strip()

        if not user or not pwd:
            self.lbl_status.configure(text="Podaj login i hasło!")
            return

        success, msg = self.network.connect_and_auth("127.0.0.1", action, user, pwd)
        self.lbl_status.configure(text=msg)

        if success and action == "login":
            self.auth_frame.destroy()
            self.setup_chat_ui()

    def setup_chat_ui(self):
        self.chat_box = ctk.CTkTextbox(self, state="disabled")
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.entry = ctk.CTkEntry(self, placeholder_text="Wpisz wiadomość (zostanie zaszyfrowana AES-em)...")
        self.entry.pack(fill="x", padx=10, pady=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        self.write_to_chat("[SYSTEM] Połączono! Wszystko co wyślesz, przejdzie przez AES-128.")
        self.poll_queue()

    def send_message(self, event=None):
        text = self.entry.get().strip()
        if text:
            self.network.send_secure_msg(text)
            self.write_to_chat(f"JA: {text}")
            self.entry.delete(0, "end")

    def poll_queue(self):
        try:
            while True:
                packet = self.network.queue.get_nowait()
                if packet.get("type") == "msg":
                    self.write_to_chat(f"KTOŚ: {packet.get('body')}")
        except:
            pass
        self.after(50, self.poll_queue)

    def write_to_chat(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", text + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

if __name__ == "__main__":
    app = Sprint2Client()
    app.mainloop()