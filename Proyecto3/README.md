# Proyecto 3: Cumbre & Bosque — Tiendita Full-Stack con CSV y Pandas

Sistema web Full-Stack desarrollado para la asignatura **Programación IV** (CUGDL - Universidad de Guadalajara). Gestiona el catálogo, inventario y registro de ventas de una tienda de campismo mediante persistencia en archivos planos CSV, análisis de datos con Pandas y dashboard interactivo con Chart.js.

## Arquitectura del Proyecto

```text
Proyecto3/
├── backend/
│   ├── main.py          # API REST con FastAPI, validaciones Pydantic, CRUD en CSV y analítica Pandas
│   ├── productos.csv    # Base de datos plana del catálogo e inventario
│   └── ventas.csv       # Registro histórico de transacciones
├── frontend/
│   └── index.html       # Interfaz web responsiva, consumo asíncrono con fetch() y gráficas Chart.js
├── .gitignore           # Exclusión de archivos temporales
└── README.md            # Documentación del proyecto