import bcrypt
import pymysql
from pymysql.err import IntegrityError


class UsuarioManager:
    def __init__(self, host, user, password, database):
        self.connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.usuario_actual = None  # Mantiene la sesión activa

    def cerrar_conexion(self):
        """Cierra la conexión con la base de datos."""
        self.connection.close()

    def generar_hash_contrasena(self, contrasena):
        """Genera un hash seguro para la contraseña proporcionada."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(contrasena.encode('utf-8'), salt)

    def crear_usuario(self, identify, usuario, nombre, apellido, contrasena, nivel_acceso):
        """
        Crea un nuevo usuario en la base de datos.
        """
        try:
            cursor = self.connection.cursor()
            contrasena_hash = self.generar_hash_contrasena(contrasena)
            query = """
                INSERT INTO usuarios (identify, usuario, nombre, apellido, contrasena_hash, nivel_acceso)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (identify, usuario, nombre, apellido, contrasena_hash, nivel_acceso))
            self.connection.commit()
            print(f"Usuario {usuario} creado exitosamente.")
        except IntegrityError:
            print("Error: El identificador o el usuario ya existen.")
        except Exception as e:
            print(f"Error al crear usuario: {e}")
        finally:
            cursor.close()
    def actualizar_contrasena(self, identify, nueva_contrasena):
        """
        Actualiza la contraseña de un usuario utilizando su 'identity'.
        """
        try:
            cursor = self.connection.cursor()
            
            # Generar el hash para la nueva contraseña
            contrasena_hash = self.generar_hash_contrasena(nueva_contrasena)

            # Actualizar la contraseña en la base de datos
            query = """
                UPDATE usuarios
                SET contrasena_hash = %s
                WHERE identify = %s
            """
            cursor.execute(query, (contrasena_hash, identify))
            self.connection.commit()
            print(f"Contraseña actualizada exitosamente para el usuario con identity {identify}.")
        except Exception as e:
            print(f"Error al actualizar la contraseña: {e}")
        finally:
            cursor.close()
            
    def iniciar_sesion(self, usuario, contrasena):
        """
        Inicia sesión validando usuario y contraseña.
        """
        try:
            cursor = self.connection.cursor()
            query = "SELECT id,identify, nombre, apellido, contrasena_hash, nivel_acceso FROM usuarios WHERE usuario = %s"
            cursor.execute(query, (usuario,))
            resultado = cursor.fetchone()

            if resultado:
                id,identify, nombre, apellido, contrasena_hash, nivel_acceso = resultado

                # Verificar la contraseña
                if bcrypt.checkpw(contrasena.encode('utf-8'), contrasena_hash.encode('utf-8')):
                    self.usuario_actual = {
                        "id": id,
                        "identify": identify,
                        "usuario": usuario,
                        "nombre": nombre,
                        "apellido": apellido,
                        "nivel_acceso": nivel_acceso
                    }
                    print(f"Sesión iniciada: {nombre} {apellido} (Nivel: {nivel_acceso})")
                    return True
                else:
                    print("Error: Credenciales incorrectas.")
            else:
                print("Error: Usuario no encontrado.")
            return False
        except Exception as e:
            print(f"Error al iniciar sesión: {e}")
            return False
        finally:
            cursor.close()

    def cerrar_sesion(self):
        """Cierra la sesión actual."""
        if self.usuario_actual:
            print(f"Sesión cerrada: {self.usuario_actual}")
            self.usuario_actual = None
        else:
            print("No hay sesión activa.")

    def obtener_sesion(self):
        """Devuelve los datos de la sesión activa."""
        return self.usuario_actual
