import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection

class ModuloAdministracion:
    def __init__(self, master, sesion_usuario):
        """
        Inicializa el módulo de administración.
        :param master: Ventana principal donde se anida el módulo.
        :param sesion_usuario: Diccionario con la información de la sesión activa.
        """
        self.master = master
        self.sesion_usuario = sesion_usuario  # Información de la sesión activa
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

        # Crear TabView
        self.tabview = ctk.CTkTabview(self.frame_principal)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        # Crear pestañas
        self.tab_sistemas = self.tabview.add("Sistemas")
        self.tab_subsistemas = self.tabview.add("Subsistemas")
        self.tab_permisos = self.tabview.add("Permisos")

        # Crear interfaces de cada pestaña
        self._crear_interfaz_sistemas()
        self._crear_interfaz_subsistemas()
        self._crear_interfaz_permisos()

    def _crear_interfaz_sistemas(self):
        self.treeview_sistemas = ttk.Treeview(self.tab_sistemas,style='Custom.Treeview', columns=("ID", "Nombre"), show="headings")
        self.treeview_sistemas.pack(expand=True, fill="both", padx=10, pady=5)

        self.treeview_sistemas.heading("ID", text="ID")
        self.treeview_sistemas.heading("Nombre", text="Nombre")

        ctk.CTkButton(self.tab_sistemas, text="Agregar Sistema", command=self._crear_sistema).pack(pady=5)
        ctk.CTkButton(self.tab_sistemas, text="Editar Sistema", command=self._editar_sistema).pack(pady=5)

        self._llenar_treeview_sistemas()

    def _llenar_treeview_sistemas(self):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT id, nombre FROM sistemas;")
            resultados = cursor.fetchall()

            self.treeview_sistemas.delete(*self.treeview_sistemas.get_children())
            for fila in resultados:
                self.treeview_sistemas.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar sistemas: {e}")

    def _crear_sistema(self):
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Sistema")
        formulario.geometry("300x150")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Sistema:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.pack(pady=5)

        def guardar_sistema():
            nombre = nombre_entry.get()
            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para el sistema.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute("INSERT INTO sistemas (nombre) VALUES (%s);", (nombre,))
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Sistema creado correctamente.")
                self._llenar_treeview_sistemas()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear sistema: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_sistema).pack(pady=10)

    def _editar_sistema(self):
        seleccion = self.treeview_sistemas.focus()
        valores = self.treeview_sistemas.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un sistema para editar.")
            return

        sistema_id, sistema_nombre = valores

        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Editar Sistema")
        formulario.geometry("300x150")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Sistema:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.insert(0, sistema_nombre)
        nombre_entry.pack(pady=5)

        def guardar_cambios():
            nombre = nombre_entry.get()
            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para el sistema.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute("UPDATE sistemas SET nombre = %s WHERE id = %s;", (nombre, sistema_id))
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Sistema actualizado correctamente.")
                self._llenar_treeview_sistemas()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar sistema: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_cambios).pack(pady=10)

    def _crear_interfaz_subsistemas(self):
        # Crear un frame para los filtros
        frame_filtros = ctk.CTkFrame(self.tab_subsistemas)
        frame_filtros.pack(side="top", fill="x", padx=10, pady=5)

        # Filtro por subsistema
        self.filtro_subsistema = ctk.CTkEntry(frame_filtros, placeholder_text="Filtrar por subsistema")
        self.filtro_subsistema.pack(side="left", padx=5, pady=5)

        # Filtro por sistema
        self.filtro_sistema = ctk.CTkEntry(frame_filtros, placeholder_text="Filtrar por sistema")
        self.filtro_sistema.pack(side="left", padx=5, pady=5)

        # Botón para aplicar el filtro
        ctk.CTkButton(frame_filtros, text="Filtrar", command=self._filtrar_subsistemas).pack(side="left", padx=5, pady=5)

        # Crear Treeview para mostrar subsistemas
        self.treeview_subsistemas = ttk.Treeview(self.tab_subsistemas, style="Custom.Treeview", columns=("ID", "Nombre", "Sistema"), show="headings")
        self.treeview_subsistemas.pack(expand=True, fill="both", padx=10, pady=5)

        self.treeview_subsistemas.heading("ID", text="ID")
        self.treeview_subsistemas.heading("Nombre", text="Nombre")
        self.treeview_subsistemas.heading("Sistema", text="Sistema")

        ctk.CTkButton(self.tab_subsistemas, text="Agregar Subsistema", command=self._crear_subsistema).pack(pady=5)
        ctk.CTkButton(self.tab_subsistemas, text="Editar Subsistema", command=self._editar_subsistema).pack(pady=5)

        self._llenar_treeview_subsistemas()

    def _editar_subsistema(self):
        seleccion = self.treeview_subsistemas.focus()
        valores = self.treeview_subsistemas.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un subsistema para editar.")
            return

        subsistema_id, subsistema_nombre, sistema_nombre = valores

        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Editar Subsistema")
        formulario.geometry("300x220")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Subsistema:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.insert(0, subsistema_nombre)
        nombre_entry.pack(pady=5)

        ctk.CTkLabel(formulario, text="Sistema:").pack(pady=10)
        sistema_combobox = ttk.Combobox(formulario, state="readonly")
        sistema_combobox.pack(pady=5)

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT id, nombre FROM sistemas;")
            resultados = cursor.fetchall()
            sistema_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in resultados]

            for fila in resultados:
                if fila[1] == sistema_nombre:
                    sistema_combobox.set(f"{fila[0]} - {fila[1]}")

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar sistemas: {e}")

        def guardar_cambios():
            nombre = nombre_entry.get()
            sistema = sistema_combobox.get().split(" - ")[0]

            if not nombre or not sistema:
                messagebox.showerror("Error", "Debe ingresar un nombre y seleccionar un sistema.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute("UPDATE subsistemas SET nombre = %s, sistema = %s WHERE id = %s;", (nombre, sistema, subsistema_id))
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Subsistema actualizado correctamente.")
                self._llenar_treeview_subsistemas()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar subsistema: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_cambios).pack(pady=10)
        
    def _crear_subsistema(self):
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Subsistema")
        formulario.geometry("400x220")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Subsistema:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.pack(pady=5)

        ctk.CTkLabel(formulario, text="Sistema:").pack(pady=10)
        sistema_combobox = ttk.Combobox(formulario, state="readonly")
        sistema_combobox.pack(pady=5)

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT id, nombre FROM sistemas;")
            sistemas = cursor.fetchall()
            sistema_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in sistemas]

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar sistemas: {e}")

        def guardar_subsistema():
            nombre = nombre_entry.get()
            sistema = sistema_combobox.get().split(" - ")[0]

            if not nombre or not sistema:
                messagebox.showerror("Error", "Debe ingresar un nombre y seleccionar un sistema.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    "INSERT INTO subsistemas (nombre, sistema) VALUES (%s, %s);",
                    (nombre, sistema)
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Subsistema creado correctamente.")
                self._llenar_treeview_subsistemas()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear subsistema: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_subsistema).pack(pady=10)

    def _filtrar_subsistemas(self):
        subsistema = self.filtro_subsistema.get().strip()
        sistema = self.filtro_sistema.get().strip()

        # Pasamos los filtros a la función que llena el Treeview
        self._llenar_treeview_subsistemas(subsistema, sistema)

    def _llenar_treeview_subsistemas(self, filtro_subsistema="", filtro_sistema=""):
        """Llena el TreeView de subsistemas con datos de la base de datos."""
        try:
            # Conexión a la base de datos
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            # Modificamos la consulta para aceptar los filtros
            consulta = """
            SELECT 
                subsistemas.id, 
                subsistemas.nombre AS subsistema_nombre, 
                sistemas.nombre AS sistema_nombre
            FROM subsistemas
            LEFT JOIN sistemas ON subsistemas.sistema = sistemas.id
            WHERE 1=1
            """

            # Aplicamos los filtros en la consulta
            if filtro_subsistema:
                consulta += " AND subsistemas.nombre LIKE %s"
            if filtro_sistema:
                consulta += " AND sistemas.nombre LIKE %s"

            parametros = []
            if filtro_subsistema:
                parametros.append(f"%{filtro_subsistema}%")
            if filtro_sistema:
                parametros.append(f"%{filtro_sistema}%")

            cursor.execute(consulta, parametros)
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar datos
            self.treeview_subsistemas.delete(*self.treeview_subsistemas.get_children())

            # Insertar cada registro en el TreeView
            for fila in resultados:
                self.treeview_subsistemas.insert("", "end", values=fila)

            # Cerrar conexión
            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los subsistemas: {e}")

    def _crear_interfaz_permisos(self):
        # Filtros
        frame_filtros = ctk.CTkFrame(self.tab_permisos)
        frame_filtros.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkLabel(frame_filtros, text="Filtros", font=("Arial", 12)).pack(pady=5)

        # Filtro por subsistema
        ctk.CTkLabel(frame_filtros, text="Subsistema:").pack(side="left", padx=5)
        self.filtro_subsistema = ctk.CTkEntry(frame_filtros)
        self.filtro_subsistema.pack(side="left", padx=5)

        # Filtro por grupo
        ctk.CTkLabel(frame_filtros, text="Grupo:").pack(side="left", padx=5)
        self.filtro_grupo = ctk.CTkEntry(frame_filtros)
        self.filtro_grupo.pack(side="left", padx=5)

        # Filtro por estado (activo/inactivo)
        ctk.CTkLabel(frame_filtros, text="Activo:").pack(side="left", padx=5)
        self.filtro_activo = ttk.Combobox(frame_filtros, state="readonly", values=["Activo", "Inactivo"], width=15)
        self.filtro_activo.set("Activo")
        self.filtro_activo.pack(side="left", padx=5)

        # Botón para aplicar filtro
        ctk.CTkButton(frame_filtros, text="Filtrar", command=self._filtrar_permisos).pack(side="left", padx=5, pady=5)

        # Crear Treeview para mostrar permisos
        self.treeview_permisos = ttk.Treeview(self.tab_permisos, style='Custom.Treeview', columns=("ID", "Subsistema", "Grupo", "Activo", "Creado Por", "Fecha Creado", "Cerrado Por", "Fecha Cierre"), show="headings")
        self.treeview_permisos.pack(expand=True, fill="both", padx=10, pady=5)

        self.treeview_permisos.heading("ID", text="ID")
        self.treeview_permisos.heading("Subsistema", text="Subsistema")
        self.treeview_permisos.heading("Grupo", text="Grupo")
        self.treeview_permisos.heading("Activo", text="Activo")
        self.treeview_permisos.heading("Creado Por", text="Creado Por")
        self.treeview_permisos.heading("Fecha Creado", text="Fecha Creado")
        self.treeview_permisos.heading("Cerrado Por", text="Cerrado Por")
        self.treeview_permisos.heading("Fecha Cierre", text="Fecha Cierre")

        ctk.CTkButton(self.tab_permisos, text="Agregar Permiso", command=self._crear_permiso).pack(pady=5)
        ctk.CTkButton(self.tab_permisos, text="Editar Permiso", command=self._editar_permiso).pack(pady=5)

        # Llenar Treeview con los permisos iniciales
        self._llenar_treeview_permisos()

    def _filtrar_permisos(self):
        subsistema = self.filtro_subsistema.get().strip()
        grupo = self.filtro_grupo.get().strip()
        activo = "S" if self.filtro_activo.get() == "Activo" else "N"

        # Pasar los filtros a la función que llena el Treeview
        self._llenar_treeview_permisos(subsistema, grupo, activo)

    def _llenar_treeview_permisos(self, subsistema="", grupo="", activo=""):
        try:
            # Conexión a la base de datos
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            # Modificar la consulta para aceptar los filtros
            consulta = """
            SELECT 
                p.id, 
                s.nombre AS subsistema, 
                g.nombre AS grupo, 
                p.activo, 
                u1.usuario AS creado_por, 
                p.fecha_creado,
                u2.usuario AS cerrado_por, 
                p.fecha_cierre
            FROM permisos p
            LEFT JOIN subsistemas s ON s.id = p.subsistema
            LEFT JOIN grupo_usuario g ON g.id = p.grupo
            LEFT JOIN usuarios u1 ON u1.id = p.creado_por
            LEFT JOIN usuarios u2 ON u2.id = p.cerrado_por
            WHERE 1=1
            """

            parametros = []
            if subsistema:
                consulta += " AND s.nombre LIKE %s"
                parametros.append(f"%{subsistema}%")
            if grupo:
                consulta += " AND g.nombre LIKE %s"
                parametros.append(f"%{grupo}%")
            if activo:
                consulta += " AND p.activo = %s"
                parametros.append(activo)

            cursor.execute(consulta, parametros)
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_permisos.delete(*self.treeview_permisos.get_children())

            # Insertar los resultados en el TreeView
            for fila in resultados:
                self.treeview_permisos.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar permisos: {e}")



    def _crear_permiso(self):
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Permiso")
        formulario.geometry("400x300")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Subsistema:").pack(pady=10)
        subsistema_combobox = ttk.Combobox(formulario, state="readonly")
        subsistema_combobox.pack(pady=5)

        ctk.CTkLabel(formulario, text="Grupo:").pack(pady=10)
        grupo_combobox = ttk.Combobox(formulario, state="readonly")
        grupo_combobox.pack(pady=5)

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT id, nombre FROM subsistemas;")
            subsistemas = cursor.fetchall()
            subsistema_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in subsistemas]

            cursor.execute("SELECT id, nombre FROM grupo_usuario;")
            grupos = cursor.fetchall()
            grupo_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in grupos]

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar subsistemas o grupos: {e}")

        def guardar_permiso():
            subsistema = subsistema_combobox.get().split(" - ")[0]
            grupo = grupo_combobox.get().split(" - ")[0]

            if not subsistema or not grupo:
                messagebox.showerror("Error", "Debe seleccionar un subsistema y un grupo.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    """
                    INSERT INTO permisos (subsistema, grupo, creado_por, fecha_creado, activo)
                    VALUES (%s, %s, %s, NOW(), 'S');
                    """,
                    (subsistema, grupo, self.sesion_usuario["id"])
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Permiso creado correctamente.")
                self._llenar_treeview_permisos()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear permiso: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_permiso).pack(pady=10)

    def _editar_permiso(self):
        seleccion = self.treeview_permisos.focus()
        valores = self.treeview_permisos.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un permiso para editar.")
            return

        permiso_id, subsistema_nombre, grupo_nombre, activo, creado_por, fecha_creado, cerrado_por, fecha_cierre = valores

        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Editar Permiso")
        formulario.geometry("350x300")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Subsistema:").pack(pady=10)
        subsistema_combobox = ttk.Combobox(formulario, state="readonly")
        subsistema_combobox.pack(pady=5)

        ctk.CTkLabel(formulario, text="Grupo:").pack(pady=10)
        grupo_combobox = ttk.Combobox(formulario, state="readonly")
        grupo_combobox.pack(pady=5)

        ctk.CTkLabel(formulario, text="Activo:").pack(pady=10)
        activo_combobox = ttk.Combobox(formulario, state="readonly", values=["S", "N"])
        activo_combobox.pack(pady=5)
        activo_combobox.set(activo)

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT id, nombre FROM subsistemas;")
            subsistemas = cursor.fetchall()
            subsistema_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in subsistemas]

            cursor.execute("SELECT id, nombre FROM grupo_usuario;")
            grupos = cursor.fetchall()
            grupo_combobox['values'] = [f"{fila[0]} - {fila[1]}" for fila in grupos]

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar subsistemas o grupos: {e}")

        def guardar_cambios():
            subsistema = subsistema_combobox.get().split(" - ")[0]
            grupo = grupo_combobox.get().split(" - ")[0]
            activo = activo_combobox.get()

            if not subsistema or not grupo or not activo:
                messagebox.showerror("Error", "Debe completar todos los campos.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    """
                    UPDATE permisos 
                    SET subsistema = %s, grupo = %s, activo = %s, 
                        ultima_alteracion = NOW(), alterado_por = %s
                    WHERE id = %s;
                    """,
                    (subsistema, grupo, activo, self.sesion_usuario["id"], permiso_id)
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Permiso actualizado correctamente.")
                self._llenar_treeview_permisos()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar permiso: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_cambios).pack(pady=10)
        
