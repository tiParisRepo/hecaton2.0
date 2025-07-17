import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection

class ModuloChoferes:
    def __init__(self, master, sesion_usuario):
        """
        Inicializa el módulo de gestión de choferes.
        :param master: Ventana principal donde se anida el módulo.
        :param sesion_usuario: Diccionario con la información de la sesión activa.
        """
        self.master = master
        self.sesion_usuario = sesion_usuario  # Almacena la sesión activa
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both")

        style = ttk.Style()
        style.theme_use("clam")  # Usar un tema base limpio
        
        # Estilizar filas y encabezados
        style.configure("Custom.Treeview",
                        background="#2b2b2b",  # Fondo oscuro
                        foreground="#E9F0ED",   # Texto blanco
                        rowheight=25,         # Altura de las filas
                        fieldbackground="#333333",  # Fondo de las celdas
                        font=("Arial", 12))   # Fuente para las filas
        style.map("Custom.Treeview",
                  background=[("selected", "#144870")])  # Color al seleccionar
        style.configure("Custom.Treeview.Heading",
                        background="#1F6AA5",  # Fondo del encabezado
                        foreground="#E9F0ED",   # Texto del encabezado
                        font=("Arial", 13, "bold"),  # Fuente del encabezado
                        relief='flat')        # Estilo de borde
        style.map("Custom.Treeview.Heading",
                    background=[("active", "#1F6AA5")])
        
        # Crear la interfaz
        self._crear_interfaz()

    def _crear_interfaz(self):
        # Filtro por usuario
        self._crear_filtro_usuario()

        # Crear TreeView de usuarios
        self._crear_treeview_usuarios()

        # Crear TreeView de choferes
        self._crear_treeview_choferes()

    def _crear_filtro_usuario(self):
        """Crear caja de texto para filtrar por usuario."""
        frame_filtro = ctk.CTkFrame(self.frame_principal)
        frame_filtro.pack(pady=10, fill="x")
        
        ctk.CTkLabel(frame_filtro, text="Filtrar por Usuario:", font=("Arial", 12)).pack(side="left", padx=5)

        self.entry_filtro_usuario = ctk.CTkEntry(frame_filtro, placeholder_text="Nombre del usuario")
        self.entry_filtro_usuario.pack(side="left", padx=5)

        # Botón para aplicar filtro
        ctk.CTkButton(frame_filtro, text="Filtrar", command=self._filtrar_usuarios).pack(side="left", padx=5)

    def _filtrar_usuarios(self):
        """Filtra los usuarios por el nombre del usuario ingresado en el filtro."""
        filtro = self.entry_filtro_usuario.get().strip()
        self._llenar_treeview_usuarios(filtro)

    def _crear_treeview_usuarios(self):
        frame_usuarios = ctk.CTkFrame(self.frame_principal, height=700)
        frame_usuarios.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_usuarios, text="Usuarios", font=("Arial", 14, "bold")).pack()

        self.treeview_usuarios = ttk.Treeview(frame_usuarios,style='Custom.Treeview', columns=("ID", "Usuario", "Nombre", "Apellido"), show="headings")
        self.treeview_usuarios.pack(expand=True, fill="both", padx=10, pady=5)

        # Configurar encabezados
        self.treeview_usuarios.heading("ID", text="ID")
        self.treeview_usuarios.heading("Usuario", text="Usuario")
        self.treeview_usuarios.heading("Nombre", text="Nombre")
        self.treeview_usuarios.heading("Apellido", text="Apellido")

        # Botón para inscribir un usuario como chofer
        ctk.CTkButton(frame_usuarios, text="Inscribir", command=self._abrir_formulario_inscripcion).pack(pady=2)

        # Llenar datos iniciales
        self._llenar_treeview_usuarios()

    def _llenar_treeview_usuarios(self, filtro_usuario=None):
        """Llenar el treeview de usuarios, aplicando filtro si es necesario."""
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            # Si se proporciona un filtro de usuario, añadirlo a la consulta
            consulta = """
            SELECT id, usuario, nombre, apellido
            FROM usuarios
            WHERE usuario LIKE %s;
            """
            cursor.execute(consulta, ('%' + (filtro_usuario or '') + '%',))
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_usuarios.delete(*self.treeview_usuarios.get_children())

            for fila in resultados:
                self.treeview_usuarios.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar usuarios: {e}")

    def _abrir_formulario_inscripcion(self):
        """Abre un formulario para inscribir un usuario como chofer."""
        seleccion = self.treeview_usuarios.focus()
        valores = self.treeview_usuarios.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un usuario para inscribir.")
            return

        usuario_id = valores[0]

        # Crear ventana de formulario
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Inscribir Usuario como Chofer")
        formulario.geometry("400x400")

        ctk.CTkLabel(formulario, text="ID Usuario:").pack(pady=5)
        id_label = ctk.CTkLabel(formulario, text=usuario_id)
        id_label.pack(pady=5)

        ctk.CTkLabel(formulario, text="Documento (opcional):").pack(pady=5)
        documento_entry = ctk.CTkEntry(formulario)
        documento_entry.pack(pady=5)

        ctk.CTkLabel(formulario, text="Activo:").pack(pady=5)
        activo_var = ctk.StringVar(value="S")
        ctk.CTkRadioButton(formulario, text="Activo", variable=activo_var, value="S").pack()
        ctk.CTkRadioButton(formulario, text="Inactivo", variable=activo_var, value="N").pack()

        def inscribir_chofer():
            documento = documento_entry.get()
            activo = activo_var.get()
            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                if conexion is None:
                    raise Exception("No se pudo establecer conexión con MySQL.")

                cursor = conexion.cursor()
                consulta = """
                INSERT INTO choferes (id, documento, activo, fecha_creado, creado_por)
                VALUES (%s, %s, %s, NOW(), %s);
                """
                cursor.execute(consulta, (usuario_id, documento, activo, self._obtener_usuario_actual_id()))
                conexion.commit()

                messagebox.showinfo("Éxito", "Usuario inscrito como chofer.")
                self._llenar_treeview_choferes()
                formulario.destroy()

                conexion.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al inscribir chofer: {e}")

        ctk.CTkButton(formulario, text="Inscribir", command=inscribir_chofer).pack(pady=10)

    def _crear_treeview_choferes(self):
        frame_choferes = ctk.CTkFrame(self.frame_principal, height=300)
        frame_choferes.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_choferes, text="Choferes", font=("Arial", 14, "bold")).pack()

        self.treeview_choferes = ttk.Treeview(frame_choferes,style='Custom.Treeview', columns=("ID", "Documento", "Usuario", "Nombre", "Apellido", "Activo", "Fecha Creado", "CreadoPor", "UltimaAlteracion", "AlteradoPor"), show="headings")
        self.treeview_choferes.pack(expand=True, fill="both", padx=10, pady=5)

        # Configurar encabezados
        self.treeview_choferes.heading("ID", text="ID")
        self.treeview_choferes.heading("Documento", text="Documento")
        self.treeview_choferes.heading("Usuario", text="Usuario")
        self.treeview_choferes.heading("Nombre", text="Nombre")
        self.treeview_choferes.heading("Apellido", text="Apellido")
        self.treeview_choferes.heading("Activo", text="Activo")
        self.treeview_choferes.heading("Fecha Creado", text="Fecha Creado")
        self.treeview_choferes.heading("CreadoPor", text="Creado Por")
        self.treeview_choferes.heading("UltimaAlteracion", text="Última Alteración")
        self.treeview_choferes.heading("AlteradoPor", text="Alterado Por")

        # Botón para editar chofer
        ctk.CTkButton(frame_choferes, text="Editar", command=self._abrir_formulario_edicion).pack(pady=5)

        # Llenar datos iniciales
        self._llenar_treeview_choferes()

    def _llenar_treeview_choferes(self):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = """
                SELECT c.id, c.documento, u.usuario, u.nombre, u.apellido, c.activo, 
                       DATE_FORMAT(c.fecha_creado, '%d/%m/%y %H:%i:%s') AS fecha_creado, 
                       u2.usuario AS creado_por, 
                       DATE_FORMAT(c.ultima_alteracion, '%d/%m/%y %H:%i:%s') AS ultima_alteracion, 
                       u3.usuario AS alterado_por
                FROM choferes c
                LEFT JOIN usuarios u ON u.id = c.id
                LEFT JOIN usuarios u2 ON u2.id = c.creado_por
                LEFT JOIN usuarios u3 ON u3.id = c.alterado_por;
            """
            cursor.execute(consulta)
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_choferes.delete(*self.treeview_choferes.get_children())

            for fila in resultados:
                self.treeview_choferes.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar choferes: {e}")

    def _abrir_formulario_edicion(self):
        """Abre un formulario para editar un chofer."""
        seleccion = self.treeview_choferes.focus()
        valores = self.treeview_choferes.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un chofer para editar.")
            return

        chofer_id = valores[0]

        # Crear ventana de formulario
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Editar Chofer")
        formulario.geometry("400x400")

        ctk.CTkLabel(formulario, text="ID Chofer:").pack(pady=5)
        id_label = ctk.CTkLabel(formulario, text=chofer_id)
        id_label.pack(pady=5)

        ctk.CTkLabel(formulario, text="Documento:").pack(pady=5)
        documento_entry = ctk.CTkEntry(formulario)
        documento_entry.insert(0, valores[1])
        documento_entry.pack(pady=5)

        ctk.CTkLabel(formulario, text="Activo:").pack(pady=5)
        activo_var = ctk.StringVar(value=valores[5])
        ctk.CTkRadioButton(formulario, text="Activo", variable=activo_var, value="S").pack()
        ctk.CTkRadioButton(formulario, text="Inactivo", variable=activo_var, value="N").pack()

        def guardar_cambios():
            documento = documento_entry.get()
            activo = activo_var.get()
            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                if conexion is None:
                    raise Exception("No se pudo establecer conexión con MySQL.")

                cursor = conexion.cursor()
                consulta = """
                UPDATE choferes
                SET documento = %s, activo = %s, ultima_alteracion = NOW(), alterado_por = %s
                WHERE id = %s;
                """
                cursor.execute(consulta, (documento, activo, self._obtener_usuario_actual_id(), chofer_id))
                conexion.commit()

                messagebox.showinfo("Éxito", "Cambios guardados correctamente.")
                self._llenar_treeview_choferes()
                formulario.destroy()

                conexion.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar cambios: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_cambios).pack(pady=10)

    def _obtener_usuario_actual_id(self):
        """Obtiene el ID del usuario actualmente autenticado.""" 
        return self.sesion_usuario.get("id", None)
