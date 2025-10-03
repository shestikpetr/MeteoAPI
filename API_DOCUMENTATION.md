# API Документация MeteoApp

Полная документация REST API для приложения MeteoApp - системы управления метеорологическими данными на базе FastAPI.

**Версия API:** v1

**Аутентификация:** JWT Bearer Token (требуется для всех эндпоинтов кроме `/api/v1/auth/login` и `/api/v1/auth/register`)

---

## 1. Аутентификация

### POST /api/v1/auth/register
- **Описание:** Регистрация нового пользователя в системе
- **Аутентификация:** Не требуется
- **Тело запроса:**
  ```
  {
    "username": string (3-50 символов, только буквы, цифры и _),
    "email": string (валидный email),
    "password": string (минимум 6 символов)
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "user_id": string,
      "username": string,
      "access_token": string,
      "refresh_token": string
    }
  }
  ```
- **Коды статуса:**
  - `201 Created` - успешная регистрация
  - `400 Bad Request` - ошибка валидации данных
  - `409 Conflict` - пользователь с таким именем/email уже существует

---

### POST /api/v1/auth/login
- **Описание:** Вход пользователя в систему
- **Аутентификация:** Не требуется
- **Тело запроса:**
  ```
  {
    "username": string,
    "password": string
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "user_id": string,
      "username": string,
      "access_token": string,
      "refresh_token": string
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - успешный вход
  - `401 Unauthorized` - неверные учетные данные

---

### POST /api/v1/auth/refresh
- **Описание:** Обновление access токена с использованием refresh токена
- **Аутентификация:** Refresh Token (передается в заголовке Authorization)
- **Тело запроса:** Не требуется
- **Ответ:**
  ```
  {
    "success": true,
    "access_token": string
  }
  ```
- **Коды статуса:**
  - `200 OK` - токен успешно обновлен
  - `401 Unauthorized` - недействительный refresh token

---

### GET /api/v1/auth/me
- **Описание:** Получить информацию о текущем авторизованном пользователе
- **Аутентификация:** JWT Bearer Token
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "id": string,
      "username": string,
      "email": string,
      "role": "user" | "admin",
      "is_active": boolean,
      "created_at": datetime (ISO 8601),
      "updated_at": datetime (ISO 8601)
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - информация получена
  - `401 Unauthorized` - неавторизован

---

### POST /api/v1/auth/logout
- **Описание:** Выход пользователя из системы (клиентский logout - удаление токенов происходит на стороне клиента)
- **Аутентификация:** JWT Bearer Token
- **Ответ:**
  ```
  {
    "message": "Успешный выход. Удалите токены на клиенте."
  }
  ```
- **Коды статуса:**
  - `200 OK` - успешный выход

---

## 2. Управление станциями

### GET /api/v1/stations
- **Описание:** Получить все станции пользователя (без параметров и данных)
- **Аутентификация:** JWT Bearer Token
- **Ответ:**
  ```
  {
    "success": true,
    "data": [
      {
        "id": string,
        "user_id": string,
        "station_id": string,
        "custom_name": string | null,
        "is_favorite": boolean,
        "created_at": datetime (ISO 8601),
        "station": {
          "id": string,
          "station_number": string,
          "name": string,
          "location": string | null,
          "latitude": float | null,
          "longitude": float | null,
          "altitude": float | null,
          "is_active": boolean,
          "created_at": datetime (ISO 8601),
          "updated_at": datetime (ISO 8601)
        }
      }
    ]
  }
  ```
- **Коды статуса:**
  - `200 OK` - список получен
  - `401 Unauthorized` - неавторизован
  - `500 Internal Server Error` - ошибка сервера

---

### POST /api/v1/stations
- **Описание:** Добавить станцию пользователю по номеру станции (8 цифр). При добавлении все параметры станции становятся видимыми по умолчанию
- **Аутентификация:** JWT Bearer Token
- **Тело запроса:**
  ```
  {
    "station_id": string (номер станции, 8 цифр),
    "custom_name": string | null (опционально),
    "is_favorite": boolean (по умолчанию false)
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "id": string,
      "user_id": string,
      "station_id": string,
      "custom_name": string | null,
      "is_favorite": boolean,
      "created_at": datetime (ISO 8601)
    }
  }
  ```
- **Коды статуса:**
  - `201 Created` - станция успешно добавлена
  - `404 Not Found` - станция с указанным номером не существует
  - `409 Conflict` - станция уже добавлена пользователю
  - `401 Unauthorized` - неавторизован

---

### PATCH /api/v1/stations/{station_number}
- **Описание:** Обновить настройки станции пользователя (пользовательское название и/или отметка "избранное")
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
- **Параметры запроса (query):**
  - `custom_name` (string, опционально) - новое пользовательское название
  - `is_favorite` (boolean, опционально) - отметка избранной станции
- **Ответ:**
  ```
  {
    "success": boolean
  }
  ```
- **Коды статуса:**
  - `200 OK` - настройки обновлены
  - `404 Not Found` - станция не найдена у пользователя
  - `401 Unauthorized` - неавторизован

---

### DELETE /api/v1/stations/{station_number}
- **Описание:** Удалить станцию у пользователя. При удалении также удаляются все настройки видимости параметров
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
- **Ответ:**
  ```
  {
    "success": boolean
  }
  ```
- **Коды статуса:**
  - `200 OK` - станция удалена
  - `404 Not Found` - станция не найдена у пользователя
  - `401 Unauthorized` - неавторизован

---

## 3. Управление видимостью параметров

### GET /api/v1/stations/{station_number}/parameters
- **Описание:** Получить все параметры станции с информацией о видимости для пользователя
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
- **Ответ:**
  ```
  {
    "success": true,
    "data": [
      {
        "code": string,
        "name": string,
        "unit": string | null,
        "description": string | null,
        "category": string | null,
        "is_visible": boolean,
        "display_order": integer
      }
    ]
  }
  ```
- **Коды статуса:**
  - `200 OK` - список параметров получен
  - `404 Not Found` - станция не найдена у пользователя
  - `401 Unauthorized` - неавторизован

---

### PATCH /api/v1/stations/{station_number}/parameters/{parameter_code}
- **Описание:** Изменить видимость одного параметра (показать или скрыть параметр для пользователя)
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
  - `parameter_code` (string) - код параметра (например, "4402")
- **Тело запроса:**
  ```
  {
    "is_visible": boolean
  }
  ```
- **Ответ:**
  ```
  {
    "success": boolean,
    "parameter_code": string,
    "is_visible": boolean
  }
  ```
- **Коды статуса:**
  - `200 OK` - видимость изменена
  - `404 Not Found` - станция или параметр не найдены
  - `401 Unauthorized` - неавторизован

---

### PATCH /api/v1/stations/{station_number}/parameters
- **Описание:** Массовое изменение видимости параметров (одним запросом изменить видимость нескольких параметров)
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
- **Тело запроса:**
  ```
  {
    "parameters": [
      {"code": "4402", "visible": true},
      {"code": "5402", "visible": false},
      {"code": "700", "visible": true}
    ]
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "updated": integer (количество обновленных записей),
    "total": integer (общее количество записей)
  }
  ```
- **Коды статуса:**
  - `200 OK` - параметры обновлены
  - `404 Not Found` - станция не найдена
  - `401 Unauthorized` - неавторизован

---

## 4. Данные датчиков

### GET /api/v1/data/latest
- **Описание:** Получить последние данные всех станций пользователя. **ГЛАВНЫЙ ЭНДПОИНТ ДЛЯ МОБИЛЬНОГО ПРИЛОЖЕНИЯ**. Один запрос возвращает все станции с местоположением и последними значениями ТОЛЬКО видимых параметров
- **Аутентификация:** JWT Bearer Token
- **Ответ:**
  ```
  {
    "success": true,
    "data": [
      {
        "station_number": string,
        "custom_name": string | null,
        "is_favorite": boolean,
        "location": string | null,
        "latitude": float | null,
        "longitude": float | null,
        "parameters": [
          {
            "code": string,
            "name": string,
            "value": float | null,
            "unit": string | null,
            "category": string | null
          }
        ],
        "timestamp": string (ISO 8601) | null
      }
    ]
  }
  ```
- **Коды статуса:**
  - `200 OK` - данные получены
  - `401 Unauthorized` - неавторизован
  - `500 Internal Server Error` - ошибка сервера

---

### GET /api/v1/data/{station_number}/latest
- **Описание:** Получить последние данные одной станции. Возвращает последние значения ТОЛЬКО видимых параметров станции
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
- **Ответ:**
  ```
  {
    "station_number": string,
    "custom_name": string | null,
    "is_favorite": boolean,
    "location": string | null,
    "latitude": float | null,
    "longitude": float | null,
    "parameters": [
      {
        "code": string,
        "name": string,
        "value": float | null,
        "unit": string | null,
        "category": string | null
      }
    ],
    "timestamp": string (ISO 8601) | null
  }
  ```
- **Коды статуса:**
  - `200 OK` - данные получены
  - `404 Not Found` - станция не найдена у пользователя
  - `401 Unauthorized` - неавторизован

---

### GET /api/v1/data/{station_number}/{parameter_code}/history
- **Описание:** Получить исторические данные параметра за период. Пользователь заходит на станцию и выбирает параметр для просмотра истории. Возвращает временной ряд значений параметра. Параметр должен быть видимым для пользователя
- **Аутентификация:** JWT Bearer Token
- **Параметры пути:**
  - `station_number` (string) - номер станции (8 цифр)
  - `parameter_code` (string) - код параметра (например, "4402")
- **Параметры запроса (query):**
  - `start_time` (integer, опционально) - Unix timestamp начала периода
  - `end_time` (integer, опционально) - Unix timestamp конца периода
  - `limit` (integer, опционально) - максимальное количество записей (по умолчанию 1000, минимум 1, максимум 10000)
- **Ответ:**
  ```
  {
    "success": true,
    "station_number": string,
    "parameter": {
      "code": string,
      "name": string,
      "unit": string | null,
      "category": string | null
    },
    "data": [
      {
        "time": integer (Unix timestamp),
        "value": float
      }
    ],
    "count": integer
  }
  ```
- **Примечания:** Данные возвращаются в порядке убывания времени (свежие первыми)
- **Коды статуса:**
  - `200 OK` - данные получены
  - `404 Not Found` - станция или параметр не найдены, или параметр не видим
  - `401 Unauthorized` - неавторизован
  - `400 Bad Request` - некорректные параметры запроса

---

## 5. Админ-панель API

**Примечание:** Все эндпоинты админ-панели требуют роль `admin`

### GET /admin/api/dashboard-stats
- **Описание:** Получить статистику для главного дашборда админ-панели
- **Аутентификация:** JWT Bearer Token + роль admin
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "users": {
        "total": integer,
        "active": integer,
        "inactive": integer,
        "admins": integer
      },
      "stations": {
        "total": integer,
        "active": integer,
        "inactive": integer
      },
      "database": {
        "pooling_enabled": boolean
      },
      "system": {
        "timestamp": string (ISO 8601),
        "uptime": string,
        "version": string
      }
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - статистика получена
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав (не admin)

---

### GET /admin/api/users
- **Описание:** Получить список всех пользователей системы
- **Аутентификация:** JWT Bearer Token + роль admin
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "total_count": integer,
      "users": [
        {
          "id": integer,
          "username": string,
          "email": string,
          "role": "user" | "admin",
          "is_active": boolean,
          "created_at": datetime,
          "updated_at": datetime
        }
      ]
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - список получен
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### POST /admin/api/users
- **Описание:** Создать нового пользователя
- **Аутентификация:** JWT Bearer Token + роль admin
- **Тело запроса:**
  ```
  {
    "username": string,
    "email": string,
    "password": string,
    "role": "user" | "admin" (опционально, по умолчанию "user"),
    "is_active": boolean (опционально, по умолчанию true)
  }
  ```
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string,
    "user_id": integer (если успех)
  }
  ```
