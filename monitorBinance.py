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
from enum import Enum #para enumerados mayor, menor, igual
from tradingview_ta import TA_Handler
import pandas as pd

PAUSA_BINANCE = 500 #pausa entre consultas a Binances. Unidad: milisegundos
ARCHIVO_LOG = "log.txt"
LOG_MAXIMO = 1024 #tamaño máximo del archivo de log (en kilobytes) antes de ser cortado

class comparacion(Enum):
    MAYOR = 1
    IGUAL = 2
    MENOR =3
    
def parsear_regla(regla):
    # Definir el patrón de la regla
    patron = r"\+(\w+\/\w+)\s*([<>])\s*([\d,]+)"

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
    # Definir el patrón de la regla con una expresión regular
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

def parsear_regla_subida(regla):
    # Definir el patrón de la regla con una expresión regular
    patron = r'(?i)(subida)\s+(\S+)/(\S+)\s+(\S+)\s+(\d+(?:[.,]\d+)?)' #ejemplo: subida JASMY/USDT 1m 0,1

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
    
def parsear_regla_linea(regla):
    # Definir el patrón de la regla con una expresión regular
    patron = r"linea (sobre|bajo) (\S+)/(\S+) \d{2}/\d{2}/\d{4} (\d+(?:[.,]\d+)?) \d{2}/\d{2}/\d{4} (\d+(?:[.,]\d+)?)" #ejemplo linea bajo BTC/USDT 01/01/2023 123.45 02/02/2024 678.90
    
    # Intentar hacer coincidir el patrón con la cadena
    coincidencia = re.match(patron, regla)

    if coincidencia:
        # Si hay una coincidencia, extraer los grupos
        bajoOsobre = coincidencia.group(1)
        par = coincidencia.group(2)+"/"+coincidencia.group(3)
        fechaA = re.findall(r"\d{2}/\d{2}/\d{4}",regla)[0]
        valorA = coincidencia.group(4)
        fechaB = re.findall(r"\d{2}/\d{2}/\d{4}",regla)[1]
        valorB = coincidencia.group(5)        
        reglaOk = True
    else:
        # Si no hay una coincidencia, establecer las variables en None
        bajoOsobre, par, fechaA, valorA, fechaB, valorB, reglaOk = None,None, None, None,None,False

    return bajoOsobre, par, fechaA, valorA, fechaB, valorB, reglaOk

def parsear_regla_RSI(regla):
    # Definir el patrón de la regla con una expresión regular
    patron = r'(?i)(RSI)\s+(\S+)/(\S+)\s+(\S+)\s*([<>])\s*(\d+(?:[.,]\d+)?)' #ejemplo: RSI LTC/USDT 15m <41

    # Intentar hacer coincidir el patrón con la cadena
    coincidencia = re.match(patron, regla)
    
    if coincidencia:
        # Si hay una coincidencia, extraer los grupos
        par = coincidencia.group(2)+"/"+coincidencia.group(3)
        intervalo = coincidencia.group(4)
        relacion = comparacion.MAYOR if coincidencia.group(5) == '>' else comparacion.MENOR
        valor = coincidencia.group(6)
        valor = float(valor.replace(',', '.'))
        reglaOk = True
    else:
        # Si no hay una coincidencia, establecer las variables en None
        par, intervalo, relacion, valor, reglaOk = None, None, None, None, False
        
    return par, intervalo, relacion, valor, reglaOk

def parsear_regla_EMA(regla):
    # Definir el patrón de la regla con una expresión regular
    patron = r'(?i)(EMA)\s+(\d+)+\s+(\S+)\s+(\S+)/(\S+)\s+(\+\d+(?:[.,]\d+)?)' #ejemplo: EMA 20 1h BTC/USDT +200

    # Intentar hacer coincidir el patrón con la cadena
    coincidencia = re.match(patron, regla)

    if coincidencia:
        # Si hay una coincidencia, extraer los grupos
        intervalo = int(coincidencia.group(2))
        periodo = coincidencia.group(3)
        par = coincidencia.group(4)+"/"+coincidencia.group(5)
        margen = float((coincidencia.group(6)[1:]).replace(',', '.'))
        reglaOk = True
    else:
        # Si no hay una coincidencia, establecer las variables en None
        intervalo, periodo, par, margen, reglaOk = None, None, None, None, False
    
    return intervalo, periodo, par, margen, reglaOk

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
        elif regla.startswith('s'):
            #regla de verificación de subidas de valor
            # Descomponer la regla
            par, intervalo, valor, reglaOk = parsear_regla_subida(regla)
            if not reglaOk:
                return False, False
            else:
                return True, verificar_subida(binance, par, intervalo, valor)
        elif regla.startswith('R'):
            #RSI
            # Descomponer la regla
            par, intervalo, relacion, valor, reglaOk = parsear_regla_RSI(regla)
            if not reglaOk:
                return False, False
            else:
                return True, verificar_RSI(par, intervalo, relacion, valor)
        elif regla.startswith('l'):
            #cruce de linea
            bajoOsobre, par, fechaA, valorA, fechaB, valorB, reglaOk = parsear_regla_linea(regla)
            if not reglaOk:
                return False, False
            else:
                return True, verificar_linea(binance, bajoOsobre, par, fechaA, valorA, fechaB, valorB)
        elif regla.startswith('E'):
            #EMA
            # Descomponer la regla
            intervalo, periodo, par, margen, reglaOk = parsear_regla_EMA(regla)
            if not reglaOk:
                return False, False
            else:
                return True, verificar_EMA(binance, par, intervalo, periodo, margen)
            
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

