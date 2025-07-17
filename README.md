# 🕵️‍♂️ Openlicita – Herramienta OSINT para Contratos Públicos

**Openlicita** es una herramienta OSINT que permite crear informes de forma automática sobre contratos públicos adjudicados por la administración española. El objetivo es facilitar análisis de adjudicatarios, órganos de contratación y patrones de adjudicación, generando informes en formato **HTML**, **PDF** y **Excel**.

---

## 🚀 Características principales

- 🔍 Búsqueda por nombre de empresa o CIF
- 📅 Filtro por año de adjudicación
- 📄 Generación de informes en:
  - JSON, listo para integrar en software de terceros
  - HTML interactivo (gráficos, mapas, filtros)
  - PDF listo para imprimir
  - Excel con información en tablas de todos los contratos
- 📊 Visualización de:
  - Top CPVs
  - Provincias con más adjudicaciones
  - Organismos contratantes más activos
  - Contratos sin competencia, anulados o con sobrecostes

---

## ⚠️ A tener en cuenta
  - Esta aplicación utiliza datos descargados de la web del ministerio de hacienda. Los datos disponibles para descargar se encuentran en ficheros en formato xml agrupados por años y comprimidos en un fichero zip. Hay 2 cosas a tener en cuenta: 
    1. Los servidores del ministerio son lentos.
    2. Cada fichero ocupa aproximadamente 1 GB o algo más dependiendo del año. 
  Esto implica que descargar estos ficheros es lento y puede llevar hasta 30 minutos dependiendo de tu conexión.
  - Una vez descargado el fichero de datos de un año en concreto, este se descomprime y almacen en tu ordenador. Es importante tener en cuenta que este fichero descomprimido puede ocupar hasta 10 veces más, por lo que ocupará un espacio considerable en tu disco duro.
  - Una vez descargado el fichero de datos de un año determinado, y mientras no lo borres, no volverá a descargarse el fichero de datos de ese año para cualquier investigación posterior, por lo que la creación de informes para ese año será mucho más rápida.
  - Los ficheros de datos clasificados por año se almacenan en la carpeta **temp/** dentro de la carpeta de __openlicita__. En cualquier momento puedes borrar la carpeta de un año de forma manual para liberar espacio en disco. 

## 📂 Estructura del proyecto

openlicita/  
│  
├── templates/ # Plantillas Jinja2 (HTML del informe)  
├── data/ # Archivos json auxiliares  
├── temp/ # Almacenamiento de los datos anuales descargados de la administración  
└── openlicita.py # Script principal

## 🛠 Requisitos

- Python 3.10+
- Recomendado: entorno virtual

## 📦 Librerías necesarias

```
pip install -r requirements.txt
```
O instalar manualmente:

```
pip install pandas jinja2 openpyxl playwright requests tqdm
playwright install
```

# 🧪 Ejecución básica

`python openlicita.py -e "NTT DATA" -y 2022`

# 🙋‍♂️ Autor
**Santi** – Creador de Openlicita  
**Contacto:** [salvarez@ornova.es]