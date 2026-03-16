# 🗺️ Proyecto: Andalucía Quick Data — Resumen Ejecutivo

## ¿Qué hay que construir?

Una **librería Python** que permita a analistas y estudiantes acceder a datos territoriales de Andalucía con **3 líneas de código**, sin necesidad de conocer APIs, WFS ni scraping.

```python
# Así de simple debe ser el resultado final:
aqd = AndaluciaQuickData("Sevilla")
mapa = aqd.get_map("municipios")
aqd.plot_choropleth("paro")
```

---

## 📦 Lo que hay que desarrollar

| Módulo | Qué hace |
|---|---|
| **Cliente WFS (DERA)** | Descarga capas vectoriales (municipios, hospitales, parques…) del GeoServer IECA |
| **Scraper SIMA/IECA** | Extrae estadísticas municipales (población, paro, renta…) de fichas HTML |
| **Sistema de Caché** | Guarda datos localmente en `.aqd_cache/` con TTL de 24h |
| **API de Alto Nivel** | `get_map()`, `get_stats()`, `plot_choropleth()` |
| **Visualización** | Mapas coropléticos con Folium, gráficos con Plotly |
| **Empaquetado** | `pyproject.toml` + tests con pytest |

---

## 🏗️ Estructura de carpetas

```
andalucia_quick_data/
├── pyproject.toml
├── README.md
├── tests/
└── andalucia_quick_data/
    ├── __init__.py
    ├── wfs_client.py       # Conexión DERA
    ├── sima_scraper.py     # Scraping SIMA/IECA
    ├── cache.py            # Sistema caché 24h
    ├── api.py              # get_map(), get_stats(), plot_choropleth()
    └── visualizer.py       # Folium + Plotly
```

---

## ❓ Opciones para empezar

1. **🚀 Inicializar el proyecto con Poetry** — crear la estructura base y `pyproject.toml`
2. **📡 Módulo WFS** — conexión al GeoServer IECA (DERA)
3. **🔍 Módulo Scraper SIMA** — extracción de estadísticas municipales
4. **💾 Sistema de Caché** — persistencia local 24h
5. **🎨 API + Visualización** — `get_map()`, `plot_choropleth()`

---

## 🔗 Referencias

- [DERA / GeoServer IECA](https://www.juntadeandalucia.es/datosabiertos/portal/dataset/datos-espaciales-de-referencia-andalucia-dera)
- [SIMA fichas municipales](https://www.juntadeandalucia.es/institutodeestadisticaycartografia/sima/ficha.htm?mun=29060)
- [Documentación GeoPandas](https://geopandas.org)
- [Documentación Folium](https://python-visualization.github.io/folium/)
- [Guía empaquetado PyPA](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Protocolo WFS 2.0 (OGC)](https://www.ogc.org/standard/wfs/)

---

> **Contacto del proyecto:** David Robert — david.robert@factoriaf5.org


Sesión 1 → Setup + Cliente WFS
Sesión 2 → Scraper SIMA + Caché
Sesión 3 → API + Visualización
Sesión 4 → Tests + Empaquetado + README
