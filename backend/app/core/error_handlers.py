"""全局异常处理器 — 统一错误响应格式"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("error_handlers")


class AppError(Exception):
    """业务异常基类"""
    def __init__(self, message: str, code: int = 400, detail: str = ""):
        self.message = message
        self.code = code
        self.detail = detail


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException 统一处理"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} [{request.method} {request.url.path}]")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": exc.status_code,
            "message": str(exc.detail),
            "path": request.url.path,
        },
    )


async def app_error_handler(request: Request, exc: AppError):
    """业务异常处理"""
    logger.warning(f"AppError {exc.code}: {exc.message} [{request.method} {request.url.path}]")
    return JSONResponse(
        status_code=exc.code,
        content={
            "error": True,
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(request: Request, exc: Exception):
    """Pydantic 校验异常处理"""
    from fastapi.exceptions import RequestValidationError
    if isinstance(exc, RequestValidationError):
        errors = []
        for e in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in e["loc"]),
                "message": e["msg"],
            })
        logger.warning(f"Validation error [{request.method} {request.url.path}]: {errors}")
        return JSONResponse(
            status_code=422,
            content={
                "error": True,
                "code": 422,
                "message": "请求参数校验失败",
                "errors": errors,
                "path": request.url.path,
            },
        )
    # 非校验异常，回退到通用处理
    return await general_exception_handler(request, exc)


async def general_exception_handler(request: Request, exc: Exception):
    """通用未捕获异常处理"""
    logger.error(f"Unhandled error [{request.method} {request.url.path}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": 500,
            "message": "服务器内部错误",
            "path": request.url.path,
        },
    )


def register_error_handlers(app):
    """注册所有异常处理器到 FastAPI app"""
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("全局异常处理器已注册")
