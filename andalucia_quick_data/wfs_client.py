"""
wfs_client.py
=============
Cliente WFS para conectar con los servicios DERA de la Junta de Andalucía.

Fuente oficial:
    http://www.ideandalucia.es/services/DERA_gXX_nombre/wfs?service=wfs&request=getcapabilities

El patrón de URL es siempre:
    BASE_URL = "http://www.ideandalucia.es/services/{servicio}/wfs"

Capas disponibles (grupos DERA):
    - DERA_g1_relieve              → Relieve
    - DERA_g2_infra_geografica     → Infraestructura Geográfica
    - DERA_g3_hidrografia          → Hidrografía
    - DERA_g5_medio_marino         → Medio Marino
    - DERA_g6_usos_suelo           → Usos del Suelo
    - DERA_g7_sistema_urbano       → Sistema Urbano
    - DERA_g9_transport_com        → Transportes y Comunicaciones
    - DERA_g10_infra_energetica    → Infraestructuras Energéticas y Medioambientales
    - DERA_g11_patrimonio          → Patrimonio
    - DERA_g13_limites_administrativos → Límites Administrativos (municipios, provincias)
"""

import logging
from typing import Optional

import geopandas as gpd
import requests
from owslib.wfs import WebFeatureService

from andalucia_quick_data.cache import Cache

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Diccionario de capas disponibles: alias → (servicio_dera, nombre_capa_wfs)
# ---------------------------------------------------------------------------
LAYER_CATALOG: dict[str, tuple[str, str]] = {
    # Límites administrativos (más usados)
    "municipios": ("DERA_g13_limites_administrativos", "DERA_g13_limites_administrativos:g13_01_TerminoMunicipal"),
    "provincias": ("DERA_g13_limites_administrativos", "DERA_g13_limites_administrativos:g13_01_Provincia"),
    "comarcas": ("DERA_g13_limites_administrativos", "DERA_g13_limites_administrativos:g13_10_ComarcaAgraria"),
    # Sistema urbano
    "nucleos_urbanos": ("DERA_g7_sistema_urbano", "DERA_g7_sistema_urbano:g7_010_nucleos_pob"),
    # Transportes
    "carreteras": ("DERA_g9_transport_com", "DERA_g9_transport_com:g9_010_carreteras"),
    "ferrocarril": ("DERA_g9_transport_com", "DERA_g9_transport_com:g9_020_ferrocarril"),
    # Hidrografía
    "rios": ("DERA_g3_hidrografia", "DERA_g3_hidrografia:g3_010_rios"),
    "embalses": ("DERA_g3_hidrografia", "DERA_g3_hidrografia:g3_040_embalses"),
    # Relieve
    "cotas": ("DERA_g1_relieve", "DERA_g1_relieve:g1_010_cotas"),
}

WFS_BASE_URL = "http://www.ideandalucia.es/services/{servicio}/wfs"
WFS_VERSION = "2.0.0"


