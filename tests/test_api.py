"""
Tests para AndaluciaQuickData API.
"""

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from unittest.mock import patch, MagicMock

from andalucia_quick_data.api import AndaluciaQuickData


@pytest.fixture
def mock_aqd(tmp_path):
    return AndaluciaQuickData(provincia="Málaga", cache_dir=tmp_path / ".test_cache")


def test_init_sets_provincia(mock_aqd):
    assert mock_aqd.provincia == "Málaga"


@patch('andalucia_quick_data.api.WFSClient.list_layers')
def test_list_layers(mock_list, mock_aqd):
    mock_list.return_value = {"municipios": ("TEST", "test_layer")}
    layers = mock_aqd.list_layers()
    assert "municipios" in layers
    mock_list.assert_called_once()


@patch('andalucia_quick_data.api.WFSClient.get_layer')
def test_get_map(mock_get_layer, mock_aqd):
    # Crear un GeoDataFrame super básico
    gdf = gpd.GeoDataFrame(
        {"codigo": ["29060"]}, 
        geometry=[Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        crs="EPSG:4326"
    )
    mock_get_layer.return_value = gdf
    
    result = mock_aqd.get_map("municipios")
    
    # Validar que WFSClient.get_layer fue llamado con la provincia correcta
    mock_get_layer.assert_called_once_with("municipios", provincia="Málaga", max_features=5000)
    assert not result.empty
    assert "codigo" in result.columns


def test_get_stats(mock_aqd):
    df_mock = pd.DataFrame({"Indicador": ["Población"], "Valor": ["1000"]})
    mock_sima = MagicMock()
    mock_sima.get_stats.return_value = df_mock
    mock_aqd._sima = mock_sima
    
    result = mock_aqd.get_stats("29060", indicators=["Población"])
    
    mock_sima.get_stats.assert_called_once_with("29060", indicators=["Población"])
    assert not result.empty
    assert result.iloc[0]["Valor"] == "1000"


def test_plot_stats(mock_aqd):
    mock_viz = MagicMock()
    mock_viz.plot_stats.return_value = "figura"
    mock_aqd._viz = mock_viz
    
    with patch.object(mock_aqd, 'get_stats', return_value=pd.DataFrame()):
        fig = mock_aqd.plot_stats("29060", "Población")
    
    assert fig == "figura"
    mock_viz.plot_stats.assert_called_once()

