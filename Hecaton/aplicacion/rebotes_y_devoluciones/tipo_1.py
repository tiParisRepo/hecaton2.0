import customtkinter as ctk
from tkinter import ttk, messagebox
from aplicacion.conectiondb.conexion import DBConnection

class ModuloTipo1:
    def __init__(self, master):
        self.master = master
        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both", padx=10, pady=10)

        self._crear_interfaz()
        self._cargar_datos()

    def _crear_interfaz(self):
        titulo = ctk.CTkLabel(self.frame_principal, text="Gestión de Tipo 1", font=("Arial", 16, "bold"))
        titulo.pack(pady=10)

        # Sección de entradas
        entrada_frame = ctk.CTkFrame(self.frame_principal)
        entrada_frame.pack(pady=5, fill="x")

        self.entry_nombre = ctk.CTkEntry(entrada_frame, placeholder_text="Nombre")
        self.entry_nombre.pack(side="left", padx=5, fill="x", expand=True)

        self.entry_descripcion = ctk.CTkEntry(entrada_frame, placeholder_text="Descripción")
        self.entry_descripcion.pack(side="left", padx=5, fill="x", expand=True)

        # Botones
        frame_botones = ctk.CTkFrame(self.frame_principal)
        frame_botones.pack(pady=10, fill="x")

        # Botón de guardar
        self.boton_guardar = ctk.CTkButton(frame_botones, text="Guardar", command=self._guardar)
        self.boton_guardar.pack(side="left", padx=5)

        # Botón de editar
        self.boton_editar = ctk.CTkButton(frame_botones, text="Editar", command=self._editar_registro)
        self.boton_editar.pack(side="left", padx=5)
        self.boton_editar.configure(state="disabled")  # Desactivar hasta que se seleccione un registro

        # Botón de eliminar
        self.boton_eliminar = ctk.CTkButton(frame_botones, text="Eliminar", command=self._eliminar_registro)
        self.boton_eliminar.pack(side="left", padx=5)
        self.boton_eliminar.configure(state="disabled")  # Desactivar hasta que se seleccione un registro

        # Tabla
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="#E9F0ED",
                        rowheight=25,
                        fieldbackground="#333333",
                        font=("Arial", 12))
        style.map("Custom.Treeview", background=[("selected", "#144870")])
        style.configure("Custom.Treeview.Heading",
                        background="#1F6AA5",
                        foreground="#E9F0ED",
                        font=("Arial", 13, "bold"),
                        relief='flat')
        style.map("Custom.Treeview.Heading", background=[("active", "#1F6AA5")])

        self.tree = ttk.Treeview(self.frame_principal, columns=("id", "nombre", "descripcion"), show="headings", style="Custom.Treeview")
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("descripcion", text="Descripción")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("nombre", width=150)
        self.tree.column("descripcion", width=250)
        self.tree.pack(fill="both", expand=True, pady=10)

        self.tree.bind("<Double-1>", self._seleccionar_registro)

    def _cargar_datos(self):
        self.tree.delete(*self.tree.get_children())
        try:
            db = DBConnection()
            conn = db.connect_mysql()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, descripcion FROM tipo1")
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar datos: {e}")

    def _guardar(self):
        nombre = self.entry_nombre.get().strip()
        descripcion = self.entry_descripcion.get().strip()

        if not nombre:
            messagebox.showwarning("Campo requerido", "El campo 'Nombre' es obligatorio.")
            return

        try:
            db = DBConnection()
            conn = db.connect_mysql()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tipo1 (nombre, descripcion) VALUES (%s, %s)", (nombre, descripcion))
            conn.commit()
            conn.close()
            self.entry_nombre.delete(0, "end")
            self.entry_descripcion.delete(0, "end")
            self._cargar_datos()
            messagebox.showinfo("Éxito", "Registro agregado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _editar_registro(self, event=None):
        item = self.tree.selection()

        # Verificar si hay un item seleccionado
        if not item:
            messagebox.showwarning("Selección", "Por favor, seleccione un registro para editar.")
            return

        # Obtener los valores de la selección
        valores = self.tree.item(item[0], "values")
        id_tipo1 = valores[0]
        nombre_actual = self.entry_nombre.get().strip()
        descripcion_actual = self.entry_descripcion.get().strip()

        try:
            db = DBConnection()
            conn = db.connect_mysql()
            cursor = conn.cursor()
            cursor.execute("""UPDATE tipo1 SET
                                nombre = %s,
                                descripcion = %s
                           WHERE id = %s""",
                           (nombre_actual, descripcion_actual, id_tipo1))
            conn.commit()
            conn.close()
            self.entry_nombre.delete(0, "end")
            self.entry_descripcion.delete(0, "end")
            self._cargar_datos()
            messagebox.showinfo("Éxito", "Registro actualizado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

        # Desactivar los botones después de la edición
        self.boton_guardar.configure(state="normal")  # Activar guardar
        self.boton_editar.configure(state="disabled")  # Desactivar editar
        self.boton_eliminar.configure(state="disabled")  # Desactivar eliminar

    def _seleccionar_registro(self, event=None):
        item = self.tree.selection()

        valores = self.tree.item(item[0], "values")
        nombre_actual = valores[1]
        descripcion_actual = valores[2]

        # Prellenar los campos con la información del registro seleccionado
        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, nombre_actual)
        self.entry_descripcion.delete(0, "end")
        self.entry_descripcion.insert(0, descripcion_actual)

        # Activar los botones de editar y eliminar
        self.boton_guardar.configure(state="disabled")  # Desactivar guardar
        self.boton_editar.configure(state="normal")  # Activar editar
        self.boton_eliminar.configure(state="normal")  # Activar eliminar

    def _eliminar_registro(self):
        item = self.tree.selection()

        if not item:
            messagebox.showwarning("Selección", "Por favor, seleccione un registro para eliminar.")
            return

        id_tipo1 = self.tree.item(item[0], "values")[0]

        confirmacion = messagebox.askyesno("Confirmar eliminación", "¿Está seguro que desea eliminar este registro?")
        if confirmacion:
            try:
                db = DBConnection()
                conn = db.connect_mysql()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tipo1 WHERE id = %s", (id_tipo1,))
                conn.commit()
                conn.close()
                self._cargar_datos()
                messagebox.showinfo("Eliminado", "Registro eliminado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

        # Desactivar los botones después de la eliminación
        self.boton_editar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
