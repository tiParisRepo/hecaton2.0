import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection
from sesion.sesion import UsuarioManager

class ModuloUsuarios:
    def __init__(self, master):
        """
        Inicializa el módulo de usuarios.
        :param master: Ventana principal donde se anida el módulo.
        """
        self.master = master
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
        # Crear Filtros
        self._crear_filtros()

        # Crear Treeview de usuarios
        self._crear_treeview_usuarios()

        # Crear sección inferior de edición
        self._crear_seccion_edicion()


    def _crear_filtros(self):
        """Crea los filtros para el usuario y el identify."""
        frame_filtros = ctk.CTkFrame(self.frame_principal)
        frame_filtros.pack(side="top", fill="x", padx=10, pady=10)

        # Filtro de Usuario
        self.label_usuario = ctk.CTkLabel(frame_filtros, text="Usuario:")
        self.label_usuario.pack(side="left", padx=5)
        self.entry_usuario = ctk.CTkEntry(frame_filtros)
        self.entry_usuario.pack(side="left", padx=5)

        # Filtro de Identidad
        self.label_identify = ctk.CTkLabel(frame_filtros, text="Identidad:")
        self.label_identify.pack(side="left", padx=5)
        self.entry_identify = ctk.CTkEntry(frame_filtros)
        self.entry_identify.pack(side="left", padx=5)

        # Botón de aplicar filtro
        self.boton_filtrar = ctk.CTkButton(frame_filtros, text="Filtrar", command=self._aplicar_filtros)
        self.boton_filtrar.pack(side="left", padx=10)

    def _crear_treeview_usuarios(self):
        frame_usuarios = ctk.CTkFrame(self.frame_principal)
        frame_usuarios.pack(side="top", fill="x", padx=10, pady=5)

        self.treeview = ttk.Treeview(
            frame_usuarios,
            style="Custom.Treeview",
            columns=("ID", "Identidad", "Usuario", "Grupo"),
            show="headings"
            )
        self.treeview.pack(expand=True, fill="both", padx=10, pady=5)

        # Configurar encabezados
        self.treeview.heading("ID", text="ID")
        self.treeview.heading("Identidad", text="Identidad")
        self.treeview.heading("Usuario", text="Usuario")
        self.treeview.heading("Grupo", text="Grupo")

        self.treeview.bind("<<TreeviewSelect>>", self._cargar_detalles_usuario)

        # Llenar datos iniciales
        self._llenar_treeview_usuarios()

    def _aplicar_filtros(self):
        """Aplicar los filtros de usuario e identidad."""
        filtro_usuario = self.entry_usuario.get()
        filtro_identify = self.entry_identify.get()

        self._llenar_treeview_usuarios(filtro_usuario, filtro_identify)


    def _llenar_treeview_usuarios(self, filtro_usuario="", filtro_identify=""):
        """Carga los usuarios en el Treeview según los filtros aplicados."""
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            # Consulta con filtros
            consulta = """
            SELECT u.id, u.identify, u.usuario, gu.nombre
            FROM usuarios u
            LEFT JOIN grupo_usuario gu ON gu.id = u.nivel_acceso
            WHERE u.activo = 'S'
            """

            # Agregar condiciones de filtro si son proporcionadas
            condiciones = []
            parametros = []
            
            if filtro_usuario:
                condiciones.append("u.usuario LIKE %s")
                parametros.append(f"%{filtro_usuario}%")
            if filtro_identify:
                condiciones.append("u.identify LIKE %s")
                parametros.append(f"%{filtro_identify}%")

            # Si hay filtros, agregarlos a la consulta
            if condiciones:
                consulta += " AND " + " AND ".join(condiciones)

            cursor.execute(consulta, parametros)  # Usamos parámetros en lugar de concatenar directamente
            resultados = cursor.fetchall()

            # Limpiar Treeview antes de insertar
            self.treeview.delete(*self.treeview.get_children())

            for fila in resultados:
                self.treeview.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al llenar usuarios: {e}")


    def _crear_seccion_edicion(self):
        edicion_frame = ctk.CTkFrame(self.frame_principal, height=200)
        edicion_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        # Campos de edición
        ctk.CTkLabel(edicion_frame, text="ID Usuario:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.id_label = ctk.CTkLabel(edicion_frame, text="")
        self.id_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(edicion_frame, text="Identidad:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.identidad_label = ctk.CTkLabel(edicion_frame, text="")
        self.identidad_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(edicion_frame, text="Usuario:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.usuario_label = ctk.CTkLabel(edicion_frame, text="")
        self.usuario_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(edicion_frame, text="Grupo:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.grupo_combobox = ttk.Combobox(edicion_frame, state="disabled")
        self.grupo_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        self._llenar_combobox_grupos()

        ctk.CTkLabel(edicion_frame, text="Nueva Contraseña:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.nueva_contraseña_entry = ctk.CTkEntry(edicion_frame, show="*", state="disabled")
        self.nueva_contraseña_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(edicion_frame, text="Confirmar Contraseña:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.confirmar_contraseña_entry = ctk.CTkEntry(edicion_frame, show="*", state="disabled")
        self.confirmar_contraseña_entry.grid(row=5, column=1, padx=5, pady=5, sticky="w")

        # Botones de edición y guardar
        self.boton_editar = ctk.CTkButton(edicion_frame, text="Editar", command=self._habilitar_edicion)
        self.boton_editar.grid(row=6, column=0, padx=5, pady=10)

        self.boton_guardar = ctk.CTkButton(edicion_frame, text="Guardar Cambios", command=self._guardar_cambios, state="disabled")
        self.boton_guardar.grid(row=6, column=1, padx=5, pady=10)

    def _llenar_combobox_grupos(self):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = "SELECT id, nombre FROM grupo_usuario;"
            cursor.execute(consulta)
            resultados = cursor.fetchall()

            self.grupos = {fila[1]: fila[0] for fila in resultados}  # {nombre: id}
            self.grupo_combobox["values"] = list(self.grupos.keys())

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar grupos: {e}")

    def _cargar_detalles_usuario(self, event):
        seleccion = self.treeview.focus()
        valores = self.treeview.item(seleccion, "values")

        if valores:
            self.id_label.configure(text=valores[0])
            self.identidad_label.configure(text=valores[1])
            self.usuario_label.configure(text=valores[2])
            self.grupo_combobox.set(valores[3])

    def _habilitar_edicion(self):
        self.grupo_combobox.configure(state="readonly")
        self.nueva_contraseña_entry.configure(state="normal")
        self.confirmar_contraseña_entry.configure(state="normal")
        self.boton_guardar.configure(state="normal")

    def _guardar_cambios(self):
        usuario_id = self.id_label.cget("text")
        nuevo_grupo = self.grupo_combobox.get()
        nueva_contraseña = self.nueva_contraseña_entry.get()
        confirmar_contraseña = self.confirmar_contraseña_entry.get()

        if not usuario_id or not nuevo_grupo:
            messagebox.showerror("Error", "Debe seleccionar un usuario y un grupo.")
            return

        if nueva_contraseña != confirmar_contraseña:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            # Actualizar nivel de acceso
            consulta_grupo = "UPDATE usuarios SET nivel_acceso = %s WHERE id = %s;"
            cursor.execute(consulta_grupo, (self.grupos[nuevo_grupo], usuario_id))

            # Actualizar contraseña si se proporcionó
            if nueva_contraseña:
                usuario_manager = UsuarioManager(host=db.mysql_config["host"],
                                                 user=db.mysql_config["user"],
                                                 password=db.mysql_config["password"],
                                                 database=db.mysql_config["database"])

                contrasena_hash = usuario_manager.generar_hash_contrasena(nueva_contraseña)
                consulta_contraseña = "UPDATE usuarios SET contrasena_hash = %s WHERE id = %s;"
                cursor.execute(consulta_contraseña, (contrasena_hash, usuario_id))

            conexion.commit()

            messagebox.showinfo("Éxito", "Cambios guardados correctamente.")
            self._llenar_treeview_usuarios()  # Actualizar el Treeview

            # Bloquear campos nuevamente
            self.grupo_combobox.configure(state="disabled")
            self.nueva_contraseña_entry.configure(state="disabled")
            self.confirmar_contraseña_entry.configure(state="disabled")
            self.boton_guardar.configure(state="disabled")

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los cambios: {e}")
