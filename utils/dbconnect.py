import pyodbc
import sqlalchemy
from config_reader import config


# engine = pyodbc.connect(r'Driver=ODBC Driver 18 for SQL Server;Server=172.17.5.102;PORT=1433;Database=Prosoft_ASKUE;UID=PyBotUser;PWD=PyBotPWD;TrustServerCertificate=yes;Trusted_Connection=no;')

def create_db_connection():
    db_server = config.db_server
    db_port = config.db_port
    db_base = config.db_base
    db_user = config.db_user
    db_pwd = config.db_pwd
    odbc_driver = config.odbc_driver
    trust_server_certificate = config.trust_server_certificate
    trusted_connection = config.trusted_connection

    engine = sqlalchemy.create_engine(f'mssql+pyodbc://{db_user}:{db_pwd}@{db_server}:{db_port}/{db_base}?'
                                      f'driver={odbc_driver}&TrustServerCertificate={trust_server_certificate}&'
                                      f'trusted_connection={trusted_connection}')
    connection = ''
    try:
        connection = engine.raw_connection()
        print(f"Connection successful.")
    except ConnectionError as e:
        print(f"The error {e} is occurred!")

    return connection


