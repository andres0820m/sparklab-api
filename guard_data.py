import os
from cryptography.fernet import Fernet
import json

BANK_DATA = {"bank": "",
             "user_name": "",
             "password": "",
             "account_number": "",
             "welcome_name": ""}


def create_file():
    file_key = Fernet.generate_key()
    with open('filekey.key', 'wb') as filekey:
        filekey.write(file_key)
    fernet = Fernet(file_key)
    banks = int(input("cuantos bancos quieres agregar? "))
    print("")
    data = {}
    for i in range(banks):
        bank_data = {}
        for key in BANK_DATA:
            bank_data[key] = input("ingresa {} ".format(key))
        data[bank_data['bank']] = bank_data
    print(data)

    encrypted = fernet.encrypt(json.dumps(data, indent=4).encode())
    with open('banks_data.data', 'wb') as encrypted_file:
        encrypted_file.write(encrypted)

    with open('banks_data.data', 'rb') as enc_file:
        encrypted = enc_file.read()

    # decrypting the file
    decrypted = fernet.decrypt(encrypted)
    print(json.loads(decrypted.decode("utf-8")))
    print(file_key)


def read_file(file_path: str) -> dict:
    with open(file_path, 'rb') as enc_file:
        encrypted = enc_file.read()
        fernet = Fernet(os.environ['guard_key'])
        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode("utf-8"))


# GkXg44cTOcqJMtTRp5qD2Hbnr79EoWrNbSUbbYmOQUs=
#create_file()
#print(read_file('banks_data.data'))
