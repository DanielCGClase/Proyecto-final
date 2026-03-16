"""
api.py
======
API de alto nivel de Andalucía Quick Data.

Este módulo expone la clase principal AndaluciaQuickData que actúa como
fachada (facade pattern) sobre los módulos internos: WFSClient, SimaScraper,
Cache y Visualizer.

Uso::

    from andalucia_quick_data import AndaluciaQuickData

    aqd = AndaluciaQuickData("Sevilla")

    # Obtener capa vectorial de municipios
    mapa_gdf = aqd.get_map("municipios")

    # Obtener estadísticas de un municipio
    stats_df = aqd.get_stats("29060")  # Málaga capital

    # Visualizar mapa coropl
    aqd.plot_choropleth(layer="municipios", indicator="paro", provincia="Málaga")
"""

import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

from andalucia_quick_data.cache import Cache
from andalucia_quick_data.wfs_client import WFSClient

logger = logging.getLogger(__name__)


class AndaluciaQuickData:
    """
    Punto de entrada principal de la librería Andalucía Quick Data.

    Permite acceder a datos espaciales y estadísticos de Andalucía con
    una interfaz mínima y sin necesidad de conocer WFS, APIs REST ni scraping.

    Parameters
    ----------
    provincia : str, optional
        Provincia de trabajo por defecto (ej: "Sevilla", "Málaga").
        Si se especifica, todas las consultas se filtran por esta provincia.
    cache_dir : Path | str, optional
        Directorio para almacenar la caché local. Default: '.aqd_cache/'.
    cache_ttl_hours : int
        Tiempo de vida de la caché en horas. Default: 24.
    timeout : int
        Timeout en segundos para las peticiones HTTP. Default: 30.
    log_level : int
        Nivel de logging (ej: logging.INFO, logging.DEBUG). Default: WARNING.

    Examples
    --------
    >>> aqd = AndaluciaQuickData("Sevilla")
    >>> gdf = aqd.get_map("municipios")
    >>> print(gdf.head())
    """

    def __init__(
        self,
        provincia: Optional[str] = None,
        cache_dir: Optional[Union[Path, str]] = None,
        cache_ttl_hours: int = 24,
        timeout: int = 30,
        log_level: int = logging.WARNING,
    ) -> None:
        # Configurar logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )

        self.provincia = provincia
        self._cache = Cache(
            cache_dir=cache_dir,
            ttl_seconds=cache_ttl_hours * 3600,
        )
        self._wfs = WFSClient(cache=self._cache, timeout=timeout)

        # Importación diferida para evitar error si el módulo no existe aún
        try:
            from andalucia_quick_data.sima_scraper import SimaScraper
            self._sima = SimaScraper(cache=self._cache)
        except ImportError:
            self._sima = None
            logger.debug("SimaScraper no disponible aún.")

        try:
            from andalucia_quick_data.visualizer import Visualizer
            self._viz = Visualizer()
        except ImportError:
            self._viz = None
            logger.debug("Visualizer no disponible aún.")

        logger.info(
            f"AndaluciaQuickData inicializado "
            f"(provincia='{provincia or 'todas'}', "
            f"cache='{self._cache.cache_dir}')"
        )

    # ------------------------------------------------------------------
    # Datos Espaciales (WFS / DERA)
    # ------------------------------------------------------------------

    def get_map(
        self,
        layer: str = "municipios",
        provincia: Optional[str] = None,
        max_features: int = 5000,
    ) -> gpd.GeoDataFrame:
        """
        Descarga una capa vectorial del DERA como GeoDataFrame.

        Parameters
        ----------
        layer : str
            Alias de la capa. Opciones: 'municipios', 'provincias',
            'comarcas', 'rios', 'embalses', 'carreteras', etc.
        provincia : str, optional
            Filtra por provincia. Si no se indica, usa la provincia
            del constructor. Si ninguna, devuelve toda Andalucía.
        max_features : int
            Máximo de features a descargar.

        Returns
        -------
        geopandas.GeoDataFrame

        Examples
        --------
        >>> aqd = AndaluciaQuickData()
        >>> gdf = aqd.get_map("municipios", provincia="Granada")
        """
        prov = provincia or self.provincia
        return self._wfs.get_layer(layer, provincia=prov, max_features=max_features)

    def list_layers(self) -> dict:
        """
        Devuelve el catálogo de capas vectoriales disponibles.

        Returns
        -------
        dict
            Diccionario con alias → (servicio, nombre_capa).
        """
        return self._wfs.list_layers()

    # ------------------------------------------------------------------
    # Datos Estadísticos (SIMA / IECA)
    # ------------------------------------------------------------------

    def get_stats(
        self,
        municipio_cod: Union[str, int],
        indicators: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Obtiene estadísticas municipales del SIMA/IECA.

        Parameters
        ----------
        municipio_cod : str | int
            Código INE del municipio de 5 dígitos (ej: '29060' = Málaga).
        indicators : list[str], optional
            Lista de indicadores a extraer. Si None, devuelve todos.

        Returns
        -------
        pandas.DataFrame

        Examples
        --------
        >>> aqd = AndaluciaQuickData()
        >>> df = aqd.get_stats("41091")  # Sevilla capital
        """
        if self._sima is None:
            raise RuntimeError(
                "SimaScraper no disponible. Ejecuta: "
                "pip install andalucia-quick-data[full]"
            )
        return self._sima.get_stats(str(municipio_cod), indicators=indicators)

    # ------------------------------------------------------------------
    # Visualización
    # ------------------------------------------------------------------

    def plot_choropleth(
        self,
        layer: str = "municipios",
        indicator: Optional[str] = None,
        provincia: Optional[str] = None,
        title: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
    ):
        """
        Genera un mapa coroplético iterativo con Folium.

        Parameters
        ----------
        layer : str
            Capa vectorial base (default: 'municipios').
        indicator : str, optional
            Indicador estadístico del SIMA para colorear el mapa.
            Si la capa no es 'municipios', el indicador no se cargará automáticamente.
        provincia : str, optional
            Filtra por provincia.
        title : str, optional
            Título del mapa.
        output_path : str | Path, optional
            Ruta donde guardar el HTML. Si None, muestra en notebook.

        Returns
        -------
        folium.Map
        """
        if self._viz is None:
            raise RuntimeError("Visualizer no disponible. Ejecuta: pip install andalucia-quick-data[full]")

        prov = provincia or self.provincia
        gdf = self.get_map(layer, provincia=prov)
        
        indicator_data = None
        if indicator and layer == "municipios":
            logger.info(f"Descargando/recuperando indicador '{indicator}' para todos los municipios...")
            geom_key = next((c for c in ['codigo', 'cod_muni', 'cod_ine', 'c_muni_ine'] if c in gdf.columns), None)
            
            if geom_key:
                dfs = []
                municipios = gdf[geom_key].dropna().unique()
                for cod in municipios:
                    try:
                        df_mun = self.get_stats(cod, indicators=[indicator])
                        if not df_mun.empty:
                            # Nos quedamos con el último valor disponible del indicador
                            last_val = df_mun.iloc[-1].copy()
                            last_val["Codigo"] = cod
                            dfs.append(last_val.to_frame().T)
                    except Exception as exc:
                        logger.debug(f"Saltando municipio {cod}: {exc}")
                        
                if dfs:
                    indicator_data = pd.concat(dfs, ignore_index=True)

        return self._viz.choropleth(
            gdf=gdf,
            indicator_data=indicator_data,
            indicator_name=indicator,
            title=title or f"Mapa de {layer} — {prov or 'Andalucía'}",
            output_path=output_path,
        )

    def plot_stats(
        self,
        municipio_cod: Union[str, int],
        indicator: str,
        chart_type: str = "bar",
    ):
        """
        Genera un gráfico estadístico con Plotly.

        Parameters
        ----------
        municipio_cod : str | int
            Código INE del municipio.
        indicator : str
            Indicador estadístico (ej: 'paro', 'renta').
        chart_type : str
            Tipo de gráfico: 'bar', 'line', 'pie'. Default: 'bar'.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        if self._viz is None:
            raise RuntimeError("Visualizer no disponible.")

        df = self.get_stats(municipio_cod)
        return self._viz.plot_stats(df, indicator=indicator, chart_type=chart_type)

    # ------------------------------------------------------------------
    # Gestión de caché
    # ------------------------------------------------------------------

    def cache_info(self) -> dict:
        """Devuelve información sobre el estado de la caché."""
        return self._cache.info()

    def cache_clear(self) -> int:
        """Limpia toda la caché local. Devuelve el número de entradas eliminadas."""
        return self._cache.clear()
