"""
Backend de la Tiendita de Campismo (Proyecto 3 - Programación IV).
Proporciona una API REST con FastAPI para gestionar el inventario y las ventas
mediante persistencia en archivos CSV, además de exponer métricas analíticas
calculadas con Pandas para su visualización en el dashboard.
"""

from datetime import datetime
import os
from typing import Any, Dict, List

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Inicialización de la aplicación FastAPI con metadatos descriptivos
app = FastAPI(
    title="API Tiendita de Campismo",
    description="Sistema de gestión de inventario, ventas en CSV y analítica con Pandas.",
    version="1.0.0",
)

# Configuración de CORS para permitir la comunicación desde el cliente web (HTML/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se restringe al dominio específico del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definición de rutas absolutas hacia los archivos planos de persistencia
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTOS_CSV = os.path.join(BASE_DIR, "productos.csv")
VENTAS_CSV = os.path.join(BASE_DIR, "ventas.csv")


# ==============================================================================
# MODELOS DE VALIDACIÓN DE DATOS (PYDANTIC)
# ==============================================================================

class ProductoNuevo(BaseModel):
    """Esquema de validación para registrar un nuevo artículo en el catálogo."""
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del artículo de campismo")
    precio: float = Field(..., gt=0, description="Precio unitario (debe ser mayor a 0)")
    stock: int = Field(..., ge=0, description="Existencias iniciales (no puede ser negativo)")


class CompraRequest(BaseModel):
    """Esquema de validación para procesar la compra de un producto."""
    cantidad: int = Field(default=1, gt=0, description="Cantidad de unidades a comprar")


# ==============================================================================
# FUNCIONES AUXILIARES DE PERSISTENCIA (PRINCIPIO DRY - DON'T REPEAT YOURSELF)
# ==============================================================================

def leer_csv_seguro(ruta_archivo: str, columnas_default: List[str]) -> pd.DataFrame:
    """
    Lee un archivo CSV y lo retorna como DataFrame de Pandas.
    Si el archivo no existe o está vacío, devuelve un DataFrame vacío con las columnas esperadas.
    """
    if not os.path.exists(ruta_archivo):
        return pd.DataFrame(columns=columnas_default)
    try:
        return pd.read_csv(ruta_archivo)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columnas_default)


def guardar_csv(df: pd.DataFrame, ruta_archivo: str) -> None:
    """Guarda un DataFrame en su archivo CSV correspondiente sin incluir el índice numérico."""
    df.to_csv(ruta_archivo, index=False)


# ==============================================================================
# ENDPOINTS CRUD DE INVENTARIO Y VENTAS (PERSISTENCIA EN CSV)
# ==============================================================================

@app.get("/productos", response_model=List[Dict[str, Any]], tags=["Inventario"])
def obtener_productos() -> List[Dict[str, Any]]:
    """
    Consulta y retorna todos los productos almacenados en productos.csv.
    """
    df_productos = leer_csv_seguro(PRODUCTOS_CSV, ["id", "nombre", "precio", "stock"])
    return df_productos.to_dict(orient="records")


@app.post("/productos", status_code=status.HTTP_201_CREATED, tags=["Inventario"])
def crear_producto(producto: ProductoNuevo) -> Dict[str, Any]:
    """
    Registra un nuevo producto asignándole un ID autoincremental y lo persiste en productos.csv.
    """
    df_productos = leer_csv_seguro(PRODUCTOS_CSV, ["id", "nombre", "precio", "stock"])

    # Calcular el siguiente ID disponible de forma segura
    nuevo_id = int(df_productos["id"].max() + 1) if not df_productos.empty else 1

    # Crear el registro del nuevo artículo limpiando espacios innecesarios en el nombre
    nuevo_registro = pd.DataFrame([{
        "id": nuevo_id,
        "nombre": producto.nombre.strip(),
        "precio": round(producto.precio, 2),
        "stock": producto.stock,
    }])

    # Concatenar al DataFrame existente y sobrescribir el archivo CSV
    df_actualizado = pd.concat([df_productos, nuevo_registro], ignore_index=True)
    guardar_csv(df_actualizado, PRODUCTOS_CSV)

    return {
        "mensaje": "Producto registrado exitosamente en el catálogo.",
        "producto": nuevo_registro.to_dict(orient="records")[0],
    }


