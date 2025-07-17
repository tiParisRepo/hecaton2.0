import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import base64
import io
import os
import sys
import fdb
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from aplicacion.conectiondb.conexion import DBConnection

class orderPDFGenerator:
    def __init__(self, master, sesion_usuario):
        self.master = master
        self.sesion_usuario = sesion_usuario
        self.setup_gui()

    def setup_gui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.master)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Etiqueta de título
        titulo = ctk.CTkLabel(main_frame, text="Generador de Presupuestos - PDF", font=("Arial", 16, "bold"))
        titulo.grid(column=0,row=0,columnspan=3,pady=10)

        # Número de orden
        ctk.CTkLabel(main_frame, text="Número de Orden:").grid(column=1,row=1,padx=5)
        self.order_number = ctk.CTkEntry(main_frame)
        self.order_number.grid(column=1,row=2, padx=5)

        # Botón generar PDF
        ttk.Button(main_frame, text="Generar PDF", command=self.generate_pdf).grid(column=1,row=3,pady=20)

        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.grid(column=1,row=4,pady=10)

        # Mensaje de estado
        self.status_label = ttk.Label(main_frame, text="",background="#222A2A", foreground="white")
        self.status_label.grid(column=1,row=5,pady=10)

    def generate_pdf(self):
        order_num = self.order_number.get().strip()
        if not order_num:
            messagebox.showerror("Error", "Por favor ingrese un número de orden")
            return

        self.progress.start()
        self.status_label.config(text="Generando PDF...")

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"orden_{order_num}.pdf"
            )

            if file_path:
                # Crear una nueva conexión para cada generación de PDF
                connection = DBConnection().connect_firebird()
                if connection:
                    generator = OrderPDFGenerator(connection)
                    generator.generate_pdf(order_num, file_path)
                    self.status_label.config(text="PDF generado exitosamente")
                    messagebox.showinfo("Éxito", f"PDF generado exitosamente:\n{file_path}")
                else:
                    raise Exception("No se pudo establecer la conexión con la base de datos")

        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el PDF:\n{str(e)}")
            self.status_label.config(text="Error al generar PDF")

        finally:
            self.progress.stop()

