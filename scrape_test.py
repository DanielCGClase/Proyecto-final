import requests
import pandas as pd
from io import StringIO

url = 'https://www.juntadeandalucia.es/institutodeestadisticaycartografia/sima/ficha.htm?mun=29060'
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)
response.raise_for_status()

# Guardar HTML para inspeccion local por si acaso
with open('sima_29060.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

try:
    # Usar StringIO para call a read_html evitando FutureWarning
    tables = pd.read_html(StringIO(response.text))
    print(f'Exito! Tablas encontradas: {len(tables)}')
    
    # Imprimir un resumen de las primeras 5 tablas
    for i, t in enumerate(tables[:5]):
        print(f"\n--- Tabla {i} ({t.shape[0]} filas, {t.shape[1]} cols) ---")
        print(t.head(3))
except Exception as e:
    print(f"Error parseando tablas: {e}")
