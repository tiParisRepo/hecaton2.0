import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection

class ModuloGruposUsuarios:
    def __init__(self, master):
        self.master = master
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=5)
        
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
        # Crear TreeView de grupos de usuarios
        self._crear_treeview_grupos()

        # Crear botones para agregar, editar y eliminar
        self._crear_botones()

        # Cargar los datos iniciales
        self._llenar_treeview_grupos()

    def _crear_treeview_grupos(self):
        frame_grupos = ctk.CTkFrame(self.frame_principal)
        frame_grupos.pack(side="top", fill="x", padx=10, pady=5)

        self.treeview_grupos = ttk.Treeview(
            frame_grupos,
            style='Custom.Treeview',
            columns=("ID", "Grupo", "Miembros"),
            show="headings"
        )
        self.treeview_grupos.pack(expand=True, fill="both", padx=10, pady=5)

        # Configurar encabezados
        self.treeview_grupos.heading("ID", text="ID")
        self.treeview_grupos.heading("Grupo", text="Grupo")
        self.treeview_grupos.heading("Miembros", text="Miembros")

    def _llenar_treeview_grupos(self):
        try:
            # Conexión a la base de datos
            db = DBConnection()
            conexion = db.connect_mysql()
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT gu.id, gu.nombre, COUNT(u.id) AS miembros
                FROM grupo_usuario gu
                LEFT JOIN usuarios u ON u.nivel_acceso = gu.id
                GROUP BY gu.id, gu.nombre;
            """)
            resultados = cursor.fetchall()

            # Limpiar TreeView antes de insertar
            self.treeview_grupos.delete(*self.treeview_grupos.get_children())

            # Insertar registros en el TreeView
            for fila in resultados:
                self.treeview_grupos.insert("", "end", values=fila)

            conexion.close()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los grupos de usuarios: {e}")

    def _crear_botones(self):
        # Crear botón para agregar un nuevo grupo
        ctk.CTkButton(self.frame_principal, text="Agregar Grupo", command=self._crear_grupo).pack(pady=5)

        # Crear botón para editar el grupo seleccionado
        ctk.CTkButton(self.frame_principal, text="Editar Grupo", command=self._editar_grupo).pack(pady=5)

        # Crear botón para eliminar el grupo seleccionado
        ctk.CTkButton(self.frame_principal, text="Eliminar Grupo", command=self._eliminar_grupo).pack(pady=5)

    def _crear_grupo(self):
        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Crear Grupo")
        formulario.geometry("300x200")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Grupo:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.pack(pady=5)

        def guardar_grupo():
            nombre = nombre_entry.get()

            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para el grupo.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    "INSERT INTO grupo_usuario (nombre) VALUES (%s);",
                    (nombre,)
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Grupo creado correctamente.")
                self._llenar_treeview_grupos()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al crear el grupo: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_grupo).pack(pady=10)

    def _editar_grupo(self):
        seleccion = self.treeview_grupos.focus()
        valores = self.treeview_grupos.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un grupo para editar.")
            return

        grupo_id, grupo_nombre, _ = valores

        formulario = ctk.CTkToplevel(self.master)
        formulario.title("Editar Grupo")
        formulario.geometry("300x200")
        formulario.grab_set()

        ctk.CTkLabel(formulario, text="Nombre del Grupo:").pack(pady=10)
        nombre_entry = ctk.CTkEntry(formulario)
        nombre_entry.insert(0, grupo_nombre)
        nombre_entry.pack(pady=5)

        def guardar_cambios():
            nombre = nombre_entry.get()

            if not nombre:
                messagebox.showerror("Error", "Debe ingresar un nombre para el grupo.")
                return

            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    "UPDATE grupo_usuario SET nombre = %s WHERE id = %s;",
                    (nombre, grupo_id)
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Grupo actualizado correctamente.")
                self._llenar_treeview_grupos()
                formulario.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar el grupo: {e}")

        ctk.CTkButton(formulario, text="Guardar", command=guardar_cambios).pack(pady=10)

    def _eliminar_grupo(self):
        seleccion = self.treeview_grupos.focus()
        valores = self.treeview_grupos.item(seleccion, "values")

        if not valores:
            messagebox.showerror("Error", "Debe seleccionar un grupo para eliminar.")
            return

        grupo_id, grupo_nombre, _ = valores

        confirmacion = messagebox.askyesno(
            "Confirmación", f"¿Está seguro de que desea eliminar el grupo '{grupo_nombre}'?"
        )

        if confirmacion:
            try:
                db = DBConnection()
                conexion = db.connect_mysql()
                cursor = conexion.cursor()

                cursor.execute(
                    "DELETE FROM grupo_usuario WHERE id = %s;",
                    (grupo_id,)
                )
                conexion.commit()
                conexion.close()

                messagebox.showinfo("Éxito", "Grupo eliminado correctamente.")
                self._llenar_treeview_grupos()
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar el grupo: {e}")
