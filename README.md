# MeteoApp API

Современный REST API для управления метеорологическими данными на базе FastAPI.

## Описание

MeteoApp API — это серверное приложение для сбора, хранения и предоставления метеорологических данных с метеостанций.

### Основные возможности

- 🔐 **JWT аутентификация** - безопасная система входа с refresh токенами
- 🏢 **Управление станциями** - добавление, редактирование, удаление метеостанций
- 📊 **Управление параметрами** - настройка видимости параметров для каждого пользователя
- 📡 **Данные в реальном времени** - получение актуальных данных с датчиков
- 📈 **История измерений** - доступ к историческим данным
- 👤 **Админ-панель** - управление пользователями и мониторинг системы
- ⚡ **Redis кэширование** - оптимизация производительности
- 🎯 **Mobile-first API** - оптимизация для мобильных приложений

## Технологический стек

- **FastAPI 0.104.1** - современный async веб-фреймворк
- **Python 3.8+** - язык программирования
- **MySQL** - реляционная база данных
- **Redis** - кэширование и сессии
- **PyMySQL** - коннектор для MySQL
- **python-jose** - JWT токены
- **Pydantic** - валидация данных
- **Uvicorn/Gunicorn** - ASGI серверы

## Архитектура

Проект построен на принципах **SOLID** с использованием **Dependency Injection**:

```
app/
├── config.py              # Конфигурация приложения
├── models/                # Dataclass модели
├── schemas/               # Pydantic схемы для API
├── routers/               # FastAPI роутеры (endpoints)
├── services/              # Бизнес-логика (SOLID)
├── repositories/          # Слой доступа к данным
├── security/              # JWT и аутентификация
├── middleware/            # Middleware и обработчики ошибок
├── utils/                 # Валидаторы и исключения
└── database/              # Управление подключениями к БД
```

### Сервисы (SOLID)

- `StationManagementService` - CRUD операции со станциями
- `ParameterVisibilityService` - управление видимостью параметров
- `SensorDataService` - получение данных с датчиков
- `AccessControlService` - проверка прав доступа
- `AuthService` - аутентификация пользователей

## Установка и запуск

### Требования

- Python 3.8+
- MySQL 5.7+
- Redis (опционально, для кэширования)

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/shestikpetr/MeteoAPI.git
cd MeteoAPI
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, указав ваши настройки БД и секретные ключи
```

5. Создайте базы данных:
```bash
# Импортируйте схему из sql.sql в MySQL
mysql -u root -p < sql.sql
```

### Запуск

**Режим разработки:**
```bash
python main.py
```

**Production с Gunicorn:**
```bash
gunicorn main:app -c gunicorn.conf.py
```

## API Endpoints

### Аутентификация

- `POST /api/v1/auth/login` - Вход пользователя
- `POST /api/v1/auth/register` - Регистрация
- `POST /api/v1/auth/refresh` - Обновление токена
- `POST /api/v1/auth/logout` - Выход

### Управление станциями

- `GET /api/v1/stations` - Список станций пользователя
- `POST /api/v1/stations` - Добавить станцию
- `PATCH /api/v1/stations/{station_number}` - Обновить настройки станции
- `DELETE /api/v1/stations/{station_number}` - Удалить станцию

### Управление параметрами

- `GET /api/v1/stations/{station_number}/parameters` - Список параметров с настройками видимости
- `PATCH /api/v1/stations/{station_number}/parameters/{parameter_code}` - Переключить видимость параметра
- `PATCH /api/v1/stations/{station_number}/parameters` - Массовое обновление видимости

### Данные с датчиков

- `GET /api/v1/data/latest` - **Главный endpoint для мобильного приложения** - все станции с актуальными данными
- `GET /api/v1/data/{station_number}/latest` - Актуальные данные одной станции
- `GET /api/v1/data/{station_number}/{parameter_code}/history` - История измерений параметра

### Админ-панель

- `GET /admin/` - Панель администратора (требуется роль admin)
- `GET /admin/users` - Управление пользователями
- `GET /admin/stations` - Управление станциями
- `GET /admin/monitoring` - Мониторинг системы

## Документация API

После запуска приложения документация доступна по адресам:

- **Swagger UI**: http://localhost:8085/docs
- **ReDoc**: http://localhost:8085/redoc

## Конфигурация

Все настройки задаются через переменные окружения в файле `.env`:

## База данных

### Основные таблицы

- `users` - Пользователи системы
- `stations` - Метеостанции
- `parameters` - Параметры измерений (температура, давление и т.д.)
- `user_stations` - Связь пользователей и станций
- `station_parameters` - Связь станций и параметров
- `user_station_parameters` - Настройки видимости параметров для пользователя

Полная схема БД находится в файле `sql.sql`.

## Принципы работы

### Видимость параметров

1. Пользователь добавляет станцию → создается запись в `user_stations`
2. Система автоматически создает записи в `user_station_parameters` для всех параметров станции (по умолчанию все видимы)
3. Пользователь может скрывать/показывать параметры через API
4. При запросе данных возвращаются только видимые параметры

### Оптимизация для мобильных приложений

Endpoint `GET /api/v1/data/latest` возвращает все необходимые данные за один запрос:
- Список всех станций пользователя
- Координаты станций
- Актуальные значения только видимых параметров
- Настройки (избранное, пользовательское имя)

## Production deployment

### С использованием systemd

Скопируйте `meteoapi.service` в `/etc/systemd/system/` и запустите:

```bash
sudo systemctl enable meteoapi
sudo systemctl start meteoapi
```

### С использованием Nginx

Пример конфигурации находится в файле `nginx.conf`.

## Разработка

### Структура кода

Проект следует принципам **SOLID**:

- **Single Responsibility** - каждый сервис отвечает за одну задачу
- **Open/Closed** - расширение через наследование
- **Dependency Inversion** - зависимость от абстракций через DI

### Добавление новых endpoint'ов

1. Создайте Pydantic схемы в `app/schemas/`
2. Добавьте бизнес-логику в соответствующий сервис в `app/services/`
3. Создайте роутер в `app/routers/`
4. Зарегистрируйте роутер в `main.py`

## Безопасность

- ✅ JWT токены для аутентификации
- ✅ Хеширование паролей с bcrypt
- ✅ Валидация всех входных данных с Pydantic
- ✅ Защита от SQL инъекций через параметризованные запросы
- ✅ CORS настраивается через конфигурацию
- ✅ Проверка прав доступа для всех операций

## Лицензия

MIT

## Автор

Шестопалов Пётр Андреевич

## Контакты

- **GitHub**: [shestikpetr](https://github.com/shestikpetr)
- **Email**: [shestikpetr@gmail.com](mailto:shestikpetr@gmail.com)
- **Telegram**: [@shestikpetr](https://t.me/shestikpetr)
