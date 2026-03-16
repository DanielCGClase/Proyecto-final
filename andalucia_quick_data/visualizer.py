"""
visualizer.py
=============
Módulo de visualización con Folium (mapas interactivos) y Plotly (gráficos).
"""

import logging
from pathlib import Path
from typing import Optional, Union

import geopandas as gpd
import pandas as pd
import folium
import plotly.express as px

logger = logging.getLogger(__name__)


class Visualizer:
    """Genera mapas coropléticos con Folium y gráficos con Plotly."""

    def choropleth(
        self,
        gdf: gpd.GeoDataFrame,
        indicator_data: Optional[pd.DataFrame] = None,
        indicator_name: Optional[str] = None,
        title: str = "Mapa Andalucía",
        fill_color: str = "YlOrRd",
        output_path: Optional[Union[str, Path]] = None,
    ):
        """
        Genera un mapa coroplético interactivo con Folium.
        
        Parameters
        ----------
        gdf : GeoDataFrame
            Datos espaciales (ej. municipios).
        indicator_data : DataFrame, optional
            Datos estadísticos a unir con el mapa. Debe tener al menos
            las columnas empleadas para el join ('Codigo', 'Valor').
        indicator_name : str, optional
            Nombre del indicador mostrado en la leyenda.
        title : str
            Título del mapa.
        fill_color : str
            Paleta de colores de folium (ColorBrewer).
        output_path : str | Path, optional
            Ruta para guardar fichero HTML. Si no se indica, devuelve el objeto Folium.
        """
        if gdf.empty:
            logger.warning("El GeoDataFrame está vacío. No se puede generar mapa.")
            return None

        # Asegurar CRS estándar web
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Centrar el mapa en las coordenadas promedio de Andalucía aprox
        center_lat = gdf.geometry.centroid.y.mean()
        center_lon = gdf.geometry.centroid.x.mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

        # Si no hay datos de indicador, solo dibujamos la capa base
        if indicator_data is None or indicator_data.empty:
            folium.GeoJson(
                gdf,
                name="Capa Base",
                style_function=lambda x: {'fillColor': '#3186cc', 'color': 'black', 'weight': 1, 'fillOpacity': 0.5}
            ).add_to(m)
        else:
            # Asumimos que gdf tiene 'cod_municipio' o similar y indicator_data tiene 'Codigo' o 'Municipio'
            # En DERA los municipios suelen tener 'cod_ine' o 'cod_muni'. Adaptaremos según lo que tenga.
            
            # Para hacer el join, necesitamos identificar la columna clave en gdf.
            # DERA suele usar 'codigo', 'cod_municipio', etc. Identificamos la primera que parezca un código.
            geom_key = None
            for col in ['codigo', 'cod_muni', 'cod_ine', 'c_muni_ine']:
                if col in gdf.columns:
                    geom_key = col
                    break
            
            if not geom_key and len(gdf.columns) > 1:
                geom_key = gdf.columns[0] # Fallback a la primera columna
                
            # Limpiamos los datos
            df_plot = indicator_data.copy()
            
            # Asumimos que df_plot tiene columnas como ["Codigo", "Valor"] o se ha procesado previamente.
            # Convertimos "Valor" a numérico
            if "Valor" in df_plot.columns:
                df_plot["Valor"] = pd.to_numeric(df_plot["Valor"].astype(str).str.replace(".", "").str.replace(",", "."), errors='coerce')
                
            # Identificamos columna clave en df_plot (por defecto 'Codigo' o 'Municipio')
            data_key = "Codigo" if "Codigo" in df_plot.columns else df_plot.columns[0]

            try:
                folium.Choropleth(
                    geo_data=gdf,
                    name='choropleth',
                    data=df_plot,
                    columns=[data_key, "Valor"],
                    key_on=f"feature.properties.{geom_key}",
                    fill_color=fill_color,
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name=indicator_name or "Indicador"
                ).add_to(m)
            except Exception as exc:
                logger.error(f"Error generando choropleth (¿claves mismatch?): {exc}")
                folium.GeoJson(gdf).add_to(m)

        folium.LayerControl().add_to(m)

        if output_path:
            m.save(str(output_path))
            logger.info(f"Mapa guardado en {output_path}")

        return m

    def plot_stats(
        self,
        df: pd.DataFrame,
        indicator: str,
        chart_type: str = "bar",
    ):
        """
        Genera un gráfico estadístico con Plotly a partir de un DataFrame.
        """
        if df.empty:
            logger.warning("DataFrame vacío, no se puede graficar.")
            return None
            
        # Limpiamos los valores para que sean numéricos
        df_plot = df.copy()
        if "Valor" in df_plot.columns:
            # Los valores de SIMA pueden venir como "1.234,56". Quitamos puntos de mil y cambiamos coma por punto.
            df_plot["Valor Numerico"] = pd.to_numeric(
                df_plot["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                errors="coerce"
            )

        title = f"{indicator} a lo largo del tiempo" if "Año" in df_plot.columns else f"Gráfico de {indicator}"
        
        # Filtramos NA
        df_plot = df_plot.dropna(subset=["Valor Numerico"])
        
        # Ordenamos por año si existe
        if "Año" in df_plot.columns and df_plot["Año"].notna().any():
            df_plot = df_plot.sort_values(by="Año")

        x_col = "Año" if "Año" in df_plot.columns and not df_plot["Año"].isna().all() else "Indicador"
        
        if chart_type == "bar":
            fig = px.bar(df_plot, x=x_col, y="Valor Numerico", title=title, text="Valor Numerico")
        elif chart_type == "line":
            fig = px.line(df_plot, x=x_col, y="Valor Numerico", title=title, markers=True)
        elif chart_type == "pie":
            fig = px.pie(df_plot, names=x_col, values="Valor Numerico", title=title)
        else:
            raise ValueError(f"Tipo de gráfico no soportado: {chart_type}")
            
        fig.update_layout(xaxis_title=x_col, yaxis_title="Valor")
        return fig