- **Коды статуса:**
  - `201 Created` - пользователь создан
  - `400 Bad Request` - ошибка валидации
  - `409 Conflict` - пользователь уже существует
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### PUT /admin/api/users/{user_id}
- **Описание:** Обновить данные пользователя
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `user_id` (integer) - ID пользователя
- **Тело запроса:**
  ```
  {
    "email": string (опционально),
    "password": string (опционально),
    "role": "user" | "admin" (опционально),
    "is_active": boolean (опционально)
  }
  ```
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string
  }
  ```
- **Коды статуса:**
  - `200 OK` - пользователь обновлен
  - `404 Not Found` - пользователь не найден
  - `400 Bad Request` - ошибка валидации
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### DELETE /admin/api/users/{user_id}
- **Описание:** Удалить (деактивировать) пользователя
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `user_id` (integer) - ID пользователя
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string
  }
  ```
- **Коды статуса:**
  - `200 OK` - пользователь деактивирован
  - `404 Not Found` - пользователь не найден
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### GET /admin/api/stations
- **Описание:** Получить список всех станций в системе
- **Аутентификация:** JWT Bearer Token + роль admin
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "total_count": integer,
      "stations": [
        {
          "id": integer,
          "station_number": string,
          "name": string,
          "location": string | null,
          "latitude": float | null,
          "longitude": float | null,
          "altitude": float | null,
          "is_active": boolean,
          "created_at": datetime,
          "updated_at": datetime
        }
      ]
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - список получен
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### POST /admin/api/stations
- **Описание:** Создать новую станцию
- **Аутентификация:** JWT Bearer Token + роль admin
- **Тело запроса:**
  ```
  {
    "station_number": string (8 цифр),
    "name": string,
    "location": string (опционально),
    "latitude": float (опционально, -90 до 90),
    "longitude": float (опционально, -180 до 180),
    "altitude": float (опционально),
    "is_active": boolean (опционально, по умолчанию true)
  }
  ```
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string,
    "station_id": integer (если успех)
  }
  ```
- **Коды статуса:**
  - `201 Created` - станция создана
  - `400 Bad Request` - ошибка валидации
  - `409 Conflict` - станция с таким номером уже существует
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### PUT /admin/api/stations/{station_id}
- **Описание:** Обновить данные станции
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `station_id` (integer) - ID станции
- **Тело запроса:**
  ```
  {
    "name": string (опционально),
    "location": string (опционально),
    "latitude": float (опционально, -90 до 90),
    "longitude": float (опционально, -180 до 180),
    "altitude": float (опционально),
    "is_active": boolean (опционально)
  }
  ```
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string
  }
  ```
