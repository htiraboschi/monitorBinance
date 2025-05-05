import os
import sys
import json


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.session import get_db_session

# Lectura de configuraciones
# Ruta al archivo JSON
config_file = './config.json'

try:
    with open(config_file, 'r') as file:
        config_data = json.load(file)      
        db_file_path = config_data["database"]["DB_FILE_PATH"]
except FileNotFoundError:
    print(f"Error: El archivo {config_file} no existe.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: El archivo {config_file} no es un JSON válido.")
    sys.exit(1)
except Exception as e:
    print(f"Error inesperado: {e} {e.__doc__}")
    sys.exit(1)


async def get_db():
    async for session in get_db_session(db_file_path):
        yield session
