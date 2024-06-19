# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 23:26:13 2023

@author: htiraboschi
"""

import time
from datetime import datetime
import TelegramBot
import ccxt
import re
import os
import platform

PAUSA_BINANCE = 500 #pausa entre consultas a Binances. Unidad: milisegundos
ARCHIVO_LOG = "log.txt"
LOG_MAXIMO = 1024 #tamaño máximo del archivo de log (en kilobytes) antes de ser cortado

def parsear_regla(regla):
    # Definir el patrón de la regla
    patron = r"\+(\w+\/\w+)([<>])([\d,]+)"

    # Intentar hacer coincidir el patrón con la cadena
    coincidencia = re.match(patron, regla)

    if coincidencia:
        # Si hay una coincidencia, extraer los grupos
        operador, simbolo, valor = coincidencia.groups()
        valor = float(valor.replace(',', '.'))
        reglaOk = True
    else:
        # Si no hay una coincidencia, establecer las variables en None
        operador, simbolo, valor, reglaOk = None, None, None, False
        
    return operador, simbolo, valor, reglaOk

def parsear_regla_caida(regla):
    # Definir el patrón de la regla
    patron = r'(?i)(caída|caida)\s+(\S+)/(\S+)\s+(\S+)\s+(\d+(?:[.,]\d+)?)' #ejemplo: caida JASMY/USDT 1m 0,1

    # Intentar hacer coincidir el patrón con la cadena
    coincidencia = re.match(patron, regla)
    
    if coincidencia:
        # Si hay una coincidencia, extraer los grupos
        par = coincidencia.group(2)+"/"+coincidencia.group(3)
        intervalo = coincidencia.group(4)
        valor = coincidencia.group(5)
        valor = float(valor.replace(',', '.'))
        reglaOk = True
    else:
        # Si no hay una coincidencia, establecer las variables en None
        par, intervalo, valor, reglaOk = None,None, None, False
        
    return par, intervalo, valor, reglaOk
    
def evaluar_regla(binance,regla):
    try:
        if regla.startswith('+'):
            #regla de verificación de limites de valor
            # Descomponer la regla
            operador,comparador,valor,reglaOk = parsear_regla(regla)
            if not reglaOk:
                return False, False
    
            # Obtener el precio actual
            precio_actual = binance.fetch_ticker(operador.upper())['last']
            # Evaluar la regla
            if comparador == '<':
                return True, precio_actual < valor
            elif comparador == '>':
                return True, precio_actual > valor
            else:
                return False, False
        elif regla.startswith('c'):
            #regla de verificación de caídas de valor
            # Descomponer la regla
            par, intervalo, valor, reglaOk = parsear_regla_caida(regla)
            if not reglaOk:
                return False, False
            else:
                return True, verificar_caida(binance, par, intervalo, valor)
            
    except:
        return False, False
    
def validar_en_binance(binance,regla):
    reglaValida , reglaResultado = evaluar_regla(binance,regla)
    return reglaValida

def evaluar_en_binance(binance,regla):
    reglaValida , reglaResultado = evaluar_regla(binance,regla)
    return reglaResultado

def verificar_caida(binance, par, duracion, caidaPorcentual):
    ohlcv = binance.fetch_ohlcv(par, timeframe=duracion)
    ultimo_periodo = ohlcv[-1]
    high = ultimo_periodo[2]
    cierre = ultimo_periodo[4]
    variacion_real = ((cierre - high) / high) * 100
    return variacion_real < -caidaPorcentual

def registrar_log(mensaje):
    with open(ARCHIVO_LOG, 'a') as f:
        f.write(f'{datetime.now()} {mensaje}\n')

def mover_entradas_log():
    # Verifica si el archivo es mayor al tamaño máximo
    if os.path.getsize(ARCHIVO_LOG) / 1024 > LOG_MAXIMO:
        # Encuentra el próximo número incremental para el nuevo nombre del archivo
        n = 1
        while os.path.exists(f'log{n:04}.txt'):
            n += 1
        
        # Renombra el archivo
        os.rename(ARCHIVO_LOG, f'log{n:04}.txt')
        
        # Registra el cambio de nombre en el archivo de log
        open(ARCHIVO_LOG, 'a')
        registrar_log(f'{ARCHIVO_LOG} renombrado a log{n:04}.txt')


# Cambiamos el directorio de trabajo
if platform.system() == 'Windows':
    os.chdir('C:/Hernan/Nextcloud/sda1/programas/raspberry/monitor Binance')
elif platform.uname()[4].startswith('arm'):
    os.chdir('/home/root/monitorBinance')

# Inicio de ejecución
registrar_log('inicio de ejecución')

try:
    
    # Crear instancia de Binance
    binance = ccxt.binance()
        
    # Consultar bot de Telegram
    mensajes = TelegramBot.MiBotTelegram().consultar_bot_telegram()
    for mensaje in mensajes:
        #reemplazo un "." por ","
        mensaje = mensaje.replace(".", ",")
        if mensaje.startswith('+') or mensaje.startswith('c'):
            # Verificar si el mensaje es una regla que se puede evaluar en Binance
            if validar_en_binance(binance,mensaje):
                # Agregar la regla al archivo de reglas y registrar en el log
                with open('reglas.txt', 'a') as f:
                    f.write(f'{mensaje}\n')
                    registrar_log(f'nueva regla {mensaje}')
            else: TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Regla {mensaje} no valida. No se incorpora a reglas actuales')
        elif mensaje.startswith('?'):
            with open('reglas.txt', 'r') as f:
                reglas = f.read();
                TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Reglas actuales:\n{reglas}')
                

    # Evaluar cada regla en Binance
    with open('reglas.txt', 'r') as f:
        reglas = f.readlines()
    with open('reglas.txt', 'w') as f:
        for regla in reglas:
            resultado_regla = evaluar_en_binance(binance,regla)
            if resultado_regla:
                # Si la regla se cumple, notificar en el bot de Telegram
                TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Regla verificada: {regla}')
            else:
                # Si la regla no se cumple, mantener la regla en el archivo
                f.write(regla)
            registrar_log(f'regla verificada {regla}, resultado {resultado_regla}')
            time.sleep(PAUSA_BINANCE / 1000)

    # Mover entradas del log del mes pasado
    mover_entradas_log()

except Exception as e:
    # Si ocurre un error, notificar en el bot de Telegram y registrar en el log
    TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Error: {str(e)}')
    registrar_log(f'Error: {str(e)}')

# Fin de ejecución
registrar_log('fin ejecución')
