# AUTOR: Santiago Alvarez
# DESCRIPCION: Software que busca todas las licitaciones de un determinado año en las que ha participado una empresa y crea un informe
# Este script descarga los ficheros necesarios de la web de hacienda.gob.es, si no están en local, y si están en local ya los procesa sin necesidad de descargarlos
# El software permite maquetar y exportar la salida en varios formatos
# CREADO: 30/05/2025
#    Copyright (C) 2025 Santiago Alvarez

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>


# NOTAS:
# Formato url: https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_AAAAMM.zip
# Año de datos más antiguos: 2012


from datetime import datetime
import requests
import argparse
import os
import zipfile
from datetime import datetime
from tqdm import tqdm
from parser_contratos import ParserContratos
from informes import Informes
from base_logger import logger

#Def. constantes
VERSION = '1.0.0'

#Global vars
today = datetime.now()
current_year = today.year
first_year = int(2012)
url_base = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_"
carpeta_descargas = "temp/"
imp = True #Con o sin prints??

#Banner
def mostrar_banner():
    banner = r"""
         
  /$$$$$$                                /$$ /$$           /$$   /$$              
 /$$__  $$                              | $$|__/          |__/  | $$              
| $$  \ $$  /$$$$$$   /$$$$$$  /$$$$$$$ | $$ /$$  /$$$$$$$ /$$ /$$$$$$    /$$$$$$ 
| $$  | $$ /$$__  $$ /$$__  $$| $$__  $$| $$| $$ /$$_____/| $$|_  $$_/   |____  $$
| $$  | $$| $$  \ $$| $$$$$$$$| $$  \ $$| $$| $$| $$      | $$  | $$      /$$$$$$$
| $$  | $$| $$  | $$| $$_____/| $$  | $$| $$| $$| $$      | $$  | $$ /$$ /$$__  $$
|  $$$$$$/| $$$$$$$/|  $$$$$$$| $$  | $$| $$| $$|  $$$$$$$| $$  |  $$$$/|  $$$$$$$
 \______/ | $$____/  \_______/|__/  |__/|__/|__/ \_______/|__/   \___/   \_______/
          | $$                                                                    
          | $$                                                                    
          |__/    
                                                                                    
            Herramienta OSINT para análisis de contratos públicos
    """
    print(banner)


#Parsea argumentos de entrada
def parse_args():

    parser = argparse.ArgumentParser(
        description="Herramienta OSINT para analizar contratos públicos adjudicados a empresas (en España)."

    )
    
    # Parámetros obligatorios (Grupo de exclusión mutua)
    grupo_exclusivo = parser.add_mutually_exclusive_group(required=True)

    grupo_exclusivo.add_argument(
        '-v', '--version', action='store_true',
        help="Muestra la versión del programa y termina."
    )
    grupo_exclusivo.add_argument(
        '-e', type=str,
        help="Nombre o CIF de la empresa para la consulta (nombre puede ser parcial, ej. INDRA)."
    )
    
    # Parámetros opcionales
    parser.add_argument(
        '-s', type=str, default="salida/",
        help="Ruta base para guardar el informe generado. Por defecto 'salida/'"
    )

    parser.add_argument(
        '-y', '--year', type=int, default=current_year,
        help=f"Año de los contratos a investigar. Por defecto, es {current_year}"
    )

    parser.add_argument(
        '--pdf', action='store_true',
        help="Además del informe en html, vuelca el informe a 'pdf'."
    )

    parser.add_argument(
        '--excel', action='store_true',
        help="Además del informe en html, vuelca los contratos en un fichero Excel."
    )

    parser.add_argument(
        '--silencioso', action='store_true',
        help="Minimiza la salida por consola para integración en scripts."
    )

    return parser.parse_args()

#Función que comprueba con el usuario si deben descargarse de nuevo los datos del año actual
def comprueba_actualiza_descarga():
    existe = os.path.isdir(carpeta_descargas + str(current_year) + "/")

    if existe:
        print(f"Los datos de {current_year} ya están descargados, pero pueden estar desactualizados.")
        logger.info(f"Los datos de {current_year} ya están descargados, pero pueden estar desactualizados.")
        while True:
            print("¿Quieres descargarlos de nuevo?")
            resp = input("Respuesta (s/n): ").lower()
            if resp in ('s', 'si', 'y', 'yes'):
                #Borramos el directorio y su contenido
                for filename in os.listdir(carpeta_descargas + str(current_year) + "/"):
                    os.remove(carpeta_descargas + str(current_year) + "/" +filename)
                os.rmdir(carpeta_descargas + str(current_year) + "/")
                break
            elif resp in ('n', 'no'):
                #Nada que hacer
                break