- **Коды статуса:**
  - `200 OK` - станция обновлена
  - `404 Not Found` - станция не найдена
  - `400 Bad Request` - ошибка валидации
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### DELETE /admin/api/stations/{station_id}
- **Описание:** Удалить (деактивировать) станцию
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `station_id` (integer) - ID станции
- **Ответ:**
  ```
  {
    "success": boolean,
    "message": string
  }
  ```
- **Коды статуса:**
  - `200 OK` - станция деактивирована
  - `404 Not Found` - станция не найдена
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### GET /admin/api/monitoring
- **Описание:** Получить данные мониторинга системы (состояние БД, пулы соединений)
- **Аутентификация:** JWT Bearer Token + роль admin
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "system": {
        "connection_pooling": boolean,
        "pool_settings": {
          "min_connections": integer,
          "max_connections": integer,
          "max_idle_time": integer
        }
      },
      "database": {
        "pools": {
          "local": {
            "active": integer,
            "idle": integer,
            "total": integer
          },
          "sensor": {
            "active": integer,
            "idle": integer,
            "total": integer
          }
        }
      },
      "timestamp": string (ISO 8601)
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - данные получены
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

## 6. Админ-панель - Управление БД

### GET /admin/api/database/tables
- **Описание:** Получить список всех таблиц в локальной базе данных
- **Аутентификация:** JWT Bearer Token + роль admin
- **Ответ:**
  ```
  {
    "success": true,
    "data": [
      {
        "name": string,
        "rows": integer,
        "comment": string
      }
    ]
  }
  ```
