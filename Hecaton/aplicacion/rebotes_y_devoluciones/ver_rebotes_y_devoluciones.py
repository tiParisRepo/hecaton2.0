import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from aplicacion.conectiondb.conexion import DBConnection

class ModuloVerRebotesYDevoluciones:
    def __init__(self, master, sesion_usuario):
        self.master = master
        self.sesion_usuario = sesion_usuario  # Información de la sesión activa
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=10)

        # Configurar el modo oscuro para toda la interfaz
        ctk.set_appearance_mode("dark")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Custom.Treeview",
                             background="#2b2b2b",
                             foreground="#E9F0ED",
                             rowheight=25,
                             fieldbackground="#333333",
                             font=("Arial", 12))
        self.style.map("Custom.Treeview", background=[("selected", "#1e527a")])
        self.style.configure("Custom.Treeview.Heading",
                             background="#1F6AA5",
                             foreground="#E9F0ED",
                             font=("Arial", 13, "bold"),
                             relief='flat')
        self.style.map("Custom.Treeview.Heading", background=[("active", "#1F6AA5")])

        self.treeview = None
        self._crear_interfaz()

    def _crear_interfaz(self):
        titulo = ctk.CTkLabel(self.frame_principal, text="Ver Devoluciones", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)

        # Sección de filtros
        filtro_frame = ctk.CTkFrame(self.frame_principal)
        filtro_frame.pack(pady=10, fill="x")

        self.entry_numero = ctk.CTkEntry(filtro_frame, placeholder_text='Número de Pedido')
        self.entry_numero.pack(side="left", padx=5, fill="x", expand=True)

        self.entry_cliente = ctk.CTkEntry(filtro_frame, placeholder_text='Nombre Cliente')
        self.entry_cliente.pack(side="left", padx=5, fill="x", expand=True)

        self.entry_vendedor = ctk.CTkEntry(filtro_frame, placeholder_text='Vendedor')
        self.entry_vendedor.pack(side="left", padx=5, fill="x", expand=True)

        # Botón de aplicar filtro
        self.boton_filtrar = ctk.CTkButton(self.frame_principal, text="Filtrar", command=self._filtrar_datos)
        self.boton_filtrar.pack(pady=5)

        # Frame para la tabla
        self.frame_consulta = ctk.CTkFrame(self.frame_principal)
        self.frame_consulta.pack(expand=True, fill="both", padx=10, pady=10)

        self.treeview = ttk.Treeview(self.frame_consulta, style='Custom.Treeview',columns=("secuencial", "pedido", "devolucion", "fecha_devolucion","cliente", "valor_devolucion", "tipo1", "tipo2", "tipo3", "tipo4", "observacion", "fecha_creacion", "creador"), show="headings")
        
        self.treeview.heading("secuencial", text="Seq")
        self.treeview.heading("pedido", text="Pedido")
        self.treeview.heading("devolucion", text="Devolución")
        self.treeview.heading("fecha_devolucion", text="Fecha Dev")
        self.treeview.heading("cliente", text="Cliente")
        self.treeview.heading("valor_devolucion", text="Valor Dev")
        self.treeview.heading("tipo1", text="Tipo 1")
        self.treeview.heading("tipo2", text="Tipo 2")
        self.treeview.heading("tipo3", text="Tipo 3")
        self.treeview.heading("tipo4", text="Tipo 4")
        self.treeview.heading("observacion", text="Observación")
        self.treeview.heading("fecha_creacion", text="Fecha Creación")
        self.treeview.heading("creador", text="Creador")

        self.treeview.column("secuencial", width=50, anchor="center")
        self.treeview.column("pedido", width=70, anchor="center")
        self.treeview.column("devolucion", width=105, anchor="center")
        self.treeview.column("fecha_devolucion", width=100, anchor="center")
        self.treeview.column("cliente", width=220, anchor="w")
        self.treeview.column("valor_devolucion", width=100, anchor="center")
        self.treeview.column("tipo1", width=120, anchor="center")
        self.treeview.column("tipo2", width=120, anchor="center")
        self.treeview.column("tipo3", width=120, anchor="center")
        self.treeview.column("tipo4", width=120, anchor="center")
        self.treeview.column("observacion", width=150, anchor="w")
        self.treeview.column("fecha_creacion", width=130, anchor="center")
        self.treeview.column("creador", width=120, anchor="center")

        self.treeview.pack(side='bottom',expand=True, fill="y")
        self.treeview.bind("<Double-1>", self._crear_devolucion)  # Doble clic para ver los detalles

        self._cargar_datos()  # Cargar datos al iniciar el módulo

    def _filtrar_datos(self):
        """Función para obtener los filtros y cargar los datos filtrados."""
        numero = self.entry_numero.get().strip()
        empresa = self.entry_cliente.get().strip()
        vendedor = self.entry_vendedor.get().strip()

        self._cargar_datos(numero, empresa, vendedor)

    def _cargar_datos(self, numero="", empresa="", vendedor=""):
        """Carga los datos de las devoluciones desde la tabla `devreb`."""
        try:
            db = DBConnection()
            conn = db.connect_mysql() 
            cursor = conn.cursor()

            query = """
                    select
                        d.secuencial,
                        d.pedido,
                        d.devolucion,
                        d.fecha_devolucion,
                        CONCAT(e.nombre, ' (',e.id,')') as cliente,
                        d.valor_devolucion,
                        CONCAT(t1.id, '-', t1.nombre) as tipo1,
                        CONCAT(t2.id, '-', t2.nombre) as tipo2,
                        CONCAT(t3.id, '-', t3.nombre) as tipo3,
                        CONCAT(t4.id, '-', t4.nombre) as tipo3,
                        d.observacion,
                        d.fecha_creacion,
                        CONCAT(d.creador, '-', u.usuario) as creador,
                        p.moneda
                    from
                        devreb d
                    left join tipo1 t1 on
                        t1.id = d.tipo1
                    left join tipo2 t2 on
                        t2.id = d.tipo2
                    left join tipo3 t3 on
                        t3.id = d.tipo3
                    left join tipo4 t4 on
                        t4.id = d.tipo4
                    left join usuarios u on
                        u.id = d.creador
                    left join pedidos p on
                        p.numero = d.pedido
                    left join empresas e on
                        e.id = p.empresa
            """

            filtros = []
            if numero:
                filtros.append(f"pedido LIKE '%{numero}%' OR devolucion LIKE '%{numero}%'")
            if empresa:
                filtros.append(f"observacion LIKE '%{empresa}%'")
            if vendedor:
                filtros.append(f"creador LIKE '%{vendedor}%'")

            if filtros:
                query += " WHERE " + " AND ".join(filtros)

            query += " ORDER BY fecha_creacion DESC;"

            cursor.execute(query)
            resultados = cursor.fetchall()

            # Limpiar el Treeview antes de insertar nuevos datos
            self.treeview.delete(*self.treeview.get_children())

            if not resultados:
                messagebox.showwarning("Sin resultados", "No se encontraron registros.")

            for row in resultados:
                valor = f"{row[5]:,.2f}" if row[13] in ('1','2') else f"{row[5]:,.0f}"
                fecha_devolucion = row[3].strftime("%d/%m/%Y") if row[3] else "N/A"
                fecha_creacion = row[11].strftime("%d/%m/%Y %H:%M") if row[11] else "N/A"
                self.treeview.insert("", "end", values=(row[0], row[1], row[2], fecha_devolucion,row[4], valor, row[6], row[7], row[8], row[9], row[10], fecha_creacion, row[12]))

            conn.close()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar los datos: {e}")

    def _crear_devolucion(self, event=None):
        """Función para crear una devolución al hacer doble clic en un registro del Treeview."""
        selected_item = self.treeview.selection()  # Obtener la selección actual en el Treeview
        if selected_item:
            # Obtener los datos del registro seleccionado
            item_values = self.treeview.item(selected_item)['values']
            numero_seleccionado = item_values[0]


            # Consultar la base de datos para obtener la información completa del registro seleccionado
            db = DBConnection()
            conn = db.connect_mysql()  # Crear conexión MySQL aquí
            cursor = conn.cursor()  # Ahora obtenemos el cursor correctamente

            try:
                query = """
            select
                e.id,
                e.nombre,
                u.identify,
                u.usuario,
                p.numero,
                p.factura,
                d.valor_devolucion,
                case
                    when p.moneda = '0' then 'Guaranies'
                    when p.moneda = '1' then 'Dolares'
                    when p.moneda = '2' then 'Reales'
                    else 'N/A'
                end as moneda,
                d.tipo1,
                d.tipo2,
                d.tipo3,
                d.tipo4,
                d.observacion,
                d.fecha_devolucion,
                d.devolucion,
                sum(pp.cantidad_final * pp.precio_principal) as valor
            from
                devreb d
            left join pedidos p on
                p.numero = d.pedido
            left join empresas e on
                e.id = p.empresa
            left join usuarios u on
                u.identify = p.vendedor
            left join producto_pedido pp on
                pp.pedido = p.numero
            where
                d.secuencial = %s
            group by
                e.id,
                e.nombre,
                u.identify,
                u.usuario,
                p.numero,
                p.factura,
                d.valor_devolucion,
                d.fecha_devolucion,
                d.observacion,
                p.moneda;
                """
                cursor.execute(query, (numero_seleccionado,))
                result = cursor.fetchone()
                result = result + (numero_seleccionado,)

                if result:
                    # Mostrar el menú de devolución con los datos completos del registro
                    self.mostrar_menu_devolucion(result)
                else:
                    messagebox.showerror("Error", "No se encontraron datos para la devolución seleccionada.")

            finally:
                cursor.close()
                conn.close()
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una devolución en el Treeview.")

    def mostrar_menu_devolucion(self, result=None, editable=False):
        menu_devolucion = ctk.CTkToplevel(self.master)
        menu_devolucion.title("Menú de Devoluciones")
        menu_devolucion.geometry("880x390")
        menu_devolucion.resizable(0, 0)

        # Crear ComboBox para tipo1, tipo2, tipo3 y tipo4
        infoframe = tk.LabelFrame(menu_devolucion, text='Información:', bg="#242424", fg="#E9F0ED", relief='sunken', bd=2)
        infoframe.grid(row=0, column=0, rowspan=2, padx=20, pady=10, sticky="news")

        # Crear los campos para tipo1, tipo2, tipo3, tipo4
        ctk.CTkLabel(infoframe, text="Emp_Código:").grid(row=0, column=1, sticky='ew')
        entry_codigo_cliente = ctk.CTkEntry(infoframe, justify='center', width=70)
        entry_codigo_cliente.grid(row=1, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(infoframe, text="Empresa:").grid(row=0, column=2, sticky='ew')
        entry_empresa = ctk.CTkEntry(infoframe, justify="left", width=300)
        entry_empresa.grid(row=1, column=2, columnspan=2, pady=(0,10), padx=10, sticky='ew') 

        ctk.CTkLabel(infoframe, text="Vend_Código:").grid(row=2, column=1, sticky='ew')
        entry_codigo_vendedor = ctk.CTkEntry(infoframe, justify='center', width=70)
        entry_codigo_vendedor.grid(row=3, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(infoframe, text="Vendedor:").grid(row=2, column=2, sticky='ew')
        entry_vendedor = ctk.CTkEntry(infoframe, justify="center", width=150)
        entry_vendedor.grid(row=3, column=2, pady=(0, 10), padx=10)

        # Entrys para completar información
        ctk.CTkLabel(infoframe, text="Número:").grid(row=4, column=1, sticky='ew')
        entry_numero = ctk.CTkEntry(infoframe, justify='center', width=65)
        entry_numero.grid(row=5, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(infoframe, text="Factura:").grid(row=4, column=2, sticky='ew')
        entry_factura = ctk.CTkEntry(infoframe, justify='center', width=65)
        entry_factura.grid(row=5, column=2, pady=(0, 10), padx=10)

        ctk.CTkLabel(infoframe, text="Valor:").grid(row=6, column=1, sticky='ew')
        entry_valor = ctk.CTkEntry(infoframe, justify="center", width=90)
        entry_valor.grid(row=7, column=1, pady=(0, 10), padx=10)

        ctk.CTkLabel(infoframe, text="Moneda:").grid(row=6, column=2, sticky='ew')
        entry_moneda = ctk.CTkEntry(infoframe, justify="center", width=70)
        entry_moneda.grid(row=7, column=2, pady=(0, 10), padx=10)

        completeFrame = tk.LabelFrame(menu_devolucion, text='Clasificación:', bg="#242424", fg="#E9F0ED", relief='sunken', bd=2)
        completeFrame.grid(row=0, column=1, padx=20, pady=10, sticky="we")

        # Tipo1, Tipo2, Tipo3, Tipo4
        ctk.CTkLabel(completeFrame, text="Tipo 1:").grid(row=0, column=0, padx=10)
        combo_tipo1 = ttk.Combobox(completeFrame, justify="left")
        combo_tipo1.grid(row=1, column=0, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Tipo 2:").grid(row=0, column=1, padx=10)
        combo_tipo2 = ttk.Combobox(completeFrame, justify="left")
        combo_tipo2.grid(row=1, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Tipo 3:").grid(row=2, column=0, padx=10)
        combo_tipo3 = ttk.Combobox(completeFrame, justify="left")
        combo_tipo3.grid(row=3, column=0, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Tipo 4:").grid(row=2, column=1, padx=10)
        combo_tipo4 = ttk.Combobox(completeFrame, justify="left")
        combo_tipo4.grid(row=3, column=1, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Valor de Devolución:").grid(row=4, column=0, padx=10,sticky='ew')
        entry_valor_devolucion = ctk.CTkEntry(completeFrame, justify="right", width=90)
        entry_valor_devolucion.grid(row=5, column=0, padx=10, pady=(0, 10),sticky='ew')

        ctk.CTkLabel(completeFrame, text="Numero de Devolución:").grid(row=4, column=1, padx=10,sticky='ew')
        entry_numero_devolucion = ctk.CTkEntry(completeFrame, justify="right", width=90)
        entry_numero_devolucion.grid(row=5, column=1, padx=10, pady=(0, 10),sticky='ew')

        ctk.CTkLabel(completeFrame, text="Fecha de Devolución:").grid(row=6, column=0, columnspan=2, padx=10)
        fecha_devolucion = DateEntry(completeFrame, justify="right", date_pattern='dd/mm/yyyy', background='darkblue', foreground='white', borderwidth=2, relief='solid')
        fecha_devolucion.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Observación:").grid(row=8, column=0, columnspan=2, padx=10)
        entry_observacion = ctk.CTkEntry(completeFrame, justify="left", width=350)
        entry_observacion.grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 10),sticky='ew')
        
        if result:
            entry_codigo_cliente.insert(0, result[0])
            entry_codigo_cliente.configure(state="normal" if editable else "readonly") 
            entry_empresa.insert(0, result[1])
            entry_empresa.configure(state="normal" if editable else "readonly") 
            entry_codigo_vendedor.insert(0, result[2])
            entry_codigo_vendedor.configure(state="normal" if editable else "readonly")
            entry_vendedor.insert(0, result[3])
            entry_vendedor.configure(state="normal" if editable else "readonly")
            entry_numero.insert(0, result[4])
            entry_numero.configure(state="normal" if editable else "readonly")
            entry_factura.insert(0, result[5] if result[5] else "N/A")
            entry_factura.configure(state="normal" if editable else "readonly")
            entry_valor.insert(0, f'{result[15]:,.0f}' if result[7] == 'Guaranies' else f'{result[15]:,.2f}')
            entry_valor.configure(state="normal" if editable else "readonly")
            entry_moneda.insert(0, result[7])
            entry_moneda.configure(state="normal" if editable else "readonly")
            entry_valor_devolucion.insert(0, f'{result[6]:,.0f}' if result[7] == 'Guaranies' else f'{result[6]:,.2f}')
            entry_numero_devolucion.insert(0, result[14])
            entry_observacion.insert(0, result[12])
            fecha_devolucion.set_date(result[13])



        # Llenar ComboBox de tipo1, tipo2, tipo3
        combo1 = self._llenar_combobox_tipo1()
        combo_tipo1['values'] = list(combo1.keys())

        actual_tipo1 = result[8] if result else None

        if actual_tipo1 in combo1.values():

            index = list(combo1.values()).index(actual_tipo1)
            
            combo_tipo1.current(index)  
        else:
            if combo_tipo1['values']:
                combo_tipo1.current(0)

        def _obtener_id_tipo1(combo_tipo1):
            id_tipo1 = int(combo1[combo_tipo1.get()]) if combo_tipo1.get() in combo1 else 0
            return id_tipo1

        combo2 = self._llenar_combobox_tipo2()
        combo_tipo2['values'] = list(combo2.keys())

        actual_tipo2 = result[9] if result else None

        if actual_tipo2 in combo2.values():
            index = list(combo2.values()).index(actual_tipo2)
            
            combo_tipo2.current(index)
        else:
            if combo_tipo2['values']:
                combo_tipo2.current(0)
        
        def _obtener_id_tipo2(combo_tipo2):
            id_tipo2 = int(combo2[combo_tipo2.get()]) if combo_tipo2.get() in combo2 else 0
            return id_tipo2

        combo3 = self._llenar_combobox_tipo3()
        combo_tipo3['values'] = list(combo3.keys())

        actual_tipo3 = result[10] if result else None
        if actual_tipo3 in combo3.values():
            index = list(combo3.values()).index(actual_tipo3)
            
            combo_tipo3.current(index)
        else:
            if combo_tipo3['values']:
                combo_tipo3.current(0)
        
        def _obtener_id_tipo3(combo_tipo3):
            id_tipo3 = int(combo3[combo_tipo3.get()]) if combo_tipo3.get() in combo3 else 0
            return id_tipo3

        combo4 = self._llenar_tipo4(combo_tipo3)
        combo_tipo4['values'] = list(combo4.keys())
        actual_tipo4 = result[11] if result else None
        if actual_tipo4 in combo4.values():
            index = list(combo4.values()).index(actual_tipo4)
            
            combo_tipo4.current(index)
        else:
            if combo_tipo4['values']:
                combo_tipo4.current(0)

        def _obtener_id_tipo4(combo_tipo4):
            combo4 = self._llenar_tipo4(combo_tipo3)
            id_tipo4 = int(combo4[combo_tipo4.get()]) if combo_tipo4.get() in combo4 else 0
            return id_tipo4
        
        # Vincular el cambio de tipo3 para actualizar tipo4
        combo_tipo3.bind("<<ComboboxSelected>>", lambda event: self._actualizar_tipo4(event, combo_tipo3, combo_tipo4))

        def _obterner_valor_devolucion(entry_valor_devolucion):
            valor_devolucion = entry_valor_devolucion.get()
            if valor_devolucion:
                valor_devolucion = valor_devolucion.replace(',', '')
                try:
                    valor_devolucion = float(valor_devolucion)
                except ValueError:
                    messagebox.showerror("Error", "El valor de devolución no es válido.")
                    return None
            return valor_devolucion
        

        def formatear_numero(event):
                if entry_valor_devolucion.get() != '':
                    valor = entry_valor_devolucion.get().replace(',', '')
                    dev = float(valor) if valor else None
                    
                    try:
                    # Formatear el número (por ejemplo, convertir a número entero)
                        numero_formateado = f"{dev:,.0f}" if entry_moneda.get() == 'Guaranies' else f"{dev:,.2f}"
                    # Establecer el texto formateado de nuevo en el Entr
                        entry_valor_devolucion.delete(0,tk.END)
                        entry_valor_devolucion.insert(0, numero_formateado)  # Insertar el nuevo texto
                        
                    except ValueError:
                        messagebox.showerror('Valor no numerico','Solo se admite la entrada de valores numerico.')  # Ignorar si no se puede convertir el texto a número
                
                else:
                    dev = None
        entry_valor_devolucion.bind("<FocusOut>", formatear_numero)
        
        # Botón de guardar
        frame_boton_guardar = tk.Frame(menu_devolucion, bg="#242424")
        frame_boton_guardar.grid(row=1, column=1, columnspan=2, padx=20, sticky="n")

        ctk.CTkButton(frame_boton_guardar, text="Guardar", command=lambda: self._guardar_devolucion(result[-1], 
                                                                                                    _obtener_id_tipo1(combo_tipo1),
                                                                                                    _obtener_id_tipo2(combo_tipo2),
                                                                                                    _obtener_id_tipo3(combo_tipo3),
                                                                                                    _obtener_id_tipo4(combo_tipo4),
                                                                                                   _obterner_valor_devolucion(entry_valor_devolucion),
                                                                                                    entry_numero_devolucion.get(),
                                                                                                    entry_observacion.get(),
                                                                                                    menu_devolucion
                                                                                                    )).grid(row=0, column=0, pady=10, padx=20)
        ctk.CTkButton(frame_boton_guardar, text="Cancelar", fg_color='red', hover_color="darkred", command=menu_devolucion.destroy).grid(row=0, column=1, pady=10, padx=20)

    def _guardar_devolucion(self,secuencial_devolucion,tipo1_id,tipo2_id,tipo3_id,tipo4_id,valor=None,numero_devolucion=None,observacion=None,menu_devolucion=None):
        try:
            db = DBConnection()
            conn = db.connect_mysql() 
            cursor = conn.cursor()

            date_act = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            act = self.sesion_usuario['id']
            query = """
                update devreb
                set tipo1=%s, tipo2=%s, tipo3=%s, tipo4=%s,valor_devolucion=%s,devolucion=%s,observacion=%s, ultimo_ajust=%s, date_ult_ajust=CURRENT_TIMESTAMP
                where secuencial=%s
            """
            cursor.execute(query,(tipo1_id,tipo2_id,tipo3_id,tipo4_id,valor,numero_devolucion,observacion,act,secuencial_devolucion))
            print('aca bien 4')
            conn.commit() 
            cursor.close()
            print('aca bien 5')
            conn.close()
            messagebox.showinfo("Éxito", "Devolución guardada exitosamente.")
            if menu_devolucion:
                menu_devolucion.destroy()
            self._cargar_datos()  # Recargar datos después de guardar la devolución
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la devolución: {e}")

    def _llenar_combobox_tipo1(self):
        db = DBConnection()
        conn = db.connect_mysql()
        cursor = conn.cursor()

        query = "SELECT t1.id, t1.nombre FROM tipo1 t1"
        cursor.execute(query)
        tipo1_data = cursor.fetchall()
        tipo1_data = {nombre: id for id, nombre in tipo1_data}  # Cambiar el orden a {nombre: id}
        conn.close()
        return tipo1_data

    def _llenar_combobox_tipo2(self):
        # Consulta a la base de datos para llenar el ComboBox de tipo2
        db = DBConnection()
        conn = db.connect_mysql()  # Crear conexión MySQL aquí
        cursor = conn.cursor()

        query = "SELECT t2.id, t2.nombre FROM tipo2 t2"
        cursor.execute(query)
        tipo2_data = cursor.fetchall()
        tipo2_data = {nombre: id for id, nombre in tipo2_data}  # Cambiar el orden a {nombre: id}

        conn.close()

        return tipo2_data

    def _llenar_combobox_tipo3(self):
        # Consulta a la base de datos para llenar el ComboBox de tipo3
        db = DBConnection()
        conn = db.connect_mysql()  # Crear conexión MySQL aquí
        cursor = conn.cursor()

        query = "SELECT t3.id, t3.nombre FROM tipo3 t3"
        cursor.execute(query)
        tipo3_data = cursor.fetchall()
        tipo3_data = {nombre: id for id, nombre in tipo3_data}  # Cambiar el orden a {nombre: id}

        conn.close()

        return tipo3_data
    
    def _llenar_tipo4(self,combo_tipo3):
        tipo3_seleccionado = combo_tipo3.get()
        
        # Consultar la base de datos para llenar el ComboBox de tipo4 dependiendo de tipo3
        db = DBConnection()
        conn = db.connect_mysql()  # Crear conexión MySQL aquí
        cursor = conn.cursor()

        query = "SELECT t4.id, t4.nombre FROM tipo4 t4 JOIN tipo3 t3 ON t4.id_tipo3 = t3.id WHERE t3.nombre = %s"
        cursor.execute(query, (tipo3_seleccionado,))
        tipo4_data = cursor.fetchall()
        tipo4_data = {nombre: id for id, nombre in tipo4_data}  # Cambiar el orden a {nombre: id}
        conn.close()
        return tipo4_data

    def _actualizar_tipo4(self, event, combo_tipo3, combo_tipo4):
        tipo3_seleccionado = combo_tipo3.get()
        
        # Consultar la base de datos para llenar el ComboBox de tipo4 dependiendo de tipo3
        db = DBConnection()
        conn = db.connect_mysql()  # Crear conexión MySQL aquí
        cursor = conn.cursor()

        query = "SELECT t4.id, t4.nombre FROM tipo4 t4 JOIN tipo3 t3 ON t4.id_tipo3 = t3.id WHERE t3.nombre = %s"
        cursor.execute(query, (tipo3_seleccionado,))
        tipo4_data = cursor.fetchall()

        combo_tipo4['values'] = [nombre for _, nombre in tipo4_data]
        if combo_tipo4['values']:
            combo_tipo4.current(0)
        conn.close()
