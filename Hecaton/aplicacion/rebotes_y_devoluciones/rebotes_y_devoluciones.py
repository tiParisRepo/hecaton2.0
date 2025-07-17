import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox,LabelFrame
from tkcalendar import DateEntry
from datetime import datetime
from aplicacion.conectiondb.conexion import DBConnection

class ModuloRebotesDevoluciones:
    def __init__(self, master, sesion_usuario):
        self.master = master
        self.sesion_usuario = sesion_usuario  # Información de la sesión activa
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=10)

        # Configurar el modo oscuro para toda la interfaz
        ctk.set_appearance_mode("dark")  # Habilita el modo oscuro

        # Configurar estilo para el Treeview
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Custom.Treeview",
                             background="#2b2b2b",
                             foreground="#E9F0ED",
                             rowheight=25,
                             fieldbackground="#333333",
                             font=("Arial", 12))
        self.style.map("Custom.Treeview", background=[("selected", "#144870")])
        self.style.configure("Custom.Treeview.Heading",
                             background="#1F6AA5",
                             foreground="#E9F0ED",
                             font=("Arial", 13, "bold"),
                             relief='flat')
        self.style.map("Custom.Treeview.Heading", background=[("active", "#1F6AA5")])


        self.tipo3_opciones = {}
        self._crear_interfaz()

    def _crear_interfaz(self):
        titulo = ctk.CTkLabel(self.frame_principal, text="Gestión de Rebotes y Devoluciones", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)

        # Sección de filtros
        filtro_frame = ctk.CTkFrame(self.frame_principal)
        filtro_frame.pack(pady=10, fill="x")
        
        self.entry_numero = ctk.CTkEntry(filtro_frame, placeholder_text='16558 o 1963')
        self.entry_numero.pack(side="left", padx=5, fill="x", expand=True)
        
        self.entry_cliente = ctk.CTkEntry(filtro_frame, placeholder_text='803 o AGROVETERINARIA MUNDO RURAL')
        self.entry_cliente.pack(side="left", padx=5, fill="x", expand=True)

        self.entry_vendedor = ctk.CTkEntry(filtro_frame, placeholder_text='039 o GENERAL')
        self.entry_vendedor.pack(side="left", padx=5, fill="x", expand=True)

        # Botón de aplicar filtro
        self.boton_filtrar = ctk.CTkButton(self.frame_principal, text="Filtrar", command=self._filtrar_datos)  # Botón con color claro
        self.boton_filtrar.pack(pady=5)

        # Frame para la tabla
        self.frame_consulta = ctk.CTkFrame(self.frame_principal)
        self.frame_consulta.pack(expand=True, fill="both", padx=10, pady=10)

        self.treeview = ttk.Treeview(self.frame_consulta, style='Custom.Treeview', columns=("numero", "factura", "fecha", "cod_emp", "empresa", "valor", "cod_vend", "vendedor", "devolucion"), show="headings")
        self.treeview.heading("numero", text="Número")
        self.treeview.heading("factura", text="Factura")
        self.treeview.heading("fecha", text="Fecha")
        self.treeview.heading("cod_emp", text="Cod_Empresa", anchor="center")
        self.treeview.heading("empresa", text="Empresa")
        self.treeview.heading("valor", text="Valor")
        self.treeview.heading("cod_vend", text="Cod_Vendedor", anchor="center")
        self.treeview.heading("vendedor", text="Vendedor")
        self.treeview.heading("devolucion", text="Devolución")

        self.treeview.column("numero", width=5, anchor="center")
        self.treeview.column("factura", width=5, anchor="center")
        self.treeview.column("fecha", width=5, anchor="center")
        self.treeview.column("cod_emp", width=5, anchor="center")
        self.treeview.column("empresa", width=200, anchor='w')
        self.treeview.column("valor", width=5, anchor="e")
        self.treeview.column("cod_vend", width=5, anchor="center")
        self.treeview.column("vendedor", width=5, anchor="center")
        self.treeview.column("devolucion", width=5, anchor="e")

        self.treeview.pack(expand=True, fill="both")
        self.treeview.bind("<Double-1>", self._crear_devolucion)  # Doble clic para abrir el menú de devolución
        self._cargar_datos()  # Cargar datos al iniciar el módulo

    def _filtrar_datos(self):
        """Función para obtener los filtros y cargar los datos filtrados."""
        numero = self.entry_numero.get().strip()
        empresa = self.entry_cliente.get().strip()
        vendedor = self.entry_vendedor.get().strip()

        # Pasar los filtros a la función que carga los datos
        self._cargar_datos(numero, empresa, vendedor)

    def _cargar_datos(self, numero="", empresa="", vendedor=""):
        """Carga los datos en el Treeview desde la base de datos, con o sin filtro."""
        try:
            db = DBConnection()
            conn = db.connect_mysql()  # Crear conexión MySQL aquí
            cursor = conn.cursor()  # Ahora obtenemos el cursor correctamente

            # Consulta base
            query = """
                    select
                        coalesce(p.numero, 'N/A') as numero,
                        coalesce(p.factura, 'N/A') as factura,
                        coalesce(cast(p.fecha as date), 'N/A') as fecha,
                        coalesce(e.id, 'N/A') as cod_emp,
                        coalesce(e.nombre, 'N/A') as empresa,
                        pp.valor,
                        coalesce(u.id, 'N/A') as cod_vend,
                        coalesce(u.usuario, 'N/A') as vendedor,
                        (select sum(dr.valor_devolucion) 
                        from devreb dr 
                        where dr.pedido = p.numero) as devolucion,
                        p.moneda
                    from pedidos p
                    left join empresas e on e.id = p.empresa
                    left join usuarios u on u.identify = p.vendedor
                    left join devreb d on d.pedido = p.numero
                    left join (
                        select secuencialpedido, sum(precio * cantidad_final) as valor
                        from producto_pedido
                        group by secuencialpedido
                    ) pp on pp.secuencialpedido = p.sequencial
            """

            # Aplicar filtros
            filtros = []
            if numero:
                filtros.append(f"(p.numero LIKE '%{numero}%' OR p.factura LIKE '%{numero}%')")
            if empresa:
                filtros.append(f"e.nombre LIKE '%{empresa}%' OR e.id LIKE '%{empresa}%'")
            if vendedor:
                filtros.append(f"u.usuario LIKE '%{vendedor}%' OR u.id LIKE '%{vendedor}%'")

            if filtros:
                query += " WHERE " + " AND ".join(filtros)

            query += """
                group by
                    p.numero,
                    p.factura,
                    p.fecha,
                    e.id,
                    e.nombre,
                    u.id,
                    u.usuario,
                    p.moneda,
                    pp.valor
                order by
                    p.numero desc
                limit 500;
            """

            cursor.execute(query)
            resultados = cursor.fetchall()

            # Limpiar el Treeview antes de insertar nuevos datos
            self.treeview.delete(*self.treeview.get_children())

            if not resultados:
                messagebox.showwarning("Sin resultados", "No se encontraron registros.")

            for row in resultados:
                # Verificar si los valores son None, si es así, asignar 0
                valor = row[5] if row[5] is not None else 0
                devolucion = row[8] if row[8] is not None else 0

                # Formatear las columnas "valor" y "devolucion" como moneda
                valor_formateado = f"{valor:,.2f}" if row[-1] in ('1','2') else f"{valor:,.0f}"
                devolucion_formateado = f"{devolucion:,.2f}" if row[-1] in ('1','2') else f"{devolucion:,.0f}"	

                # Formatear la fecha en el formato dd/mm/yyyy
                fecha_raw = row[2]
                if fecha_raw and fecha_raw != 'N/A':
                    try:
                        fecha = datetime.strptime(fecha_raw, '%Y-%m-%d')  # Suponiendo que la fecha está en formato YYYY-MM-DD
                        fecha_formateada = fecha.strftime('%d/%m/%Y')  # Formato dd/mm/yyyy
                    except ValueError:
                        fecha_formateada = 'Fecha Inválida'
                else:
                    fecha_formateada = 'N/A'

                # Insertar los resultados en el Treeview
                self.treeview.insert("", "end", values=(row[0], row[1], fecha_formateada, row[3], row[4], valor_formateado, row[6], row[7], devolucion_formateado))

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
                SELECT
                    p.numero,
                    coalesce(p.factura, 'N/A') AS factura,
                    e.id AS cod_emp,
                    e.nombre AS empresa,
                    sum(pp.precio * pp.cantidad_final) AS valor,
                    case
                    when p.moneda = '0' then 'Guaranies'
                    when p.moneda = '1' then 'Dolares'
                    when p.moneda = '2' then 'Reales'
                    else 'N/A'
                    end as moneda,
                    p.vendedor,
                    u.usuario
                FROM pedidos p
                LEFT JOIN empresas e ON e.id = p.empresa
                left join producto_pedido pp on pp.pedido = p.numero
                left join usuarios u on u.identify = p.vendedor
                WHERE p.numero = %s
                group by p.numero,p.factura, e.id,e.nombre,p.moneda,p.vendedor,u.usuario;
                """
                cursor.execute(query, (numero_seleccionado,))
                result = cursor.fetchone()

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

    def mostrar_menu_devolucion(self, result=None):
        menu_devolucion = ctk.CTkToplevel(self.master)
        menu_devolucion.title("Menú de Devoluciones")
        menu_devolucion.geometry("880x390")
        menu_devolucion.resizable(0, 0)

        # Crear ComboBox para tipo1, tipo2, tipo3 y tipo4
        infoframe = tk.LabelFrame(menu_devolucion, text='Información:', bg="#242424", fg="#E9F0ED", relief='sunken', bd=2)
        infoframe.grid(row=0, column=0, rowspan=2, padx=20, pady=10, sticky="news")

        # Crear los campos para tipo1, tipo2, tipo3, tipo4
        ctk.CTkLabel(infoframe, text="Emp_Código:").grid(row=0, column=1,sticky='ew')
        entry_codigo_cliente = ctk.CTkEntry(infoframe, justify='center', width=70)
        entry_codigo_cliente.grid(row=1, column=1, padx=10, pady=(0,10))

        ctk.CTkLabel(infoframe, text="Empresa:").grid(row=0, column=2,sticky='ew')
        entry_empresa = ctk.CTkEntry(infoframe, justify="left", width=300)
        entry_empresa.grid(row=1, column=2, columnspan=2, pady=(0,10), padx=10, sticky='ew') 

        ctk.CTkLabel(infoframe, text="Vend_Código:").grid(row=2, column=1,sticky='ew')
        entry_codigo_vendedor = ctk.CTkEntry(infoframe, justify='center', width=70)
        entry_codigo_vendedor.grid(row=3, column=1, padx=10, pady=(0,10))

        ctk.CTkLabel(infoframe, text="Vendedor:").grid(row=2, column=2,sticky='ew')
        entry_vendedor = ctk.CTkEntry(infoframe, justify="center", width=150)
        entry_vendedor.grid(row=3, column=2, pady=(0,10), padx=10)

        # Entrys para completar información
        ctk.CTkLabel(infoframe, text="Número:").grid(row=4, column=1,sticky='ew')
        entry_numero = ctk.CTkEntry(infoframe, justify='center', width=65)
        entry_numero.grid(row=5, column=1, padx=10,pady=(0,10))

        ctk.CTkLabel(infoframe, text="Factura:").grid(row=4, column=2,sticky='ew')
        entry_factura = ctk.CTkEntry(infoframe, justify='center', width=65)
        entry_factura.grid(row=5, column=2, pady=(0,10), padx=10)

        ctk.CTkLabel(infoframe, text="Valor:").grid(row=6, column=1,sticky='ew')
        entry_valor = ctk.CTkEntry(infoframe, justify="center", width=90)
        entry_valor.grid(row=7, column=1, pady=(0,10), padx=10)

        ctk.CTkLabel(infoframe, text="Moneda:").grid(row=6, column=2,sticky='ew')
        entry_moneda = ctk.CTkEntry(infoframe, justify="center", width=70)
        entry_moneda.grid(row=7, column=2, pady=(0,10), padx=10)

        valor_default = ''
        # Insertar los valores obtenidos desde la base de datos
        if result:
            entry_numero.insert(0, result[0])
            entry_numero.configure(state="readonly")  # Hacer el campo de número de pedido de solo lectura
            entry_factura.insert(0, result[1])
            entry_factura.configure(state="readonly")  # Hacer el campo de factura de solo lectura
            entry_codigo_cliente.insert(0, result[2])  # Código cliente si está disponible
            entry_codigo_cliente.configure(state="readonly") # Hacer el campo de código cliente de solo lectura
            entry_empresa.insert(0, result[3])
            entry_empresa.configure(state="readonly")  # Hacer el campo de empresa de solo lectura
            entry_codigo_vendedor.insert(0, result[6])
            entry_codigo_vendedor.configure(state="readonly")  # Hacer el campo de código vendedor de solo lectura
            entry_vendedor.insert(0, result[7])
            entry_vendedor.configure(state="readonly")
            entry_valor.insert(0, f'{result[4]:,.0f}' if result[5] == 'Guaranies' else f'{result[4]:,.2f}')
            valor_default = entry_valor.get()
            entry_valor.configure(state="readonly")  # Hacer el campo de valor de solo lectura
            entry_moneda.insert(0, result[5])
            entry_moneda.configure(state="readonly")

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

        # Llenar ComboBox de tipo1, tipo2, tipo3
        combo1 = self._llenar_combobox_tipo1()
        combo_tipo1['values'] = list(combo1.keys())
        
        if combo_tipo1['values']:
            combo_tipo1.current(0)

        def _obtener_id_tipo1(combo_tipo1):
            id_tipo1 = combo1[combo_tipo1.get()] if combo_tipo1.get() in combo1 else 0
            return id_tipo1

        combo2 = self._llenar_combobox_tipo2()
        combo_tipo2['values'] = list(combo2.keys())

        if combo_tipo2['values']:
            combo_tipo2.current(0)
        
        def _obtener_id_tipo2(combo_tipo2):
            id_tipo2 = combo2[combo_tipo2.get()] if combo_tipo2.get() in combo2 else 0
            return id_tipo2

        combo3 = self._llenar_combobox_tipo3()
        combo_tipo3['values'] = list(combo3.keys())

        if combo_tipo3['values']:
            combo_tipo3.current(0)
        
        def _obtener_id_tipo3(combo_tipo3):
            id_tipo3 = combo3[combo_tipo3.get()] if combo_tipo3.get() in combo3 else 0
            return id_tipo3

        combo4 = self._llenar_tipo4(combo_tipo3)
        combo_tipo4['values'] = list(combo4.keys())

        if combo_tipo4['values']:
            combo_tipo4.current(0)

        def _obtener_id_tipo4(combo_tipo4):
            combo4 = self._llenar_tipo4(combo_tipo3)
            id_tipo4 = combo4[combo_tipo4.get()] if combo_tipo4.get() in combo4 else 0
            return id_tipo4
        
        # Vincular el cambio de tipo3 para actualizar tipo4
        combo_tipo3.bind("<<ComboboxSelected>>", lambda event: self._actualizar_tipo4(event, combo_tipo3, combo_tipo4))
        

        ctk.CTkLabel(completeFrame, text="Valor de Devolución:").grid(row=4, column=0, padx=10,sticky='ew')
        entry_valor_devolucion = ctk.CTkEntry(completeFrame, justify="right", width=90)
        entry_valor_devolucion.grid(row=5, column=0, padx=10, pady=(0, 10),sticky='ew')
        entry_valor_devolucion.insert(0, valor_default)

        ctk.CTkLabel(completeFrame, text="Numero de Devolución:").grid(row=4, column=1, padx=10,sticky='ew')
        entry_numero_devolucion = ctk.CTkEntry(completeFrame, justify="right", width=90)
        entry_numero_devolucion.grid(row=5, column=1, padx=10, pady=(0, 10),sticky='ew')

        ctk.CTkLabel(completeFrame, text="Fecha de Devolución:").grid(row=6, column=0, columnspan=2, padx=10)
        fecha_devolucion = DateEntry(completeFrame, justify="right", date_pattern='dd/mm/yyyy', background='darkblue', foreground='white', borderwidth=2, relief='solid')
        fecha_devolucion.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10))

        ctk.CTkLabel(completeFrame, text="Observación:").grid(row=8, column=0, columnspan=2, padx=10)
        entry_observacion = ctk.CTkEntry(completeFrame, justify="left", width=350)
        entry_observacion.grid(row=9, column=0, columnspan=2, padx=10, pady=(0, 10),sticky='ew')

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
                
        frame_boton_guardar = tk.Frame(menu_devolucion, bg="#242424")
        frame_boton_guardar.grid(row=1, column=1, columnspan=2, padx=20, sticky="n")


        ctk.CTkButton(frame_boton_guardar, text="Guardar", command=lambda: self._guardar_devolucion(result[0],
                                                                                                    _obtener_id_tipo1(combo_tipo1),
                                                                                                    _obtener_id_tipo2(combo_tipo2),
                                                                                                    _obtener_id_tipo3(combo_tipo3),
                                                                                                    _obtener_id_tipo4(combo_tipo4),
                                                                                                    fecha_devolucion.get_date(),
                                                                                                    _obterner_valor_devolucion(entry_valor_devolucion),
                                                                                                    '' if entry_numero_devolucion.get() is None else entry_numero_devolucion.get(),
                                                                                                    '' if entry_observacion.get() is None else entry_observacion.get(),
                                                                                                    menu_devolucion
                                                                                                    )).grid(row=0, column=0, pady=10, padx=20)
        ctk.CTkButton(frame_boton_guardar, text="Cancelar", fg_color='red', hover_color="darkred", command=menu_devolucion.destroy).grid(row=0, column=1, pady=10, padx=20)


    def _guardar_devolucion(self, pedido, tipo1_id, tipo2_id, tipo3_id, tipo4_id,
                            fecha_devolucion, valor=None, numero_devolucion=None,
                            observacion=None, menu_devolucion=None):
        try:
            db = DBConnection()
            conn = db.connect_mysql() 
            cursor = conn.cursor()

            fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            creador = self.sesion_usuario['id']

            query = """
                insert into devreb(pedido,devolucion,fecha_devolucion,valor_devolucion,
                                tipo1,tipo2,tipo3,tipo4,observacion,fecha_creacion,creador)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(query, (pedido, numero_devolucion, fecha_devolucion, valor,
                                tipo1_id, tipo2_id, tipo3_id, tipo4_id,
                                observacion, fecha_creacion, creador))
            conn.commit()
            cursor.close()
            conn.close()

            # --------- Registrar incidencia si aplica ----------
            estado_entrega = None
            tipo_incidencia = None
            if tipo1_id == 4:
                estado_entrega = "R"
                tipo_incidencia = "reenv"
            elif tipo1_id == 2 and tipo2_id == 1:
                estado_entrega = "N"
                tipo_incidencia = "reb"

            if estado_entrega and tipo_incidencia:
                self._registrar_incidencia_simple(pedido, estado_entrega, tipo_incidencia)

            messagebox.showinfo("Éxito", "Devolución guardada exitosamente.")
            if menu_devolucion:
                menu_devolucion.destroy()
            self._cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la devolución: {e}")


    def _registrar_incidencia_simple(self, pedido, estado_entrega, tipo_incidencia):
        try:
            db = DBConnection()
            conn = db.connect_mysql()
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Obtener el cargamento al que está vinculado el pedido
            cursor.execute("SELECT cargamento FROM carga_pedido WHERE pedido = %s AND activo = 'S'", (pedido,))
            resultado = cursor.fetchone()
            if not resultado:
                messagebox.showwarning("Advertencia", f"No se encontró cargamento activo para el pedido {pedido}.")
                return
            cargamento_id = resultado[0]

            # Insertar incidencia
            cursor.execute("""
                INSERT INTO incidencias (pedido, cargamento, tipo, creado_por)
                VALUES (%s, %s, %s, %s)
            """, (pedido, cargamento_id, tipo_incidencia, self.sesion_usuario["id"]))

            if estado_entrega == "R":
                cursor.execute("""
                    UPDATE pedidos
                    SET en_cargamento = 'N', entregado = %s, fecha_entrega = %s
                    WHERE numero = %s
                """, (estado_entrega, fecha_actual, pedido))

                cursor.execute("""
                    UPDATE carga_pedido
                    SET activo = 'R', fecha_cancelacion = CURRENT_TIMESTAMP(), cancelado_por = %s
                    WHERE pedido = %s AND cargamento = %s
                """, (self.sesion_usuario["id"], pedido, cargamento_id))
            else:
                cursor.execute("""
                    UPDATE pedidos
                    SET entregado = %s, fecha_entrega = %s
                    WHERE numero = %s
                """, (estado_entrega, fecha_actual, pedido))

            conn.commit()
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar la incidencia: {e}")


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
