# Proyecto: Andalucía Quick Data

Este plan detalla la ejecución de una librería Python para facilitar el acceso a datos espaciales y estadísticos de Andalucía, diseñada para un equipo de 4 personas.

## 1. Estructura Organizativa

Se define un equipo multidisciplinar equilibrado para cubrir todas las áreas críticas:

| Perfil | Rol Principal | Responsabilidades Clave |
| :--- | :--- | :--- |
| **Lead Backend & Architect** | Arquitectura y Core | Diseño del sistema, integración WFS (DERA), sistema de caché. |
| **Data Engineer** | Ingesta y Normalización | Scraping de SIMA/IECA, limpieza de datos, mantenimiento de diccionarios. |
| **UX/Visualization Specialist** | Interfaz y Visualización | Desarrollo de mapas (Folium), gráficos (Plotly) y API de alto nivel. |
| **QA & DevOps Engineer** | Calidad y Despliegue | Suite de tests (pytest), empaquetado (pyproject.toml), documentación. |

### Workflow de Comunicación
- **Sincronía**: Daily de 15 min (vía Slack/Teams) para bloquear/desbloquear tareas.
- **Cisterna de Código**: GitHub/GitLab con Pull Requests obligatorias revisadas por el Lead Backend.
- **Documentación**: Wiki interna o README.md técnico centralizado.

## 2. Asignación de Tareas

| Fase | Tarea Actionable | Perfil Responsable |
| :--- | :--- | :--- |
| **I. Core** | Diseño de la arquitectura base y estructura de paquetes. | Lead Backend & Architect |
| **I. Core** | Implementación del cliente WFS para capas DERA. | Lead Backend & Architect |
| **II. Data** | Motor de scraping para fichas HTML de SIMA. | Data Engineer |
| **II. Data** | Normalización de GeoDataFrames y DataFrames. | Data Engineer |
| **III. Logic** | Sistema de caché local (24h) con persistencia. | Lead Backend & Architect |
| **III. UI** | Integración de Folium para mapas coropléticos. | UX/Visualization Specialist |
| **III. UI** | Generación de gráficos estadísticos con Plotly. | UX/Visualization Specialist |
| **IV. QA** | Implementación de tests unitarios e integración (pytest). | QA & DevOps Engineer |
| **IV. DevOps** | Configuración de `pyproject.toml` y empaquetado. | QA & DevOps Engineer |

## 3. Stack Tecnológico

| Capa | Tecnología | Justificación |
| :--- | :--- | :--- |
| **Lenguaje** | Python 3.10+ | Estándar en análisis de datos y compatible con todo el ecosistema Geo. |
| **Datos Espaciales** | GeoPandas / OWSLib | Simplifican drásticamente el manejo de capas vectoriales y protocolos OGC (WFS). |
| **Scraping** | BS4 + Requests | Herramientas ligeras y robustas para extraer datos de fichas HTML del SIMA. |
| **Visualización** | Folium / Plotly | Mapas interactivos listos para Notebooks y dashboards web. |
| **Caché** | SQLite / File system | Persistencia simple para cumplir con el requisito de 24h sin complejidad de servidores. |
| **Testing** | Pytest | Facilidad para testing parametrizado y reportes de cobertura. |

## 4. Guion de Trabajo (Roadmap)

1.  **Semana 1: Cimentación (MVP Core)**: Definición de la estructura del paquete y conexión inicial a DERA (WFS).
2.  **Semana 2: Enriquecimiento de Datos**: Finalización del scraper de SIMA y lógica de unión (merge) de datos geo/estadísticos.
3.  **Semana 3: Visualización y API**: Implementación de `get_map()`, `get_stats()` y `plot_choropleth()`. Lógica de caché.
4.  **Semana 4: Pulido y Entrega**: Testing exhaustivo, documentación de API y empaquetado final para distribución (.whl).

## 5. Estimación de Tiempos

- **Desarrollo Core & Data**: 80 horas hombre.
- **Visualización & API**: 45 horas hombre.
- **Testing, DevOps & Doc**: 35 horas hombre.
- **Subtotal**: 160 horas (4 semanas para el equipo).
- **Contingencia (15%)**: 24 horas.
- **Total Estimado**: **184 horas**.

> [!IMPORTANT]
> El éxito del proyecto depende de la estabilidad de los endpoints de la Junta de Andalucía. Se recomienda implementar un sistema de alertas para cuando un endpoint cambie su estructura.
