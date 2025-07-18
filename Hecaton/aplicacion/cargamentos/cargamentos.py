from importlib.resources import Anchor
from pickle import TRUE
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from aplicacion.conectiondb.conexion import DBConnection
from collections import defaultdict
from datetime import datetime
from fpdf import FPDF
from datetime import date, datetime, timedelta


class ModuloCargamentos:
    def __init__(self, master, sesion_usuario):
        self.master = master
        self.sesion_usuario = sesion_usuario
        self._configurar_interfaz()

    def _configurar_interfaz(self):
        self.frame_principal = ctk.CTkFrame(self.master)
        self.frame_principal.pack(expand=True, fill="both")
        self.frame_principal.grid_rowconfigure(1, weight=1)
        self._aplicar_estilos()
        
        # Crear Bloques
        self._crear_bloque_A()
        self._crear_bloque_B()

    def formatear_fecha(self, fecha):
        """Convierte una fecha a formato 'dd/mm/yy'."""
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, "%d/%m/%Y")
                except ValueError:
                    raise ValueError("Formato de fecha no reconocido.")
        elif isinstance(fecha, date) and not isinstance(fecha, datetime):
            fecha = datetime.combine(fecha, datetime.min.time())

        if not isinstance(fecha, datetime):
            raise ValueError("El valor proporcionado no es una fecha válida.")

        return fecha.strftime("%d/%m/%y")

    def _aplicar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="#E9F0ED",
                        rowheight=25,
                        fieldbackground="#333333",
                        font=("Arial", 10))
        style.map("Custom.Treeview",
                  background=[("selected", "#144870")])
        style.configure("Custom.Treeview.Heading",
                        background="#1F6AA5",
                        foreground="#E9F0ED",
                        font=("Arial", 10, "bold"),
                        relief='flat')
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#1F6AA5")])

    def _crear_bloque_A(self):
        self.bloque_A = ctk.CTkFrame(self.frame_principal)
        self.bloque_A.grid(row=0, column=0, sticky="nsew")
        
        self._crear_bloque_A1()
        self._crear_bloque_A2()
    
    def _crear_bloque_A1(self):
        frame_botones = ctk.CTkFrame(self.bloque_A)
        frame_botones.pack(fill="x")

        # 4 Botones
        ctk.CTkButton(frame_botones, text="Crear Carga", command=self._crear_cargamento).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(frame_botones, text="Cerrar Carga", command=self._desactivar_cargamento).pack(side="left", padx=5, pady=5)

    # ------------------------------------------------------------
    # BLOQUE A-2: Switch + TreeView
    # ------------------------------------------------------------
    def _crear_bloque_A2(self):
        """
        Bloque A-2 con tres CTkRadioButton (verde/rojo/gris) y un TreeView
        con jerarquía de Cargamentos.
        """
        frame_treeview = ctk.CTkFrame(self.bloque_A)
        frame_treeview.pack(expand=True, fill="both", padx=5, pady=5)

        # ---------- Grupo de RadioButtons para filtrar c.activo ----------
        self.switch_var = ctk.StringVar(value="verde")

        # Frame para ubicar los 3 RadioButtons lado a lado
        frame_radios = ctk.CTkFrame(frame_treeview)
        frame_radios.pack(side="top", pady=5)

        # ---------- TreeView ----------
        self.treeview_cargamentos = ttk.Treeview(
            frame_treeview,
            style='Custom.Treeview',
            columns=("Valor", "Peso", "Volumen", "Emp"),
            show="tree headings"
        )
        self.treeview_cargamentos.pack(expand=True, fill="both", padx=5, pady=5)

        # Radio 1: Verde
        radio_verde = ctk.CTkRadioButton(
            master=frame_radios,
            text="Abiertos",
            variable=self.switch_var,
            value="verde",
            command=self._on_switch_cambio
        )
        radio_verde.pack(side="left", padx=10)

        # Radio 2: Rojo
        radio_rojo = ctk.CTkRadioButton(
            master=frame_radios,
            text="Cerrados",
            variable=self.switch_var,
            value="rojo",
            command=self._on_switch_cambio
        )
        radio_rojo.pack(side="left", padx=10)

        # Radio 3: Gris
        radio_gris = ctk.CTkRadioButton(
            master=frame_radios,
            text="Todos",
            variable=self.switch_var,
            value="gris",
            command=self._on_switch_cambio
        )
        radio_gris.pack(side="left", padx=10)

        self.treeview_cargamentos.heading("Valor", text="Valor")
        self.treeview_cargamentos.heading("Peso", text="Peso")
        self.treeview_cargamentos.heading("Volumen", text="Vol")
        self.treeview_cargamentos.heading("Emp", text="Emp")

        self.treeview_cargamentos.column("Valor",width=100, anchor="center", stretch=False)
        self.treeview_cargamentos.column("Peso",width=70,  anchor="center", stretch=False)
        self.treeview_cargamentos.column("Volumen",width=70, anchor="center", stretch=False)
        self.treeview_cargamentos.column("Emp",width=70, anchor="center", stretch=False)

        # Tag para inactivos
        self.treeview_cargamentos.tag_configure("inactivo", background="#1e5a00")

        # Evento de selección
        self.treeview_cargamentos.bind("<<TreeviewSelect>>", self._on_cargamento_selected)

        # Llenar el TreeView
        self._llenar_treeview_cargamentos()
        
        
    def _on_switch_cambio(self):
        """Se invoca cuando el switch cambia (verde/rojo/gris)."""
        filtros = self._obtener_filtros_seleccionados()
        cargamento_id = filtros["cargamento"]
        self._llenar_treeview_cargamentos()
        self._cargamentos_cerrados()
        self._reseleccionar_cargamento(cargamento_id)



        
    def _llenar_treeview_cargamentos(self):
        """Ejecuta la consulta y llena el Treeview de cargamentos con jerarquía colapsable."""
        # Determinar el filtro segun switch
        estado_switch = self.switch_var.get()
        if estado_switch == "verde":
            filtro_activo = "WHERE c.activo = 'S'"
        elif estado_switch == "rojo":
            filtro_activo = "WHERE c.activo = 'N'"
        else:
            filtro_activo = ""  # gris => sin filtro

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()

            consulta = f"""
            SELECT 
                c.id AS id_cargamento, 
                c.identidad AS descripcion,
                case 
                	when c.activo = 'S' then c.fecha_creacion
                	else c.fecha_cierre
                end as Fecha,           
                c.activo,
                r.id AS id_region, 
                r.nombre AS nombre_region, 
                cr.ciudad, 
                e.id AS id_empresa, 
                e.nombre AS nombre_empresa,
                IFNULL(SUM(pp.cantidad_final * pp.precio_principal), 0) AS valor,
                IFNULL(SUM(p2.peso * pp.cantidad_final), 0) AS peso,
                IFNULL(SUM(p3.volumen_total), 0) AS volumen,
                count(distinct e.id) as empresas
            FROM cargamentos c
            LEFT JOIN carga_pedido cp ON cp.cargamento = c.id AND cp.activo = 'S'
            LEFT JOIN pedidos p ON p.numero = cp.pedido AND p.liberado <> 'C'
            LEFT JOIN empresas e ON e.id = p.empresa
            LEFT JOIN ciudad_region cr ON cr.ciudad = e.ciudad
            LEFT JOIN regiones r ON r.id = cr.region
            LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
            LEFT JOIN productos p2 ON p2.id = pp.item
            LEFT JOIN (
                SELECT numero, SUM(volumen) AS volumen_total FROM pedidos GROUP BY numero
            ) p3 ON p3.numero = p.numero
            {filtro_activo}
            GROUP BY c.id, c.identidad, c.activo, r.id, r.nombre, cr.ciudad, e.id, e.nombre
            ORDER BY c.id;
            """

            cursor.execute(consulta)
            resultados = cursor.fetchall()

            self.treeview_cargamentos.delete(*self.treeview_cargamentos.get_children())  # Limpiar treeview
            self._insertar_datos_treeview(resultados)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al llenar Treeview de Cargamentos: {e}")

    def _insertar_datos_treeview(self, resultados):
        """Inserta los datos en el Treeview respetando la jerarquía:
           Cargamento -> Región -> Ciudad -> Empresa."""

        totales = self._acumular_valores(resultados)
        nodos = {}

        for fila in resultados:
            (id_cargamento, descripcion,Fecha,activo,
             id_region, nombre_region, ciudad, 
             id_empresa, nombre_empresa, valor, 
             peso, volumen,empresas) = fila
            Fecha = Fecha.strftime("%d/%m/%Y %H:%M")
            # Formato
            valor_str = f"{valor:,.0f}"
            peso_str = f"{peso:.2f}"
            vol_str = f"{int(volumen)}"
            emp_str = f"{int(empresas if empresas is not None else 0)}"

            # Nivel 1: Cargamento
            cargamento_key = f"{id_cargamento}_{descripcion}"
            if cargamento_key not in nodos:
                peso_total, valor_total, vol_total, emp_total = totales["cargamento"][cargamento_key]
                peso_total_str = f"{peso_total:.2f}"
                valor_total_str = f"{valor_total:,.0f}"
                vol_total_str = f"{int(vol_total)}"
                emp_total_str = f"{int(emp_total)}"

                # Si c.activo = 'N', usar tag inactivo
                tags = ("inactivo",) if activo == "N" else ()

                nodo_cargamento = self.treeview_cargamentos.insert(
                    "", "end",
                    text=f"{id_cargamento} - {descripcion} ({Fecha})",
                    values=(valor_total_str, peso_total_str, vol_total_str,emp_total_str),
                    tags=tags
                )
                nodos[cargamento_key] = nodo_cargamento

            # Nivel 2: Región
            region_key = f"{cargamento_key}_{nombre_region}"
            if region_key not in nodos:
                pt, vt, volg, empc = totales["region"][region_key]
                nodo_region = self.treeview_cargamentos.insert(
                    nodos[cargamento_key], "end",
                    text=f"{id_region} - {nombre_region}",
                    values=(f"{vt:,.0f}", f"{pt:.2f}", f"{int(volg)}",f"{int(empc)}")
                )
                nodos[region_key] = nodo_region

            # Nivel 3: Ciudad
            ciudad_key = f"{region_key}_{ciudad}"
            if ciudad_key not in nodos:
                pt, vt, volg, empc = totales["ciudad"][ciudad_key]
                nodo_ciudad = self.treeview_cargamentos.insert(
                    nodos[region_key], "end",
                    text=f"{ciudad}",
                    values=(f"{vt:,.0f}", f"{pt:.2f}", f"{int(volg)}",f"{int(empc)}")
                )
                nodos[ciudad_key] = nodo_ciudad

            # Nivel 4: Empresa
            empresa_key = f"{ciudad_key}_{id_empresa}_{nombre_empresa}"
            pt, vt, volg, empc = totales["empresa"][empresa_key]
            self.treeview_cargamentos.insert(
                nodos[ciudad_key], "end",
                text=f"{id_empresa} - {nombre_empresa}",
                values=(f"{vt:,.0f}", f"{pt:.2f}", f"{int(volg)}",f"{int(empc)}")
            )

    def _acumular_valores(self, resultados):
        """Acumula peso, valor y volumen en cada nivel de la jerarquía."""
        totales = {
            "cargamento": defaultdict(lambda: [0, 0, 0, 0]),
            "region": defaultdict(lambda: [0, 0, 0, 0]),
            "ciudad": defaultdict(lambda: [0, 0, 0, 0]),
            "empresa": defaultdict(lambda: [0, 0, 0, 0])
        }

        for fila in resultados:
            (id_cargamento, descripcion,Fecha,activo,
             id_region, nombre_region, ciudad,
             id_empresa, nombre_empresa, valor,
             peso, volumen,empresas) = fila

            valor = valor or 0
            peso = peso or 0
            volumen = volumen or 0
            empresas = empresas or 0

            cargamento_key = f"{id_cargamento}_{descripcion}"
            region_key = f"{cargamento_key}_{nombre_region}"
            ciudad_key = f"{region_key}_{ciudad}"
            empresa_key = f"{ciudad_key}_{id_empresa}_{nombre_empresa}"

            for key in [cargamento_key, region_key, ciudad_key, empresa_key]:
                level = (
                    "cargamento" if key == cargamento_key else
                    "region" if key == region_key else
                    "ciudad" if key == ciudad_key else
                    "empresa"
                )
                totales[level][key][0] += peso
                totales[level][key][1] += valor
                totales[level][key][2] += volumen
                totales[level][key][3] += empresas

        return totales

    def _reseleccionar_cargamento(self, cargamento_id_str):
        """ Dado un cargamento_id_str, busca el nodo 'Cargamento: ID - ...' y lo selecciona. """
        # Recorrer los nodos al nivel 1 (los 'cargamentos')
        for carg_node in self.treeview_cargamentos.get_children(""):
            texto_nodo = self.treeview_cargamentos.item(carg_node, "text")  # p.ej. "Cargamento: 12 - Sur"
            try:
                if texto_nodo.startswith(cargamento_id_str + " -") or texto_nodo.startswith("Cargamento: " + cargamento_id_str):
                    self.treeview_cargamentos.selection_set(carg_node)
                    self.treeview_cargamentos.see(carg_node)
                    # Llamar a _cargar_pedidos_en_cargamento() si quieres auto-refrescar
                    break
            except:
                pass

    def _obtener_filtros_seleccionados(self):
        """Extrae cargamento, region, ciudad, empresa del item seleccionado."""
        seleccion = self.treeview_cargamentos.selection()
        if not seleccion:
            return {
                "cargamento": None,
                "region": None,
                "ciudad": None,
                "empresa": None
            }
        item = seleccion[0]
        texto_seleccionado = self.treeview_cargamentos.item(item, 'text')

        filtros = {
            "cargamento": None,
            "region": None,
            "ciudad": None,
            "empresa": None
        }

        # Función para obtener el text del padre
        def obtener_texto_padre(nodo):
            padre = self.treeview_cargamentos.parent(nodo)
            return self.treeview_cargamentos.item(padre, 'text') if padre else None

        padres = []
        nodo_actual = item
        while True:
            padre = obtener_texto_padre(nodo_actual)
            if not padre:
                break
            padres.insert(0, padre)
            nodo_actual = self.treeview_cargamentos.parent(nodo_actual)

        # Split de padres
        filtros_lista = [p.split(" - ")[0] for p in padres]
        niveles = ["cargamento", "region", "ciudad", "empresa"]

        # Asignar padres a los niveles
        for i, nivel in enumerate(niveles[:len(filtros_lista)]):
            filtros[nivel] = filtros_lista[i]

        # El nodo seleccionado
        if len(padres) != 2:
            seleccionado_id = texto_seleccionado.split(" - ")[0]
            filtros[niveles[len(filtros_lista)]] = seleccionado_id
        else:
            # no hace split
            filtros[niveles[len(filtros_lista)]] = texto_seleccionado

        return filtros

    def _crear_bloque_B(self):
        """
        Crea el bloque B que incluye filtros, listas de pedidos sin cargamento y asignados,
        y botones de asignación.
        """
        bloque_b_frame = ctk.CTkFrame(self.frame_principal)
        bloque_b_frame.grid(row=0, column=1, sticky="nsew")
        
        # Crear subbloques
        self._crear_bloque_b1(bloque_b_frame)
        self._crear_bloque_b2(bloque_b_frame)
        self._crear_bloque_b3(bloque_b_frame)

    def _crear_bloque_b1(self, parent):
        """ Crea el bloque de filtros (Región y Ciudad) y pedidos sin cargamento. """
        frame_b1 = ctk.CTkFrame(parent)
        frame_b1.pack(expand=True, fill="both", padx=5, pady=5)

        # Usaremos un sub-frame para los filtros, aplicado con grid
        frame_filtros = ctk.CTkFrame(frame_b1)
        frame_filtros.pack(side="top", fill="x", pady=5)


        # ============== Filtro de Región (izquierda) ==============
        region_label = ctk.CTkLabel(frame_filtros, text="Filtrar por Región:")
        region_label.grid(row=0, column=0, sticky="nsew", padx=(150,0))

        self.combo_region = ttk.Combobox(frame_filtros, state="readonly")
        self.combo_region.grid(row=1, column=0, sticky="nses", padx=(170,0),pady=(0,20)) 
        # Ajustar padx o usar más columnas para más control en la separación


        # ============== Filtro de Ciudad (derecha) ==============
        ciudad_label = ctk.CTkLabel(frame_filtros, text="Filtrar por Ciudad:")
        ciudad_label.grid(row=0, column=1, sticky="nses", padx=(0,20))

        self.combo_ciudad = ttk.Combobox(frame_filtros, state="readonly")
        self.combo_ciudad.grid(row=1, column=1, sticky="nses", padx=(170,0),pady=(0,20))

        # ============== TreeView de Pedidos ==============
        self.treeview_sin_cargamento = ttk.Treeview(
            frame_b1,
            style='Custom.Treeview', 
            columns=("Número", "Factura", "Fecha","ID", "Empresa","Ciudad", "Vendedor", "Valor", "Peso", "Vol"),
            show="headings"
        )
        self.treeview_sin_cargamento.pack(expand=True, fill="both", padx=5, pady=5)
        self._configurar_columnas(self.treeview_sin_cargamento)

        self.treeview_sin_cargamento.tag_configure("reenvio", background="#c8b900",foreground="#2B2B2B")

        self.combo_region.bind("<<ComboboxSelected>>", self._actualizar_ciudades)
        self.combo_ciudad.bind("<<ComboboxSelected>>", self._cargar_pedidos_sin_cargamento)

        # Cargar data
        self._cargar_filtros()
        self._cargar_pedidos_sin_cargamento()


    def _cargar_filtros(self):
        """Carga las opciones de región y ciudad en los combobox, incluyendo opción de deselección."""
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # Cargar regiones con opción de "Todas"
            cursor.execute("SELECT DISTINCT nombre FROM regiones;")
            lista_regiones = [row[0] for row in cursor.fetchall()]
            regiones = ["-- Todas --"] + lista_regiones
            self.combo_region["values"] = regiones
            self.combo_region.set("-- Todas --")  # Seleccionar por defecto

            # Cargar ciudades con opción de "Todas"
            cursor.execute("SELECT DISTINCT ciudad FROM ciudad_region;")
            lista_ciudades = [row[0] for row in cursor.fetchall()]
            ciudades = ["-- Todas --"] + lista_ciudades
            self.combo_ciudad["values"] = ciudades
            self.combo_ciudad.set("-- Todas --")  # Seleccionar por defecto

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar filtros: {e}")

    def _actualizar_ciudades(self, event):
        """Filtra las ciudades según la región seleccionada, agregando `-- Todas --`."""
        region = self.combo_region.get()
        self.combo_ciudad.set("-- Todas --")  # Resetear la selección
        self.combo_ciudad["values"] = []      # Limpiar opciones anteriores

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            if region == "-- Todas --" or not region:
                # Si no hay región específica, cargar todas las ciudades + `-- Todas --`
                cursor.execute("SELECT DISTINCT ciudad FROM ciudad_region;")
                ciudades_disponibles = [row[0] for row in cursor.fetchall()]
                ciudades = ["-- Todas --"] + ciudades_disponibles
                self.combo_ciudad["values"] = ciudades
                self.combo_ciudad["state"] = "readonly"
            else:
                # Filtrar ciudades por la región seleccionada
                cursor.execute("""
                    SELECT ciudad FROM ciudad_region 
                    WHERE region = (SELECT id FROM regiones WHERE nombre = %s)
                """, (region,))
                ciudades_disponibles = [row[0] for row in cursor.fetchall()]
                ciudades = ["-- Todas --"] + ciudades_disponibles
                self.combo_ciudad["values"] = ciudades
                self.combo_ciudad["state"] = "readonly"

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar ciudades: {e}")
        self._cargar_pedidos_sin_cargamento()  # Recargar pedidos con el nuevo filtro

    def _cargar_pedidos_sin_cargamento(self, event=None):
        """Carga los pedidos sin cargamento en el treeview correspondiente."""
        region = self.combo_region.get()
        ciudad = self.combo_ciudad.get()

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            query = """
                    select
                        p.numero,
                        p.factura,
                        p.fecha,
                        p.empresa,
                        e.nombre,
                        e.ciudad,
                        u.usuario,
                        p.entregado,
                        IFNULL(SUM(pp.cantidad_final * pp.precio_principal), 0) as valor,
                        IFNULL(SUM(prod.peso * pp.cantidad_final), 0) as peso,
                        IFNULL((select SUM(ppp.volumen) from pedidos ppp where ppp.numero = p.numero), 0) as volumen
                    from
                        pedidos p
                    left join empresas e on
                        e.id = p.empresa
                    left join ciudad_region cr on
                        cr.ciudad = e.ciudad
                    left join usuarios u on
                        u.identify = p.vendedor
                    left join producto_pedido pp on
                        pp.pedido = p.numero
                    left join productos prod on
                        prod.id = pp.item
                    WHERE
                        ((
                            p.liberado <> 'C'
                            AND p.tipo = 'Pedido'
                            AND p.preliberado = 'S'
                            AND p.en_cargamento IS NULL
                        )
                        OR (
                            (p.ENTREGADO = 'R' OR p.ENTREGADO IS NULL)
                            AND p.en_cargamento = 'N'
                        ))

            """

            # Construir filtros
            filtros = []
            if region and region != "-- Todas --":
                query += " AND cr.region = (SELECT id FROM regiones WHERE nombre = %s)"
                filtros.append(region)
            if ciudad and ciudad != "-- Todas --":
                query += " AND e.ciudad = %s"
                filtros.append(ciudad)


            query += """
                    group by p.numero,p.factura,p.fecha,p.empresa,e.nombre,e.ciudad,u.usuario,p.entregado
                    order by p.ENTREGADO DESC,e.ciudad desc,p.fecha desc,p.numero DESC;
            """

            cursor.execute(query, tuple(filtros))
            pedidos = cursor.fetchall()

            # Limpiar el treeview antes de insertar nuevos datos
            self.treeview_sin_cargamento.delete(*self.treeview_sin_cargamento.get_children())

            for pedido in pedidos:
                num, factura,fecha, empresa_id, empresa,ciudad,vendedor,entregado, valor, peso, volumen = pedido

                fecha = self.formatear_fecha(fecha) if fecha else "N/A"

                if entregado == 'R':
                    tag = ('reenvio',)
                else:
                    tag = ()

                # Formatear los valores correctamente
                valor = f"{valor:,.0f}"
                peso = f"{peso:.2f}" if peso else "0.00"
                volumen = f"{int(volumen)}" if volumen else "0"

                self.treeview_sin_cargamento.insert("", "end", 
                                                    values=(num, factura,fecha,empresa_id, empresa,ciudad, vendedor, valor, peso, volumen),
                                                    tags=tag)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pedidos sin cargamento: {e}")

    
    def _crear_bloque_b2(self, parent):
        """Crea el bloque de botones para mover elementos entre los TreeView."""
        frame_b2 = ctk.CTkFrame(parent)
        frame_b2.pack(fill="y", padx=5, pady=5)
        
        # NOTA: Asignar a self, sin .pack() en la misma línea
        self.rem_cargamento = ctk.CTkButton(frame_b2, text="↑", command=self._agregar_a_sin_cargamento)
        self.rem_cargamento.pack(expand=True, side="top", padx=5, pady=5)

        self.agg_cargamento = ctk.CTkButton(frame_b2, text="↓", command=self._agregar_a_en_cargamento)
        self.agg_cargamento.pack(expand=True, side="top", padx=5, pady=5)

    def _cargamentos_cerrados(self):
        """
        Habilita o deshabilita los botones rem_cargamento y agg_cargamento
        según el estado del switch.
        """
        estado_switch = self.switch_var.get()
        
        if estado_switch == "verde":
            self.rem_cargamento.configure(state="normal")
            self.agg_cargamento.configure(state="normal")
        elif estado_switch == "rojo":
            self.rem_cargamento.configure(state="disabled")
            self.agg_cargamento.configure(state="disabled")
        else:  # gris
            self.rem_cargamento.configure(state="disabled")
            self.agg_cargamento.configure(state="disabled")

    def _crear_bloque_b3(self, parent):
        """Crea el bloque de pedidos en cargamento."""
        frame_b3 = ctk.CTkFrame(parent)
        frame_b3.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.treeview_en_cargamento = ttk.Treeview(frame_b3,style='Custom.Treeview', columns=("Número", "Factura","Fecha", "ID", "Empresa","Ciudad","Vendedor", "Valor", "Peso", "Vol"),selectmode='extended', show="headings")
        self.treeview_en_cargamento.pack(expand=True, fill="both", padx=5, pady=5)
        self._configurar_columnas(self.treeview_en_cargamento)
        self.treeview_en_cargamento.tag_configure("reenvio", background="#c8b900",foreground="#2B2B2B")



    def _configurar_columnas(self, tabla):
        """Configura las columnas de las tablas."""
        columnas_anchos = {
            "Número":60,
            "Factura":60,
            "Fecha":70,
            "ID":40,
            "Empresa":165,
            "Ciudad":130,
            "Vendedor":130,
            "Valor":75,  # Espacio adicional para el formato de moneda
            "Peso":60,
            "Vol":60
        }

        for col,anch in columnas_anchos.items():
            tabla.heading(col, text=col)
            tabla.column(col,width=anch, anchor="center", stretch=False)

            if col == "Empresa":
                tabla.column(col, anchor="w")

    
    def _agregar_a_sin_cargamento(self):
        """Mueve los pedidos seleccionados en treeview_en_cargamento a pedidos sin cargamento."""
        
        # Obtener pedidos seleccionados
        seleccion = self.treeview_en_cargamento.selection()
        if not seleccion:
            messagebox.showerror("Error", "Debe seleccionar al menos un pedido.")
            return

        pedidos_seleccionados = [self.treeview_en_cargamento.item(item, "values")[0] for item in seleccion]

        # Obtener el cargamento seleccionado
        filtros = self._obtener_filtros_seleccionados()
        cargamento_id = filtros["cargamento"]

        if not cargamento_id:
            messagebox.showerror("Error", "Debe seleccionar un cargamento válido en el árbol.")
            return

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # 1. Desactivar los pedidos en `carga_pedido`
            consulta_1 = """
                UPDATE carga_pedido 
                SET activo = 'N', fecha_cancelacion = CURRENT_TIMESTAMP(), cancelado_por = %s
                WHERE cargamento = %s AND pedido IN (%s) AND activo = 'S';
            """ % (self.sesion_usuario["id"], cargamento_id, ",".join(pedidos_seleccionados))

            cursor.execute(consulta_1)

            # 2. Desasociar pedidos en `pedidos`
            consulta_2 = """
                UPDATE pedidos 
                SET en_cargamento = NULL
                WHERE numero IN (%s);
            """ % ",".join(pedidos_seleccionados)

            cursor.execute(consulta_2)

            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", "Pedidos removidos del cargamento correctamente.")
            self._cargar_pedidos_sin_cargamento()
            self._llenar_treeview_cargamentos()
            self._reseleccionar_cargamento(cargamento_id)
            self._cargar_pedidos_en_cargamento()

        except Exception as e:
            messagebox.showerror("Error", f"Error al mover pedidos: {e}")

    def _agregar_a_en_cargamento(self):
        """Mueve los pedidos seleccionados en treeview_sin_cargamento a pedidos con cargamento."""
        
        # Obtener pedidos seleccionados
        seleccion = self.treeview_sin_cargamento.selection()
        if not seleccion:
            messagebox.showerror("Error", "Debe seleccionar al menos un pedido.")
            return

        pedidos_seleccionados = [self.treeview_sin_cargamento.item(item, "values")[0] for item in seleccion]

        # Obtener el cargamento seleccionado
        filtros = self._obtener_filtros_seleccionados()
        cargamento_id = filtros["cargamento"]
        
        if not cargamento_id:
            messagebox.showerror("Error", "Debe seleccionar un cargamento válido en el árbol.")
            return

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # 1. Asignar pedidos en `pedidos`
            consulta_1 = """
                UPDATE pedidos 
                SET en_cargamento = 'S'
                WHERE numero IN (%s);
            """ % ",".join(pedidos_seleccionados)

            
            cursor.execute(consulta_1)

            # 2. Insertar pedidos en `carga_pedido`
            valores_insert = ", ".join(
                f"({pedido}, {cargamento_id}, 'S', CURRENT_TIMESTAMP(), {self.sesion_usuario['id']})"
                for pedido in pedidos_seleccionados
            )

            consulta_2 = f"""
                INSERT INTO carga_pedido (pedido, cargamento, activo, fecha_conexion, conectado_por)
                VALUES {valores_insert};
            """

            cursor.execute(consulta_2)

            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", "Pedidos asignados al cargamento correctamente.")
            self._cargar_pedidos_sin_cargamento()
            self._llenar_treeview_cargamentos()
            self._reseleccionar_cargamento(cargamento_id)
            self._cargar_pedidos_en_cargamento()

        except Exception as e:
            messagebox.showerror("Error", f"Error al mover pedidos: {e}")

    def _on_cargamento_selected(self, event):
        """
        Función que se invoca cuando se selecciona un nuevo elemento en el treeview_cargamentos.
        Carga los pedidos filtrados en la tabla B-3.
        """
        self._cargar_pedidos_en_cargamento()


    def _cargar_pedidos_en_cargamento(self):
        """Carga los pedidos asignados a un cargamento, aplicando filtros jerárquicos."""
        filtros = self._obtener_filtros_seleccionados()
        if not filtros["cargamento"]:
            messagebox.showerror("Error", "Debe seleccionar un cargamento válido.")
            return

        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            consulta = """
                SELECT p.numero, p.factura,p.fecha, p.empresa, e.nombre,e.ciudad, u.usuario,p.entregado,
                    SUM(pp.cantidad_final * pp.precio_principal) AS valor,
                    SUM(prod.peso * pp.cantidad_final) AS peso,
                    (SELECT SUM(ppp.volumen) FROM pedidos ppp WHERE ppp.numero = p.numero) AS volumen
                FROM pedidos p
                LEFT JOIN empresas e ON e.id = p.empresa
                LEFT JOIN ciudad_region cr ON cr.ciudad = e.ciudad
                LEFT JOIN usuarios u ON u.identify = p.vendedor
                LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                LEFT JOIN productos prod ON prod.id = pp.item
                LEFT JOIN carga_pedido cp ON cp.pedido = p.numero AND cp.activo = 'S'
                LEFT JOIN cargamentos c ON c.id = cp.cargamento
                WHERE c.id = %s
            """

            parametros = [filtros["cargamento"]]

            if filtros["region"]:
                consulta += " AND cr.region = %s"
                parametros.append(filtros["region"])

            if filtros["ciudad"]:
                consulta += " AND e.ciudad = %s"
                parametros.append(filtros["ciudad"])

            if filtros["empresa"]:
                consulta += " AND e.id = %s"
                parametros.append(filtros["empresa"])

            consulta += """
                GROUP BY p.numero, p.factura,p.fecha, p.empresa, e.nombre, u.usuario
                order by p.ENTREGADO DESC,e.ciudad asc,p.fecha desc,p.numero DESC;
            """
            cursor.execute(consulta, parametros)
            resultados = cursor.fetchall()

            # Limpiar la tabla antes de insertar
            self.treeview_en_cargamento.delete(*self.treeview_en_cargamento.get_children())

            for fila in resultados:
                # Separar los campos devueltos por la consulta
                (num, factura,fecha, empresa_id, empresa_nombre,ciudad, vendedor,entrega, valor, peso, volumen) = fila
                
                fecha = self.formatear_fecha(fecha) if fecha else "N/A"
                
                if entrega == 'R':
                    tag = ('reenvio',)
                else:
                    tag = ()
                
                # Formatear los valores correctamente
                # valor => Ej: "1,200,000 PYG"
                valor_str = f"{valor:,.0f}" if valor else "0"

                # peso => Ej: "12.34 kg"
                peso_str = f"{peso:.2f}" if peso else "0.00"

                # volumen => entero
                volumen_str = f"{int(volumen)}" if volumen else "0"

                self.treeview_en_cargamento.insert(
                    "", "end",
                    values=(
                        num, 
                        factura, 
                        fecha,
                        empresa_id, 
                        empresa_nombre,
                        ciudad, 
                        vendedor, 
                        valor_str, 
                        peso_str, 
                        volumen_str
                    ),
                    tags=tag
                )

            conexion.close()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pedidos en cargamento: {e}")


    def _crear_cargamento(self):
        """Abre un formulario para crear un nuevo cargamento."""
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Cargamento")
        formulario.geometry("400x400")
        formulario.grab_set()  # Mantiene el formulario al frente

        # Campo de identidad
        ctk.CTkLabel(formulario, text="Identidad del Cargamento:").pack(pady=5)
        identidad_entry = ctk.CTkEntry(formulario)
        identidad_entry.pack(pady=5)

        # Selección de Vehículo
        ctk.CTkLabel(formulario, text="Vehículo:").pack(pady=5)
        vehiculo_combobox = ttk.Combobox(formulario, state="readonly")
        vehiculo_combobox.pack(pady=5)

        # Selección de Chofer
        ctk.CTkLabel(formulario, text="Chofer:").pack(pady=5)
        chofer_combobox = ttk.Combobox(formulario, state="readonly")
        chofer_combobox.pack(pady=5)

        # Estado del cargamento
        ctk.CTkLabel(formulario, text="Estado del Cargamento:").pack(pady=5)
        estado_var = ctk.StringVar(value="S")
        ctk.CTkRadioButton(formulario, text="Abierto", variable=estado_var, value="S").pack(pady=2)
        ctk.CTkRadioButton(formulario, text="Cerrado", variable=estado_var, value="N").pack(pady=2)

        # Llenar combobox con datos de la base de datos
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # Llenar combobox de Vehículos
            cursor.execute("SELECT id, nombre FROM vehiculos WHERE activo = 'S';")
            vehiculos = cursor.fetchall()
            vehiculo_combobox['values'] = [f"{v[0]} - {v[1]}" for v in vehiculos]

            # Llenar combobox de Choferes
            cursor.execute("""
                SELECT c.id, u.nombre 
                FROM choferes c 
                LEFT JOIN usuarios u ON u.id = c.id
                WHERE c.activo = 'S';
            """)
            choferes = cursor.fetchall()
            chofer_combobox['values'] = [f"{c[0]} - {c[1]}" for c in choferes]

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")
            return

        def guardar_cargamento():
            """Guarda el nuevo cargamento en la base de datos."""
            identidad = identidad_entry.get()
            vehiculo_id = vehiculo_combobox.get().split(" - ")[0] if vehiculo_combobox.get() else None
            chofer_id = chofer_combobox.get().split(" - ")[0] if chofer_combobox.get() else None
            estado = estado_var.get()

            if not identidad or not vehiculo_id or not chofer_id:
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                # Inserción del nuevo cargamento
                consulta_insert_cargamento = """
                    INSERT INTO cargamentos (identidad, vehiculo, chofer, activo, fecha_creacion, creado_por)
                    VALUES (%s, %s, %s, %s, NOW(), %s);
                """
                cursor.execute(consulta_insert_cargamento, (identidad, vehiculo_id, chofer_id, estado, self.sesion_usuario["id"]))
                cargamento_id = cursor.lastrowid  # Obtener el ID del cargamento insertado

                # Verificar si el chofer tiene primera_carga
                consulta_check_chofer = """
                    SELECT primera_carga FROM choferes WHERE id = %s;
                """
                cursor.execute(consulta_check_chofer, (chofer_id,))
                primera_carga = cursor.fetchone()[0]

                # Si no tiene primera_carga, actualizar el campo con el nuevo cargamento
                if not primera_carga:
                    consulta_update_chofer = """
                        UPDATE choferes SET primera_carga = %s WHERE id = %s;
                    """
                    cursor.execute(consulta_update_chofer, (cargamento_id, chofer_id))

                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Cargamento creado exitosamente.")
                self._llenar_treeview_cargamentos()  # Actualizar el TreeView de cargamentos
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear cargamento: {e}")

        # Botón para guardar el cargamento
        ctk.CTkButton(formulario, text="Guardar", command=guardar_cargamento).pack(pady=20)

    def _crear_cargamento(self):
        """Abre un formulario para crear un nuevo cargamento."""
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Cargamento")
        formulario.geometry("400x400")
        formulario.grab_set()  # Mantiene el formulario al frente

        # Campo de identidad
        ctk.CTkLabel(formulario, text="Identidad del Cargamento:").pack(pady=5)
        identidad_entry = ctk.CTkEntry(formulario)
        identidad_entry.pack(pady=5)

        # Selección de Vehículo
        ctk.CTkLabel(formulario, text="Vehículo:").pack(pady=5)
        vehiculo_combobox = ttk.Combobox(formulario, state="readonly")
        vehiculo_combobox.pack(pady=5)

        # Selección de Chofer
        ctk.CTkLabel(formulario, text="Chofer:").pack(pady=5)
        chofer_combobox = ttk.Combobox(formulario, state="readonly")
        chofer_combobox.pack(pady=5)

        # Estado del cargamento
        ctk.CTkLabel(formulario, text="Estado del Cargamento:").pack(pady=5)
        estado_var = ctk.StringVar(value="S")
        ctk.CTkRadioButton(formulario, text="Abierto", variable=estado_var, value="S").pack(pady=2)
        ctk.CTkRadioButton(formulario, text="Cerrado", variable=estado_var, value="N").pack(pady=2)

        # Llenar combobox con datos de la base de datos
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            # Llenar combobox de Vehículos
            cursor.execute("SELECT id, nombre FROM vehiculos WHERE activo = 'S';")
            vehiculos = cursor.fetchall()
            vehiculo_combobox['values'] = [f"{v[0]} - {v[1]}" for v in vehiculos]

            # Llenar combobox de Choferes
            cursor.execute("""
                SELECT c.id, u.nombre 
                FROM choferes c 
                LEFT JOIN usuarios u ON u.id = c.id
                WHERE c.activo = 'S';
            """)
            choferes = cursor.fetchall()
            chofer_combobox['values'] = [f"{c[0]} - {c[1]}" for c in choferes]

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")
            return

        def guardar_cargamento():
            """Guarda el nuevo cargamento en la base de datos."""
            identidad = identidad_entry.get()
            vehiculo_id = vehiculo_combobox.get().split(" - ")[0] if vehiculo_combobox.get() else None
            chofer_id = chofer_combobox.get().split(" - ")[0] if chofer_combobox.get() else None
            estado = estado_var.get()

            if not identidad or not vehiculo_id or not chofer_id:
                messagebox.showerror("Error", "Todos los campos son obligatorios.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                # Inserción del nuevo cargamento
                consulta_insert_cargamento = """
                    INSERT INTO cargamentos (identidad, vehiculo, chofer, activo, fecha_creacion, creado_por)
                    VALUES (%s, %s, %s, %s, NOW(), %s);
                """
                cursor.execute(consulta_insert_cargamento, (identidad, vehiculo_id, chofer_id, estado, self.sesion_usuario["id"]))
                cargamento_id = cursor.lastrowid  # Obtener el ID del cargamento insertado

                # Verificar si el chofer tiene primera_carga
                consulta_check_chofer = """
                    SELECT primera_carga FROM choferes WHERE id = %s;
                """
                cursor.execute(consulta_check_chofer, (chofer_id,))
                primera_carga = cursor.fetchone()[0]

                # Si no tiene primera_carga, actualizar el campo con el nuevo cargamento
                if not primera_carga:
                    consulta_update_chofer = """
                        UPDATE choferes SET primera_carga = %s WHERE id = %s;
                    """
                    cursor.execute(consulta_update_chofer, (cargamento_id, chofer_id))

                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Cargamento creado exitosamente.")
                self._llenar_treeview_cargamentos()  # Actualizar el TreeView de cargamentos
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear cargamento: {e}")

        # Botón para guardar el cargamento
        ctk.CTkButton(formulario, text="Guardar", command=guardar_cargamento).pack(pady=20)

    
    def _desactivar_cargamento(self):
        """Desactiva el cargamento seleccionado usando la función _obtener_filtros_seleccionados()."""
        filtros = self._obtener_filtros_seleccionados()
        cargamento_id_str = filtros["cargamento"]

        # Verificar si es realmente nivel CARGAMENTO (los otros niveles vacíos)
        if (not cargamento_id_str
            or filtros["region"] is not None
            or filtros["ciudad"] is not None
            or filtros["empresa"] is not None):
            messagebox.showerror("Error", "Debe seleccionar un nodo de nivel CARGAMENTO para cerrar.")
            return

        # Obtener texto del nodo seleccionado (solo para mostrar en el askyesno)
        seleccion = self.treeview_cargamentos.selection()
        if not seleccion:
            messagebox.showerror("Error", "No hay elemento seleccionado.")
            return

        item = seleccion[0]
        texto_seleccionado = self.treeview_cargamentos.item(item, 'text')

        # Preguntar confirmación al usuario
        respuesta = messagebox.askyesno("Confirmar", f"¿Desea desactivar el cargamento {texto_seleccionado}?")
        if not respuesta:
            return

        # Convertir id a entero
        try:
            cargamento_id = int(cargamento_id_str)
        except ValueError:
            messagebox.showerror("Error", f"ID de cargamento inválido: {cargamento_id_str}")
            return

        # Ejecutar el UPDATE en la base de datos
        try:
            db = DBConnection()
            conexion = db.connect_mysql()
            if conexion is None:
                raise Exception("No se pudo establecer conexión con MySQL.")

            cursor = conexion.cursor()
            consulta = """
                UPDATE cargamentos
                SET activo = 'N',
                    fecha_cierre = CURRENT_TIMESTAMP(),
                    cerrado_por = %s
                WHERE id = %s
            """
            cursor.execute(consulta, (self.sesion_usuario["id"], cargamento_id))
            conexion.commit()
            conexion.close()

            messagebox.showinfo("Éxito", f"Cargamento {cargamento_id} cerrado correctamente.")
            # Refrescar el TreeView
            self._llenar_treeview_cargamentos()
            self._reseleccionar_cargamento(cargamento_id)
            self._cargar_pedidos_en_cargamento()

        except Exception as e:
            messagebox.showerror("Error", f"Error al desactivar cargamento: {e}")
