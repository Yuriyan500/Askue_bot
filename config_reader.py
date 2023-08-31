from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Желательно вместо str использовать SecretStr
    # для конфиденциальных данных, например, токена бота
    bot_token: SecretStr
    admin_id: int
    db_server: str
    db_port: str
    db_base: str
    db_user: str
    db_pwd: str
    odbc_driver: str
    trust_server_certificate: str
    trusted_connection: str


    # Вложенный класс с дополнительными указаниями для настроек
    class Config:
        # Имя файла, откуда будут прочитаны данные
        # (относительно текущей рабочей директории)
        env_file = '.env'
        # Кодировка читаемого файла
        env_file_encoding = 'utf-8'


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест
config = Settings()
