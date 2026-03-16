<<<<<<< HEAD
# Andalucía Quick Data

**Andalucía Quick Data** es una librería Python diseñada para que Analistas de Datos puedan consumir de forma **extremadamente rápida y sencilla** los datos espaciales (DERA) y las estadísticas municipales (SIMA) de la Junta de Andalucía.

La motivación principal del proyecto es ocultar toda la complejidad de APIs WFS de OGC, los parsers GeoJSON, los CRSs y el scraping de HTMLs bajo una **fachada elegante (Facade Pattern)** orientada a Análisis y Data Science.

---

## Características Clave

1. **Catálogo Integrado**: Descarga capas vectoriales de Geoserver (`municipios`, `provincias`, `rios`, etc.) referenciándolas por su alias, sin namespaces farragosos.
2. **Scraper de Indicadores (SIMA)**: Lee automáticamente las tablas HTML oficiales del Instituto de Estadística y Cartografía de Andalucía (IECA) y devuelve `pandas.DataFrame` limpios y procesados.
3. **Smart Caching**: Incluye un sistema de caché transparente basado en Parquet (con política TTL configurable) para evitar bombardear los servidores públicos y acelerar tus análisis.
4. **Visualización Activa**: Incorpora generadores *one-liner* para trazar gráficas de evolución anual (Plotly) y mapas interactivos coropléticos (Folium).

---

## Instalación

El proyecto utiliza `poetry` para la gestión de dependencias. 

```bash
# Clonar o copiar el proyecto
git clone <url-repo> andalucia-quick-data
cd andalucia-quick-data

# Instalar dependencias con Poetry
poetry install
```

---

## Uso Rápido (Quickstart)

Toda la interacción pasa por la clase `AndaluciaQuickData`.

### Inicialización y Datos Base

```python
from andalucia_quick_data import AndaluciaQuickData

# Instancia la API (puedes filtrarla por provincia por defecto)
aqd = AndaluciaQuickData(provincia="Málaga")

# 1. Obtener la capa geográfica de todos los municipios malagueños
mapa_malaga_gdf = aqd.get_map(layer="municipios")
print(mapa_malaga_gdf.head())

# 2. Descargar las estadísticas demográficas del municipio "29060" (Málaga capital)
stats_df = aqd.get_stats(municipios_cod="29060", indicators=["Población", "Paro", "Renta"])
print(stats_df)
```

### Mapas y Gráficos (One-Liners)

```python
# Generar un gráfico (Plotly) de barras con la evolución temporal del paro registrado
figura = aqd.plot_stats(municipio_cod="29060", indicator="Paro registrado", chart_type="bar")
figura.show()

# Generar un mapa HTML Coroplético (Folium) rellenado según la población total
# La librería se encarga silenciosamente de descargar el GeoJSON, extraer 
# los datos del SIMA para cada polígono, hacer el join espacial, y colorear el mapa.
mapa_folium = aqd.plot_choropleth(layer="municipios", indicator="Población total")
mapa_folium.save("mi_mapa_málaga.html")
```

---

## Arquitectura

- `api.py`: Fachada principal del usuario. Orquesta las llamadas.
- `wfs_client.py`: Cliente y catálogo de OGC WFS 2.0 (DERA).
- `sima_scraper.py`: Rascador de DataFrames (SIMA/IECA).
- `cache.py`: Subsistema de persistencia en disco con formato `.parquet`.
- `visualizer.py`: Motor de rendering con Plotly y Folium.

---

> Diseñado con pragmatismo para simplificar la vida a los Analistas de Datos de Andalucía.
=======
# Proyecto-final
>>>>>>> origin/main
