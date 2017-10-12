import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESEngine(object):

    # sha256 makes it easy to have a 256 bit key there's collision concerns
    # but no one is going to use this for anything real
    # this exists only to make it hard for lazy people
    # to figure out what stored secrets are
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, data):
        # easy to get a random iv so we do
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        # tack the iv on the beginning and base64encode
        return base64.b64encode(iv + cipher.encrypt(data))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        # iv is the first block
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        # important to discard the iv here
        enc = enc[AES.block_size:]
        # decrypt
        data = cipher.decrypt(enc)
        # decode as utf-8
        return data.decode('utf-8')

