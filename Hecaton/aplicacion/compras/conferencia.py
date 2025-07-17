import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
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


class OrderPdfApp:
    def __init__(self, master, sesion_usuario):
        self.master = master
        self.sesion_usuario = sesion_usuario
        self.setup_gui()

    def setup_gui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.master)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Etiqueta de título
        titulo = ctk.CTkLabel(main_frame, text="Generador de Pedidos - PDF", font=("Arial", 18, "bold"))
        titulo.grid(row=0, column=0, pady=(0, 20))

        # Número de orden
        ctk.CTkLabel(main_frame, text="Número de Pedido:").grid(row=1, column=0, padx=5, sticky="we")
        self.order_number = ctk.CTkEntry(main_frame, width=300)
        self.order_number.grid(row=2, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Botón generar PDF
        self.generate_button = ctk.CTkButton(main_frame, text="Generar PDF", command=self.generate_pdf)
        self.generate_button.grid(row=3, column=0, pady=20)

        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.grid(row=4, column=0, pady=10)

        # Mensaje de estado
        self.status_label = ctk.CTkLabel(main_frame, text="", font=("Arial", 12))
        self.status_label.grid(row=5, column=0, pady=10)

    def generate_pdf(self):
        order_num = self.order_number.get().strip()
        if not order_num:
            messagebox.showerror("Error", "Por favor ingrese un número de pedido")
            return

        self.progress.start(10)
        self.status_label.configure(text="Generando PDF...")
        self.master.update_idletasks()

        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"pedido_{order_num}.pdf",
                title="Guardar PDF como..."
            )

            if file_path:
                # Crear una nueva conexión para cada generación de PDF usando la clase importada
                connection = DBConnection().connect_firebird()
                if connection:
                    generator = OrderPdfGenerator(connection)
                    generator.generate(order_num, file_path)
                    self.status_label.configure(text="PDF generado exitosamente", text_color="green")
                    messagebox.showinfo("Éxito", f"PDF generado exitosamente:\n{file_path}")
                    connection.close() # Cerrar la conexión después de usarla
                else:
                    # Esto es para demostración si no hay conexión a la base de datos
                    messagebox.showwarning("Modo Demostración", "No se pudo conectar a la base de datos. Se generará un PDF de muestra.")
                    generator = OrderPdfGenerator(None) # Pasar None para indicar modo demo
                    generator.generate(order_num, file_path, demo_mode=True)
                    self.status_label.configure(text="PDF de muestra generado exitosamente", text_color="blue")


        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el PDF:\n{str(e)}")
            self.status_label.configure(text="Error al generar PDF", text_color="red")
        finally:
            self.progress.stop()
            self.progress['value'] = 0

