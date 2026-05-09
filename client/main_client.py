import customtkinter as ctk
from datetime import datetime
from plyer import notification
from network import SecureNetwork
from tkinter import filedialog
import base64
import os
import queue


class NexusApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Komunikator")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.network = SecureNetwork()
        self.all_users = []
        self.dm_boxes = {}
        self.chat_font = ("Segoe UI", 15)
        self.notif_enabled = ctk.BooleanVar(value=True)

        self.staged_file = None

        self.setup_auth_ui()

    def setup_auth_ui(self):
        self.auth = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.auth.pack(fill="both", expand=True)

        login_card = ctk.CTkFrame(self.auth, width=480, height=600, corner_radius=20, border_width=4,
                                  border_color="#2ecc71", fg_color="#161616")
        login_card.place(relx=0.5, rely=0.5, anchor="center")
        login_card.pack_propagate(False)

        ctk.CTkLabel(login_card, text="NEXUS", font=("Impact", 64), text_color="#2ecc71").pack(pady=(40, 0))
        ctk.CTkLabel(login_card, text="SECURE TERMINAL", font=("Segoe UI", 13, "bold"), text_color="#555555").pack(
            pady=(0, 20))

        self.e_user = ctk.CTkEntry(login_card, placeholder_text="Login", width=340, height=50, border_color="#2ecc71")
        self.e_user.pack(pady=10)

        self.e_pass = ctk.CTkEntry(login_card, placeholder_text="Hasło", show="*", width=340, height=50,
                                   border_color="#2ecc71")
        self.e_pass.pack(pady=10)

        self.lbl_err = ctk.CTkLabel(login_card, text="", text_color="#2ecc71")
        self.lbl_err.pack(pady=5)

        ctk.CTkButton(login_card, text="ZALOGUJ SIĘ", command=lambda: self.authenticate("login"), width=340, height=50,
                      font=("Segoe UI", 16, "bold")).pack(pady=10)
        ctk.CTkButton(login_card, text="REJESTRACJA", command=lambda: self.authenticate("register"), width=340,
                      height=40, fg_color="transparent", border_width=2, text_color="#2ecc71",
                      hover_color="#1a1a1a").pack(pady=5)
        self.after(200, self.e_user.focus_set)

    def authenticate(self, action):
        user, pwd = self.e_user.get().strip(), self.e_pass.get().strip()
        if not user or not pwd:
            self.lbl_err.configure(text="Wypełnij pola!")
            return

        success, msg = self.network.connect_and_auth("127.0.0.1", action, user, pwd)
        self.lbl_err.configure(text=msg)

        if success and action == "login":
            self.auth.destroy()
            self.setup_main_ui()
            self.poll_queue()

    def setup_main_ui(self):
        self.main = ctk.CTkFrame(self, fg_color="#0d0d0d")
        self.main.pack(fill="both", expand=True)
        self.main.grid_columnconfigure(1, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self.main, width=280, fg_color="#161616", border_width=2, border_color="#333333")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="Użytkownicy", font=("Segoe UI", 18, "bold"), text_color="#2ecc71").pack(
            pady=(20, 5))
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Szukaj...")
        self.search_entry.pack(fill="x", padx=20, pady=10)
        self.search_entry.bind("<KeyRelease>", self.draw_roster)

        self.scroll = ctk.CTkScrollableFrame(self.sidebar, label_text="ONLINE", fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkSwitch(self.sidebar, text="Powiadomienia PUSH", variable=self.notif_enabled).pack(pady=20)

        self.chat_container = ctk.CTkFrame(self.main, fg_color="transparent")
        self.chat_container.grid(row=0, column=1, sticky="nsew", padx=(0, 15), pady=15)
        self.chat_container.grid_rowconfigure(0, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(self.chat_container, fg_color="#161616")
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self.tab_pub = self.tabs.add("OGÓLNY")
        self.tab_dm_root = self.tabs.add("PRYWATNE ")
        self.tab_log = self.tabs.add("POWIADOMIENIA ")

        self.box_pub = ctk.CTkTextbox(self.tab_pub, state="disabled", font=self.chat_font)
        self.box_pub.pack(fill="both", expand=True, padx=10, pady=10)

        self.box_log = ctk.CTkTextbox(self.tab_log, state="disabled", text_color="#7f8c8d")
        self.box_log.pack(fill="both", expand=True, padx=10, pady=10)

        self.dm_tabs = ctk.CTkTabview(self.tab_dm_root, fg_color="transparent")
        self.dm_tabs.pack(fill="both", expand=True)

        input_frame = ctk.CTkFrame(self.chat_container, height=80, fg_color="#161616")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        self.btn_file = ctk.CTkButton(input_frame, text="📁", width=50, height=45, font=("Segoe UI", 20),
                                      fg_color="#222222", hover_color="#2ecc71", command=self.stage_file)
        self.btn_file.pack(side="left", padx=(15, 5), pady=15)

        self.entry = ctk.CTkEntry(input_frame, placeholder_text="Napisz wiadomość...", font=self.chat_font, height=45)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=15)
        self.entry.bind("<Return>", lambda e: self.send())

        ctk.CTkButton(input_frame, text="WYŚLIJ", width=100, height=45, font=("Segoe UI", 14, "bold"),
                      command=self.send).pack(side="right", padx=(0, 15), pady=15)

    def log_event(self, text):
        self.box_log.configure(state="normal")
        self.box_log.insert("end", f"[{datetime.now().strftime('%H:%M')}] {text}\n")
        self.box_log.configure(state="disabled")

    def get_box(self, name):
        if name not in self.dm_boxes:
            self.dm_tabs.add(name)
            b = ctk.CTkTextbox(self.dm_tabs.tab(name), state="disabled", font=self.chat_font)
            b.pack(fill="both", expand=True, padx=10, pady=10)
            self.dm_boxes[name] = b
        return self.dm_boxes[name]

    def prep_dm(self, name):
        self.get_box(name)
        self.dm_tabs.set(name)
        self.tabs.set("PRYWATNE ")

    def draw_roster(self, event=None):
        query = self.search_entry.get().lower()
        for w in self.scroll.winfo_children(): w.destroy()

        for u in self.all_users:
            name = u["name"]
            if query in name.lower() and name != self.network.current_user:
                ctk.CTkButton(self.scroll, text=f" ● {name}", anchor="w", fg_color="transparent",
                              text_color="#2ecc71", command=lambda n=name: self.prep_dm(n)).pack(fill="x", pady=2)

    def stage_file(self):
        path = filedialog.askopenfilename(title="Wybierz plik do wysłania")
        if path:
            with open(path, "rb") as f:
                data_b64 = base64.b64encode(f.read()).decode('utf-8')
            filename = os.path.basename(path)
            self.staged_file = {"filename": filename, "data": data_b64}

            self.entry.configure(state="normal")
            self.entry.delete(0, "end")
            self.entry.insert(0, f"[PLIK GOTOWY DO WYSŁANIA: {filename}]")
            self.entry.configure(state="disabled", text_color="#f1c40f")

    def download_file(self, filename, data_b64):
        path = filedialog.asksaveasfilename(initialfile=filename, title="Zapisz załącznik jako...")
        if path:
            try:
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data_b64))
                self.log_event(f"Zapisano plik na dysku: {path}")
            except Exception as e:
                self.log_event(f"Błąd zapisu pliku: {e}")

    def send(self):
        time_str = datetime.now().strftime("%H:%M")
        current_tab = self.tabs.get()
        target = None

        if "PRYWATNE" in current_tab:
            try:
                target = self.dm_tabs.get() or None
            except:
                target = None
            if not target:
                self.box_pub.configure(state="normal")
                self.box_pub.insert("end", f"[{time_str}] SYSTEM: Wybierz najpierw użytkownika!\n")
                self.box_pub.see("end")
                self.box_pub.configure(state="disabled")
                return

        box = self.get_box(target) if target else self.box_pub

        try:
            if self.staged_file:
                self.network.send_secure_file(self.staged_file["filename"], self.staged_file["data"], to=target)
                box.configure(state="normal")
                box.insert("end", f"[{time_str}] JA (Plik): {self.staged_file['filename']}\n")
                box.see("end")
                box.configure(state="disabled")

                self.staged_file = None
                self.entry.configure(state="normal", text_color="white")
                self.entry.delete(0, "end")
            else:
                text = self.entry.get().strip()
                if not text: return
                self.network.send_secure_msg(text, to=target)
                box.configure(state="normal")
                box.insert("end", f"[{time_str}] JA: {text}\n")
                box.see("end")
                box.configure(state="disabled")
                self.entry.delete(0, "end")
        except Exception as e:
            box.configure(state="normal")
            box.insert("end", f"[{time_str}]  BŁĄD: {str(e)}\n")
            box.see("end")
            box.configure(state="disabled")

    def poll_queue(self):
        try:
            while True:
                data = self.network.queue.get_nowait()
                t = data.get("type")

                if t == "msg":
                    self.box_pub.configure(state="normal")
                    self.box_pub.insert("end", f"[{data['time']}] {data['author']}: {data['body']}\n")
                    self.box_pub.see("end")
                    self.box_pub.configure(state="disabled")

                elif t == "private":
                    box = self.get_box(data['author'])
                    box.configure(state="normal")
                    box.insert("end", f"[{data['time']}] {data['author']}: {data['body']}\n")
                    box.see("end")
                    box.configure(state="disabled")

                    self.log_event(f"Nowy DM od {data['author']}")
                    if self.notif_enabled.get():
                        notification.notify(title=f"Nexus DM: {data['author']}", message=data['body'][:40], timeout=3)

                elif t == "file":
                    author, filename, file_data = data["author"], data["filename"], data["data"]
                    time_str, target = data["time"], data.get("to")

                    box = self.get_box(author) if target else self.box_pub

                    box.configure(state="normal")
                    box.insert("end", f"[{time_str}] {author}: ")

                    tag_name = f"file_{datetime.now().timestamp()}"
                    box.insert("end", f"[POBIERZ PLIK] {filename}\n", tag_name)

                    box.tag_config(tag_name, foreground="#00e5ff", underline=True)
                    box.tag_bind(tag_name, "<Button-1>",
                                 lambda e, name=filename, d=file_data: self.download_file(name, d))

                    box.see("end")
                    box.configure(state="disabled")

                    self.log_event(f"Załącznik od {author}: {filename}")
                    if self.notif_enabled.get():
                        notification.notify(title=f"Plik od {author}", message=filename, timeout=3)

                elif t == "notif":
                    self.log_event(data['content'])

                elif t == "roster_update":
                    self.all_users = data["list"]
                    self.draw_roster()
        except queue.Empty:
            pass
        self.after(50, self.poll_queue)


if __name__ == "__main__":
    app = NexusApp()
    app.mainloop()