def verificar_subida(binance, par, duracion, subidaPorcentual):
    ohlcv = binance.fetch_ohlcv(par, timeframe=duracion)
    ultimo_periodo = ohlcv[-1]
    low = ultimo_periodo[3]
    cierre = ultimo_periodo[4]
    variacion_real = ((cierre - low) / low) * 100
    return variacion_real > subidaPorcentual

def calcular_rsi(par, intervalo='1h', periodo=14):
    try:
        handler = TA_Handler(
        symbol=par.replace('/',''),
        exchange="binance",
        screener="crypto",
        interval=intervalo,
        timeout=None
        )
        return handler.get_analysis().indicators["RSI"]
    except Exception as e:
        print(f"Error al calcular el RSI: {e}")
        return None
    
def calcular_EMA(binance, par, intervalo, periodo): 
    def calcular_EMA_Binance(cierres, longitud, suavizado):
        if suavizado==0:
            EMA = sum(cierres[-longitud:])/longitud
        else:
            multiplicador = 2 / (longitud+1)
            EMA_anterior = calcular_EMA_Binance(cierres[:-1],longitud, suavizado-1)
            EMA = (cierres[-1] - EMA_anterior)*multiplicador + EMA_anterior
        return EMA
    
    def obtener_datos_binance(binance, par, intervalo, periodo):
        try:
            velas = binance.fetch_ohlcv(par.upper().replace('/',''), timeframe=periodo, limit=intervalo)
            datos = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return datos
        except Exception as e:
            print("Error en obtener_datos_binance:")
            print(str(e))
        
    datos = obtener_datos_binance(binance, par, intervalo+12, periodo)
    ema = calcular_EMA_Binance(list(datos["close"]),intervalo,12)
    return ema

def verificar_RSI(par, intervalo, relacion, valor):
    RSI = calcular_rsi(par, intervalo, periodo=14)
    if relacion == comparacion.MENOR:
        return RSI < valor
    else:
        return RSI > valor

def convertir_fecha_a_numero(fecha):
    #Convierte una fecha en formato dd/mm/yyyy a un número de días desde una fecha inicial.
    fecha_inicial = datetime.strptime("01/01/1970", "%d/%m/%Y")
    fecha_obj = datetime.strptime(fecha, "%d/%m/%Y")
    return (fecha_obj - fecha_inicial).days

def verificar_linea(binance,bajoOsobre, par, fechaA, valorA, fechaB, valorB):
    precio_actual = binance.fetch_ticker(par.upper())['last']
    fechaAnumero = convertir_fecha_a_numero(fechaA)
    fechaBnumero = convertir_fecha_a_numero(fechaB)
    fechahoynumero = convertir_fecha_a_numero(datetime.now().strftime("%d/%m/%Y"))

    # Calcular la pendiente y la ordenada en el origen
    pendiente = (float(valorB.replace(",", ".")) - float(valorA.replace(",", "."))) / (fechaBnumero - fechaAnumero)
    ordenada_origen = float(valorA.replace(",", ".")) - pendiente * fechaAnumero

    # Calcular el valor de y en la recta para la fecha del punto
    y_en_recta = pendiente * fechahoynumero + ordenada_origen

    if (bajoOsobre == "bajo"):
        return precio_actual < y_en_recta
    else:
        return precio_actual > y_en_recta

def verificar_EMA(binance, par, intervalo, periodo, margen):
    EMA = calcular_EMA(binance, par, intervalo, periodo)
    if EMA:
        valorPar = binance.fetch_ticker(par.upper())['last']
        return valorPar < EMA + margen
    else:
        return None

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
        if mensaje.startswith('+') or mensaje.startswith('c') or mensaje.startswith('s') or mensaje.startswith('R') or mensaje.startswith('l') or mensaje.startswith('E'):
            # Verificar si el mensaje es una regla que se puede evaluar en Binance
            if validar_en_binance(binance,mensaje):
                # Agregar la regla al archivo de reglas y registrar en el log
                with open('reglas.txt', 'a') as f:
                    f.write(f'{mensaje}\n')
                    f.close()
                    registrar_log(f'nueva regla {mensaje}')
            else: TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Regla {mensaje} no valida. No se incorpora a reglas actuales')
        elif mensaje.startswith('?'):
            with open('reglas.txt', 'r') as f:
                reglas = f.read();
                TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Reglas actuales:\n{reglas}')
                

    # Evaluar cada regla en Binance
    with open('reglas.txt', 'r') as f:
        reglas = f.readlines()
        f.close()

    for regla in reglas:
        resultado_regla = evaluar_en_binance(binance,regla)
        if resultado_regla:
            # Si la regla se cumple, notificar en el bot de Telegram y eliminarla del listado de reglas
            TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Regla verificada: {regla}')
            reglas.remove(regla)
           
        registrar_log(f'regla verificada {regla}, resultado {resultado_regla}')

        time.sleep(PAUSA_BINANCE / 1000)

    with open('reglas-tmp.txt', 'w') as f:
        for regla in reglas:
            f.write(regla)
        f.close()
        os.remove('reglas.txt')
        os.rename(f.name,'reglas.txt')

    # Mover entradas del log del mes pasado
    mover_entradas_log()

except Exception as e:
    # Si ocurre un error, notificar en el bot de Telegram y registrar en el log
    TelegramBot.MiBotTelegram().notificar_en_bot_telegram(f'Error: {str(e)}')
    registrar_log(f'Error: {str(e)}')

# Fin de ejecución
registrar_log('fin ejecución')
