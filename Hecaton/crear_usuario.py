from sesion.sesion import UsuarioManager

if __name__ == "__main__":
    # Configuración de conexión a la base de datos
    gestor = UsuarioManager(
        host="localhost",
        user="root",
        password="caramba1!",
        database="dbhecaton"
    )

    # Datos del nuevo usuario
    identify = "085"
    usuario = "LUCAS"
    nombre = "LUCAS JOSIAS"
    apellido = "MOLINAS GONZALEZ"
    contrasena = "molinas"
    nivel_acceso = 1

    # Crear el usuario
    try:
        gestor.crear_usuario(identify, usuario, nombre, apellido, contrasena, nivel_acceso)
        print("Usuario creado exitosamente.")
    except Exception as e:
        print(f"Error al crear el usuario: {e}")
    finally:
        gestor.cerrar_conexion()
