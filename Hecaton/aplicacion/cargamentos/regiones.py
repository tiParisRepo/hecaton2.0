import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection


class ModuloRegionesCiudades:
    def __init__(self, master):
        """
        Inicializa el módulo de gestión de regiones y ciudades.
        :param master: Ventana principal donde se anida el módulo.
        """
        self.master = master
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both")
        self.frame_principal.grid_rowconfigure(0, weight=1)
        self.frame_principal.grid_columnconfigure(1, weight=1)
        self.frame_principal.grid_columnconfigure(3, weight=1)

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
        # Crear TreeView de regiones
        self._crear_treeview_regiones()


        # Crear TreeView de ciudades de una región
        self._crear_treeview_ciudades_region()

        # Crear botones de acción entre ciudades con región y sin región
        self._crear_botones_accion_vertical()

        # Crear TreeView de ciudades sin región
        self._crear_treeview_ciudades_sin_region()

    def _crear_treeview_regiones(self):
        frame_regiones = ctk.CTkFrame(self.frame_principal, width=300)
        frame_regiones.grid(sticky='nsew',row=0, column=0, padx=10, pady=5)

        ctk.CTkButton(frame_regiones, text="+ Nueva Región", command=self._crear_region).pack(pady=5)

        ctk.CTkLabel(frame_regiones, text="Regiones", font=("Arial", 14, "bold")).pack()

        self.treeview_regiones = ttk.Treeview(frame_regiones,selectmode='browse',style='Custom.Treeview', columns=("ID", "Nombre"), show="headings")
        self.treeview_regiones.pack(expand=True, fill="y", padx=10, pady=5)

        # Configurar encabezados
        self.treeview_regiones.heading("ID", text="ID")
        self.treeview_regiones.heading("Nombre", text="Nombre")

        self.treeview_regiones.bind("<<TreeviewSelect>>", self._mostrar_ciudades_region)

        # Llenar datos iniciales
        self._llenar_treeview_regiones()

    def _llenar_treeview_regiones(self):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = "SELECT id, nombre FROM regiones;"
            cursor.execute(consulta)
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_regiones.delete(*self.treeview_regiones.get_children())

            for fila in resultados:
                self.treeview_regiones.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar regiones: {e}")

    def _crear_treeview_ciudades_region(self):
        frame_ciudades_region = ctk.CTkFrame(self.frame_principal, width=300)
        frame_ciudades_region.grid(sticky='nsew',row=0, column=1, padx=10, pady=5)
        
        ctk.CTkLabel(frame_ciudades_region, text="Ciudades de la Región Seleccionada", font=("Arial", 14, "bold")).pack()

        self.treeview_ciudades_region = ttk.Treeview(frame_ciudades_region,style='Custom.Treeview',columns=("Ciudad"), show="headings")
        self.treeview_ciudades_region.pack(expand=True, fill="both", padx=10, pady=5)

        # Configurar encabezados
        self.treeview_ciudades_region.heading("Ciudad", text="Ciudad")

    def _mostrar_ciudades_region(self, event=None):
        seleccion = self.treeview_regiones.focus()
        valores = self.treeview_regiones.item(seleccion, "values")

        if not valores:
            return

        region_id = valores[0]

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = "SELECT ciudad FROM ciudad_region WHERE region = %s;"
            cursor.execute(consulta, (region_id,))
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_ciudades_region.delete(*self.treeview_ciudades_region.get_children())

            for fila in resultados:
                self.treeview_ciudades_region.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar ciudades de la región: {e}")

    def _crear_treeview_ciudades_sin_region(self):
        frame_ciudades_sin_region = ctk.CTkFrame(self.frame_principal)
        frame_ciudades_sin_region.grid(sticky='nsew',row=0, column=3, padx=10, pady=5)

        ctk.CTkLabel(frame_ciudades_sin_region, text="Ciudades Sin Región", font=("Arial", 14, "bold")).pack()

        # Caja de texto para filtrar por ciudad
        self.entry_filtro_ciudades_sin_region = ctk.CTkEntry(frame_ciudades_sin_region, placeholder_text="Filtrar por ciudad")
        self.entry_filtro_ciudades_sin_region.pack(padx=5)

        # Botón de filtro
        ctk.CTkButton(frame_ciudades_sin_region, text="Filtrar", command=self._filtrar_ciudades_sin_region).pack(padx=5,pady=5)

        self.treeview_ciudades_sin_region = ttk.Treeview(frame_ciudades_sin_region,style='Custom.Treeview',columns=("Ciudad"), show="headings")
        self.treeview_ciudades_sin_region.pack(expand=True, fill="both", padx=10)

        # Configurar encabezados
        self.treeview_ciudades_sin_region.heading("Ciudad", text="Ciudad")


        # Llenar datos iniciales
        self._llenar_treeview_ciudades_sin_region()

    def _filtrar_ciudades_sin_region(self):
        filtro = self.entry_filtro_ciudades_sin_region.get().strip()
        self._llenar_treeview_ciudades_sin_region(filtro)

    def _llenar_treeview_ciudades_sin_region(self, filtro=None):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            
            # Consulta base
            consulta = "SELECT ciudad FROM ciudad_region WHERE region IS NULL order by ciudad asc;"
            
            # Si hay un filtro, modificar la consulta para incluir el filtro
            if filtro:
                consulta += " AND ciudad LIKE %s"

            # Ejecutar la consulta
            if filtro:
                cursor.execute(consulta, ('%' + filtro + '%',))  # Pasar el filtro como parámetro
            else:
                cursor.execute(consulta)  # Sin filtro

            # Obtener los resultados
            resultados = cursor.fetchall()

            # Limpiar el Treeview antes de insertar
            self.treeview_ciudades_sin_region.delete(*self.treeview_ciudades_sin_region.get_children())

            # Insertar los resultados en el Treeview
            for fila in resultados:
                self.treeview_ciudades_sin_region.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar ciudades sin región: {e}")




    def _crear_botones_accion_vertical(self):
        frame_botones_vertical = ctk.CTkFrame(self.frame_principal, width=20)
        frame_botones_vertical.grid(row=0, column=2, padx=10, pady=5)

        # Botón para agregar ciudad a región
        ctk.CTkButton(frame_botones_vertical, text="←",width=15, command=self._agregar_ciudad_a_region).pack(pady=10,padx=10)

        # Botón para remover ciudad de región
        ctk.CTkButton(frame_botones_vertical, text="→",width=15, command=self._remover_ciudad_de_region).pack(pady=10,padx=10)

    def _agregar_ciudad_a_region(self):
        seleccion_ciudad = self.treeview_ciudades_sin_region.focus()
        ciudad_valores = self.treeview_ciudades_sin_region.item(seleccion_ciudad, "values")

        seleccion_region = self.treeview_regiones.focus()
        region_valores = self.treeview_regiones.item(seleccion_region, "values")

        if not ciudad_valores or not region_valores:
            messagebox.showerror("Error", "Debe seleccionar una ciudad y una región.")
            return

        ciudad = ciudad_valores[0]
        region_id = region_valores[0]

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = "UPDATE ciudad_region SET region = %s WHERE ciudad = %s;"
            cursor.execute(consulta, (region_id, ciudad))
            conexion.commit()

            messagebox.showinfo("Éxito", "Ciudad agregada a la región correctamente.")
            self._mostrar_ciudades_region()
            self._llenar_treeview_ciudades_sin_region()

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar ciudad a región: {e}")

    def _remover_ciudad_de_region(self):
        seleccion_ciudad = self.treeview_ciudades_region.focus()
        ciudad_valores = self.treeview_ciudades_region.item(seleccion_ciudad, "values")

        if not ciudad_valores:
            messagebox.showerror("Error", "Debe seleccionar una ciudad de la región.")
            return

        ciudad = ciudad_valores[0]

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = "UPDATE ciudad_region SET region = NULL WHERE ciudad = %s;"
            cursor.execute(consulta, (ciudad,))
            conexion.commit()

            messagebox.showinfo("Éxito", "Ciudad removida de la región correctamente.")
            self._mostrar_ciudades_region()
            self._llenar_treeview_ciudades_sin_region()

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al remover ciudad de región: {e}")

    def _crear_region(self):
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Región")
        formulario.geometry("300x150")
        formulario.lift()  # Asegura que la ventana esté encima de otras
        formulario.grab_set()  # Bloquea interacción con otras ventanas

        ctk.CTkLabel(formulario, text="Nombre de la Región:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.pack(pady=5)

        def guardar_region():
            nombre = nombre_entry.get()

            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para la región.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                if conexion is None:
                    raise Exception("No se pudo establecer conexión con MySQL.")

                cursor = conexion.cursor()
                consulta = "INSERT INTO regiones (nombre) VALUES (%s);"
                cursor.execute(consulta, (nombre,))
                conexion.commit()

                messagebox.showinfo("Éxito", "Región creada correctamente.")
                self._llenar_treeview_regiones()
                formulario.destroy()

                conexion.close()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear región: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_region).pack(pady=10)
