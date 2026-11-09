class DevelopmentConfig:

    DEBUG = True

    SECRET_KEY = 'pizzeria-clave-local-2026'

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'pizzeria'
    MYSQL_CURSORCLASS = 'DictCursor'


config = {
    'development': DevelopmentConfig
}