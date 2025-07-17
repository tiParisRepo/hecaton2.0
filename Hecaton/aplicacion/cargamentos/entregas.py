import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection
from datetime import datetime


class ModuloEntregas:
    def __init__(self, master, sesion_usuario):
        """
        Inicializa el módulo de registro de entregas, rebotes y reenvíos.
        :param master: Ventana principal donde se anida el módulo.
        :param sesion_usuario: Diccionario con la información de la sesión activa.
        """
        self.master = master
        self.sesion_usuario = sesion_usuario
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both")

        self._estilizar_treeview()
        self._crear_interfaz()

    def _estilizar_treeview(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Custom.Treeview",
                         background="#2b2b2b",
                         foreground="#E9F0ED",
                         rowheight=25,
                         fieldbackground="#333333",
                         font=("Arial", 12))
        estilo.map("Custom.Treeview",
                   background=[("selected", "#144870")])
        estilo.configure("Custom.Treeview.Heading",
                         background="#1F6AA5",
                         foreground="#E9F0ED",
                         font=("Arial", 13, "bold"),
                         relief='flat')
        estilo.map("Custom.Treeview.Heading",
                   background=[("active", "#1F6AA5")])

    def _crear_interfaz(self):
        self._crear_bloque_cargamentos()
        self._crear_bloque_pedidos()
        self._crear_bloque_botones()

    def _crear_bloque_cargamentos(self):
        frame_cargamentos = ctk.CTkFrame(self.frame_principal)
        frame_cargamentos.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(frame_cargamentos, text="Cargamentos", font=("Arial", 14, "bold")).pack()
        self.treeview_cargamentos = ttk.Treeview(frame_cargamentos,
                                                 style="Custom.Treeview",
                                                 columns=("ID", "Identidad"),
                                                 show="headings",
                                                 selectmode="browse",
                                                 height=10)
        self.treeview_cargamentos.heading("ID", text="ID")
        self.treeview_cargamentos.column("ID",width=30)
        self.treeview_cargamentos.heading("Identidad", text="Identidad")
        self.treeview_cargamentos.column("Identidad",width=160)
        self.treeview_cargamentos.pack(expand=True, fill="both", padx=5, pady=5)
        self.treeview_cargamentos.bind("<<TreeviewSelect>>", self._llenar_treeview_pedidos)

        self._llenar_treeview_cargamentos()

    def _crear_bloque_pedidos(self):
        frame_pedidos = ctk.CTkFrame(self.frame_principal)
        frame_pedidos.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        import tkinter as tk  # Asegúrate de importar tkinter si no está importado arriba

        self.var_filter = tk.StringVar()
        entry_filter = ctk.CTkEntry(frame_pedidos, textvariable=self.var_filter, placeholder_text="Filtrar…")
        entry_filter.pack(fill="x", padx=10, pady=(10, 0))
        entry_filter.bind("<KeyRelease>", self._llenar_treeview_pedidos)

        ctk.CTkLabel(frame_pedidos, text="Pedidos del Cargamento", font=("Arial", 14, "bold")).pack()
        self.treeview_pedidos = ttk.Treeview(frame_pedidos,
                                             style="Custom.Treeview",
                                             columns=("Nro", "Factura", "Empresa","Ciudad","Valor", "Peso", "Volumen"),
                                             show="headings",
                                             selectmode="extended",
                                             height=15)
        for col in self.treeview_pedidos["columns"]:
            self.treeview_pedidos.heading(col, text=col)
        self.treeview_pedidos.column("Nro",width=10,anchor="center")
        self.treeview_pedidos.column("Factura",width=30,anchor="center")
        self.treeview_pedidos.column("Empresa",width=200,anchor="w")
        self.treeview_pedidos.column("Ciudad",width=100,anchor="center")
        self.treeview_pedidos.column("Valor",width=70,anchor="center")
        self.treeview_pedidos.column("Peso",width=70,anchor="center")
        self.treeview_pedidos.column("Volumen",width=50,anchor="center")

        self.treeview_pedidos.tag_configure("reenvio", background="#c8b900",foreground="#2B2B2B")
        self.treeview_pedidos.tag_configure("entregado", background="#00c834",foreground="#2B2B2B")
        self.treeview_pedidos.tag_configure("rebote", background="#c80000",foreground="#2B2B2B")

        self.treeview_pedidos.pack(expand=True, fill="both", padx=5, pady=5)


    def _crear_bloque_botones(self):
        """
        Crea el frame lateral con los botones de acción para registrar incidencias.
        """
        frame_botones = ctk.CTkFrame(self.frame_principal)
        frame_botones.pack(side="right", fill="y", padx=10, pady=10)

        ctk.CTkLabel(frame_botones, text="Acciones", font=("Arial", 14, "bold")).pack(pady=10)

        # Botón para registrar entrega exitosa
        ctk.CTkButton(
            frame_botones,
            text="Entregado",
            command=lambda: self._registrar_incidencias("S", "ent"),
            fg_color="#00c834",          # Color verde para éxito
            hover_color="#009628"       # Tono más oscuro para el hover
        ).pack(pady=5, padx=10)

        # Botón para registrar un rebote
        ctk.CTkButton(
            frame_botones,
            text="Rebote",
            command=lambda: self._registrar_incidencias("N", "reb"),
            fg_color="#c80000",          # Color rojo para rebote/error
            hover_color="#960000"       # Tono más oscuro para el hover
        ).pack(pady=5, padx=10)

        # Botón para registrar un reenvío
        ctk.CTkButton(
            frame_botones,
            text="Reenvío",
            command=lambda: self._registrar_incidencias("R", "reenv"),
            fg_color="#c8b900",          # Color amarillo/dorado para advertencia o reintento
            hover_color="#968b00"       # Tono más oscuro para el hover
        ).pack(pady=5, padx=10)

    def _llenar_treeview_cargamentos(self):
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("SELECT c.id, c.identidad FROM cargamentos c WHERE c.activo = 'N'")
            resultados = cursor.fetchall()

            self.treeview_cargamentos.delete(*self.treeview_cargamentos.get_children())
            for fila in resultados:
                self.treeview_cargamentos.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar cargamentos: {e}")

    def _llenar_treeview_pedidos(self, event=None, filtro=None):
        seleccion = self.treeview_cargamentos.focus()
        valores = self.treeview_cargamentos.item(seleccion, "values")
        if not valores:
            return
        cargamento_id = valores[0]

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            consulta = """
                SELECT
                    p.numero,
                    p.factura,
                    CONCAT(e.id, '--', e.nombre) AS empresa,
                    e.ciudad,
                    i.tipo,
                    SUM(pp.cantidad_final * pp.precio_principal) AS valor,
                    SUM(p2.peso * pp.cantidad_final) AS peso,
                    (SELECT SUM(p3.volumen) FROM pedidos p3 WHERE p3.numero = p.numero) AS volumen
                FROM cargamentos c
                LEFT JOIN carga_pedido cp ON cp.cargamento = c.id AND cp.activo in ('S','R')
                LEFT JOIN pedidos p ON p.numero = cp.pedido
                LEFT JOIN empresas e ON e.id = p.empresa
                LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                LEFT JOIN productos p2 ON p2.id = pp.item
                LEFT JOIN incidencias i on i.pedido = p.numero
                WHERE c.id = %s
            """

            params = [cargamento_id]

            # Si hay filtro y no está vacío, agregar condición
            if filtro is None and hasattr(self, 'var_filter'):
                filtro = self.var_filter.get()
            if filtro:
                consulta += " AND p.numero LIKE %s"
                params.append(f"%{filtro}%")

            consulta += """
                GROUP BY p.numero, p.factura, empresa, e.ciudad, i.tipo
                ORDER BY e.ciudad ASC, p.numero DESC
            """
            cursor.execute(consulta, tuple(params))
            resultados = cursor.fetchall()

            self.treeview_pedidos.delete(*self.treeview_pedidos.get_children())
            for fila in resultados:
                peso_total_str = f"{fila[6]:.2f}"
                valor_total_str = f"{fila[5]:,.0f} PYG"
                vol_total_str = f"{int(fila[7])}"

                tag = ()

                if fila[4] == 'reenv':
                    tag = ('reenvio',)
                elif fila[4] == 'reb':
                    tag = ('rebote',)
                elif fila[4] == 'ent':
                    tag = ('entregado',)

                self.treeview_pedidos.insert("", "end", 
                                             values=(fila[0],fila[1],fila[2],fila[3],valor_total_str,peso_total_str,vol_total_str),
                                             tags=tag)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pedidos: {e}")

    def _registrar_incidencias(self, estado_entrega, tipo_incidencia):
        seleccion_cargamento = self.treeview_cargamentos.focus()
        cargamento_valores = self.treeview_cargamentos.item(seleccion_cargamento, "values")
        if not cargamento_valores:
            messagebox.showwarning("Advertencia", "Seleccione un cargamento.")
            return
        cargamento_id = cargamento_valores[0]

        pedidos_seleccionados = [self.treeview_pedidos.item(i)["values"][0] for i in self.treeview_pedidos.selection()]
        if not pedidos_seleccionados:
            messagebox.showwarning("Advertencia", "Seleccione al menos un pedido.")
            return

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for pedido in pedidos_seleccionados:
                # Insertar incidencia
                sql_insert = """
                    INSERT INTO incidencias (pedido, cargamento, tipo, creado_por)
                    VALUES (%s, %s, %s, %s);
                """
                cursor.execute(sql_insert, (pedido, cargamento_id, tipo_incidencia, self.sesion_usuario["id"]))

                if estado_entrega == 'R':
                    sql_update = """
                    UPDATE pedidos
                    SET en_cargamento = 'N', entregado = %s, fecha_entrega = %s
                    WHERE numero = %s;
                    """    

                    sql_deslinked = """
                    UPDATE carga_pedido set
                    ACTIVO = 'R',fecha_cancelacion = CURRENT_TIMESTAMP(), cancelado_por=%s
                    WHERE pedido = %s and cargamento = %s
                """
                    cursor.execute(sql_deslinked,(pedido,cargamento_id,self.sesion_usuario["id"]))
                else:
                    sql_update = """
                    UPDATE pedidos
                    SET entregado = %s, fecha_entrega = %s
                    WHERE numero = %s;
                    """

                cursor.execute(sql_update, (estado_entrega, fecha_actual, pedido))
                    
                


            conexion.commit()
            messagebox.showinfo("Éxito", "Incidencias registradas correctamente.")
            self._llenar_treeview_pedidos(None)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar incidencias: {e}")