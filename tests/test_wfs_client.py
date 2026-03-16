"""
Tests para el módulo WFSClient.

Ejecutar con:
    poetry run pytest tests/ -v
"""

import pytest
import geopandas as gpd
from unittest.mock import MagicMock, patch

from andalucia_quick_data.cache import Cache
from andalucia_quick_data.wfs_client import WFSClient, LAYER_CATALOG


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_cache(tmp_path):
    """Cache real en directorio temporal."""
    return Cache(cache_dir=tmp_path / ".aqd_cache_test")


@pytest.fixture
def client(mock_cache):
    """WFSClient con caché temporal."""
    return WFSClient(cache=mock_cache)


# ---------------------------------------------------------------------------
# Tests del catálogo de capas
# ---------------------------------------------------------------------------

class TestLayerCatalog:
    def test_catalog_not_empty(self):
        assert len(LAYER_CATALOG) > 0

    def test_catalog_has_municipios(self):
        assert "municipios" in LAYER_CATALOG

    def test_catalog_has_provincias(self):
        assert "provincias" in LAYER_CATALOG

    def test_catalog_values_are_tuples(self):
        for alias, value in LAYER_CATALOG.items():
            assert isinstance(value, tuple), f"'{alias}' debe ser una tupla"
            assert len(value) == 2, f"'{alias}' debe tener (servicio, capa)"

    def test_list_layers_returns_copy(self, client):
        layers = client.list_layers()
        assert layers is not LAYER_CATALOG  # Debe ser una copia


# ---------------------------------------------------------------------------
# Tests de errores
# ---------------------------------------------------------------------------

class TestWFSClientErrors:
    def test_invalid_layer_raises_value_error(self, client):
        with pytest.raises(ValueError, match="no encontrada"):
            client.get_layer("capa_inexistente_xyz")

    def test_error_message_shows_available_layers(self, client):
        try:
            client.get_layer("capa_que_no_existe")
        except ValueError as e:
            assert "municipios" in str(e)


# ---------------------------------------------------------------------------
# Tests con mock del endpoint WFS
# ---------------------------------------------------------------------------

class TestWFSClientMocked:
    @patch("andalucia_quick_data.wfs_client.requests.get")
    def test_get_layer_calls_correct_url(self, mock_get, client):
        """Verifica que se llama al endpoint correcto para 'municipios'."""
        # Mock de respuesta GeoJSON mínima
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"type":"FeatureCollection","features":[]}'
        mock_get.return_value = mock_response

        with patch("andalucia_quick_data.wfs_client.gpd.read_file") as mock_read:
            import geopandas as gpd_mod
            mock_read.return_value = gpd_mod.GeoDataFrame()
            client.get_layer("municipios")

        call_args = mock_get.call_args
        url = call_args[0][0]
        assert "DERA_g13_limites_administrativos" in url

    @patch("andalucia_quick_data.wfs_client.requests.get")
    def test_local_filter_on_provincia(self, mock_get, client):
        """Verifica que si pasamos provincia el gdf se filtra localmente"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"type":"FeatureCollection","features":[]}'
        mock_get.return_value = mock_response

        with patch("andalucia_quick_data.wfs_client.gpd.read_file") as mock_read:
            import geopandas as gpd_mod
            from shapely.geometry import Point
            # Simulamos un dataframe con provincia y geometria
            mock_read.return_value = gpd_mod.GeoDataFrame(
                {"provincia": ["Sevilla", "Málaga", "Cádiz"]},
                geometry=[Point(0,0), Point(1,1), Point(2,2)],
                crs="EPSG:4326"
            )
            gdf = client.get_layer("municipios", provincia="Sevilla")

        assert len(gdf) == 1
        assert "Sevilla" in gdf["provincia"].values


# ---------------------------------------------------------------------------
# Tests de caché
# ---------------------------------------------------------------------------

class TestCacheIntegration:
    def test_cache_miss_then_hit(self, mock_cache, tmp_path):
        """Verifica que la segunda llamada usa caché."""
        import geopandas as gpd
        from shapely.geometry import Point

        # Guardar algo en caché
        gdf = gpd.GeoDataFrame(
            {"nombre": ["Test"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        mock_cache.set("wfs_municipios_all", gdf)

        # Recuperar
        result = mock_cache.get("wfs_municipios_all")
        assert result is not None
        assert len(result) == 1

    def test_cache_info(self, mock_cache):
        info = mock_cache.info()
        assert "cache_dir" in info
        assert "ttl_hours" in info
        assert "entries" in info

    def test_cache_clear(self, mock_cache):
        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame(
            {"nombre": ["Test"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        mock_cache.set("wfs_test_layer", gdf)
        count = mock_cache.clear()
        assert count >= 1
        assert mock_cache.get("wfs_test_layer") is None