class OrderPDFGenerator:
    def __init__(self, connection):
        self.connection = connection
        self.styles = getSampleStyleSheet()

    def format_currency(self, value, currency_type='0'):
        """Formatear como moneda"""
        if currency_type == '0':  # Guaraníes
            return f"Gs. {value:,.0f}"
        else:  # Dólares
            return f"$ {value:,.2f}"

    def get_order_data(self, order_number):
        """Obtiene los datos de la orden desde la base de datos"""
        cursor = self.connection.cursor()
        query = """
            SELECT i.NUMERO, i2.CODIGO, i3.IMAGEM, i2.CODIGOBARRAS, i2.DESCRICAO, 
                   i.QUANTIDADE, i.PRECO, i.VALORTOTAL, o.CONDICAOPGTO, e.NOME, 
                   o.TIPO, e.CODIGO, o.MOEDA, e.ENDERECO, e.BAIRRO, e.CIDADE,
                   v.NOME,e.CELULAR,e.CGC
            FROM ITENSORCAMENTOS i
            LEFT JOIN ITENS i2 ON i2.CODIGO = i.ITEM
            LEFT JOIN ITENSCOMPLEMENTO i3 ON i3.CODIGO = i2.CODIGO
            LEFT JOIN ORCAMENTOS o ON o.NUMERO = i.NUMERO
            LEFT JOIN EMPRESAS e ON e.CODIGO = o.EMPRESACODIGO
            LEFT JOIN VENDEDORES v ON v.CODIGO = o.VENDEDOR
            WHERE i.QUANTIDADE > 0 AND i.NUMERO = ?
        """
        cursor.execute(query, (order_number,))
        return cursor.fetchall()

    def process_image(self, image_data):
        """Procesar las imágenes de la base de datos"""
        if not image_data:
            return None

        try:
            if isinstance(image_data, fdb.BlobReader):
                img_data = image_data.read()
            elif isinstance(image_data, str):
                img_data = base64.b64decode(image_data)
            else:
                img_data = image_data

            img = PILImage.open(io.BytesIO(img_data))
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            return Image(img_buffer, width=50, height=50)
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def generate_pdf(self, order_number, output_path):
        """Generar el archivo PDF de la orden de compra"""
        try:
            data = self.get_order_data(order_number)
            if not data:
                raise ValueError("No data found for the specified order number")

            # Get the first row for header information
            first_row = data[0]

            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=20,
                leftMargin=20,
                topMargin=20,
                bottomMargin=20
            )

            elements = []

            # Logo del encabezado
            try:
                if hasattr(sys, '_MEIPASS'):
                    logo_path = os.path.join(sys._MEIPASS, 'recursos', 'paris.png')
                else:
                    logo_path = "Hecaton/aplicacion/recursos/paris.png"
                logo = Image(logo_path, width=1.5 * inch, height=0.5 * inch)
            except:
                logo = None

            # Definir el tipo de documento basado en la consulta
            orden = 'PEDIDO' if first_row[10] == 'Pedido' else 'PRESUPUESTO'

            # Información del encabezado
            header_data = [
                [logo, 
                "PARIS IMPORT EXPORT S.A.\nKM 14 MONDAY - RUTA LOS CEDRALES - MINGA GUAZÚ\nTEL.: (0983) 153 581    RUC: 80078115-5", 
                f"NUMERO DE\n{orden}:\n{first_row[0]}/1\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"]
            ]

            header_table = Table(header_data, colWidths=[120, 250, 200])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                ('ALIGN', (2, 0), (2, 0), 'CENTER'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (1, 0), (1, 0), 9),
                ('FONTSIZE', (2, 0), (2, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('SPACEBELOW', (0, 0), (0, 0), 10)
            ]))
            elements.append(header_table)

            # Definir un estilo personalizado para los datos
            custom_style = ParagraphStyle(name='CustomStyle', fontSize=10, textColor=colors.black)

            # Información del cliente
            info_cliente = []
            for i in (9, 14, 11, 13, 16, 11, 17, 15, 18):
                info_cliente.append(Paragraph(str(first_row[i]), custom_style))

            client_data = [
                [Paragraph("CLIENTE:", custom_style), info_cliente[0], 
                Paragraph("BARRIO:", custom_style), info_cliente[1], 
                Paragraph("COD.:", custom_style), info_cliente[2]],

                [Paragraph("DIRECCION:", custom_style), info_cliente[3], 
                Paragraph("VENDEDOR:", custom_style), info_cliente[4], 
                Paragraph("RUC:", custom_style), info_cliente[8]],

                [Paragraph("TELEFONO:", custom_style), info_cliente[6], 
                Paragraph("CIUDAD:", custom_style), info_cliente[7], "", ""]
            ]

            client_table = Table(client_data, colWidths=[75, 160, 80, 120, 40, 70])
            client_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
            ]))
            elements.append(Spacer(0, 0.1*inch))
            elements.append(client_table)

            # Tabla de items
            table_data = [['N°', 'COD', 'FOTO', 'BARRA', 'DESCRIPCION', 'CANT', 'PRECIO', 'VALOR']]
            
            for idx, row in enumerate(data, 1):
                image = self.process_image(row[2])
                row_data = [
                    idx,
                    row[1],
                    image if image else "",
                    row[3],
                    Paragraph(row[4], custom_style),
                    format(f"{row[5]:,.0f}"),
                    self.format_currency(row[6], row[12]),
                    self.format_currency(row[7], row[12]),
                ]
                table_data.append(row_data)

            total = sum(row[7] for row in data)
            table_data.append(['', '', '', '', '', '', 'Total:', self.format_currency(total, data[0][12])])

            col_widths = [25, 45, 50, 80, 180, 35, 60, 60]
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))

            elements.append(table)
            doc.build(elements)

        except Exception as e:
            print(f"Error generating PDF: {e}")

def obtener_conexion():
    return DBConnection().connect_firebird()

def main():
    root = tk.Tk()
    app = orderPDFGenerator(root, sesion_usuario=None)  # Asigna la sesión de usuario si es necesario
    root.mainloop()

if __name__ == "__main__":
    main()
