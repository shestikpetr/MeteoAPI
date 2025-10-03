import re
from typing import Optional


class Validators:
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_username(username: str) -> bool:
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return bool(re.match(pattern, username))

    @staticmethod
    def validate_password(password: str) -> bool:
        return len(password) >= 6

    @staticmethod
    def validate_station_number(station_number: str) -> bool:
        pattern = r'^\d{8}$'  # 8 цифр
        return bool(re.match(pattern, station_number))
