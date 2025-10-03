-- MeteoApp Database Schema
-- FastAPI метеорологическое приложение с SOLID архитектурой

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица станций
CREATE TABLE IF NOT EXISTS stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    altitude DECIMAL(10, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_station_number (station_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица связи пользователей и станций
CREATE TABLE IF NOT EXISTS user_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    station_id INT NOT NULL,
    custom_name VARCHAR(100),
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_station (user_id, station_id),
    INDEX idx_user_id (user_id),
    INDEX idx_station_id (station_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица параметров
CREATE TABLE IF NOT EXISTS parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(20),
    description TEXT,
    category VARCHAR(50),
    INDEX idx_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица параметров станций
CREATE TABLE IF NOT EXISTS station_parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    station_id INT NOT NULL,
    parameter_code VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (station_id) REFERENCES stations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_station_parameter (station_id, parameter_code),
    INDEX idx_station_id (station_id),
    INDEX idx_parameter_code (parameter_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица настроек видимости параметров пользователя (НОВАЯ - 2025-09-30)
-- Позволяет пользователям скрывать/показывать параметры для каждой станции
CREATE TABLE IF NOT EXISTS user_station_parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_station_id INT NOT NULL,
    parameter_code VARCHAR(20) NOT NULL,
    is_visible BOOLEAN DEFAULT TRUE,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_station_id) REFERENCES user_stations(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_station_parameter (user_station_id, parameter_code),
    INDEX idx_user_station_id (user_station_id),
    INDEX idx_parameter_code (parameter_code),
    INDEX idx_is_visible (is_visible)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- НАЧАЛЬНЫЕ ДАННЫЕ
-- ============================================================================

-- Вставка демо параметров
INSERT INTO parameters (code, name, unit, description, category) VALUES
('4402', 'Температура воздуха', '°C', 'Температура воздуха на высоте 2 м', 'temperature'),
('5402', 'Влажность воздуха', '%', 'Относительная влажность воздуха', 'humidity'),
('700', 'Атмосферное давление', 'гПа', 'Атмосферное давление', 'pressure'),
('6002', 'Скорость ветра', 'м/с', 'Средняя скорость ветра', 'wind'),
('7002', 'Направление ветра', 'град', 'Направление ветра', 'wind'),
('961', 'Осадки', 'мм', 'Количество осадков', 'precipitation');

-- Заполнить user_station_parameters для существующих пользователей
-- Для каждой связки user_station создать записи для всех доступных параметров станции
-- Все параметры видимы по умолчанию
INSERT INTO user_station_parameters (user_station_id, parameter_code, is_visible, display_order)
SELECT
    us.id AS user_station_id,
    sp.parameter_code,
    TRUE AS is_visible,
    0 AS display_order
FROM user_stations us
INNER JOIN station_parameters sp ON us.station_id = sp.station_id
WHERE sp.is_active = TRUE
ON DUPLICATE KEY UPDATE is_visible = is_visible;  -- Избегаем дублирования, если уже есть

-- ============================================================================
-- КОММЕНТАРИИ К АРХИТЕКТУРЕ
-- ============================================================================

-- user_station_parameters:
--   - user_station_id: ссылка на связь пользователя со станцией
--   - parameter_code: код параметра (4402, 5402, 700, и т.д.)
--   - is_visible: видим ли параметр пользователю (TRUE по умолчанию)
--   - display_order: порядок отображения в приложении (0 по умолчанию)
--
-- Логика работы:
--   1. Пользователь добавляет станцию → создается user_stations
--   2. Система автоматически создает user_station_parameters для всех параметров станции
--   3. Пользователь может скрыть параметры через API
--   4. Эндпоинты данных возвращают только видимые параметры