#Función que comprueba si existe la carpeta de salida. Si no existe la crea, si es posible, y si no para la ejecución del programa
def comprueba_carpeta_salida(salida):
    #if salida.endswith('/') or salida.endswith("\"):
                                               
    existe = os.path.isdir(salida)

    if not existe:
        try:
            os.mkdir(salida)
        except Exception as e:
            print(f"La carpeta de salida ({salida}) no existe y no puede crearse.")
            logger.info(f"La carpeta de salida ({salida}) no existe y no puede crearse.")
            return False
    return True


#Función que comprueba si el fichero de un determinado año está descargado y si no lo descarga
def descarga_ficheros(year):
    #Comprueba si está descargado el fichero de ese año
    if not os.path.isdir(carpeta_descargas):
        os.makedirs(carpeta_descargas)
    
    existe = os.path.isdir(carpeta_descargas + str(year) + "/")
    
    if not existe:
        try:
            url = url_base + str(year) + ".zip"
            if imp: print(f"Descargando datos de {year}. Ten paciencia, tardaremos un rato:")
            response = requests.get(url, stream=True, timeout=(5,20))
            total = int(response.headers.get('content-length', 0))
            chunk_size = 1024

            #Gestión barra de estado
            with open(carpeta_descargas+str(year)+".zip", 'wb') as archivo, tqdm(
                desc=f"Descargando {str(year)+'.zip'}",
                total=total,
                unit='B',
                unit_scale=True,
                unit_divisor=1024
            ) as barra:
                for data in response.iter_content(chunk_size=chunk_size):
                    archivo.write(data)
                    barra.update(len(data))

            if imp: print("Terminado, flipas...")
        except Exception as e:
            print(f"ERROR: No se pudo completar la descarga del fichero de {year}.")
            if os.path.exists(carpeta_descargas+str(year)+".zip"):
                os.remove(carpeta_descargas+str(year)+".zip")
        except KeyboardInterrupt:
            print("Descarga interrumpida por el usuario.")
            if os.path.exists(carpeta_descargas+str(year)+".zip"):
                os.remove(carpeta_descargas+str(year)+".zip")

        #Comprueba si existe fichero zip. Si existe lo descomprime y luego lo borra
        if os.path.exists(carpeta_descargas+str(year)+".zip"):
            with zipfile.ZipFile(carpeta_descargas+str(year)+".zip", 'r') as archivo_zip:
                try:
                    if imp: print("Descomprimiendo fichero...")
                    archivo_zip.extractall(carpeta_descargas + str(year) + "/")
                    if imp: print("Fichero descomprimido con éxito")
                except Exception as e:
                    print(f"ERROR: Fallo al descomprimir fichero de {year}.")
                    for filename in os.listdir(carpeta_descargas + str(year) + "/"):
                        os.remove(carpeta_descargas + str(year) + "/" +filename)
                    os.rmdir(carpeta_descargas + str(year) + "/")
                except KeyboardInterrupt:
                    if os.path.exists(carpeta_descargas+str(year)+".zip"):
                        os.remove(carpeta_descargas+str(year)+".zip")
                    for filename in os.listdir(carpeta_descargas + str(year) + "/"):
                        os.remove(carpeta_descargas + str(year) + "/" +filename)
                    os.rmdir(carpeta_descargas + str(year) + "/")
                    
            #Eliminar zip
            os.remove(carpeta_descargas+str(year)+".zip")

        

if __name__ == "__main__":
    args = parse_args()
    if args.version:
        print(f"Versión {VERSION}")
        exit()
    
    if args.silencioso:
        imp = False
    
    if imp: mostrar_banner()

    #Comprueba si el año existe
    if args.year < first_year or args.year > current_year:
        print(f"No existen datos para el año {args.year}")
        logger.info(f"No existen datos para el año {args.year}")
        exit()

    if args.year == current_year:
        comprueba_actualiza_descarga()

    #Comprueba carpeta de salida
    if not comprueba_carpeta_salida(args.s):
        exit()

    #Descarga ficheros
    descarga_ficheros(args.year)

    #Parsea ficheros
    nombre_salida = args.e + '-' + str(args.year)
    parser = ParserContratos(carpeta_descargas+str(args.year),imp)
    resultado = parser.buscar_contratos(args.e, args.s+'/'+nombre_salida+'.json')
    logger.info(f"Encontrados: {resultado} contratos para la empresa {args.e} en el año {args.year}")
    if imp: print(f"Encontrados: {resultado} contratos")

    #Crea ficheros de salida
    if resultado > 0:
        inf = Informes(args.s, nombre_salida+'.json', str(args.year))
        inf.genera_informes(args.pdf, args.excel)


    #print(args.e)