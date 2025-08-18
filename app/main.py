from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
from routers import routers_api
from typing import Callable
import time
from utils.logger import setup_logging


logger = setup_logging()


def cors_setup(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://billing.klubok-kz.com:5173", "http://localhost:3000", "http://billing.cc-poker.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"],
        allow_headers=[
            "Set-Cookie",
            "Access-Control-Allow-Headers",
            "Content-Type",
            "Authorization",
            "Access-Control-Allow-Origin",
        ],
    )


def start_application():
    app = FastAPI()
    app.include_router(routers_api)
    cors_setup(app)
    app.mount("/uploads", StaticFiles(directory=str(settings.BASE_DIR) + "/uploads"), name="uploads")
    return app


app = start_application()


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    start_time = time.time()
    
    # Считываем тело запроса в память
    request_body = await request.body()
    
    # Переопределяем метод receive
    async def receive_override():
        return {
            "type": "http.request",
            "body": request_body,
            "more_body": False
        }

    modified_request = Request(request.scope, receive_override)

    try:
        # Отдаём запрос дальше
        response = await call_next(modified_request)
        duration = time.time() - start_time
        
        # ИСПРАВЛЕНО: Проверяем, не вернулся ли статус-код ошибки (4xx, 5xx)
        if response.status_code >= 400:  # Заменил True на response.status_code >= 400
            logger.error(
                f"⛑️ Ошибка: {response.status_code}. "
                f"Метод: {request.method}, Путь: {request.url.path}, Время: {duration:.2f}s"
            )
            # Логируем тело запроса только при ошибках
            logger.error(f"Тело запроса: {request_body.decode('utf-8', errors='replace')}")

            # Читаем тело ответа
            response_body = b"".join([chunk async for chunk in response.body_iterator])
            logger.error(f"Тело ответа: {response_body.decode('utf-8', errors='replace')}")

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

        # Если всё ок, просто логируем инфо-лог
        logger.info(
            f"✅ Успех: {response.status_code}. Метод: {request.method}, Путь: {request.url.path}, "
            f"Время: {duration:.2f}s"
        )

        return response

    except Exception as e:
        # Остальная часть кода остаётся без изменений
        duration = time.time() - start_time
        logger.error(
            f"💥 Internal Server Error (500). "
            f"Method: {request.method}, Path: {request.url.path}, Duration: {duration:.2f}s Error: {str(e)}"
        )
        logger.error(f"Тело запроса: {request_body.decode('utf-8', errors='replace')}")
        logger.exception("Full traceback:")
        
        return Response(
            content='{"detail": "Internal Server Error"}',
            media_type="application/json",
            status_code=500
        )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.PROJECT_IP,
        port=settings.PROJECT_PORT,
        ssl_keyfile="./cert/privkey1.pem",
        ssl_certfile="./cert/fullchain1.pem"
    )
