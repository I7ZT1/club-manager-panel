from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user
from routers.v1.auth_router import router as auth_router
from routers.v1.users_router import router as users_router
from routers.v1.bonus_router import router as bonus_router
from routers.v1.billing_router import router as billing_router
from routers.v1.payment_router import router as payment_router

routers_api = APIRouter(prefix="/api/v1")
routers_api.include_router(auth_router)
routers_api.include_router(users_router)
#routers_api.include_router(bonus_router)
routers_api.include_router(billing_router)
routers_api.include_router(payment_router)
