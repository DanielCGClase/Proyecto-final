import requests
import xml.etree.ElementTree as ET

url = "http://www.ideandalucia.es/services/DERA_g13_limites_administrativos/wfs"
params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetCapabilities"
}
try:
    r = requests.get(url, params=params)
    r.raise_for_status()
    # xml puede ser lioso pero vamos a buscar los tags Name bajo FeatureType
    root = ET.fromstring(r.content)
    # Los namespaces del XML pueden ser dinamicos, quitaremos todo para mas facil
    namespaces = {'wfs': 'http://www.opengis.net/wfs/2.0'}
    for ft in root.findall('.//wfs:FeatureType', namespaces):
        name = ft.find('wfs:Name', namespaces).text
        title = ft.find('wfs:Title', namespaces).text
        print(f"Layer found: Name='{name}', Title='{title}'")
        
    print("--RAW TEXT--")
    print(r.text[:500])
except Exception as e:
    print("ERROR:", e)
