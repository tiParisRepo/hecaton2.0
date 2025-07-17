from collections import defaultdict
from datetime import date, datetime
from pydoc import text
import tkinter as tk
from tkinter import messagebox,filedialog
import customtkinter as ctk
from fpdf import FPDF
from tkcalendar import DateEntry
from aplicacion.conectiondb.conexion import DBConnection

class ModuloRecoleccion:
        def __init__(self,master):
            maestro = master

            self._bloque_filtro(maestro)

        def _bloque_filtro(self, parent):
            ventana_fechas = ctk.CTkFrame(parent)
            ventana_fechas.grid(row=1,column=0,pady=10,padx=10)
            ventana_fechas.rowconfigure(1, weight=1)
            ventana_fechas.columnconfigure(0, weight=1)

            titulo = ctk.CTkLabel(parent, text="Reporte de Recoleccion", font=('Arial', 18, 'bold'))
            titulo.grid(row=0, column=0, pady=[10, 0])

            filterFrame = ctk.CTkFrame(ventana_fechas)
            filterFrame.grid(row=1, column=0)

            f_beging = DateEntry(filterFrame, justify="right", date_pattern='dd/mm/yyyy', background='black', foreground='white', borderwidth=2, relief='solid')
            f_beging.grid(row=0,column=0,padx=5,pady=5)

            h_beging = ctk.CTkEntry(filterFrame,placeholder_text='00:00')
            h_beging.grid(row=0,column=1,padx=5,pady=5)
            h_beging.bind("<KeyRelease>",self._auto_formatear_hora)

            f_end = DateEntry(filterFrame, justify="right", date_pattern='dd/mm/yyyy', background='black', foreground='white', borderwidth=2, relief='solid')
            f_end.grid(row=1,column=0,padx=5,pady=5)

            h_end = ctk.CTkEntry(filterFrame,placeholder_text='00:00')
            h_end.grid(row=1,column=1,padx=5,pady=5)
            h_end.bind("<KeyRelease>",self._auto_formatear_hora)

            separacion = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(filterFrame,
                            text="Reporte de Separación",
                            variable=separacion).grid(row=3,column=0,pady=[10,0],columnspan=2)
            
            ctk.CTkButton(filterFrame,
                          text='Exportar',
                          command=lambda:self._procesar_solicitud(filterFrame)
                          ).grid(column=0,row=4,pady=[10,0],columnspan=2)


        def _procesar_solicitud(self,formulario: ctk.CTkFrame):
            f_inicio = formulario.winfo_children()[0].get_date()  # Assuming the first DateEntry is for start date
            hora_inicio = formulario.winfo_children()[1].get()  # Assuming the first CTkEntry is for start time
            fecha_fin = formulario.winfo_children()[2].get_date()  # Assuming the second DateEntry is for end date
            hora_fin = formulario.winfo_children()[3].get()  # Assuming the second CTkEntry is for end time
            bolean = formulario.winfo_children()[4].get() #the four is the bolean

            inicio = f'{f_inicio} {hora_inicio if hora_inicio != "" else "00:00"}'
            fin = f'{fecha_fin} {hora_fin if hora_fin != "" else "00:00"}'

            if inicio > fin:
                messagebox.showerror("Error", "La fecha/hora de inicio es mayor que la de fin.")
                formulario.winfo_children()[1].delete(0,'end')
                formulario.winfo_children()[3].delete(0,'end')
                return
            
            # Generar PDF de recolección
            dt_inicio = datetime.strptime(inicio, '%Y-%m-%d %H:%M')
            dt_fin = datetime.strptime(fin, '%Y-%m-%d %H:%M')
            self._generar_recoleccion_pdf(dt_inicio, dt_fin)

            # Si el checkbox está activo, generar PDF de separación
            if bolean:
                self._generar_separacion_pdf(dt_inicio, dt_fin)

            messagebox.showinfo("Éxito", "Reportes generados con éxito.")

            print(inicio)
            print(fin)
            print(bolean)







        def _auto_formatear_hora(self, event):
            """Autoformatea la entrada para el formato hh:mm."""
            widget = event.widget
            texto = widget.get()
            filtrado = "".join(ch for ch in texto if ch.isdigit() or ch in ("/", " ", ":"))
            digits = "".join(ch for ch in filtrado if ch.isdigit())

            resultado = []
            idx = 0

            # hh (2 dígitos)
            for i in range(idx, min(idx+2, len(digits))):
                resultado.append(digits[i])
            idx = min(idx+2, len(digits))
            if idx == 2:
                resultado.append(":")

            # mm (2 dígitos)
            for i in range(idx, min(idx+2, len(digits))):
                resultado.append(digits[i])

            formateado = "".join(resultado)

            if formateado != texto:
                widget.delete(0, "end")
                widget.insert(0, formateado)
                widget.icursor("end")

        def _generar_recoleccion_pdf(self, dt_inicio: datetime, dt_fin: datetime):
            """Genera el reporte PDF de recolección."""
            data = self._consultar_recoleccion(dt_inicio, dt_fin)

            # Fecha/hora para el nombre de archivo
            fecha_str = f"{dt_inicio.strftime('%Y-%m-%d_%H-%M')}_al_{dt_fin.strftime('%Y-%m-%d_%H-%M')}"
            default_filename = f"Planilla de recoleccion - {fecha_str}.pdf"

            # Dialog para seleccionar dónde guardar
            ruta_pdf = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=default_filename,
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if not ruta_pdf:  # Si el usuario canceló, no hacemos nada
                return

            self._crear_pdf_recoleccion(data, f"Reporte de Recolección\n{dt_inicio.strftime('%d/%m/%Y %H:%M')} al {dt_fin.strftime('%d/%m/%Y %H:%M')}", ruta_pdf)

        def _consultar_recoleccion(self, dt_inicio, dt_fin):
            """Consulta real para recolección."""
            try:
                db = DBConnection()
                conn = db.connect_mysql()
                if conn is None:
                    raise Exception("No se pudo conectar con MySQL.")

                cursor = conn.cursor()
                fecha_inicio_str = dt_inicio.strftime("%Y-%m-%d %H:%M:%S")
                fecha_fin_str = dt_fin.strftime("%Y-%m-%d %H:%M:%S")

                sql = f"""
                    select
                        p2.calle, p2.id, p2.descripcion, p2.codigo_barras, p2.codigo_fabricante, SUM(pp.cantidad_final) as cantidad
                    from pedidos p
                    left join producto_pedido pp on
                        pp.pedido = p.numero
                    left join productos p2 on
                        p2.id = pp.item
                    where
                        p.preliberado = 'S'
                        and p.liberado not in ('C', 'S')
                        and p.tipo = 'Pedido'
                        and p.ultimaalteracion between '{fecha_inicio_str}' AND '{fecha_fin_str}'
                    group by
                        p2.id, p2.descripcion, p2.calle, p2.fabricante
                    order by
                        p2.calle, p2.fabricante, p2.id, p2.codigo_barras;
                """
                cursor.execute(sql)
                data = cursor.fetchall()

                conn.close()
                return data

            except Exception as e:
                messagebox.showerror("Error", f"Error consultando recolección: {e}")
                return []

        def _crear_pdf_recoleccion(self, data, titulo, ruta_pdf):
            """Genera el PDF de recolección con formato y cabecera."""
            pdf = FPDF()
            pdf.add_page()

            # Cabecera
            self._dibujar_cabecera(pdf)

            # Fuente más pequeña
            pdf.set_font("Arial", size=7)
            pdf.cell(0, 5, txt=titulo, ln=1, align="C") # type: ignore
            pdf.ln(2)

            # Encabezados => 5 columnas
            encabezados = ["Calle", "ID","Cant", "Descripción","Cod_Barras","Cod_Fabricante"]
            anchos = [23,15,25,80,20,27]

            # Fila de encabezado
            for enc, ancho in zip(encabezados, anchos):
                pdf.cell(ancho, 5, enc, border=1, align="C")
            pdf.ln()
            i=1
            # Filas de datos
            for fila in data:
                # Formato ID (5 dígitos)
                id_formateado = f"{fila[1]:05d}"

                # Descripción -> cortamos si excede 20 chars
                descripcion_corta = (fila[2][:50] + '...') if len(fila[2]) > 50 else fila[2]


                pdf.cell(23, 5, str(fila[0]), border=1, align="C")
                pdf.cell(15, 5, id_formateado, border=1, align="C")
                pdf.cell(25, 5, str(fila[5]), border=1, align="C")            
                pdf.cell(80, 5, descripcion_corta, border=1, align="L")
                pdf.cell(20, 5, str(fila[3]), border=1, align="C")
                pdf.cell(27, 5, str(fila[4]), border=1, align="C")
                pdf.ln()

            pdf.output(ruta_pdf)


        def _generar_separacion_pdf(self, dt_inicio: datetime, dt_fin: datetime):
            """
            Genera el reporte PDF de separación agrupando por empresa y luego pedido.
            """
            data = self._consultar_separacion(dt_inicio, dt_fin)
            if not data:
                messagebox.showinfo("Sin datos", "No se encontraron datos para generar el reporte de separación.")
                return

            # Construir nombre de archivo por defecto
            fecha_str = f"{dt_inicio.strftime('%Y-%m-%d_%H-%M')}_al_{dt_fin.strftime('%Y-%m-%d_%H-%M')}"
            default_filename = f"Planilla de separacion - {fecha_str}.pdf"

            ruta_pdf = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=default_filename,
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if not ruta_pdf:
                return  # Usuario canceló

            # Título que se mostrará dentro del PDF
            titulo = f"Reporte de Separación\n{dt_inicio.strftime('%d/%m/%Y %H:%M')} al {dt_fin.strftime('%d/%m/%Y %H:%M')}"
            self._crear_pdf_separacion_agrupado(data, titulo, ruta_pdf)
            messagebox.showinfo("Éxito", f"Reporte de separación generado en:\n{ruta_pdf}")


        # ----------------------------------------------------------------
        # Consulta para la planilla de separación con la SQL que incluye 'empresa'
        # y 'sum(p2.peso) as peso'
        # ----------------------------------------------------------------
        def _consultar_separacion(self, dt_inicio: datetime, dt_fin: datetime):
            """
            Devuelve filas con estructura:
            (empresa_str, pedido_num, prod_id, descripcion,
            codigo_barras, codigo_fabricante, peso, cantidad)
            """
            try:
                db = DBConnection()
                conn = db.connect_mysql()
                if conn is None:
                    raise Exception("No se pudo conectar con MySQL.")

                cursor = conn.cursor()
                fecha_inicio_str = dt_inicio.strftime("%Y-%m-%d %H:%M:%S")
                fecha_fin_str = dt_fin.strftime("%Y-%m-%d %H:%M:%S")

                sql = f"""
                    SELECT
                        CONCAT(e.id,' -- ', e.nombre) AS empresa,
                        p.numero,
                        p2.id,
                        p2.descripcion,
                        p2.codigo_barras,
                        p2.codigo_fabricante,
                        SUM(p2.peso * pp.cantidad_final) AS peso,
                        SUM(pp.cantidad_final) AS cantidad
                    FROM pedidos p
                    LEFT JOIN empresas e ON e.id = p.empresa
                    LEFT JOIN producto_pedido pp ON pp.pedido = p.numero
                    LEFT JOIN productos p2 ON p2.id = pp.item
                    WHERE p.preliberado = 'S'
                    AND p.liberado NOT IN ('C', 'S')
                    AND p.tipo = 'Pedido'
                    AND p.ultimaalteracion BETWEEN '{fecha_inicio_str}' AND '{fecha_fin_str}'
                    GROUP BY
                        e.id, e.nombre,
                        p.numero,
                        p2.id, p2.descripcion, p2.codigo_fabricante
                    ORDER BY
                        e.id, p.numero,
                        p2.codigo_fabricante,
                        p2.id, p2.codigo_barras;
                """

                cursor.execute(sql)
                data = cursor.fetchall()
                conn.close()
                return data

            except Exception as e:
                messagebox.showerror("Error", f"Error consultando separación: {e}")
                return []


        # ----------------------------------------------------------------
        # Genera el PDF agrupado por Empresa -> Pedido
        # ----------------------------------------------------------------
        def _crear_pdf_separacion_agrupado(self, data, titulo, ruta_pdf):
            """
            data: lista de tuplas (empresa, pedido, prod_id, desc, barras, fab, peso, cant)
            """
            pdf = FPDF()
            pdf.add_page()

            # Dibujar cabecera con fecha/hora
            self._dibujar_cabecera(pdf)

            pdf.set_font("Arial", size=7)
            pdf.cell(0, 5, txt=titulo, ln=1, align="C") # type: ignore
            pdf.ln(2)

            # 1) Agrupar en memoria: dict[empresa][pedido] = lista de rows
            grupos = defaultdict(lambda: defaultdict(list))
            for row in data:
                (empresa, pedido, prod_id, descripcion,
                codigo_barras, codigo_fab, peso, cantidad) = row
                grupos[empresa][pedido].append(row)

            # 2) Recorrer cada empresa en orden
            for empresa in grupos:
                pdf.set_font("Arial", 'B', 7)
                pdf.cell(0, 5, f"EMPRESA: {empresa}", ln=1)
                pdf.ln(2)

                # 3) Dentro de la empresa, recorrer cada pedido
                for pedido, filas_pedido in grupos[empresa].items():
                    # Calcular peso total sumado de este pedido
                    peso_total_pedido = sum(fil[6] for fil in filas_pedido)  # fil[6] = peso
                    pdf.set_font("Arial", 'B', 7)
                    pdf.cell(0, 5, f"PEDIDO: {pedido}   PESO: {int(peso_total_pedido)} KG", ln=1)
                    pdf.ln(1)

                    # 4) Crear la cabecera de la tabla
                    pdf.set_font("Arial", 'B', 7)
                    # Columnas: ID, Descripción, Barras, Fabricante, Cant
                    # Ajusta anchos según tus necesidades
                    pdf.cell(15, 5, "ID", border=1, align="C")
                    pdf.cell(15, 5, "Cant", border=1, align="C")                
                    pdf.cell(90, 5, "Descripción", border=1, align="C")
                    pdf.cell(30, 5, "Barras", border=1, align="C")
                    pdf.cell(40, 5, "Fabricante", border=1, align="C")
                    pdf.ln()

                    # 5) Imprimir cada producto del pedido
                    pdf.set_font("Arial", size=8)
                    for fil in filas_pedido:
                        # (empresa, pedido, prod_id, desc, barras, fab, peso, cant)
                        pid_str = f"{fil[2]:05d}"
                        desc = fil[3] or ""
                        barras = fil[4] or ""
                        fab = fil[5] or ""
                        cant = fil[7] or 0

                        # Si la descripción es muy larga, la acortamos
                        if len(desc) > 50:
                            desc = desc[:50] + "..."

                        pdf.cell(15, 5, pid_str, border=1, align="C")
                        pdf.cell(15, 5, str(cant), border=1, align="C")
                        pdf.cell(90, 5, desc, border=1, align="L")
                        pdf.cell(30, 5, barras, border=1, align="C")
                        pdf.cell(40, 5, fab, border=1, align="C")
                        pdf.ln()

                    pdf.ln(3)  # Espacio entre pedidos

            pdf.output(ruta_pdf)

        def _dibujar_cabecera(self, pdf):
            """
            Dibuja la cabecera con:
            - "PARIS IMPORT EXPORT S.A." y la fecha/hora actual centrados
            - Una línea horizontal arriba
            """
            pdf.set_font("Arial", size=8)
            # Texto centrado
            pdf.cell(
                w=0,
                h=5,
                txt=f"PARIS IMPORT EXPORT S.A. -- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                border=0,
                ln=1,
                align="C"
            )
            # Línea horizontal arriba (x1,y1,x2,y2)
            pdf.line(10, 15, 200, 15)
            pdf.ln(3)