- **Коды статуса:**
  - `200 OK` - список получен
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### GET /admin/api/database/{table_name}/schema
- **Описание:** Получить схему таблицы (структуру полей)
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "columns": [
        {
          "name": string,
          "type": string,
          "nullable": boolean,
          "key": string,
          "default": any,
          "extra": string
        }
      ],
      "primary_key": string,
      "foreign_keys": [
        {
          "column": string,
          "referenced_table": string,
          "referenced_column": string
        }
      ]
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - схема получена
  - `404 Not Found` - таблица не найдена
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### GET /admin/api/database/{table_name}/data
- **Описание:** Получить данные таблицы с пагинацией, поиском и сортировкой
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
- **Параметры запроса (query):**
  - `page` (integer, опционально) - номер страницы (по умолчанию 1)
  - `page_size` (integer, опционально) - размер страницы (по умолчанию 50)
  - `search` (string, опционально) - поисковый запрос
  - `sort_by` (string, опционально) - поле для сортировки
  - `sort_order` (string, опционально) - порядок сортировки ("ASC" или "DESC", по умолчанию "ASC")
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "rows": [
        {
          "field_name": value,
          ...
        }
      ],
      "total": integer,
      "page": integer,
      "page_size": integer,
      "total_pages": integer
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - данные получены
  - `404 Not Found` - таблица не найдена
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### POST /admin/api/database/{table_name}
- **Описание:** Создать новую запись в таблице
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
- **Тело запроса:**
  ```
  {
    "field_name": value,
    ...
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "id": integer | string,
      "message": string
    }
  }
  ```
