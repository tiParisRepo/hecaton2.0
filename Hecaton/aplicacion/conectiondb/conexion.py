import os
import pymysql
import fdb
from dotenv import load_dotenv

# Obtener la ruta del directorio actual
dir_path = os.path.dirname(os.path.realpath(__file__))

# Cargar las variables de entorno desde el archivo .env
dotenv_path = os.path.join(dir_path, "py_password.env")
load_dotenv(dotenv_path=dotenv_path)

class DBConnection:
    def __init__(self):
        """
        Inicializa las configuraciones de conexión a las bases de datos Firebird y MySQL.
        """
        # Configuración de MySQL
        self.mysql_config = {
            "host": os.getenv("MYSQL_HOST"),
            "user": os.getenv("MYSQL_USER"),
            "password": os.getenv("MYSQL_PASSWORD"),
            "database": os.getenv("MYSQL_DATABASE"),
            "port": int(os.getenv("MYSQL_PORT", 3306)),
        }

        # Construir DSN para Firebird
        firebird_host = os.getenv("FIREBIRD_HOST")
        firebird_database = os.getenv("FIREBIRD_DATABASE")
        self.firebird_config = {
            "dsn": f"{firebird_host}:{firebird_database}",
            "user": os.getenv("FIREBIRD_USER"),
            "password": os.getenv("FIREBIRD_PASSWORD"),
            "charset": os.getenv("FIREBIRD_CHARSET", "UTF8"),
        }

    def connect_mysql(self):
        """
        Crea una conexión a la base de datos MySQL.
        :return: Conexión MySQL.
        """
        try:
            connection = pymysql.connect(**self.mysql_config)
            return connection
        except pymysql.MySQLError as err:
            print(f"Error al conectar a MySQL: {err}")
            return None

    def connect_firebird(self):
        """
        Crea una conexión a la base de datos Firebird.
        :return: Conexión Firebird.
        """
        try:
            connection = fdb.connect(**self.firebird_config)
            return connection
        except fdb.DatabaseError as err:
            print(f"Error al conectar a Firebird: {err}")
            return None

    def test_connections(self):
        """
        Prueba ambas conexiones a las bases de datos.
        """
        print("Probando conexión a MySQL...")
        mysql_conn = self.connect_mysql()
        if mysql_conn:
            mysql_conn.close()

        print("Probando conexión a Firebird...")
        firebird_conn = self.connect_firebird()
        if firebird_conn:
            firebird_conn.close()

    def show_configs(self):
        """
        Muestra los valores de configuración para MySQL y Firebird.
        """
        print("Configuración de MySQL:")
        print(f"  Host: {self.mysql_config['host']}")
        print(f"  Usuario: {self.mysql_config['user']}")
        print(f"  Contraseña: {'*' * len(self.mysql_config['password']) if self.mysql_config['password'] else 'No especificada'}")
        print(f"  Base de datos: {self.mysql_config['database']}")
        print(f"  Puerto: {self.mysql_config['port']}")

        print("\nConfiguración de Firebird:")
        print(f"  DSN: {self.firebird_config['dsn']}")
        print(f"  Usuario: {self.firebird_config['user']}")
        print(f"  Contraseña: {'*' * len(self.firebird_config['password']) if self.firebird_config['password'] else 'No especificada'}")
        print(f"  Charset: {self.firebird_config['charset']}")

if __name__ == "__main__":
    test = DBConnection()
    test.show_configs()
    test.test_connections()
