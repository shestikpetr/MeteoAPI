"""
Admin Panel Routes
FastAPI роутеры для административной панели MeteoApp
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
import json

from app.security.dependencies import get_current_user, require_admin_role
from app.models.user import User
from .services import AdminService, UserManagementService, StationManagementService
from .database_service import DatabaseService


def optional_admin_role(request: Request):
    """Проверка админ роли для HTML страниц с редиректом на логин"""
    try:
        # Пытаемся получить токен из заголовка
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Если запрос к HTML странице (не API), редирект на логин
            if request.url.path != "/admin/login" and not request.url.path.startswith("/admin/api/"):
                return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Если токен есть, проверяем через стандартную зависимость
        # (это будет работать только для API запросов)
        return None
    except HTTPException:
        if request.url.path != "/admin/login" and not request.url.path.startswith("/admin/api/"):
            return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
        raise

# Создаем роутер для админ-панели
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Инициализация сервисов
admin_service = AdminService()
user_management_service = UserManagementService()
station_management_service = StationManagementService()
database_service = DatabaseService()


@admin_router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Страница входа в админ панель"""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )


@admin_router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Главная панель администратора (авторизация через JavaScript)"""
    # HTML страница - авторизация проверяется JavaScript в auth_check.html
    # Placeholder данные, реальные загрузятся через API
    placeholder_stats = {
        "users": {"total": 0, "active": 0, "inactive": 0, "admins": 0},
        "stations": {"total": 0, "active": 0, "inactive": 0},
        "database": {"pooling_enabled": False},
        "system": {"timestamp": "", "uptime": "", "version": "2.0.0"}
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "stats": placeholder_stats,
            "page_title": "Административная панель"
        }
    )


@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    """Дашборд (алиас для главной панели)"""
    # HTML страница - авторизация проверяется JavaScript в auth_check.html
    placeholder_stats = {
        "users": {"total": 0, "active": 0, "inactive": 0, "admins": 0},
        "stations": {"total": 0, "active": 0, "inactive": 0},
        "database": {"pooling_enabled": False},
        "system": {"timestamp": "", "uptime": "", "version": "2.0.0"}
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "stats": placeholder_stats,
            "page_title": "Dashboard"
        }
    )


@admin_router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request):
    """Управление пользователями"""
    # HTML страница - авторизация проверяется JavaScript, данные загружаются через API
    placeholder_users = {
        "total_count": 0,
        "users": []
    }
    # Placeholder user info (реальные данные загружаются через JWT в JavaScript)
    user_info = {"id": 0, "username": "admin", "role": "admin"}
    return templates.TemplateResponse(
        "admin/users.html",
        {
            "request": request,
            "user": user_info,
            "current_user": user_info,  # Добавлено для совместимости с шаблоном
            "users_data": placeholder_users,
            "page_title": "Управление пользователями"
        }
    )


@admin_router.get("/stations", response_class=HTMLResponse)
async def admin_stations(request: Request):
    """Управление станциями"""
    # HTML страница - авторизация проверяется JavaScript, данные загружаются через API
    placeholder_stations = {
        "total_count": 0,
        "stations": []
    }
    return templates.TemplateResponse(
        "admin/stations.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "stations_data": placeholder_stations,
            "page_title": "Управление станциями"
        }
    )


@admin_router.get("/monitoring", response_class=HTMLResponse)
async def admin_monitoring(request: Request):
    """Мониторинг системы"""
    # HTML страница - авторизация проверяется JavaScript, данные загружаются через API
    placeholder_monitoring = {
        "system": {
            "connection_pooling": False,
            "pool_settings": {
                "min_connections": 0,
                "max_connections": 0,
                "max_idle_time": 0
            }
        },
        "database": {
            "pools": {}
        },
        "timestamp": ""
    }
    return templates.TemplateResponse(
        "admin/monitoring.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "monitoring_data": placeholder_monitoring,
            "page_title": "Мониторинг системы"
        }
    )


# API endpoints для AJAX запросов

@admin_router.get("/api/dashboard-stats")
async def api_dashboard_stats(current_user: User = Depends(require_admin_role)):
    """API для получения статистики dashboard"""
    try:
        stats = admin_service.get_dashboard_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/users")
async def api_get_users(current_user: User = Depends(require_admin_role)):
    """API для получения списка пользователей"""
    try:
        users_data = admin_service.get_user_management_data()
        return {"success": True, "data": users_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.post("/api/users")
async def api_create_user(
    request: Request,
    current_user: User = Depends(require_admin_role)
):
    """API для создания пользователя"""
    try:
        data = await request.json()
        result = user_management_service.create_user(data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.put("/api/users/{user_id}")
async def api_update_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role)
):
    """API для обновления пользователя"""
    try:
        data = await request.json()
        result = user_management_service.update_user(user_id, data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.delete("/api/users/{user_id}")
async def api_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin_role)
):
    """API для удаления (деактивации) пользователя"""
    try:
        result = user_management_service.delete_user(user_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/stations")
async def api_get_stations(current_user: User = Depends(require_admin_role)):
    """API для получения списка станций"""
    try:
        stations_data = admin_service.get_station_management_data()
        return {"success": True, "data": stations_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.post("/api/stations")
async def api_create_station(
    request: Request,
    current_user: User = Depends(require_admin_role)
):
    """API для создания станции"""
    try:
        data = await request.json()
        result = station_management_service.create_station(data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.put("/api/stations/{station_id}")
async def api_update_station(
    station_id: int,
    request: Request,
    current_user: User = Depends(require_admin_role)
):
    """API для обновления станции"""
    try:
        data = await request.json()
        result = station_management_service.update_station(station_id, data)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.delete("/api/stations/{station_id}")
async def api_delete_station(
    station_id: int,
    current_user: User = Depends(require_admin_role)
):
    """API для удаления (деактивации) станции"""
    try:
        result = station_management_service.delete_station(station_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/monitoring")
async def api_get_monitoring(current_user: User = Depends(require_admin_role)):
    """API для получения данных мониторинга"""
    try:
        monitoring_data = admin_service.get_system_monitoring_data()
        return {"success": True, "data": monitoring_data}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Database Management Routes

@admin_router.get("/database", response_class=HTMLResponse)
async def admin_database(request: Request):
    """Database management main page"""
    return templates.TemplateResponse(
        "admin/database.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "page_title": "База данных"
        }
    )


@admin_router.get("/database/{table_name}", response_class=HTMLResponse)
async def admin_database_table(request: Request, table_name: str, database: str = "local"):
    """Database table view/edit page"""
    return templates.TemplateResponse(
        "admin/database_table.html",
        {
            "request": request,
            "user": {"username": "admin", "role": "admin"},
            "table_name": table_name,
            "database": database,
            "page_title": f"Таблица: {table_name}"
        }
    )


# Database API Endpoints

@admin_router.get("/api/database/tables")
async def api_get_tables(current_user: User = Depends(require_admin_role)):
    """API to get all database tables"""
    try:
        tables = database_service.get_all_tables()
        return {"success": True, "data": tables}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/database/{table_name}/schema")
async def api_get_table_schema(
    table_name: str,
    database: str = "local",
    current_user: User = Depends(require_admin_role)
):
    """API to get table schema"""
    try:
        schema = database_service.get_table_schema(table_name, database)
        return {"success": True, "data": schema}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/database/{table_name}/data")
async def api_get_table_data(
    table_name: str,
    database: str = "local",
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "ASC",
    current_user: User = Depends(require_admin_role)
):
    """API to get table data with pagination"""
    try:
        data = database_service.get_table_data(
            table_name, database, page, page_size, search, sort_by, sort_order
        )
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.post("/api/database/{table_name}")
async def api_create_record(
    table_name: str,
    request: Request,
    database: str = "local",
    current_user: User = Depends(require_admin_role)
):
    """API to create a new record"""
    try:
        data = await request.json()
        result = database_service.create_record(table_name, data, database)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.put("/api/database/{table_name}/{record_id}")
async def api_update_record(
    table_name: str,
    record_id: str,
    request: Request,
    database: str = "local",
    current_user: User = Depends(require_admin_role)
):
    """API to update a record"""
    try:
        data = await request.json()
        result = database_service.update_record(table_name, record_id, data, database)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.delete("/api/database/{table_name}/{record_id}")
async def api_delete_record(
    table_name: str,
    record_id: str,
    database: str = "local",
    current_user: User = Depends(require_admin_role)
):
    """API to delete a record"""
    try:
        result = database_service.delete_record(table_name, record_id, database)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@admin_router.get("/api/database/{table_name}/foreign-key-options")
async def api_get_foreign_key_options(
    table_name: str,
    column: str,
    database: str = "local",
    current_user: User = Depends(require_admin_role)
):
    """API to get foreign key options for a column"""
    try:
        options = database_service.get_foreign_key_options(table_name, column, database)
        return {"success": True, "data": options}
    except Exception as e:
        return {"success": False, "error": str(e)}