"""
Andalucía Quick Data (AQD)
==========================
Librería Python para acceder en 3 líneas de código a datos espaciales
y estadísticos públicos de Andalucía.

Ejemplo de uso::

    from andalucia_quick_data import AndaluciaQuickData

    aqd = AndaluciaQuickData("Sevilla")
    mapa = aqd.get_map("municipios")
    aqd.plot_choropleth("paro")
"""

__version__ = "0.1.0"
__author__ = "Equipo Andalucía Quick Data"

from andalucia_quick_data.api import AndaluciaQuickData

__all__ = ["AndaluciaQuickData"]
