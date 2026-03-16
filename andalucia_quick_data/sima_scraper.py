"""
sima_scraper.py
===============
Scraper para las fichas HTML del SIMA/IECA de la Junta de Andalucía.

La página del SIMA está formada por tablas HTML de 2 columnas donde
la primera columna es "Indicador. Año" y la segunda es el valor.
Este módulo utiliza pandas.read_html para extraer tabularmente esos datos.
"""

import logging
from io import StringIO
from typing import Optional

import pandas as pd
import requests

from andalucia_quick_data.cache import Cache

logger = logging.getLogger(__name__)

SIMA_BASE_URL = (
    "https://www.juntadeandalucia.es/institutodeestadisticaycartografia"
    "/sima/ficha.htm"
)


class SimaScraper:
    """
    Scraper de estadísticas municipales del SIMA/IECA.

    Parameters
    ----------
    cache : Cache
        Instancia de caché compartida.
    """

    def __init__(self, cache: Cache) -> None:
        self.cache = cache
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_stats(
        self,
        municipio_cod: str,
        indicators: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Obtiene estadísticas de un municipio del SIMA.

        Parameters
        ----------
        municipio_cod : str
            Código INE del municipio (5 dígitos). Ej: '29060'.
        indicators : list[str], optional
            Filtrar por indicadores concretos. Busca ocurrencias parciales
            (ej: "Población"). Ignorando mayúsculas.

        Returns
        -------
        pandas.DataFrame
            DataFrame con columnas: Indicador, Valor
        """
        municipio_cod = str(municipio_cod).zfill(5)
        cache_key = f"sima_{municipio_cod}"
        
        # 1. Intentar acceder desde la caché
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.info(f"[SIMA] Datos para {municipio_cod} leídos de caché.")
            df = cached
        else:
            # 2. Scrapear la web si no está en caché
            logger.info(f"[SIMA] Descargando datos para municipio {municipio_cod}...")
            url = f"{SIMA_BASE_URL}?mun={municipio_cod}"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                if exc.response.status_code == 404:
                    raise ValueError(f"El municipio {municipio_cod} no existe en el SIMA.") from exc
                raise ConnectionError(f"Error HTTP accediendo al SIMA: {exc}") from exc
            
            try:
                # pandas parsea mejor si usamos utf-8
                html_io = StringIO(response.text)
                tables = pd.read_html(html_io)
            except ValueError as exc:
                raise ValueError(f"No se encontraron tablas de datos en el SIMA para {municipio_cod}.") from exc

            # 3. Concatenar y limpiar todas las tablas válidas (sólamente las de 2 columnas)
            dfs = []
            for t in tables:
                if t.shape[1] == 2:
                    t.columns = ["Indicador Original", "Valor"]
                    dfs.append(t)
            
            if not dfs:
                raise ValueError(f"El municipio {municipio_cod} no contiene datos válidos en el SIMA.")
                
            df = pd.concat(dfs, ignore_index=True)
            df = df.dropna(subset=["Indicador Original"]).copy()
            
            # Limpiar caracteres raros y normalizar columnas
            df["Indicador Original"] = df["Indicador Original"].astype(str).str.strip()
            df["Valor"] = df["Valor"].astype(str).str.strip().replace("nan", "")
            
            # Separar "Nombre. Año" en dos columnas (si es posible)
            # Ej: "Población total. 2025" -> "Población total", "2025"
            splits = df["Indicador Original"].str.rsplit(".", n=1, expand=True)
            if splits.shape[1] == 2:
                df["Indicador"] = splits[0].str.strip()
                df["Año"] = splits[1].str.strip()
            else:
                df["Indicador"] = df["Indicador Original"]
                df["Año"] = None
                
            # Guardamos en caché
            self.cache.set(cache_key, df)

        # 4. Filtrar por indicadores si el usuario lo requiere
        if indicators:
            mask = False
            for ind in indicators:
                mask |= df["Indicador Original"].str.contains(ind, case=False, na=False)
            df = df[mask]
            
        return df.reset_index(drop=True)

