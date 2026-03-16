import sys
from andalucia_quick_data import AndaluciaQuickData

def main():
    print("Inicializando la API...")
    aqd = AndaluciaQuickData("Almería")
    
    # Probando gráfico Plotly
    print("\nGenerando gráfica Plotly para Roquetas de Mar (04079)...")
    try:
        fig = aqd.plot_stats("04079", indicator="Población")
        if fig:
            print("Gráfica generada con éxito (no la mostramos para no bloquear el test).")
    except Exception as e:
        print(f"Error generando gráfica: {e}")
        
    # Probando mapa Folium sin indicador (solo geometrías)
    print("\nGenerando mapa Folium para Almería (solo base)...")
    try:
        m = aqd.plot_choropleth("municipios", output_path="mapa_almeria.html")
        print("Mapa generado y guardado en mapa_almeria.html")
    except Exception as e:
        print(f"Error generando mapa base: {e}")

if __name__ == "__main__":
    main()
