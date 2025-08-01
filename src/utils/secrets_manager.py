from cryptography.fernet import Fernet
import os
import base64

class SecretsManager:
    def __init__(self, key_path='.secrets.key'):
        if not os.path.exists(key_path):
            self._generate_key(key_path)
        with open(key_path, 'rb') as f:
            self.key = f.read()
        self.cipher = Fernet(base64.urlsafe_b64encode(self.key.ljust(32)[:32]))

    def _generate_key(self, path):
        key = Fernet.generate_key()
        with open(path, 'wb') as f:
            f.write(key)
        os.chmod(path, 0o600)

    def encrypt(self, value):
        return 'enc:' + self.cipher.encrypt(value.encode()).decode()

    def decrypt(self, encrypted):
        if encrypted.startswith('enc:'):
            return self.cipher.decrypt(encrypted[4:].encode()).decode()
        return encrypted