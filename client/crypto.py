import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class AESCipher:
    """
    Moduł kryptograficzny odpowiadający za szyfrowanie i deszyfrowanie danych
    przy użyciu algorytmu AES-128 w bezpiecznym trybie CBC.
    """

    def __init__(self, key="NEXUS_SECRET_128"):
        """
        Inicjalizuje obiekt szyfrujący.

        :param key: Główne hasło szyfrujące. Zostanie przycięte do 16 bajtów (wymóg AES-128).
        """
        self.key = key.encode('utf-8')[:16]

    def encrypt(self, raw_text):
        """
        Szyfruje tekst jawny. Tworzy unikalny wektor inicjujący (IV) dla każdej wiadomości.

        :param raw_text: Tekst do zaszyfrowania (str).
        :return: Połączony wektor IV oraz zaszyfrowany tekst w formacie Base64 (str).
        """
        cipher = AES.new(self.key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(raw_text.encode('utf-8'), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return f"{iv}:{ct}"

    def decrypt(self, encrypted_data):
        """
        Odszyfrowuje dane w formacie Base64.

        :param encrypted_data: Zaszyfrowany ciąg w formacie 'IV:ZaszyfrowanyTekst' (str).
        :return: Odszyfrowany tekst jawny (str) lub komunikat o błędzie w przypadku manipulacji danymi.
        """
        try:
            iv_b64, ct_b64 = encrypted_data.split(":")
            iv = base64.b64decode(iv_b64)
            ct = base64.b64decode(ct_b64)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except:
            return "[BŁĄD DEKRYPCJI]"