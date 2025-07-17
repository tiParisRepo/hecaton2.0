from sesion.sesion import UsuarioManager

if __name__ == "__main__":
    # Configuración de conexión a la base de datos
    gestor = UsuarioManager(
        host="localhost",
        user="root",
        password="caramba1!",
        database="dbhecaton"
    )

    # Datos para actualizar la contraseña
    identify = "085"  # Identificador del usuario
    nueva_contrasena = "molinas"  # Nueva contraseña

    try:
        gestor.actualizar_contrasena(identify, nueva_contrasena)
        print("Contraseña actualizada exitosamente.")
    except Exception as e:
        print(f"Error al actualizar la contraseña: {e}")
    finally:
        gestor.cerrar_conexion()
