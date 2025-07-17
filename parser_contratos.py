# parser_contratos.py
# Esta librería implementa la funcionalidad de parseo de los ficheros xml. Sirve para extraer los datos que nos interesan
# de las licitaciones adjudicadas a una determinada empresa, y se queda con los datos que nos interesa analizar más tarde.
# Crea un fichero json que almacena ya en la ruta de salida y devuelve el nombre del fichero como resultado

import os
import xml.etree.ElementTree as ET
from json_persistence import *
from base_logger import logger


class ParserContratos:

    # Inicializa el procesador con la ruta correspondiente al año (ej. 'temp/2022')
    # y carga los ficheros maestros requeridos.
    def __init__(self, xml_path: str, imp: bool):
        self.xml_path = xml_path.rstrip('/')
        self.licitaciones = {}
        self.imp = imp

        self.ns = { 
            'atom': 'http://www.w3.org/2005/Atom',
            'cbc-place-ext' : 'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonBasicComponents-2',
            'cac-place-ext' : 'urn:dgpe:names:draft:codice-place-ext:schema:xsd:CommonAggregateComponents-2',
            'at' : 'http://purl.org/atompub/tombstones/1.0', 
            'ns7' : 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'cbc': "urn:dgpe:names:draft:codice:schema:xsd:CommonBasicComponents-2",
            'cac': "urn:dgpe:names:draft:codice:schema:xsd:CommonAggregateComponents-2"
        }

        # Cargar diccionarios maestros
        self._load_master_files()


    #Carga los ficheros maestros necesarios. Lanza excepción si falta alguno.
    def _load_master_files(self):
        if os.path.isfile("data/procedurecodes.json"):
            self.procedureCodes = load_json("data/procedurecodes.json")
        else:
            logger.error("Fichero maestro no encontrado: procedurecodes.json")
            raise FileNotFoundError("Fichero maestro no encontrado: procedurecodes.json")
        if os.path.isfile('data/subtypecodes.json'):
            self.subTypeCodes = load_json('data/subtypecodes.json')
        else:
            logger.error("Fichero maestro no encontrado: subtypes.json")
            raise FileNotFoundError("Fichero maestro no encontrado: subtypecodes.json")
        if os.path.isfile('data/tenderresultcodes.json'):
            self.tenderResultCodes = load_json('data/tenderresultcodes.json')
        else:
            logger.error("Fichero maestro no encontrado: tenderresultcodes.json")
            raise FileNotFoundError("Fichero maestro no encontrado: tenderresultcodes.json")
        if os.path.isfile('data/typecodes.json'):
            self.typeCodes = load_json('data/typecodes.json')
        else:
            logger.error("Fichero maestro no encontrado: typecodes.json")
            raise FileNotFoundError("Fichero maestro no encontrado: typecodes.json")

    # Procesa todos los ficheros XML del directorio del año buscando el término dado.
    # Almacena el json generado en la ruta indicada por output_file
    def buscar_contratos(self, termino_busqueda: str, output_file: str) -> int:
        if not output_file.endswith(".json"):
            print("Formato fichero de salida incorrecto.")
            logger.error(f"Nombre fichero de salida incorrecto: {output_file}")
            return -1
        
        next_file = "licitacionesPerfilesContratanteCompleto3.atom"
        num_ficheros = 0
        contratos_adjudicados = 0
        if self.imp: 
            print('Procesando ficheros. Tardaremos unos minutos.')
            print('> Cada . representa un fichero leído.')
            print('> Cada + representa una coincidencia con tu búsqueda.')
        
        while os.path.exists(self.xml_path+'/'+next_file):
            with open(self.xml_path+'/'+next_file,"r",encoding='utf-8') as file:
                tree = ET.parse(file)
            
            if self.imp: print(".", end='', flush=True)
            root = tree.getroot()

            #Buscas el enlace del siguiente fichero
            for link in root.findall('atom:link', self.ns):
                if link.get('rel') == 'next':
                    next_file = link.get('href')
                    num_ficheros = num_ficheros + 1
                    #Arreglo debido a que algunos ficheros vienen mal formateados
                    if "https" in next_file:
                        next_file = next_file.split('/')[-1]
                    break
            
            #Si está adjudicada o resuelta, miras quien es el adjudicatario.
            #Si adjudicatario coincide, lo metes.
            #Si adjudicatario coincide y estado = ANUL, lo marcas, porque vas desde final a principio de año.
            
            for entry in root.findall('atom:entry', self.ns):
                contractFolderID = entry.find('.//cac-place-ext:ContractFolderStatus/cbc:ContractFolderID',self.ns)
                estado = entry.find('.//cac-place-ext:ContractFolderStatus/cbc-place-ext:ContractFolderStatusCode',self.ns)
                
                #Si al final del procesado no está vacío este campo, procesamos
                lotes = []
                
                if estado.text in ['ADJ', 'RES', 'ANUL'] and contractFolderID.text not in self.licitaciones:
                    descripcion = entry.find('atom:title',self.ns)
                    importe_modificado = 0 # Una licitación puede no tener modificaciones
                    
                    #Hay un resultado por cada lote:
                    for resultado in entry.findall('.//cac-place-ext:ContractFolderStatus/cac:TenderResult',self.ns):
                        estado2_code = resultado.find('.//cbc:ResultCode',self.ns)
                        #Estos estados son tipo renuncia, desierto, etc...
                        if estado2_code.text not in ['3', '4', '5', '6', '7']:
                            
                            nombre = resultado.find('.//cac:WinningParty/cac:PartyName/cbc:Name',self.ns)
                            cif = resultado.find('.//cac:WinningParty/cac:PartyIdentification/cbc:ID', self.ns)
                            
                            #Si hay coincidencia
                            if termino_busqueda.upper() in nombre.text.upper() or termino_busqueda.upper() in cif.text.upper():
                                num_lote = resultado.find('.//cac:AwardedTenderedProject/cbc:ProcurementProjectLotID',self.ns)
                                #Procesamos número de lote
                                if num_lote != None:
                                    num_lote = num_lote.text
                                else:
                                    num_lote = '1'

                                #Si coincide, guardamos nombre empresa y cif
                                adjudicatario = nombre.text.upper()
                                adjudicatario_cif = cif.text.upper()

                                importe = resultado.find('.//cac:AwardedTenderedProject/cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount',self.ns)
                                num_licitadores = resultado.find('.//cbc:ReceivedTenderQuantity',self.ns)
                                #Procesa oferta_mas_baja
                                oferta_mas_baja = resultado.find('.//cbc:LowerTenderAmountQuantity',self.ns)
                                if oferta_mas_baja != None:
                                    oferta_mas_baja = oferta_mas_baja.text
                                else:
                                    oferta_mas_baja = importe.text


                                #Modificación del contrato si hubo
                                for modificacion in entry.findall('.//cac-place-ext:ContractFolderStatus/cac:ContractModification/cac:ContractModificationLegalMonetaryTotal/cbc:TaxExclusiveAmount',self.ns):
                                    importe_modificado = modificacion.text
                                lote = {
                                    'num_lote': num_lote, 
                                    'resultado': self.tenderResultCodes[estado2_code.text],
                                    'num_licitadores': num_licitadores.text,
                                    'importe': importe.text,
                                    'oferta_mas_baja' : oferta_mas_baja
                                }
                                lotes.append(lote)


                    #Hubo coincidencia
                    if len(lotes) > 0:
                        enlace = entry.find('atom:link', self.ns).get('href')
                        if estado.text == 'ANUL':
                            anulado = True
                        else:
                            anulado = False
                        #Procesamos tipo
                        tipo = entry.find('.//cac-place-ext:ContractFolderStatus/cac:ProcurementProject/cbc:TypeCode', self.ns)
                        if tipo != None:
                            if tipo.text in ['2', '3']:
                                subtipo = entry.find('.//cac-place-ext:ContractFolderStatus/cac:ProcurementProject/cbc:SubTypeCode', self.ns)
                                subtipo = self.subTypeCodes[subtipo.text]
                            else:
                                subtipo = ''
                            tipo = self.typeCodes[tipo.text]
                        else:
                            tipo = ''
                            subtipo = ''

                        #Procesa codigos cpv
                        cpv = []
                        for resultado_cpv in entry.findall('.//cac-place-ext:ContractFolderStatus/cac:ProcurementProject/cac:RequiredCommodityClassification/cbc:ItemClassificationCode',self.ns):
                            cpv.append(resultado_cpv.text.strip())
                        #Procesa procedimiento
                        procedimiento = entry.find('.//cac-place-ext:ContractFolderStatus/cac:TenderingProcess/cbc:ProcedureCode', self.ns)
                        if procedimiento != None:
                            procedimiento = self.procedureCodes[procedimiento.text]
                        else:
                            procedimiento = ''
                        
                        organo_contratacion = entry.find('.//cac-place-ext:ContractFolderStatus/cac-place-ext:LocatedContractingParty/cac:Party/cac:PartyName/cbc:Name', self.ns)
                        #Procesa ciudad
                        provincia = entry.find('cac-place-ext:ContractFolderStatus/cac:ProcurementProject/cac:RealizedLocation/cbc:CountrySubentity', self.ns)
                        if provincia != None:
                            provincia = provincia.text
                        else:
                            provincia = ''
                        
                        #Componemos licitación
                        self.licitaciones[contractFolderID.text] = {
                            "expediente" : contractFolderID.text,
                            "enlace" : enlace,
                            "descripcion" : descripcion.text,
                            "adjudicatario" : adjudicatario,
                            "cif" : adjudicatario_cif,
                            "anulado" : anulado,
                            "tipo" : tipo,
                            "subtipo": subtipo,
                            "cpv" : cpv,
                            "procedimiento" : procedimiento,
                            "organo_contratacion" : organo_contratacion.text,
                            "provincia" : provincia,
                            "importe_modificado" : importe_modificado,
                            "lotes" : lotes
                        }
                        contratos_adjudicados = contratos_adjudicados + 1
                        if self.imp: print("+", end='', flush=True)
                        logger.info(f"Encontrado contrato {contractFolderID.text} para empresa {termino_busqueda} en {self.xml_path}")

        # Al final:
        if self.imp:
            print(f"\nHemos procesado {num_ficheros} ficheros.")
            print(f"Encontrados {contratos_adjudicados} contratos adjudicados.")
        store_json(output_file, self.licitaciones)
        return contratos_adjudicados