@app.post("/productos/{producto_id}", tags=["Ventas"])
def comprar_producto(producto_id: int, compra: CompraRequest) -> Dict[str, Any]:
    """
    Procesa la compra de un producto:
    1. Verifica que el producto exista y cuente con stock suficiente.
    2. Descuenta la cantidad comprada en productos.csv.
    3. Registra la transacción con la fecha actual en ventas.csv.
    """
    df_productos = leer_csv_seguro(PRODUCTOS_CSV, ["id", "nombre", "precio", "stock"])

    # Validar existencia del producto
    if producto_id not in df_productos["id"].values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún producto con el ID {producto_id}.",
        )

    # Localizar la fila del producto seleccionado
    indice = df_productos.index[df_productos["id"] == producto_id][0]
    stock_disponible = int(df_productos.loc[indice, "stock"])

    # Validar disponibilidad de inventario
    if stock_disponible < compra.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Solo quedan {stock_disponible} unidades disponibles.",
        )

    # 1. Actualizar existencias en productos.csv
    df_productos.loc[indice, "stock"] = stock_disponible - compra.cantidad
    guardar_csv(df_productos, PRODUCTOS_CSV)

    # 2. Preparar datos de la transacción para ventas.csv
    nombre_producto = str(df_productos.loc[indice, "nombre"])
    precio_unitario = float(df_productos.loc[indice, "precio"])
    monto_total = round(precio_unitario * compra.cantidad, 2)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

    df_ventas = leer_csv_seguro(
        VENTAS_CSV, ["fecha", "producto", "precio", "cantidad", "monto_total"]
    )

    nueva_venta = pd.DataFrame([{
        "fecha": fecha_hoy,
        "producto": nombre_producto,
        "precio": precio_unitario,
        "cantidad": compra.cantidad,
        "monto_total": monto_total,
    }])

    # Persistir la venta en ventas.csv
    df_ventas_actualizado = pd.concat([df_ventas, nueva_venta], ignore_index=True)
    guardar_csv(df_ventas_actualizado, VENTAS_CSV)

    return {
        "mensaje": f"Compra realizada: {compra.cantidad} unidad(es) de '{nombre_producto}'.",
        "monto_total": monto_total,
    }


@app.delete("/productos/{producto_id}", tags=["Inventario"])
def eliminar_producto(producto_id: int) -> Dict[str, str]:
    """
    Elimina un producto del catálogo según su ID y reescribe productos.csv sin dicho registro.
    """
    df_productos = leer_csv_seguro(PRODUCTOS_CSV, ["id", "nombre", "precio", "stock"])

    if producto_id not in df_productos["id"].values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el producto con ID {producto_id} para eliminar.",
        )

    # Filtrar el DataFrame conservando únicamente los registros distintos al ID eliminado
    df_filtrado = df_productos[df_productos["id"] != producto_id]
    guardar_csv(df_filtrado, PRODUCTOS_CSV)

    return {"mensaje": f"Producto con ID {producto_id} eliminado correctamente."}


# ==============================================================================
# ENDPOINTS ANALÍTICOS CON PANDAS (PARA DASHBOARD Y GRÁFICAS)
# ==============================================================================

@app.get("/api/kpis", tags=["Analítica"])
def obtener_kpis() -> Dict[str, Any]:
    """
    Calcula los indicadores clave de rendimiento (KPIs) a partir de ventas.csv:
    - Ingresos totales acumulados.
    - Número total de transacciones registradas.
    - Ticket promedio por venta.
    - Producto más vendido (por unidades acumuladas).
    """
    df_ventas = leer_csv_seguro(
        VENTAS_CSV, ["fecha", "producto", "precio", "cantidad", "monto_total"]
    )

    # Retornar valores neutros si aún no existen ventas registradas
    if df_ventas.empty:
        return {
            "ingresos_totales": 0.0,
            "total_transacciones": 0,
            "ticket_promedio": 0.0,
            "producto_estrella": "Sin ventas aún",
        }

    ingresos_totales = float(df_ventas["monto_total"].sum())
    total_transacciones = int(len(df_ventas))
    ticket_promedio = float(df_ventas["monto_total"].mean())

    # Agrupar por producto, sumar cantidades vendidas y obtener el índice con valor máximo
    producto_estrella = str(df_ventas.groupby("producto")["cantidad"].sum().idxmax())

    return {
        "ingresos_totales": round(ingresos_totales, 2),
        "total_transacciones": total_transacciones,
        "ticket_promedio": round(ticket_promedio, 2),
        "producto_estrella": producto_estrella,
    }


@app.get("/api/graficas/productos", response_model=List[Dict[str, Any]], tags=["Analítica"])
def obtener_ventas_por_producto() -> List[Dict[str, Any]]:
    """
    Agrupa el historial de ventas por producto y suma el monto total generado por cada uno.
    Retorna una lista de diccionarios lista para graficar en Chart.js.
    """
    df_ventas = leer_csv_seguro(
        VENTAS_CSV, ["fecha", "producto", "precio", "cantidad", "monto_total"]
    )
    if df_ventas.empty:
        return []

    serie_productos = (
        df_ventas.groupby("producto")["monto_total"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    return serie_productos.to_dict(orient="records")


@app.get("/api/graficas/fechas", response_model=List[Dict[str, Any]], tags=["Analítica"])
def obtener_ventas_por_fecha() -> List[Dict[str, Any]]:
    """
    Agrupa el historial de ventas cronológicamente por fecha y suma los ingresos diarios.
    Retorna una lista ordenada lista para graficar tendencias en Chart.js.
    """
    df_ventas = leer_csv_seguro(
        VENTAS_CSV, ["fecha", "producto", "precio", "cantidad", "monto_total"]
    )
    if df_ventas.empty:
        return []

    serie_fechas = (
        df_ventas.groupby("fecha")["monto_total"]
        .sum()
        .sort_index()
        .reset_index()
    )
    return serie_fechas.to_dict(orient="records")