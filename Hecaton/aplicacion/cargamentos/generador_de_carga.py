import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
import threading

# Se importa la clase de conexión desde la ruta central de la aplicación
from aplicacion.conectiondb.conexion import DBConnection


# --- Módulo de Exportación Refactorizado ---
class ExportadorDePedidos:
    """
    Módulo para exportar datos, diseñado para ser insertado en una ventana o frame maestro.
    """
    def __init__(self, master, sesion_usuario=None):
        self.master = master
        self.sesion_usuario = sesion_usuario  # Guardado para consistencia y uso futuro
        self.db_connection = DBConnection()
        self.regiones_cache = {}

        self._configurar_interfaz()

    def _configurar_interfaz(self):
        """Crea y configura el frame principal y los widgets del módulo."""
        self.frame_principal = ctk.CTkFrame(self.master, fg_color="transparent")
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=10)

        self._crear_widgets()
        self._cargar_cache_regiones()

    def _crear_widgets(self):
        """Crea los widgets de la interfaz de usuario dentro del frame principal."""
        # Frame para los controles (fechas y botón)
        controles_frame = ctk.CTkFrame(self.frame_principal)
        controles_frame.pack(pady=20, padx=20, fill="x")

        # Configuración de la grilla para centrar los elementos
        controles_frame.grid_columnconfigure(0, weight=1)
        controles_frame.grid_columnconfigure(3, weight=1)

        # --- Selector de Fecha de Inicio ---
        ctk.CTkLabel(controles_frame, text="Fecha Inicio:").grid(row=0, column=1, padx=5, pady=10, sticky="e")
        self.fecha_inicio = DateEntry(controles_frame, width=12, background='#1F6AA5',
                                      foreground='white', date_pattern='dd/mm/yyyy', borderwidth=2)
        self.fecha_inicio.grid(row=0, column=2, padx=5, pady=10, sticky="w")

        # --- Selector de Fecha de Fin ---
        ctk.CTkLabel(controles_frame, text="Fecha Fin:").grid(row=1, column=1, padx=5, pady=10, sticky="e")
        self.fecha_fin = DateEntry(controles_frame, width=12, background='#1F6AA5',
                                   foreground='white', date_pattern='dd/mm/yyyy', borderwidth=2)
        self.fecha_fin.grid(row=1, column=2, padx=5, pady=10, sticky="w")

        # --- Botón de Exportar ---
        self.boton_exportar = ctk.CTkButton(controles_frame, text="Exportar a Excel", command=self._iniciar_exportacion)
        self.boton_exportar.grid(row=2, column=1, columnspan=2, pady=20)
        
        # --- Barra de Progreso ---
        self.progreso = ctk.CTkProgressBar(self.frame_principal, orientation="horizontal", mode="indeterminate")
        
        # --- Etiqueta de Estado ---
        self.label_estado = ctk.CTkLabel(self.frame_principal, text="", text_color="gray")
        self.label_estado.pack(pady=5)


    def _cargar_cache_regiones(self):
        """Carga las regiones desde MySQL a un diccionario para un acceso rápido."""
        conn = self.db_connection.connect_mysql()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT CONCAT(r.id, '-', r.nombre) as REGION, cr.ciudad AS CIUDAD
            FROM ciudad_region cr 
            JOIN regiones r ON r.id = cr.region
            """
            cursor.execute(query)
            result = cursor.fetchall()
            # Cache: la clave es la ciudad, el valor es la región
            self.regiones_cache = {ciudad: region for region, ciudad in result}
        except Exception as e:
            messagebox.showerror("Error de MySQL", f"No se pudieron cargar las regiones: {e}")
        finally:
            # CORREGIDO: Se simplifica el cierre de la conexión para que sea compatible
            # con las librerías pymysql y fdb.
            if conn:
                cursor.close()
                conn.close()
    
    def _obtener_region_de_cache(self, ciudad):
        """Obtiene la región para una ciudad dada desde el cache."""
        return self.regiones_cache.get(ciudad, "Sin Región")

    def _obtener_datos_firebird(self, query):
        """Función genérica para ejecutar una consulta en Firebird y devolver un DataFrame."""
        conn = self.db_connection.connect_firebird()
        if not conn:
            return pd.DataFrame() # Devuelve un DataFrame vacío si no hay conexión
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(data, columns=columns)
        except Exception as e:
            messagebox.showerror("Error de Firebird", f"Error al ejecutar la consulta: {e}")
            return pd.DataFrame()
        finally:
            # CORREGIDO: Se simplifica el cierre de la conexión para que sea compatible.
            if conn:
                cursor.close()
                conn.close()

    def _crear_excel(self, df1, df2):
        """Crea un libro de Excel con dos hojas a partir de dos DataFrames."""
        self.label_estado.configure(text="Procesando datos y creando Excel...")
        
        # Inserta la columna REGION en ambos DataFrames usando el cache
        df1.insert(3, 'REGION', df1['CIUDAD'].apply(self._obtener_region_de_cache))
        df2.insert(5, 'REGION', df2['CIUDAD'].apply(self._obtener_region_de_cache))
        
        wb = Workbook()

        # Hoja 1: "Resumen por Cliente"
        ws1 = wb.active
        ws1.title = "Resumen por Cliente"
        headers1 = df1.columns.tolist()
        ws1.append(headers1)
        for cell in ws1[1]:
            cell.font = Font(bold=True)
        for row in df1.itertuples(index=False):
            ws1.append(row)

        # Hoja 2: "Detalle de Pedidos"
        ws2 = wb.create_sheet(title="Detalle de Pedidos")
        headers2 = df2.columns.tolist()
        ws2.append(headers2)
        for cell in ws2[1]:
            cell.font = Font(bold=True)
        for row in df2.itertuples(index=False):
            ws2.append(row)
            
        return wb

    def _iniciar_exportacion(self):
        """Inicia el proceso de exportación en un hilo separado para no bloquear la UI."""
        self.boton_exportar.configure(state="disabled")
        self.progreso.pack(pady=10, padx=20, fill="x")
        self.progreso.start()
        self.label_estado.configure(text="Iniciando exportación...")

        thread = threading.Thread(target=self._exportar_datos_thread)
        thread.start()

    def _exportar_datos_thread(self):
        """Contiene la lógica de exportación que se ejecuta en un hilo."""
        try:
            fecha_inicio_str = self.fecha_inicio.get_date().strftime("%Y-%m-%d 00:00:00.000")
            fecha_fin_str = self.fecha_fin.get_date().strftime("%Y-%m-%d 23:59:59.000")
            
            # --- Consulta 1 ---
            self.label_estado.configure(text="Consultando resumen de clientes...")
            query1 = f"""
                SELECT DISTINCT e.CODIGO AS COD_CLI, e.NOME AS CLIENTE, e.CIDADE AS CIUDAD, r.NOME AS SUBREGION,
                e.LOCALENTREGA AS DIAENTREGA, e.COBRANCA AS DIACOBRANCA, SUM(i.QUANTIDADE * i2.PESO) AS PESO,
                SUM(i.QUANTIDADE * i.PRECO) AS VALOR,
                SUM(CASE o.MOEDA WHEN '1' THEN (i.QUANTIDADE * i.PRECO) * 7000 WHEN '2' THEN (i.QUANTIDADE * i.PRECO) * 1400 ELSE i.QUANTIDADE * i.PRECO END) AS CAMBIO,
                CASE o.MOEDA WHEN 0 THEN 'G' WHEN 1 THEN '$' WHEN 2 THEN 'R$' ELSE 'OTROS' END AS MONEDA, v.NOME AS VENDEDOR
                FROM EMPRESAS e
                RIGHT JOIN ITENSORCAMENTOS i ON i.EMPRESACODIGO = e.CODIGO
                LEFT JOIN ORCAMENTOS o ON o.NUMERO = i.NUMERO
                LEFT JOIN ITENS i2 ON i2.CODIGO = i.ITEM
                LEFT JOIN REGIOES r ON r.CODIGO = e.REGIAO
                LEFT JOIN VENDEDORES v ON v.CODIGO = o.VENDEDOR
                WHERE o."DATA" BETWEEN '{fecha_inicio_str}' AND '{fecha_fin_str}' AND o.PRELIBERADO = 'S' AND o.TIPO = 'Pedido'
                GROUP BY e.CODIGO, e.NOME, e.CIDADE, r.NOME, e.LOCALENTREGA, e.COBRANCA, v.NOME, o.MOEDA ORDER BY e.CIDADE ASC
            """
            df1 = self._obtener_datos_firebird(query1)

            # --- Consulta 2 ---
            self.label_estado.configure(text="Consultando detalle de pedidos...")
            query2 = f"""
                SELECT o.NUMERO, o.NUMERONOTA, e.CODIGO AS COD_CLI, e.NOME AS CLIENTE, e.CIDADE AS CIUDAD, r.NOME AS SUBREGION,
                e.LOCALENTREGA AS DIAENTREGA, e.COBRANCA AS DIACOBRANCA, SUM(i.QUANTIDADE * i2.PESO) AS PESO,
                SUM(i.QUANTIDADE * i.PRECO) AS VALOR,
                SUM(CASE o.MOEDA WHEN '1' THEN (i.QUANTIDADE * i.PRECO) * 7000 WHEN '2' THEN (i.QUANTIDADE * i.PRECO) * 1400 ELSE i.QUANTIDADE * i.PRECO END) AS CAMBIO,
                CASE o.MOEDA WHEN 0 THEN 'G' WHEN 1 THEN '$' WHEN 2 THEN 'R$' ELSE 'OTROS' END AS MONEDA, v.NOME AS VENDEDOR,
                CAST(o.OBSERVACAO as VARCHAR(1000)) AS OBSERVACION
                FROM EMPRESAS e
                RIGHT JOIN ITENSORCAMENTOS i ON i.EMPRESACODIGO = e.CODIGO
                LEFT JOIN ORCAMENTOS o ON o.NUMERO = i.NUMERO
                LEFT JOIN ITENS i2 ON i2.CODIGO = i.ITEM
                LEFT JOIN REGIOES r ON r.CODIGO = e.REGIAO
                LEFT JOIN VENDEDORES v ON v.CODIGO = o.VENDEDOR
                WHERE o."DATA" BETWEEN '{fecha_inicio_str}' AND '{fecha_fin_str}' AND o.PRELIBERADO = 'S' AND o.TIPO = 'Pedido'
                GROUP BY o.NUMERO, o.NUMERONOTA, e.CODIGO, e.NOME, e.CIDADE, r.NOME, e.LOCALENTREGA, e.COBRANCA, v.NOME, o.MOEDA, o.OBSERVACAO ORDER BY e.CIDADE ASC
            """
            df2 = self._obtener_datos_firebird(query2)

            if df1.empty and df2.empty:
                self.master.after(0, lambda: messagebox.showwarning("Sin Datos", "No se encontraron datos para el rango de fechas seleccionado."))
                return

            wb = self._crear_excel(df1, df2)
            
            fecha_inicio_fmt = self.fecha_inicio.get_date().strftime("%d-%m-%Y")
            fecha_fin_fmt = self.fecha_fin.get_date().strftime("%d-%m-%Y")
            default_filename = f"Pedidos del {fecha_inicio_fmt} al {fecha_fin_fmt}.xlsx"
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=default_filename,
                filetypes=[("Archivos de Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
            )
            
            if filename:
                wb.save(filename)
                self.master.after(0, lambda: messagebox.showinfo("Éxito", f"Datos exportados exitosamente a\n{filename}"))

        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Error", f"Ocurrió un error durante la exportación: {str(e)}"))
        finally:
            # Restaurar la interfaz de usuario en el hilo principal
            self.master.after(0, self._finalizar_exportacion)

    def _finalizar_exportacion(self):
        """Restaura el estado de la UI después de que el hilo de exportación termina."""
        self.progreso.stop()
        self.progreso.pack_forget()
        self.boton_exportar.configure(state="normal")
        self.label_estado.configure(text="")

# --- Bloque de prueba para ejecutar el módulo de forma independiente ---
if __name__ == '__main__':
    # NOTA: Para ejecutar este script de forma independiente, la importación
    # 'from aplicacion.conectiondb.conexion import DBConnection' fallará.
    # Se necesitaría tener la estructura de carpetas 'aplicacion/conectiondb'
    # o definir una clase DBConnection de prueba aquí mismo.
    
    # Configuración de la ventana principal con customtkinter
    app = ctk.CTk()
    app.title("Demostración de Módulo de Exportación")
    app.geometry("500x300")
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Crear una instancia del módulo y pasarle la ventana principal como 'master'
    modulo_exportador = ModuloExportacion(app)

    # Iniciar el bucle principal de la aplicación
    app.mainloop()