# --- Clase para la Lógica de Generación de PDF ---
class OrderPdfGenerator:
    def __init__(self, connection):
        self.connection = connection
        self.styles = getSampleStyleSheet()

    def get_order_data(self, order_number):
        """Obtiene los datos del pedido desde la base de datos usando la nueva consulta."""
        if not self.connection:
            raise ConnectionError("La conexión a la base de datos no está disponible.")
        
        cursor = self.connection.cursor()
        # --- CONSULTA SQL ACTUALIZADA ---
        # Se agregó i.CODIGOFABRICANTE
        query = """
            SELECT p.NUMERO, i.CODIGO, i.CODIGOFABRICANTE, i2.IMAGEM, i.CODIGOBARRAS, 
                   i.DESCRICAO, e.NOME, e.CODIGO 
            FROM PEDIDOS p
            LEFT JOIN ITENS i ON i.CODIGO = p.ITEM
            LEFT JOIN ITENSCOMPLEMENTO i2 ON i2.CODIGO = i.CODIGO
            LEFT JOIN EMPRESAS e ON e.CODIGO = p.EMPRESA
            WHERE p.QUANTIDADE > 0 AND p.NUMERO = ?
        """
        cursor.execute(query, (order_number,))
        return cursor.fetchall()

    def get_demo_data(self, order_number):
        """Genera datos de muestra para propósitos de demostración."""
        print("Generando datos de muestra...")
        return [
            (order_number, '1010', 'REF-A1', None, '7891234567890', 'PRODUCTO DE EJEMPLO 1', 'CLIENTE DE MUESTRA', 'C001'),
            (order_number, '2020', 'REF-B2', None, '7891234567891', 'PRODUCTO DE EJEMPLO 2 CON DESCRIPCIÓN LARGA', 'CLIENTE DE MUESTRA', 'C001'),
            (order_number, '3030', 'REF-C3', None, '7891234567892', 'PRODUCTO DE EJEMPLO 3', 'CLIENTE DE MUESTRA', 'C001'),
        ]

    def process_image(self, image_data):
        """Procesar las imágenes de la base de datos."""
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
            return Image(img_buffer, width=45, height=45, kind='proportional')
        except Exception as e:
            print(f"Error procesando imagen: {e}")
            return None

    def generate(self, order_number, output_path, demo_mode=False):
        """Generar el archivo PDF del pedido."""
        try:
            if demo_mode:
                data = self.get_demo_data(order_number)
            else:
                data = self.get_order_data(order_number)

            if not data:
                raise ValueError(f"No se encontraron datos para el pedido número: {order_number}")

            first_row = data[0]
            doc = SimpleDocTemplate(
                output_path, pagesize=letter,
                rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
            )
            elements = []

            # Logo
            try:
                if hasattr(sys, '_MEIPASS'):
                    logo_path = os.path.join(sys._MEIPASS, 'recursos', 'paris.png')
                else:
                    # Asegúrate de que esta ruta sea correcta para tu entorno de desarrollo
                    logo_path = "Hecaton/aplicacion/recursos/paris.png" # Ruta relativa es mejor
                
                if not os.path.exists(logo_path):
                    # Crear un placeholder si el logo no existe
                    placeholder_img = PILImage.new('RGB', (150, 50), color = 'grey')
                    placeholder_img.save(logo_path)
                
                logo = Image(logo_path, width=1.5 * inch, height=0.5 * inch)
            except Exception as e:
                print(f"No se pudo cargar el logo: {e}")
                logo = Paragraph("PARIS IMPORT EXPORT S.A.", self.styles['h1'])

            # Encabezado
            header_data = [
                [logo, 
                 "PARIS IMPORT EXPORT S.A.\nKM 14 MONDAY - RUTA LOS CEDRALES - MINGA GUAZÚ\nTEL.: (0983) 153 581   RUC: 80078115-5", 
                 f"NUMERO DE\nPEDIDO:\n{first_row[0]}\n{datetime.now().strftime('%d/%m/%Y %H:%M')}"]
            ]
            header_table = Table(header_data, colWidths=[1.6*inch, 4*inch, 2*inch])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('ALIGN', (2, 0), (2, 0), 'CENTER'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            elements.append(header_table)

            # Información del cliente (simplificada)
            # Se ajustan los índices para la nueva consulta
            custom_style = ParagraphStyle(name='CustomStyle', fontSize=10, textColor=colors.black)
            client_name = str(first_row[6]) if first_row[6] else "N/A"
            client_code = str(first_row[7]) if first_row[7] else "N/A"

            client_data = [
                [Paragraph("<b>CLIENTE:</b>", custom_style), Paragraph(client_name, custom_style),
                 Paragraph("<b>COD.:</b>", custom_style), Paragraph(client_code, custom_style)]
            ]
            client_table = Table(client_data, colWidths=[inch, 3.5*inch, 0.5*inch, 2.5*inch])
            client_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(client_table)

            # --- Tabla de items con nuevas columnas ---
            # Se agrega 'REF' al encabezado
            table_header = ['N°', 'COD', 'REF', 'FOTO', 'BARRA', 'DESCRIPCION', 'LOTE', 'FAB', 'VENC', 'CANT REC']
            table_data = [table_header]
            
            for idx, row in enumerate(data, 1):
                # Mapeo de columnas de la nueva consulta
                # row[0]: p.NUMERO, row[1]: i.CODIGO, row[2]: i.CODIGOFABRICANTE,
                # row[3]: i2.IMAGEM, row[4]: i.CODIGOBARRAS, row[5]: i.DESCRICAO,
                # row[6]: e.NOME, row[7]: e.CODIGO
                image = self.process_image(row[3]) # El índice de la imagen ahora es 3
                row_data = [
                    idx,
                    row[1],                                     # COD
                    row[2],                                     # REF (NUEVO)
                    image if image else "",                     # FOTO
                    row[4],                                     # BARRA
                    Paragraph(str(row[5]), custom_style),       # DESCRIPCION
                    "", # LOTE (Placeholder)
                    "", # FAB (Placeholder)
                    "", # VENC (Placeholder)
                    ""  # CANT REC (Placeholder)
                ]
                table_data.append(row_data)

            # Anchos de columna ajustados para las nuevas columnas
            col_widths = [25, 40, 70, 45, 70, 140, 40, 40, 40, 40]
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            elements.append(table)
            
            doc.build(elements)

        except fdb.Error as db_error:
            print(f"Error de base de datos al generar PDF: {db_error}")
            raise Exception(f"Error de base de datos: {db_error}")
        except Exception as e:
            print(f"Error general al generar PDF: {e}")
            raise e

def main():
    # customtkinter.set_appearance_mode("dark") # Opcional: "light", "system"
    root = ctk.CTk()
    root.title("Generador de PDF de Pedidos") # El título se establece aquí
    root.geometry("450x350")
    # Crear directorio de recursos si no existe
    if not os.path.exists('recursos'):
        os.makedirs('recursos')
    app = OrderPdfApp(root, sesion_usuario=None)
    root.mainloop()

if __name__ == "__main__":
    main()
