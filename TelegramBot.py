import requests
import os
import traceback
from datetime import datetime
import time

ARCHIVO_LOG = "log.txt"

class MiBotTelegram:
    def __init__(self, telegram_token, archivo_log):
        self.token = telegram_token
        self.url_base = f"https://api.telegram.org/bot{self.token}/"
        self._archivo_log = archivo_log
        if os.path.exists('ultimo_id.txt'):
            with open('ultimo_id.txt', 'r') as f:
                ultimo_id_text = f.read()
                self.ultimo_id = int(ultimo_id_text) if ultimo_id_text.strip() != "" else None
        else:
            self.ultimo_id = None

    def obtener_actualizaciones(self):
        res = requests.get(self.url_base + "getUpdates")
        return res.json()

    def consultar_bot_telegram(self):
        try:
            intentos = 0
            max_intentos = 3
            while intentos < max_intentos:
                try:
                    actualizaciones = self.obtener_actualizaciones()
                    break
                except requests.exceptions.ConnectionError as e:
                    with open(self._archivo_log, 'a') as f:
                        f.write(f'Error en librería TelegramBot: Error de conexión: {e}. \n Intentos: {intentos}.\n')
                    intentos += 1
                    time.sleep(1)  # Esperar un segundo antes de reintentar
            mensajes_nuevos = []
            for actualizacion in actualizaciones["result"]:
                id_actualizacion = actualizacion["update_id"]
                if self.ultimo_id is None or id_actualizacion > self.ultimo_id:
                    self.ultimo_id = id_actualizacion
                    with open('ultimo_id.txt', 'w') as f:
                        f.write(str(self.ultimo_id))
                    mensajes_nuevos.append(actualizacion["message"]["text"])
            return mensajes_nuevos
        except Exception as e:
            error_trace = traceback.format_exc()
            with open(self._archivo_log, 'a') as f:
                f.write(f'Error en librería TelegramBot: {datetime.now()} \n Error: {str(e)} \n {error_trace}\n')

    def notificar_en_bot_telegram(self, mensaje):
        try:
            chat_id = "4016948"
            params = {"chat_id": chat_id, "text": mensaje}
            res = requests.post(self.url_base + "sendMessage", params)
            return res.json()
        except Exception as e:
            error_trace = traceback.format_exc()
            with open(self._archivo_log, 'a') as f:
                f.write(f'Error en librería TelegramBot: {datetime.now()} \n Error: {str(e)} \n {error_trace}\n')
