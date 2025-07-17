from pydoc import text
from turtle import bgcolor
import customtkinter as ctk
from tkinter import ttk, messagebox

from setuptools import Command
from aplicacion.conectiondb.conexion import DBConnection

class ModuloVerCargamentos:
    def __init__(self, master, sesion_usuario):
        """
        Inicializa el módulo de gestión de ver cargamentos.
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
        
        # Crear la interfaz
        self._crear_interfaz()

    def _crear_interfaz(self):
        # Crear TreeView de cargamentos
        self._crear_treeview_cargamentos()

        # Crear TabView con información adicional del cargamento
        self._crear_tabview_datos()

    def _crear_treeview_cargamentos(self):
        # Crear TreeView
        self.treeview_cargamentos = ttk.Treeview(self.frame_principal,style='Custom.Treeview', columns=(1, 2, 3, 4, 5, 6, 7), show="headings")
        self.treeview_cargamentos.pack(expand=True, fill="both")
        self.treeview_cargamentos.heading(1, text="ID")
        self.treeview_cargamentos.heading(2, text="Identificador")
        self.treeview_cargamentos.heading(3, text="Vehículo")
        self.treeview_cargamentos.heading(4, text="Chofer")
        self.treeview_cargamentos.heading(5, text="Valor")
        self.treeview_cargamentos.heading(6, text="Peso")
        self.treeview_cargamentos.heading(7, text="Volumenes")

        self.treeview_cargamentos.tag_configure("cerrado", background="#0f822d",foreground="#2B2B2B")


        self.treeview_cargamentos.bind("<<TreeviewSelect>>", self._cargar_datos_cargamento)

        # Cargar datos
        self._cargar_cargamentos()

    def _cargar_cargamentos(self):
        try:
            # Conexión a la base de datos
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # Consulta SQL
            sql = """
                SELECT 
                    c.id,
                    c.identidad,
                    v.nombre AS vehiculo,
                    u2.nombre AS chofer,
                    SUM(pp.cantidad_final * pp.precio_principal) AS valor,
                    SUM(pp.cantidad_final * p2.peso) AS peso,
                    SUM(p.volumen) AS volumen,
                    c.activo
                FROM cargamentos c
                LEFT JOIN vehiculos v ON v.id = c.vehiculo
                LEFT JOIN choferes c2 ON c2.id = c.chofer
                LEFT JOIN usuarios u2 ON u2.id = c2.id
                LEFT JOIN carga_pedido cp ON cp.cargamento = c.id and cp.activo = 'S'
                LEFT JOIN pedidos p ON p.numero = cp.pedido
                LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                LEFT JOIN productos p2 ON p2.id = pp.item
                GROUP BY c.id, c.identidad, v.nombre, u2.nombre
                ORDER BY c.id desc;
            """
            cursor.execute(sql)

            # Limpiar TreeView antes de insertar
            for item in self.treeview_cargamentos.get_children():
                self.treeview_cargamentos.delete(item)

            # Insertar registros en el TreeView
            for row in cursor.fetchall():
                # Asumiendo que la estructura de row es:
                # row = (id, identidad, vehiculo, chofer, valor, peso, volumen)

                # Aplicar el formato deseado
                valor_total = row[4]  # La columna de valor
                peso_total = row[5]  # La columna de peso
                vol_total = row[6]   # La columna de volumen

                tag = ()

                if row[7] == 'N':
                    tag = ('cerrado',)
                else:
                    tag = ()

                valor_total_str = f"{valor_total:,.0f} PYG" if valor_total is not None else "0 PYG"
                peso_total_str = f"{peso_total:.2f}" if peso_total is not None else "0.00"
                vol_total_str = f"{int(vol_total)}" if vol_total is not None else "0"

                # Insertar valores formateados en el TreeView
                self.treeview_cargamentos.insert("", "end", values=(
                    row[0],  # ID
                    row[1],  # Identidad
                    row[2],  # Vehículo
                    row[3],  # Chofer
                    valor_total_str,  # Valor formateado
                    peso_total_str,  # Peso formateado
                    vol_total_str   # Volumen formateado
                ), tags=tag)  # Aplicar el tag para el color

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los cargamentos: {e}")


    def _crear_tabview_datos(self):
        self.tabview = ctk.CTkTabview(self.frame_principal)
        self.tabview.pack(expand=True, fill="both")

        # Pestaña 1: Información del cargamento
        self.tab_informacion = self.tabview.add("Información")
        self._crear_tab_informacion()

        # Pestaña 2: Ítems del cargamento
        self.tab_items = self.tabview.add("Ítems")
        self._crear_tab_items()

        # Pestaña 3: Datos por empresa
        self.tab_empresas = self.tabview.add("Empresas")
        self._crear_tab_empresas()

    def _crear_tab_informacion(self):
        ctk.CTkLabel(self.tab_informacion, text="Información del Cargamento", font=("Arial", 14, "bold")).pack(pady=10)

        # Información básica
        self.entry_ident = ctk.CTkEntry(self.tab_informacion,state='readonly')
        self.entry_ident.pack(pady=10)

        # Campos de edición
        self.entry_vehiculo = ttk.Combobox(self.tab_informacion, state="disabled")
        self.entry_vehiculo.pack(pady=5)
        self.entry_chofer = ttk.Combobox(self.tab_informacion, state="disabled")
        self.entry_chofer.pack(pady=5)

        self.radio_activo = ctk.StringVar()
        self.radio_abierto = ctk.CTkRadioButton(self.tab_informacion, text="Abierto", variable=self.radio_activo, value="S")
        self.radio_cerrado = ctk.CTkRadioButton(self.tab_informacion, text="Cerrado", variable=self.radio_activo, value="N")

        self.radio_abierto.pack(pady=5)
        self.radio_cerrado.pack(pady=5)

        self.button_editar = ctk.CTkButton(self.tab_informacion, text="Editar", command=self._habilitar_edicion)
        self.button_editar.pack(pady=5)

        self.button_guardar = ctk.CTkButton(self.tab_informacion, text="Guardar", command=self._guardar_cambios, state="disabled")
        self.button_guardar.pack(pady=5)

    def _cargar_vehiculos(self, vehiculo_id=None):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()
            cursor.execute("SELECT id, nombre FROM vehiculos")
            vehiculos = cursor.fetchall()
            self.entry_vehiculo["values"] = [f"{v[0]} - {v[1]}" for v in vehiculos]

            # Si se pasa un `vehiculo_id`, se selecciona automáticamente el valor en el ComboBox
            if vehiculo_id:
                for i, v in enumerate(vehiculos):
                    if v[0] == vehiculo_id:
                        self.entry_vehiculo.set(f"{v[0]} - {v[1]}")  # Selecciona el vehiculo adecuado
                        break

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar vehículos: {e}")

    def _cargar_choferes(self, chofer_id=None):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()
            cursor.execute("SELECT c.id, u.nombre FROM choferes c LEFT JOIN usuarios u ON u.id = c.id")
            choferes = cursor.fetchall()
            self.entry_chofer["values"] = [f"{c[0]} - {c[1]}" for c in choferes]

            # Si se pasa un `chofer_id`, se selecciona automáticamente el valor en el ComboBox
            if chofer_id:
                for i, c in enumerate(choferes):
                    if c[0] == chofer_id:
                        self.entry_chofer.set(f"{c[0]} - {c[1]}")  # Selecciona el chofer adecuado
                        break

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar choferes: {e}")

    def _habilitar_edicion(self):
        self.entry_ident.configure(state='normal')
        self.entry_vehiculo["state"] = "readonly"
        self.entry_chofer["state"] = "readonly"
        self.button_guardar.configure(state="normal")
        self.button_editar.configure(text="Cancelar",command=self._cancelar_edicion,fg_color="red",hover_color="darkred")

    def _guardar_cambios(self):
        seleccion = self.treeview_cargamentos.focus()
        valores = self.treeview_cargamentos.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un cargamento para guardar los cambios.")
            return

        cargamento_id = valores[0]
        cargamento_nm = self.entry_ident.get()
        vehiculo_id = self.entry_vehiculo.get().split(" - ")[0]
        chofer_id = self.entry_chofer.get().split(" - ")[0]
        activo = self.radio_activo.get()

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            sql_update = """
                UPDATE cargamentos
                SET identidad = %s,vehiculo = %s, chofer = %s, activo = %s,
                    ultima_alteracion = NOW(), alterado_por = %s,
                    fecha_cierre = CASE WHEN %s = 'N' THEN NOW() ELSE NULL END,
                    cerrado_por = CASE WHEN %s = 'N' THEN %s ELSE NULL END
                WHERE id = %s;
            """
            cursor.execute(sql_update, (cargamento_nm,vehiculo_id, chofer_id, activo, self.sesion_usuario["id"], activo, activo, self.sesion_usuario["id"], cargamento_id))
            conexion.commit()

            messagebox.showinfo("Éxito", "Cambios guardados correctamente.")
            self._cargar_cargamentos()
            cursor.close()
            conexion.close()
            self._cancelar_edicion()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar los cambios: {e}")

    def _crear_tab_items(self):
        ctk.CTkLabel(self.tab_items, text="Ítems del Cargamento", font=("Arial", 14, "bold")).pack(pady=10)

        self.treeview_items = ttk.Treeview(self.tab_items,style='Custom.Treeview' , columns=("Item", "Cantidad", "Peso", "Valor"), show="headings")
        self.treeview_items.pack(expand=True, fill="both")

        self.treeview_items.heading("Item", text="Item")
        self.treeview_items.heading("Cantidad", text="Cant")
        self.treeview_items.heading("Peso", text="Peso")
        self.treeview_items.heading("Valor", text="Valor")

        self.treeview_items.column("Item", width=300)
        self.treeview_items.column("Cantidad", width=10)
        self.treeview_items.column("Peso", width=10)
        self.treeview_items.column("Valor", width=10)

    def _crear_tab_empresas(self):
        ctk.CTkLabel(self.tab_empresas, text="Datos por Empresa", font=("Arial", 14, "bold")).pack(pady=10)

        self.treeview_empresas = ttk.Treeview(self.tab_empresas,style='Custom.Treeview', columns=("Región", "Ciudad", "Empresa", "Valor", "Peso", "Volumen"), show="headings")
        self.treeview_empresas.pack(expand=True, fill="both")

        self.treeview_empresas.heading("Región", text="Región")
        self.treeview_empresas.heading("Ciudad", text="Ciudad")
        self.treeview_empresas.heading("Empresa", text="Empresa")
        self.treeview_empresas.heading("Valor", text="Valor")
        self.treeview_empresas.heading("Peso", text="Peso")
        self.treeview_empresas.heading("Volumen", text="Volumen")

        self.treeview_empresas.column("Región", width=60)
        self.treeview_empresas.column("Ciudad", width=70)
        self.treeview_empresas.column("Empresa", width=300)
        self.treeview_empresas.column("Valor", width=50)
        self.treeview_empresas.column("Peso", width=50)
        self.treeview_empresas.column("Volumen", width=50)

    def _cargar_datos_cargamento(self, event=None):
        seleccion = self.treeview_cargamentos.focus()
        valores = self.treeview_cargamentos.item(seleccion, "values")

        if not valores:
            return

        cargamento_id = valores[0]

        try:
            # Conexión a la base de datos
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # Consulta para obtener información del cargamento
            sql_cargamento = """
                SELECT c.identidad,c.vehiculo, c.chofer, c.activo 
                FROM cargamentos c
                WHERE c.id = %s;
            """
            cursor.execute(sql_cargamento, (cargamento_id,))
            resultado_cargamento = cursor.fetchone()

            if resultado_cargamento:
                cargamento_nm = resultado_cargamento[0]
                vehiculo_id = resultado_cargamento[1]
                chofer_id = resultado_cargamento[2]
                activo = resultado_cargamento[3]

                self.entry_ident.configure(state='normal')
                self.entry_ident.delete(0, "end")
                self.entry_ident.insert(0, cargamento_nm)
                self.entry_ident.configure(state='readonly')
                # Rellenar los combobox con los valores correspondientes
                self._cargar_vehiculos(vehiculo_id)
                self._cargar_choferes(chofer_id)

                # Establecer el estado de "Activo" en los radio buttons
                if activo == "S":
                    self.radio_abierto.select()
                else:
                    self.radio_cerrado.select()

            # Consulta para obtener información de los ítems
            sql_items = """
                SELECT pr.descripcion AS item, pp.cantidad_final, pr.peso, pp.cantidad_final * pp.precio_principal AS valor
                FROM carga_pedido cp
                LEFT JOIN pedidos p ON p.numero = cp.pedido
                LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                LEFT JOIN productos pr ON pr.id = pp.item
                WHERE cp.activo = 'S' and cp.cargamento = %s;
            """
            cursor.execute(sql_items, (cargamento_id,))
            resultados_items = cursor.fetchall()

            # Limpiar y cargar TreeView de ítems
            for item in self.treeview_items.get_children():
                self.treeview_items.delete(item)

            for row in resultados_items:
                # Formatear los valores de peso y valor
                valor_total = row[3]  # La columna de valor
                peso_total = row[2]   # La columna de peso

                valor_total_str = f"{valor_total:,.0f} PYG" if valor_total is not None else "0 PYG"
                peso_total_str = f"{peso_total:.2f}" if peso_total is not None else "0.00"

                # Insertar registros en el TreeView
                self.treeview_items.insert("", "end", values=(row[0], row[1], peso_total_str, valor_total_str))

            # Consulta para obtener información de empresas
            sql_empresas = """
                SELECT 
                    r.nombre AS region, cr.ciudad, CONCAT(e.id, ' - ', e.nombre) AS empresa,
                    SUM(pp.cantidad_final * pp.precio_principal) AS valor,
                    SUM(pp.cantidad_final * pr.peso) AS peso,
                    SUM(p.volumen) AS volumen
                FROM carga_pedido cp
                LEFT JOIN pedidos p ON p.numero = cp.pedido
                LEFT JOIN empresas e ON e.id = p.empresa
                LEFT JOIN ciudad_region cr ON cr.ciudad = e.ciudad
                LEFT JOIN regiones r ON r.id = cr.region
                LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                LEFT JOIN productos pr ON pr.id = pp.item
                WHERE cp.activo = 'S' and cp.cargamento = %s
                GROUP BY r.nombre, cr.ciudad, e.id, e.nombre;
            """
            cursor.execute(sql_empresas, (cargamento_id,))
            resultados_empresas = cursor.fetchall()

            # Limpiar y cargar TreeView de empresas
            for item in self.treeview_empresas.get_children():
                self.treeview_empresas.delete(item)

            for row in resultados_empresas:
                # Formatear los valores de valor, peso y volumen
                valor_total = row[3]  # La columna de valor
                peso_total = row[4]   # La columna de peso
                vol_total = row[5]    # La columna de volumen

                valor_total_str = f"{valor_total:,.0f} PYG" if valor_total is not None else "0 PYG"
                peso_total_str = f"{peso_total:.2f}" if peso_total is not None else "0.00"
                vol_total_str = f"{int(vol_total)}" if vol_total is not None else "0"

                # Insertar registros en el TreeView de empresas
                self.treeview_empresas.insert("", "end", values=(row[0], row[1], row[2], valor_total_str, peso_total_str, vol_total_str))

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los datos del cargamento: {e}")
    
    def _cancelar_edicion(self):
        self.entry_ident.configure(state='readonly')
        self.entry_vehiculo["state"] = "disabled"
        self.entry_chofer["state"] = "disabled"
        self.button_editar.configure(text="Editar", command=self._habilitar_edicion,
                                     fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                                     hover_color=ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        self.button_guardar.configure(state="disabled")
        self._cargar_datos_cargamento()


