"""
Tests para el módulo SimaScraper.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from io import StringIO

from andalucia_quick_data.cache import Cache
from andalucia_quick_data.sima_scraper import SimaScraper


@pytest.fixture
def mock_cache(tmp_path):
    return Cache(cache_dir=tmp_path / ".aqd_cache_sima_test")


@pytest.fixture
def scraper(mock_cache):
    return SimaScraper(cache=mock_cache)


def test_get_stats_calls_correct_url(scraper):
    """Prueba que el scraper llame a la URL correcta y procese el HTML mockeado."""
    mock_html = '''
    <html><body>
        <table>
            <tr><th>Indicador. 2023</th><th>Valor</th></tr>
            <tr><td>Población. 2025</td><td>1000</td></tr>
            <tr><td>Paro registrado. 2025</td><td>100</td></tr>
        </table>
    </body></html>
    '''
    
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_html
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        
        df = scraper.get_stats("29060")
        
        # Validar llamada
        mock_get.assert_called_once()
        assert "mun=29060" in mock_get.call_args[0][0]
        
        # Validar DataFrame devuelto
        assert not df.empty
        assert "Población" in df["Indicador"].values
        assert "Paro registrado" in df["Indicador"].values
        assert "1000" in df["Valor"].values


def test_get_stats_filters_indicators(scraper):
    """Prueba que se aplican correctamente los filtros de indicadores."""
    mock_html = '''
    <html><body>
        <table>
            <tr><td>Población. 2025</td><td>1000</td></tr>
            <tr><td>Renta neta. 2022</td><td>12000</td></tr>
            <tr><td>Superficie. 2023</td><td>35</td></tr>
        </table>
    </body></html>
    '''
    with patch('requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_html
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        
        df = scraper.get_stats("29060", indicators=["Renta", "Superficie"])
        
        assert len(df) == 2
        assert "Población" not in df["Indicador"].values
        assert "Renta neta" in df["Indicador"].values


def test_get_stats_uses_cache(mock_cache, scraper):
    """Verifica que si los datos están en caché no se realiza petición HTTP."""
    df_mock = pd.DataFrame({
        "Indicador Original": ["Población. 2025"],
        "Valor": ["500"],
        "Indicador": ["Población"],
        "Año": ["2025"]
    })
    
    # Pre-cargar caché
    mock_cache.set("sima_29060", df_mock)
    
    with patch('requests.get') as mock_get:
        df = scraper.get_stats("29060")
        
        # No debe haber llamado a internet
        mock_get.assert_not_called()
        assert len(df) == 1
        assert df.iloc[0]["Valor"] == "500"