class WFSClient:
    """
    Cliente para los servicios WFS del DERA de la Junta de Andalucía.

    Parameters
    ----------
    cache : Cache
        Instancia de caché compartida para evitar descargas repetidas.
    timeout : int
        Timeout en segundos para las peticiones HTTP (default: 30).
    """

    def __init__(self, cache: Cache, timeout: int = 30) -> None:
        self.cache = cache
        self.timeout = timeout
        self._wfs_connections: dict[str, WebFeatureService] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_layer(
        self,
        layer_alias: str,
        provincia: Optional[str] = None,
        max_features: int = 5000,
    ) -> gpd.GeoDataFrame:
        """
        Descarga una capa vectorial del DERA y la devuelve como GeoDataFrame.

        Parameters
        ----------
        layer_alias : str
            Alias de la capa (ver LAYER_CATALOG). Ej: "municipios", "rios".
        provincia : str, optional
            Filtra por nombre de provincia. Ej: "Sevilla", "Málaga".
        max_features : int
            Número máximo de features a descargar (default: 5000).

        Returns
        -------
        geopandas.GeoDataFrame
            Capa vectorial en CRS EPSG:4326 (WGS84).

        Raises
        ------
        ValueError
            Si el alias de capa no existe en el catálogo.
        ConnectionError
            Si el servicio WFS no está disponible.
        """
        alias = layer_alias.lower().strip()
        if alias not in LAYER_CATALOG:
            available = ", ".join(sorted(LAYER_CATALOG.keys()))
            raise ValueError(
                f"Capa '{layer_alias}' no encontrada. "
                f"Capas disponibles: {available}"
            )

        servicio, layer_name = LAYER_CATALOG[alias]
        cache_key = f"wfs_{alias}_{provincia or 'all'}"

        # Intentar recuperar de caché
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"[WFS] Capa '{alias}' recuperada de caché.")
            return cached

        # Descargar del servicio WFS
        logger.info(f"[WFS] Descargando capa '{alias}' desde DERA...")
        gdf = self._fetch_wfs(servicio, layer_name, provincia, max_features)

        # Guardar en caché
        self.cache.set(cache_key, gdf)
        return gdf

    def list_layers(self) -> dict[str, tuple[str, str]]:
        """Devuelve el catálogo completo de capas disponibles."""
        return LAYER_CATALOG.copy()

    def get_capabilities(self, servicio: str) -> list[str]:
        """
        Obtiene las capas disponibles en un servicio WFS concreto.

        Parameters
        ----------
        servicio : str
            Nombre del servicio DERA. Ej: "DERA_g13_limites_administrativos".

        Returns
        -------
        list[str]
            Lista de nombres de capas WFS disponibles en ese servicio.
        """
        wfs = self._get_wfs_connection(servicio)
        return list(wfs.contents.keys())

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _get_wfs_connection(self, servicio: str) -> WebFeatureService:
        """Obtiene (o crea) una conexión WFS para el servicio indicado."""
        if servicio not in self._wfs_connections:
            url = WFS_BASE_URL.format(servicio=servicio)
            logger.debug(f"[WFS] Conectando a: {url}")
            try:
                wfs = WebFeatureService(
                    url=url,
                    version=WFS_VERSION,
                    timeout=self.timeout,
                )
                self._wfs_connections[servicio] = wfs
            except Exception as exc:
                raise ConnectionError(
                    f"No se pudo conectar al servicio WFS '{servicio}': {exc}"
                ) from exc
        return self._wfs_connections[servicio]

    def _fetch_wfs(
        self,
        servicio: str,
        layer_name: str,
        provincia: Optional[str],
        max_features: int,
    ) -> gpd.GeoDataFrame:
        """
        Descarga una capa WFS y la convierte a GeoDataFrame.
        Usa GetFeature con output GeoJSON para máxima compatibilidad.
        """
        url = WFS_BASE_URL.format(servicio=servicio)
        params = {
            "service": "WFS",
            "version": WFS_VERSION,
            "request": "GetFeature",
            "typeNames": layer_name,
            "outputFormat": "application/json",
            "count": max_features,
            "srsName": "EPSG:4326",
        }

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise ConnectionError(
                f"Timeout al conectar con el servicio DERA '{servicio}'. "
                "Comprueba tu conexión o inténtalo más tarde."
            )
        except requests.exceptions.HTTPError as exc:
            raise ConnectionError(
                f"Error HTTP {exc.response.status_code} en el servicio DERA '{servicio}'."
            ) from exc

        try:
            gdf = gpd.read_file(response.text, driver="GeoJSON")
        except Exception as exc:
            raise ValueError(
                f"Error al parsear la respuesta GeoJSON de la capa '{layer_name}': {exc}"
            ) from exc

        # Filtrar por provincia localmente (más seguro que CQL_FILTER en GeoServer viejo)
        if provincia and not gdf.empty:
            prov_lower = provincia.lower()
            # Buscar alguna columna que pueda contener el nombre de la provincia
            found_col = None
            for col in gdf.columns:
                if col.lower() in ["provincia", "nompro", "desc_prov", "prov"]:
                    found_col = col
                    break
            
            if found_col:
                gdf = gdf[gdf[found_col].astype(str).str.lower() == prov_lower]
        
        if gdf.empty:
            logger.warning(
                f"[WFS] La capa '{layer_name}' devolvió 0 features "
                f"(provincia='{provincia}')."
            )
            return gdf

        # Asegurar CRS estándar
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")

        logger.info(
            f"[WFS] Capa '{layer_name}' descargada: {len(gdf)} features."
        )
        return gdf
