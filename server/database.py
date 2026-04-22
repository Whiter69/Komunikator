import sqlite3
import hashlib

class ChatDatabase:
    def __init__(self, db_name="chat_secure.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as db:
            db.execute('''CREATE TABLE IF NOT EXISTS users 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           username TEXT UNIQUE, 
                           password_hash TEXT)''')
        print("[DB] Baza danych gotowa.")

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        try:
            with sqlite3.connect(self.db_name) as db:
                h = self._hash_password(password)
                db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, h))
                db.commit()
                return True, "Zarejestrowano pomyślnie."
        except sqlite3.IntegrityError:
            return False, "Użytkownik już istnieje."

    def login_user(self, username, password):
        with sqlite3.connect(self.db_name) as db:
            h = self._hash_password(password)
            cursor = db.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, h))
            if cursor.fetchone():
                return True, "Zalogowano."
            return False, "Błędne dane logowania."