"""
==============================================================================
MÓDULO DE PRUEBAS DE ESTRÉS Y CONCURRENCIA CON LOCUST
==============================================================================
Descripción:
    Generador de tráfico sintético para simular la Venta Relámpago.
    Evalúa la contención sobre el producto crítico (ID 3) bajo peticiones concurrentes.

Asignatura:   Programación IV
Profesor:     Diego Alberto Ayala Vázquez
Autora:       Patricia Jaime
Fecha:        Octubre de 2026
==============================================================================
"""

from locust import HttpUser, task, between

class UsuarioTienditaCompleto(HttpUser):
    """Simulador de comportamiento de cliente en la Venta Relámpago."""
    
    # Intervalo aleatorio de descanso entre 0.2s y 0.8s por usuario
    wait_time = between(0.2, 0.8)

    @task(5)
    def comprarProducto(self):
        """Simula la intención masiva de compra del producto crítico (Café ID 3)."""
        with self.client.post("/productos/3", catch_response=True) as response:
            # catch_response=True evita registrar el agotamiento de stock (400) como falla del sistema
            if response.status_code in [200, 400]:
                response.success()

    @task(2)
    def getProducto(self):
        """Simula la consulta general del catálogo."""
        self.client.get("/productos")

    @task(1)
    def consultarInicio(self):
        """Tarea adicional requerida: Simula la navegación a la ruta raíz."""
        self.client.get("/")