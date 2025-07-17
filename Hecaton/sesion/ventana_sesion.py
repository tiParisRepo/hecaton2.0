import customtkinter as ctk
from tkinter import messagebox
from sesion.sesion import UsuarioManager
from aplicacion.index import Index

class VentanaSesion:
    def __init__(self):
        # Configuración inicial de la ventana
        self.gestor_usuarios = UsuarioManager(host="192.168.1.40", user="LUCAS", password="CARITAdePapa0s0", database="dbhecaton")
        self.ventana = ctk.CTk()
        ctk.set_appearance_mode("dark")
        self.ventana.title("LOGIN")
        self.ventana.geometry("210x200")
        self.ventana.resizable(False, False)

    def iniciar(self):
        # Crear interfaz gráfica
        self._crear_interfaz()
        self.ventana.mainloop()

    def _crear_interfaz(self):
        # Widgets para la ventana de inicio de sesión
        ctk.CTkLabel(self.ventana, text="Usuario").grid(row=0, column=0, padx=10, pady=5, columnspan=2, sticky="ew")
        self.usuario_entry = ctk.CTkEntry(self.ventana, width=170)
        self.usuario_entry.grid(row=1, column=0, padx=10, pady=5, columnspan=2, sticky="ew")
        self.ventana.after(100, self.usuario_entry.focus_set)  # Establece el foco inicial en el campo de usuario
        self.usuario_entry.bind("<Return>", lambda event: self.contrasena_entry.focus_set())  # Vincula la tecla Enter

        ctk.CTkLabel(self.ventana, text="Contraseña").grid(row=3, column=0, padx=10, pady=5, columnspan=2, sticky="ew")
        self.contrasena_entry = ctk.CTkEntry(self.ventana, width=170, show="*")
        self.contrasena_entry.grid(row=4, column=0, padx=10, pady=5, columnspan=2, sticky="ew")
        self.contrasena_entry.bind("<Return>", lambda event: self._intentar_login())  # Vincula la tecla Enter

        ctk.CTkButton(self.ventana, text="Iniciar Sesión", width=30, command=self._intentar_login).grid(row=5, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.ventana, text="Cancelar", command=self._cancelar, width=30, height=28, fg_color="red", hover_color="darkred").grid(row=5, column=0, padx=10, pady=10, sticky="w")

    def _intentar_login(self):
        usuario = self.usuario_entry.get()
        contrasena = self.contrasena_entry.get()

        if self.gestor_usuarios.iniciar_sesion(usuario, contrasena):
            messagebox.showinfo("Éxito", "Sesión iniciada correctamente.")
            self.ventana.destroy()  # Cerrar ventana de inicio de sesión
            self._abrir_index()  # Abrir ventana principal
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")

    def _cancelar(self):
        # Cierra la ventana actual
        self.ventana.destroy()

    def _abrir_index(self):
        # Abre la ventana principal (index)
        app_index = Index(self.gestor_usuarios.obtener_sesion())
        app_index.iniciar()

if __name__ == "__main__":
    app = VentanaSesion()
    app.iniciar()