- **Коды статуса:**
  - `201 Created` - запись создана
  - `400 Bad Request` - ошибка валидации
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### PUT /admin/api/database/{table_name}/{record_id}
- **Описание:** Обновить запись в таблице
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
  - `record_id` (string) - ID записи
- **Тело запроса:**
  ```
  {
    "field_name": value,
    ...
  }
  ```
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "message": string
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - запись обновлена
  - `404 Not Found` - запись не найдена
  - `400 Bad Request` - ошибка валидации
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### DELETE /admin/api/database/{table_name}/{record_id}
- **Описание:** Удалить запись из таблицы
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
  - `record_id` (string) - ID записи
- **Ответ:**
  ```
  {
    "success": true,
    "data": {
      "message": string
    }
  }
  ```
- **Коды статуса:**
  - `200 OK` - запись удалена
  - `404 Not Found` - запись не найдена
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

### GET /admin/api/database/{table_name}/foreign-key-options
- **Описание:** Получить доступные значения для внешнего ключа (foreign key) при создании/редактировании записи
- **Аутентификация:** JWT Bearer Token + роль admin
- **Параметры пути:**
  - `table_name` (string) - имя таблицы
- **Параметры запроса (query):**
  - `column` (string, обязательно) - имя столбца (внешнего ключа)
- **Ответ:**
  ```
  {
    "success": true,
    "data": [
      {
        "id": integer | string,
        "display": string
      }
    ]
  }
  ```
- **Коды статуса:**
  - `200 OK` - опции получены
  - `404 Not Found` - таблица или столбец не найдены
  - `401 Unauthorized` - неавторизован
  - `403 Forbidden` - недостаточно прав

---

## Коды ошибок и обработка

### Стандартные коды статуса HTTP:
- `200 OK` - успешный запрос
- `201 Created` - ресурс успешно создан
- `400 Bad Request` - ошибка валидации данных запроса
- `401 Unauthorized` - требуется аутентификация или токен недействителен
- `403 Forbidden` - доступ запрещен (недостаточно прав)
- `404 Not Found` - ресурс не найден
- `409 Conflict` - конфликт (например, ресурс уже существует)
- `500 Internal Server Error` - внутренняя ошибка сервера

### Формат ответа при ошибке:
```json
{
  "detail": "Описание ошибки"
}
```

или

```json
{
  "success": false,
  "error": "Описание ошибки"
}
```

---

## Аутентификация

### Использование JWT токенов:

1. **Получение токенов:** При успешной регистрации или входе (`/api/v1/auth/register` или `/api/v1/auth/login`) вы получаете `access_token` и `refresh_token`

2. **Использование access_token:** Добавьте токен в заголовок Authorization для всех защищенных эндпоинтов:
   ```
   Authorization: Bearer <access_token>
   ```

3. **Обновление токена:** Когда `access_token` истекает (24 часа), используйте `refresh_token` для получения нового через `/api/v1/auth/refresh`

4. **Logout:** Клиент удаляет токены локально при вызове `/api/v1/auth/logout`

---

## Документация API

Интерактивная документация доступна по следующим адресам:
- **Swagger UI:** `http://0.0.0.0:8085/docs`
- **ReDoc:** `http://0.0.0.0:8085/redoc`

---

## Примечания по использованию

### Для мобильного приложения:
1. **Начальная загрузка:** Используйте `/api/v1/data/latest` для получения всех станций с последними данными одним запросом
2. **Детализация:** Данные для детального просмотра станции уже получены на шаге 1
3. **История параметра:** Вызывайте `/api/v1/data/{station_number}/{parameter_code}/history` при выборе конкретного параметра
4. **Настройки видимости:** Управляйте через `/api/v1/stations/{station_number}/parameters`

### Оптимизация:
- API возвращает только видимые параметры для пользователя
- Мобильное приложение может кешировать данные локально
- Redis используется для кеширования сессий на сервере
- Данные датчиков берутся из удаленной БД в реальном времени

---

**Версия документации:** 2.0
**Дата последнего обновления:** 2025-10-01
