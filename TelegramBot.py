import requests
import os

class MiBotTelegram:
    def __init__(self):
        self.token = "6836398672:AAFZmkrgsZlRvLf79F32UiFENMKSrNChv2M"
        self.url_base = f"https://api.telegram.org/bot{self.token}/"
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
        actualizaciones = self.obtener_actualizaciones()
        mensajes_nuevos = []
        for actualizacion in actualizaciones["result"]:
            id_actualizacion = actualizacion["update_id"]
            if self.ultimo_id is None or id_actualizacion > self.ultimo_id:
                self.ultimo_id = id_actualizacion
                with open('ultimo_id.txt', 'w') as f:
                    f.write(str(self.ultimo_id))
                mensajes_nuevos.append(actualizacion["message"]["text"])
        return mensajes_nuevos

    def notificar_en_bot_telegram(self, mensaje):
        chat_id = "4016948"
        params = {"chat_id": chat_id, "text": mensaje}
        res = requests.post(self.url_base + "sendMessage", params)
        return res.json()
