from Crypto.PublicKey import RSA


def generate_private_key() -> str:
    key = RSA.generate(2048)
    private = key.exportKey()
    return private.decode()
