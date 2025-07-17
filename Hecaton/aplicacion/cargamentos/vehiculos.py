import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection

class ModuloVehiculos:
    """
    Módulo de interfaz de usuario para la gestión de vehículos (CRUD).
    Ajustado para coincidir con la estructura de la tabla 'vehiculos' proporcionada.
    """
    def __init__(self, master, sesion_usuario):
        """
        Inicializa el módulo de gestión de vehículos.
        :param master: Ventana principal donde se anida el módulo.
        :param sesion_usuario: Diccionario con la información de la sesión activa.
        """
        self.master = master
        self.sesion_usuario = sesion_usuario
        self.edit_mode = False
        self.vehiculo_id = None
        
        # Diccionario para gestionar los widgets de entrada de forma centralizada
        self.entries = {}

        # --- Configuración del Frame Principal ---
        self.frame_principal = ctk.CTkFrame(master, fg_color="transparent")
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=10)
        
        self._configurar_estilo_treeview()
        self._crear_interfaz()

    def _configurar_estilo_treeview(self):
        """Configura el estilo visual del TreeView para un tema oscuro."""
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="#E9F0ED",
                        rowheight=25,
                        fieldbackground="#333333",
                        font=("Arial", 12))
        style.map("Custom.Treeview", background=[("selected", "#144870")])

        style.configure("Custom.Treeview.Heading",
                        background="#1F6AA5",
                        foreground="#E9F0ED",
                        font=("Arial", 13, "bold"),
                        relief='flat')
        style.map("Custom.Treeview.Heading", background=[("active", "#1F6AA5")])

    def _crear_interfaz(self):
        """Crea y organiza los componentes principales de la interfaz."""
        self.frame_principal.grid_columnconfigure(0, weight=1)
        self.frame_principal.grid_rowconfigure(0, weight=1) # Treeview se expande
        self.frame_principal.grid_rowconfigure(1, weight=0) # Formulario tamaño fijo

        self._crear_treeview_vehiculos()
        self._crear_formulario_vehiculos()

        self._llenar_treeview_vehiculos()

    def _crear_treeview_vehiculos(self):
        """Crea el frame y el TreeView para mostrar la lista de vehículos."""
        frame_vehiculos = ctk.CTkFrame(self.frame_principal)
        frame_vehiculos.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        frame_vehiculos.grid_columnconfigure(0, weight=1)
        frame_vehiculos.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame_vehiculos, text="Listado de Vehículos", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10)
        
        # Definición de columnas para que coincidan con la tabla, incluyendo las de cancelación
        columnas = ("id", "nombre", "chapa", "ano", "flota", "peso", "altura", "largo", "ancho", "activo", 
                    "fecha_creado", "creado_por", "ultima_alteracion", "alterado_por", "fecha_cancelacion", "cancelado_por")
        
        self.treeview_vehiculos = ttk.Treeview(frame_vehiculos, style="Custom.Treeview", columns=columnas, show="headings")
        self.treeview_vehiculos.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Configuración de encabezados y anchos de columna
        encabezados = {
            "id": ("ID", 40), "nombre": ("Nombre", 150), "chapa": ("Chapa", 100),
            "ano": ("Año", 60), "flota": ("Flota", 100), "peso": ("Peso (kg)", 80),
            "altura": ("Altura (m)", 80), "largo": ("Largo (m)", 80), "ancho": ("Ancho (m)", 80),
            "activo": ("Activo", 60), "fecha_creado": ("Creado", 140), "creado_por": ("Creado Por", 120),
            "ultima_alteracion": ("Modificado", 140), "alterado_por": ("Modificado Por", 120),
            "fecha_cancelacion": ("Cancelado", 140), "cancelado_por": ("Cancelado Por", 120)
        }

        for col, (text, width) in encabezados.items():
            self.treeview_vehiculos.heading(col, text=text)
            self.treeview_vehiculos.column(col, width=width, anchor="center")

        scrollbar = ctk.CTkScrollbar(frame_vehiculos, command=self.treeview_vehiculos.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.treeview_vehiculos.configure(yscrollcommand=scrollbar.set)

        ctk.CTkButton(frame_vehiculos, text="Cargar para Editar", command=self._cargar_vehiculo_seleccionado).grid(row=2, column=0, pady=10)

    def _llenar_treeview_vehiculos(self):
        """Obtiene los datos de la base de datos y los carga en el TreeView."""
        try:
            db = DBConnection()
            with db.connect_mysql() as conexion:
                with conexion.cursor() as cursor:
                    # La consulta ahora selecciona v.flota directamente y añade los campos de cancelación
                    consulta = """
                        SELECT 
                            v.id, v.nombre, v.chapa, v.ano, v.flota,
                            v.peso, v.altura, v.largo, v.ancho, 
                            CASE WHEN v.activo = 'S' THEN 'Sí' ELSE 'No' END as activo,
                            DATE_FORMAT(v.fecha_creado, '%d/%m/%Y %H:%i') AS fecha_creado,
                            u1.usuario AS creado_por,
                            DATE_FORMAT(v.ultima_alteracion, '%d/%m/%Y %H:%i') AS ultima_alteracion,
                            u2.usuario AS alterado_por,
                            DATE_FORMAT(v.fecha_cancelacion, '%d/%m/%Y %H:%i') AS fecha_cancelacion,
                            u3.usuario AS cancelado_por
                        FROM vehiculos v
                        LEFT JOIN usuarios u1 ON u1.id = v.creado_por
                        LEFT JOIN usuarios u2 ON u2.id = v.alterado_por
                        LEFT JOIN usuarios u3 ON u3.id = v.cancelado_por
                        ORDER BY v.id DESC;
                    """
                    cursor.execute(consulta)
                    resultados = cursor.fetchall()

            self.treeview_vehiculos.delete(*self.treeview_vehiculos.get_children())
            for fila in resultados:
                self.treeview_vehiculos.insert("", "end", values=[v if v is not None else "" for v in fila])

        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudieron cargar los vehículos: {e}")

    def _crear_formulario_vehiculos(self):
        """Crea el formulario para agregar o editar vehículos de forma dinámica."""
        self.frame_formulario = ctk.CTkFrame(self.frame_principal)
        self.frame_formulario.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 10))

        ctk.CTkLabel(self.frame_formulario, text="Formulario de Vehículo", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=6, pady=10)

        # Se añade 'flota' a la lista de campos de texto
        campos_formulario = [
            ("nombre", "Nombre:"), ("chapa", "Chapa:"), ("ano", "Año:"),
            ("flota", "Flota:"), ("peso", "Peso (kg):"), ("altura", "Altura (m):"),
            ("largo", "Largo (m):"), ("ancho", "Ancho (m):")
        ]
        
        for i, (key, label_text) in enumerate(campos_formulario):
            row, col = divmod(i, 4) # Ajustado a 4 columnas de campos
            ctk.CTkLabel(self.frame_formulario, text=label_text).grid(row=row + 1, column=col * 2, padx=5, pady=5, sticky="e")
            entry = ctk.CTkEntry(self.frame_formulario)
            entry.grid(row=row + 1, column=col * 2 + 1, padx=5, pady=5, sticky="w")
            self.entries[key] = entry
        
        ctk.CTkLabel(self.frame_formulario, text="Activo:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.activo_var = ctk.StringVar(value="S")
        radio_frame = ctk.CTkFrame(self.frame_formulario, fg_color="transparent")
        radio_frame.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ctk.CTkRadioButton(radio_frame, text="Sí", variable=self.activo_var, value="S").pack(side="left")
        ctk.CTkRadioButton(radio_frame, text="No", variable=self.activo_var, value="N").pack(side="left", padx=10)

        self.boton_guardar = ctk.CTkButton(self.frame_formulario, text="Guardar", command=self._guardar_vehiculo)
        self.boton_guardar.grid(row=4, column=0, columnspan=4, pady=15, padx=5, sticky="e")
        ctk.CTkButton(self.frame_formulario, text="Limpiar Formulario", command=self._limpiar_formulario, fg_color="#555", hover_color="#444").grid(row=4, column=4, columnspan=4, pady=15, padx=5, sticky="w")

    def _validar_y_obtener_datos(self):
        """Valida los datos del formulario y los devuelve en un diccionario."""
        datos = {key: entry.get().strip() for key, entry in self.entries.items()}
        
        if not datos["nombre"] or not datos["chapa"]:
            messagebox.showerror("Datos Incompletos", "Los campos 'Nombre' y 'Chapa' son obligatorios.")
            return None

        # Validaciones de campos numéricos
        for key in ["ano", "peso", "altura", "largo", "ancho"]:
            if datos[key]:
                try:
                    # El campo 'peso' se valida como entero para coincidir con el DDL
                    if key == 'peso':
                         datos[key] = int(datos[key])
                    else:
                        datos[key] = float(datos[key])
                    
                    if key == "ano":
                        datos[key] = int(datos[key])
                except ValueError:
                    messagebox.showerror("Dato Inválido", f"El campo '{key.capitalize()}' debe ser un número válido.")
                    return None
            else:
                datos[key] = None

        datos["activo"] = self.activo_var.get()
        return datos

    def _guardar_vehiculo(self):
        """Guarda un vehículo nuevo o actualiza uno existente."""
        datos_vehiculo = self._validar_y_obtener_datos()
        if datos_vehiculo is None:
            return

        try:
            db = DBConnection()
            with db.connect_mysql() as conexion:
                with conexion.cursor() as cursor:
                    if self.edit_mode and self.vehiculo_id:
                        # --- MODO ACTUALIZACIÓN ---
                        # La consulta ahora actualiza el campo 'flota'
                        consulta = """
                            UPDATE vehiculos
                            SET nombre=%s, chapa=%s, ano=%s, flota=%s, peso=%s, altura=%s, largo=%s, ancho=%s, activo=%s,
                                ultima_alteracion=NOW(), alterado_por=%s
                            WHERE id=%s;
                        """
                        valores = (datos_vehiculo["nombre"], datos_vehiculo["chapa"], datos_vehiculo["ano"], datos_vehiculo["flota"],
                                   datos_vehiculo["peso"], datos_vehiculo["altura"], datos_vehiculo["largo"], datos_vehiculo["ancho"],
                                   datos_vehiculo["activo"], self.sesion_usuario["id"], self.vehiculo_id)
                    else:
                        # --- MODO INSERCIÓN ---
                        # La consulta ahora inserta en el campo 'flota'
                        consulta = """
                            INSERT INTO vehiculos (nombre, chapa, ano, flota, peso, altura, largo, ancho, activo, 
                                                   fecha_creado, creado_por)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s);
                        """
                        valores = (datos_vehiculo["nombre"], datos_vehiculo["chapa"], datos_vehiculo["ano"], datos_vehiculo["flota"],
                                   datos_vehiculo["peso"], datos_vehiculo["altura"], datos_vehiculo["largo"], datos_vehiculo["ancho"],
                                   datos_vehiculo["activo"], self.sesion_usuario["id"])
                    
                    cursor.execute(consulta, valores)
                conexion.commit()

            messagebox.showinfo("Éxito", "Vehículo guardado correctamente.")
            self._llenar_treeview_vehiculos()
            self._limpiar_formulario()

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar el vehículo: {e}")

    def _cargar_vehiculo_seleccionado(self):
        """Carga los datos del vehículo seleccionado en el TreeView al formulario."""
        seleccion = self.treeview_vehiculos.focus()
        if not seleccion:
            messagebox.showwarning("Sin Selección", "Por favor, seleccione un vehículo de la lista para editar.")
            return

        valores = self.treeview_vehiculos.item(seleccion, "values")
        
        # El mapa de columnas ahora coincide con la nueva consulta SELECT
        mapa_columnas = ["id", "nombre", "chapa", "ano", "flota", "peso", "altura", "largo", "ancho", "activo"]
        datos_cargados = dict(zip(mapa_columnas, valores))

        self._limpiar_formulario()
        self.edit_mode = True
        self.vehiculo_id = datos_cargados["id"]

        # Llenar todos los campos de texto, incluyendo el nuevo de flota
        for key, entry in self.entries.items():
            valor = datos_cargados.get(key, "")
            # Se asegura de no insertar el texto "None" en los campos
            if valor is not None:
                entry.insert(0, str(valor))

        self.activo_var.set("S" if datos_cargados.get("activo") == "Sí" else "N")
        self.boton_guardar.configure(text="Actualizar")

    def _limpiar_formulario(self):
        """Limpia todos los campos del formulario y lo resetea al modo de creación."""
        for entry in self.entries.values():
            entry.delete(0, "end")
        
        self.activo_var.set("S")
        self.edit_mode = False
        self.vehiculo_id = None
        self.boton_guardar.configure(text="Guardar")
        self.entries["nombre"].focus()

