from cryptography.fernet import Fernet
clave = Fernet.generate_key()
print(clave.decode())