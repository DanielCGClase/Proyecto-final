"""
cache.py
========
Sistema de caché local con TTL de 24 horas para evitar descargas repetidas.

Utiliza el sistema de ficheros local para persistir GeoDataFrames y DataFrames
en formato Parquet (espacial y tabular respectivamente).

Estructura del directorio de caché::

    .aqd_cache/
    ├── index.json          ← Metadatos: timestamp de cada entrada
    ├── wfs_municipios_all.parquet
    ├── wfs_rios_Sevilla.parquet
    └── sima_29060.parquet
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd

logger = logging.getLogger(__name__)

# TTL por defecto: 24 horas en segundos
DEFAULT_TTL_SECONDS = 24 * 60 * 60
CACHE_DIR_NAME = ".aqd_cache"
INDEX_FILE = "index.json"


class Cache:
    """
    Caché local basada en sistema de ficheros con TTL configurable.

    Parameters
    ----------
    cache_dir : Path | str, optional
        Directorio raíz de la caché. Por defecto, se crea '.aqd_cache/'
        en el directorio de trabajo actual.
    ttl_seconds : int
        Tiempo de vida de las entradas en segundos (default: 86400 = 24h).
    """

    def __init__(
        self,
        cache_dir: Optional[Union[Path, str]] = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        if cache_dir is None:
            cache_dir = Path.cwd() / CACHE_DIR_NAME
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self._index: dict[str, float] = {}  # key → timestamp de escritura

        self._ensure_dir()
        self._load_index()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get(
        self, key: str
    ) -> Optional[Union[gpd.GeoDataFrame, pd.DataFrame]]:
        """
        Recupera un objeto de caché si existe y no ha expirado.

        Parameters
        ----------
        key : str
            Clave única de la entrada (ej: 'wfs_municipios_Sevilla').

        Returns
        -------
        GeoDataFrame | DataFrame | None
            El objeto almacenado, o None si no existe / ha expirado.
        """
        if not self._is_valid(key):
            return None

        file_path = self._key_to_path(key)
        if not file_path.exists():
            return None

        try:
            if key.startswith("wfs_"):
                data = gpd.read_parquet(file_path)
            else:
                data = pd.read_parquet(file_path)
            logger.debug(f"[Cache] HIT: '{key}'")
            return data
        except Exception as exc:
            logger.warning(f"[Cache] Error leyendo '{key}': {exc}. Ignorando.")
            return None

    def set(
        self,
        key: str,
        data: Union[gpd.GeoDataFrame, pd.DataFrame],
    ) -> None:
        """
        Guarda un objeto en caché.

        Parameters
        ----------
        key : str
            Clave única de la entrada.
        data : GeoDataFrame | DataFrame
            Objeto a persistir.
        """
        file_path = self._key_to_path(key)
        try:
            if isinstance(data, gpd.GeoDataFrame):
                data.to_parquet(file_path)
            else:
                data.to_parquet(file_path)
            self._index[key] = time.time()
            self._save_index()
            logger.debug(f"[Cache] SET: '{key}' → {file_path.name}")
        except Exception as exc:
            logger.warning(f"[Cache] Error guardando '{key}': {exc}")

    def invalidate(self, key: str) -> bool:
        """
        Invalida (elimina) una entrada de caché.

        Returns
        -------
        bool
            True si la entrada existía y fue eliminada.
        """
        file_path = self._key_to_path(key)
        existed = file_path.exists()
        if existed:
            file_path.unlink(missing_ok=True)
        if key in self._index:
            del self._index[key]
            self._save_index()
        return existed

    def clear(self) -> int:
        """
        Limpia toda la caché.

        Returns
        -------
        int
            Número de entradas eliminadas.
        """
        count = 0
        for file in self.cache_dir.glob("*.parquet"):
            file.unlink(missing_ok=True)
            count += 1
        self._index.clear()
        self._save_index()
        logger.info(f"[Cache] Limpieza completa: {count} entradas eliminadas.")
        return count

    def info(self) -> dict:
        """Devuelve información sobre el estado actual de la caché."""
        now = time.time()
        entries = []
        for key, ts in self._index.items():
            age_secs = now - ts
            entries.append(
                {
                    "key": key,
                    "age_hours": round(age_secs / 3600, 2),
                    "expired": age_secs > self.ttl_seconds,
                    "file": self._key_to_path(key).name,
                }
            )
        return {
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl_seconds / 3600,
            "total_entries": len(entries),
            "entries": entries,
        }

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _is_valid(self, key: str) -> bool:
        """Comprueba si la entrada existe y no ha expirado."""
        ts = self._index.get(key)
        if ts is None:
            return False
        age = time.time() - ts
        if age > self.ttl_seconds:
            logger.debug(f"[Cache] MISS (expirado): '{key}' ({age/3600:.1f}h)")
            return False
        return True

    def _key_to_path(self, key: str) -> Path:
        """Convierte una clave de caché a ruta de fichero."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.parquet"

    def _ensure_dir(self) -> None:
        """Crea el directorio de caché si no existe."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_index(self) -> None:
        """Carga el índice de metadatos desde disco."""
        index_path = self.cache_dir / INDEX_FILE
        if index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception:
                self._index = {}

    def _save_index(self) -> None:
        """Persiste el índice de metadatos en disco."""
        index_path = self.cache_dir / INDEX_FILE
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2)
