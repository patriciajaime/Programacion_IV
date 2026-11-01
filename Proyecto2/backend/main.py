"""
==============================================================================
MÓDULO PRINCIPAL: SIMULADOR DE VENTA RELÁMPAGO CON FASTAPI
==============================================================================
Descripción:
    API REST para la gestión de productos y procesamiento concurrente de ventas
    relámpago. Implementa la prevención de condiciones de carrera (Race Conditions)
    mediante la sincronización asíncrona con `asyncio.Lock()`.

Asignatura:   Programación IV
Profesor:     Diego Alberto Ayala Vázquez
Autora:       Patricia Jaime
Fecha:        Octubre de 2026
==============================================================================
"""

import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware  # <-- IMPORTADO: Permite configurar políticas de origen cruzado (CORS)
from pydantic import BaseModel, Field

app = FastAPI(title="API Proyecto Tiendita - Venta Relámpago")

# ==============================================================================
# CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
# EXPLICACIÓN PARA EL PROFESOR:
# Agregamos este middleware porque los navegadores bloquean por seguridad las
# peticiones asíncronas (`fetch`) cuando el archivo `index.html` se abre localmente
# (`file://...`) e intenta consumir la API en otro origen (`http://127.0.0.1:8000`).
# Al habilitar `allow_origins=["*"]`, le permitimos al frontend consultar los datos
# sin restricciones del navegador para renderizar la tabla correctamente.
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Permite peticiones desde cualquier origen (incluyendo archivos HTML locales)
    allow_credentials=True,    # Permite el envío de credenciales/cookies si fuera necesario
    allow_methods=["*"],       # Permite todos los métodos HTTP (GET, POST, DELETE, etc.)
    allow_headers=["*"],       # Permite todas las cabeceras HTTP en las solicitudes
)

# Cerrojo para sincronización asíncrona global
lock = asyncio.Lock()

# Inventario simulado en memoria
inventario = [
    {"id": 1, "nombre": "Coca-Cola", "precio": 20.0, "cantidad": 25},
    {"id": 2, "nombre": "Papas", "precio": 15.0, "cantidad": 40},
    {"id": 3, "nombre": "Café", "precio": 18.0, "cantidad": 1}  # Producto Crítico
]

# Esquema para creación de productos
class ProductoEsquema(BaseModel):
    nombre: str = Field(..., min_length=1)
    precio: float = Field(..., gt=0)
    cantidad: int = Field(..., ge=0)


@app.get("/")
async def inicio() -> Dict[str, str]:
    """Ruta raíz de bienvenida y verificación del servidor."""
    return {"mensaje": "Bienvenido a la API de Venta Relámpago"}


@app.get("/productos")
async def consultar_catalogo() -> List[Dict[str, Any]]:
    """Consulta el catálogo completo de productos y su nivel de stock actual."""
    return inventario


@app.get("/productos/{producto_id}")
async def consultar_producto_por_id(producto_id: int) -> Dict[str, Any]:
    """Obtiene la información detallada de un producto específico por ID."""
    for objeto in inventario:
        if objeto["id"] == producto_id:
            return objeto
    raise HTTPException(status_code=404, detail="Producto no encontrado")


@app.post("/productos/{producto_id}")
async def comprar_producto(producto_id: int) -> Dict[str, str]:
    """
    Endpoint crítico de Venta Relámpago.
    Procesa la deducción de stock bajo escenarios de alta concurrencia.
    """
    try:
        # --- COMENTAR PARA EXPERIMENTO A (VULNERABLE) ---
        async with lock:
            for objeto in inventario:
                if objeto["id"] == producto_id:
                    if objeto["cantidad"] > 0:
                        await asyncio.sleep(0.05)
                        objeto["cantidad"] -= 1
                        return {"mensaje": "Producto comprado con éxito"}
                    else:
                        raise HTTPException(status_code=400, detail="No hay stock")
            raise HTTPException(status_code=404, detail="Producto no existe")

    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Error interno del servidor: {str(error)}"
        )


@app.post("/productos", status_code=status.HTTP_201_CREATED)
async def crear_producto(producto: ProductoEsquema) -> Dict[str, Any]:
    """Agrega un nuevo producto al inventario con ID autoincrementable."""
    nuevo_id = max([p["id"] for p in inventario], default=0) + 1
    nuevo_prod = {
        "id": nuevo_id,
        "nombre": producto.nombre,
        "precio": producto.precio,
        "cantidad": producto.cantidad
    }
    inventario.append(nuevo_prod)
    return nuevo_prod


@app.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: int) -> Dict[str, str]:
    """Elimina un producto del inventario por su ID."""
    global inventario
    for i, objeto in enumerate(inventario):
        if objeto["id"] == producto_id:
            inventario.pop(i)
            return {"mensaje": f"Producto con ID {producto_id} eliminado"}
    raise HTTPException(status_code=404, detail="Producto no encontrado para eliminar")