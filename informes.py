# informes.py
# Esta librería implementa la funcionalidad de generación de los informes en distintos formatos 
# a partir del filtrado de información realizado previamente. 
# Toma de base el fichero json generado previamente en parser_contratos.py

from jinja2 import Environment, FileSystemLoader
from json_persistence import *
from base_logger import logger
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import os

class Informes:
    # Inicializa los informes con ruta de salida, nombre del fichero de datos
    # y carga los ficheros maestros requeridos.
    def __init__(self, output_path: str, data_file: str, anio: str):
        self.output_path = output_path.rstrip('/')
        self.data_file = data_file
        self.output_name = data_file.rstrip('.json')
        self.anio = anio

        # Cargar diccionarios maestros
        self._load_master_files()

    # Carga los ficheros maestros necesarios. Lanza excepción si falta alguno.
    def _load_master_files(self):
        # Cargamos datos filtrados en memoria, si existen
        if os.path.isfile(f"{self.output_path}/{self.data_file}"):
            self.licitaciones = load_json(f"{self.output_path}/{self.data_file}")
            self.lista_contratos = list(self.licitaciones)
        else:
            logger.error("Fichero de datos para generar informe no encontrado")
            raise FileNotFoundError("Fichero de datos para generar informe no encontrado")

        if os.path.isfile("data/cpv_codes.json"):
            self.cpvCodes = load_json("data/cpv_codes.json")
        else:
            logger.error("Fichero maestro no encontrado: cpv_codes.json")
            raise FileNotFoundError("Fichero maestro no encontrado: cpv_codes.json")

        if os.path.isfile("data/conversion_provincias.json"):
            self.conv_p = load_json("data/conversion_provincias.json")
        else:
            logger.error("Fichero maestro no encontrado: conversion_provincias.json")
            raise FileNotFoundError("Fichero maestro no encontrado: conversion_provincias.json")
        
        if os.path.isfile("data/conversion_comunidades.json"):
            self.conv_c = load_json("data/conversion_comunidades.json")
        else:
            logger.error("Fichero maestro no encontrado: conversion_comunidades.json")
            raise FileNotFoundError("Fichero maestro no encontrado: conversion_comunidades.json")
        
    async def _html_to_pdf(self, url, output_path):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            # Exportar a PDF
            await page.pdf(
                path=output_path,
                format="A4",
                margin={"top": "20mm", "bottom": "20mm", "left": "10mm", "right": "10mm"},
                print_background=True
            )
            await browser.close()


    # Genera y compila los informes con jinja2
    def genera_informes(self, pdf: bool, excel: bool):
        #CALCULOS
        total_contratos = len(self.lista_contratos)
        empresa = self.licitaciones[self.lista_contratos[0]]['adjudicatario']
        cif = self.licitaciones[self.lista_contratos[0]]['cif']
        importe_total = 0.0
        num_lotes = 0
        suma_licitadores = 0
        num_anulados = 0
        sin_competencia = 0
        num_modificados = 0

        #Para los graficos de contratos por tipo  e importe por tipo de contrato
        tipos_contrato = {}
        importes_contrato = {}
        cpvs = {}
        provincias = {}
        organismos_contratacion = {}
        organismos_importe = {}
        provincias_importe = {}
        comunidades = {}

        #Para las tablas de contratos
        contratos_anulados = []
        contratos_sin_competencia = []
        contratos_modificados = []
        contratos_completos = []


        #Para cada contrato de la lista
        for c in self.lista_contratos:
            #Organos contratación
            if self.licitaciones[c]['organo_contratacion'] not in list(organismos_contratacion):
                organismos_contratacion[self.licitaciones[c]['organo_contratacion']] = 1
            else:
                organismos_contratacion[self.licitaciones[c]['organo_contratacion']] += 1

            #Tipos de contrato
            if self.licitaciones[c]['tipo'] not in list(tipos_contrato):
                tipos_contrato[self.licitaciones[c]['tipo']] = 1
            else:
                tipos_contrato[self.licitaciones[c]['tipo']] += 1

            #CPVs
            for cpv in self.licitaciones[c]['cpv']:
                #Solo consideramos los primeros 4 digitos
                if cpv[:4] not in cpvs:
                    cpvs[cpv[:4]] = 1
                else:
                    cpvs[cpv[:4]] += 1

            #Provincias
            if self.conv_p[self.licitaciones[c]['provincia']] not in provincias:
                provincias[self.conv_p[self.licitaciones[c]['provincia']]] = 1
            else:
                provincias[self.conv_p[self.licitaciones[c]['provincia']]] += 1

            #Comunidades
            if self.conv_c[self.licitaciones[c]['provincia']] not in comunidades:
                comunidades[self.conv_c[self.licitaciones[c]['provincia']]] = 1
            else:
                comunidades[self.conv_c[self.licitaciones[c]['provincia']]] += 1

            importe_adjudicado = 0.0

            oferta_mas_baja = True

            #Para cada lote de cada contrato
            for lote in self.licitaciones[c]['lotes']:
                importe_adjudicado = importe_adjudicado + float(lote['importe'])
                importe_total = importe_total + float(lote['importe'])
                num_lotes = num_lotes + 1
                suma_licitadores = suma_licitadores + int(lote['num_licitadores'])
                if lote['num_licitadores'] == '1':
                    sin_competencia = sin_competencia + 1
                    contratos_sin_competencia.append({"expediente" : f"{self.licitaciones[c]['expediente']} (lote {lote['num_lote']})", "enlace" : self.licitaciones[c]['enlace'], "organo_contratacion" : self.licitaciones[c]['organo_contratacion'], "importe_total": round(float(lote['importe']),2) })

                #Importes por organo de contratacion
                if self.licitaciones[c]['organo_contratacion'] not in list(organismos_importe):
                    organismos_importe[self.licitaciones[c]['organo_contratacion']] = float(lote['importe'])
                else:
                    organismos_importe[self.licitaciones[c]['organo_contratacion']] += float(lote['importe'])

                #Importes por provincia
                if self.conv_p[self.licitaciones[c]['provincia']] not in list(provincias_importe):
                    provincias_importe[self.conv_p[self.licitaciones[c]['provincia']]] = float(lote['importe'])
                else:
                    provincias_importe[self.conv_p[self.licitaciones[c]['provincia']]] += float(lote['importe'])
                
                #Importes por tipo de contrato
                if self.licitaciones[c]['tipo'] not in list(importes_contrato):
                    importes_contrato[self.licitaciones[c]['tipo']] = float(lote['importe'])
                else:
                    importes_contrato[self.licitaciones[c]['tipo']] += float(lote['importe'])

                #Oferta más baja
                if float(lote['oferta_mas_baja']) < float(lote['importe']):
                    oferta_mas_baja = False

            #Para licitaciones anuladas
            if self.licitaciones[c]['anulado']:
                contratos_anulados.append({"expediente" : self.licitaciones[c]['expediente'], "enlace" : self.licitaciones[c]['enlace'], "organo_contratacion" : self.licitaciones[c]['organo_contratacion'], "importe_total": importe_adjudicado })
                num_anulados = num_anulados + 1
            ampliado = False
            if float(self.licitaciones[c]['importe_modificado']) > 0.0:
                ampliado = True
                num_modificados = num_modificados + 1
                contratos_modificados.append({"expediente" : self.licitaciones[c]['expediente'], "enlace" : self.licitaciones[c]['enlace'], "organo_contratacion" : self.licitaciones[c]['organo_contratacion'], "importe_modificado": self.licitaciones[c]['importe_modificado'] })

            #Lista de contratos completos
            contratos_completos.append({"expediente" : self.licitaciones[c]['expediente'], "enlace" : self.licitaciones[c]['enlace'], "organo_contratacion" : self.licitaciones[c]['organo_contratacion'], "importe_total": importe_adjudicado, "territorio" : self.licitaciones[c]['provincia'], "ampliado" : ampliado, "anulado" : self.licitaciones[c]['anulado'], "oferta_mas_baja" : oferta_mas_baja })

            

        organismos_ordenados = dict(sorted(organismos_contratacion.items(), key=lambda item: item[1], reverse=True))
        top_organismos = list(organismos_ordenados)[:3]
        provincias_ordenadas = dict(sorted(provincias.items(), key=lambda item: item[1], reverse=True))
        top_provincias = list(provincias_ordenadas)[:3]
        cpvs_ordenados = dict(sorted(cpvs.items(), key=lambda item: item[1], reverse=True))
        top_cpvs = []
        for cpv in list(cpvs_ordenados)[:3]:
            top_cpvs.append(f"{cpv}0000 - {self.cpvCodes[cpv+'0000']}")
        porcentaje_sin_competencia = round(sin_competencia * 100.0 / num_lotes, 2)
        porcentaje_anulados = round(num_anulados * 100.0 / total_contratos, 2)
        porcentaje_modificados = round(num_modificados * 100.0 / total_contratos, 2)

        #Componemos tabla provincias y mapa por comunidades
        tabla_provincias = []
        #mapa_provincias = []
        mapa_comunidades = []
        for prov in list(provincias_ordenadas):
            tabla_provincias.append({"nombre" : prov, "num_contratos" : provincias_ordenadas[prov], "importe_total": round(provincias_importe[prov],2)})
            #mapa_provincias.append({"provincia" : prov, "value" : provincias_ordenadas[prov]})

        for com in list(comunidades):
            mapa_comunidades.append({"comunidad" : com, "value" : comunidades[com]})

        #Componemos tabla órganos de contratación
        tabla_organos = []
        for org in list(organismos_ordenados):
            tabla_organos.append({"nombre" : org, "num_contratos" : organismos_ordenados[org], "importe_total": round(organismos_importe[org],2)})


        #Formateamos importe total, para mejor legibilidad
        importe_total = f"{importe_total:_.2f}"
        importe_total = importe_total.replace(".",",")
        importe_total = importe_total.replace("_",".")

        #Tipos de contrato
        tipos_contrato_labels = list(tipos_contrato)

        #Porcentaje de contratos por tipo
        tipos_contrato_data = list(tipos_contrato.values())

        #Importes por tipo de contrato
        importes_contrato_data = list(importes_contrato.values())


        #################################################


        # Prepara los datos que necesita la plantilla
        contexto = {
            "empresa": empresa,
            "cif": cif,
            "anio": self.anio,
            "total_contratos": total_contratos,
            "importe_total": importe_total,
            "total_organos": len(organismos_contratacion),
            "media_licitadores": round(suma_licitadores/num_lotes),
            "porcentaje_sin_competencia": porcentaje_sin_competencia,
            "porcentaje_anulados": porcentaje_anulados,
            "porcentaje_modificados": porcentaje_modificados,
            "top_organismos": top_organismos,
            "top_cpvs": top_cpvs,
            "top_provincias" : top_provincias,
            "tipos_contrato_labels" : tipos_contrato_labels,
            "tipos_contrato_data" : tipos_contrato_data,
            "importes_contrato_data" : importes_contrato_data,
            "tabla_organos" : tabla_organos,
            "tabla_provincias" : tabla_provincias,
            "mapa_comunidades" : mapa_comunidades,
            "contratos_anulados" : contratos_anulados,
            "contratos_sin_competencia" : contratos_sin_competencia,
            "contratos_modificados" : contratos_modificados,
            "contratos_completos" : contratos_completos
        }


        # Configurar Jinja2
        env = Environment(loader=FileSystemLoader("template"))
        template = env.get_template("template_informe.html")

        # Renderizar HTML
        html_renderizado = template.render(contexto)

        # Guardar HTML en disco
        output = f"{self.output_path}/{self.output_name}.html"
        with open(output, "w", encoding="utf-8") as f:
            f.write(html_renderizado)

        #Copiar el css
        if os.name == 'nt':
            os.system(f"copy template\style.css {self.output_path}\style.css")
        else:
            os.system(f"cp template/style.css {self.output_path}/style.css")

        print(f"Informe generado: {output}")
        logger.info(f"Informe generado: {output}")

        if pdf:
            path = os.path.abspath(output)
            asyncio.run(self._html_to_pdf(path, f"{self.output_path}/{self.output_name}.pdf"))
            print(f"Se ha volcado el informe a pdf: {self.output_path}/{self.output_name}.pdf")
            logger.info(f"Se ha volcado el informe a pdf: {self.output_path}/{self.output_name}.pdf")

        if excel:
            df_completos = pd.DataFrame(contratos_completos)
            
            # Exportamos a excel expecificando openpyxl como motor de escritura
            with pd.ExcelWriter(f"{self.output_path}/{self.output_name}.xlsx", engine="openpyxl") as writer:
                df_completos.to_excel(writer, sheet_name="Todos", index=False)