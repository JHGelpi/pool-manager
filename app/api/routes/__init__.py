from app.api.routes.health import router as health_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.readings import router as readings_router

__all__ = [
    "health_router",
    "inventory_router",
    "tasks_router",
    "alerts_router",
    "readings_router",
]
