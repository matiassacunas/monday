import os

def ensure_directory_exists(directory:str):

    # asegura que el directorio existe, si no lo crea

    if not os.path.exists(directory):
        os.makedirs(directory)