import customtkinter as ctk
import datetime
from aplicacion.compras.conferencia import OrderPdfApp
from aplicacion.conectiondb.conexion import DBConnection
from aplicacion.cargamentos.cargamentos import ModuloCargamentos
from aplicacion.cargamentos.ver_cargamentos import ModuloVerCargamentos
from aplicacion.cargamentos.entregas import ModuloEntregas
from aplicacion.cargamentos.regiones import ModuloRegionesCiudades
from aplicacion.cargamentos.choferes import ModuloChoferes
from aplicacion.cargamentos.vehiculos import ModuloVehiculos
from aplicacion.cargamentos.recoleccion import ModuloRecoleccion
from aplicacion.cargamentos.Reporte_de_cargas import ReporteDeCargas
from aplicacion.cargamentos.generador_de_carga import ExportadorDePedidos
#from aplicacion.cargamentos.preparacion_carga import ModuloReporteCargas
from aplicacion.rebotes_y_devoluciones.rebotes_y_devoluciones import ModuloRebotesDevoluciones
from aplicacion.rebotes_y_devoluciones.ver_rebotes_y_devoluciones import ModuloVerRebotesYDevoluciones
from aplicacion.rebotes_y_devoluciones.tipo_1 import ModuloTipo1
from aplicacion.rebotes_y_devoluciones.tipo_2 import ModuloTipo2
from aplicacion.rebotes_y_devoluciones.tipo_3 import ModuloTipo3
from aplicacion.rebotes_y_devoluciones.tipo_4 import ModuloTipo4
from aplicacion.comercial.carteras import ModuloCarteras
from aplicacion.comercial.pedidos_con_imagenes import orderPDFGenerator
from aplicacion.usuarios.administrar_usuarios import ModuloUsuarios
from aplicacion.usuarios.administrar_permisos import ModuloAdministracion
from aplicacion.usuarios.administrar_grupos import ModuloGruposUsuarios


class Index:
    def __init__(self, sesion_usuario):
        """
        Inicializa la ventana principal del sistema.
        :param sesion_usuario: Diccionario con los datos de la sesión activa.
        """
        self.sesion_usuario = sesion_usuario
        self.ventana = ctk.CTk()
        self.ventana.title("Sistema de Gestión - Hecaton 2.0")
        self.ventana.geometry("800x600")

        # Frame principal para contener el sidebar y el área de contenido
        self.frame_principal = ctk.CTkFrame(self.ventana)
        self.frame_principal.pack(expand=True, fill="both")

        # Sidebar
        self.sidebar = ctk.CTkScrollableFrame(self.frame_principal, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        # Área principal con topbar
        self.area_principal = ctk.CTkFrame(self.frame_principal)
        self.area_principal.pack(side="right", expand=True, fill="both")

        self.topbar = ctk.CTkFrame(self.area_principal, height=30, corner_radius=0)
        self.topbar.pack(side="top", fill="x")

        self.workspace = ctk.CTkFrame(self.area_principal)
        self.workspace.pack(expand=True, fill="both")

        # Footer
        self.footer = ctk.CTkFrame(self.ventana, height=30, corner_radius=0)
        self.footer.pack(side="bottom", fill="x")

        self.fecha_inicio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Diccionario para rastrear pestañas abiertas
        self.pestañas_abiertas = {}

    def iniciar(self):
        """Inicia la ventana principal."""
        self._crear_sidebar()
        self._crear_footer()
        self.ventana.mainloop()

    def _crear_sidebar(self):
        """Crea dinámicamente el sidebar con sub-sistemas y aplicaciones."""
        ctk.CTkLabel(
            self.sidebar,
            text="Sub-Sistemas",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        db = DBConnection()
        conexion = db.connect_mysql()
        cursor = conexion.cursor()
        cursor.execute("""
                        SELECT 
                            s2.nombre AS sistema,
                            s.nombre AS subsistema
                        FROM usuarios u 
                        LEFT JOIN grupo_usuario gu ON gu.id = u.nivel_acceso
                        LEFT JOIN permisos p ON p.grupo = gu.id
                        LEFT JOIN subsistemas s ON s.id = p.subsistema
                        LEFT JOIN sistemas s2 ON s2.id = s.sistema
                        WHERE p.activo = 'S' and u.id = %s
                        order by s2.id""", (self.sesion_usuario["id"],)
                        )
        
        resultados = cursor.fetchall()
        subsistemas = {}
        
        for sistema, subsistema in resultados:
            if sistema not in subsistemas:
                subsistemas[sistema] = []  # Crear una lista para subsistemas
            subsistemas[sistema].append(subsistema)
        
        cursor.close()

        for subsistema, apps in subsistemas.items():
            # Contenedor para cada subsistema
            subsistema_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            subsistema_container.pack(fill="x", padx=5, pady=5)

            # Botón para el sub-sistema
            subsistema_btn = ctk.CTkButton(
                subsistema_container,
                text=subsistema.upper(),
                fg_color="transparent",
                text_color="white",
                hover_color="gray",
                anchor="w",
                command=lambda s=subsistema: self._toggle_apps(s)
            )
            subsistema_btn.pack(fill="x")

            # Frame oculto para las aplicaciones (submenu)
            apps_frame = ctk.CTkFrame(subsistema_container, fg_color="transparent")
            apps_frame.pack(fill="x", padx=15, pady=2)
            apps_frame.pack_forget()  # Colapsado por defecto

            setattr(self, f"frame_{subsistema}", apps_frame)

            # Añadir aplicaciones al frame
            for app in apps:
                    app_btn = ctk.CTkButton(
                        apps_frame,
                        text=f"\u00b7 {app}",
                        fg_color="transparent",
                        text_color="white",
                        hover_color="gray",
                        anchor="w",
                        command=lambda n=app: self._abrir_app(n)
                    )
                    app_btn.pack(fill="x", padx=10, pady=2)


    def _toggle_apps(self, subsistema):
        """Muestra u oculta el submenu de un sub-sistema."""
        frame = getattr(self, f"frame_{subsistema}")
        if frame.winfo_ismapped():
            frame.pack_forget()
        else:
            frame.pack(fill="x", padx=15, pady=2)

    def _abrir_app(self, nombre):
        """Abre una pestaña para la aplicación seleccionada."""
        if nombre in self.pestañas_abiertas:
            self._mostrar_tab(nombre)
            return

        # Crear pestaña en la topbar
        tab_frame = ctk.CTkFrame(self.topbar)
        tab_frame.pack(side="left", padx=5, pady=2)

        tab_btn = ctk.CTkButton(
            tab_frame,
            text=nombre,
            fg_color="gray",
            text_color="white",
            hover_color="darkgray",
            command=lambda: self._mostrar_tab(nombre)
        )
        tab_btn.pack(side="left")

        cerrar_btn = ctk.CTkButton(
            tab_frame,
            text="X",
            fg_color="red",
            hover_color="darkred",
            text_color="white",
            width=20,
            command=lambda: self._cerrar_tab(nombre)
        )
        cerrar_btn.pack(side="left")

        # Crear un frame para el contenido de la pestaña
        content_frame = ctk.CTkFrame(self.workspace)
        self.pestañas_abiertas[nombre] = {
            "tab_frame": tab_frame,
            "content_frame": content_frame
        }

        if nombre == "Cargamentos":
            ModuloCargamentos(content_frame, self.sesion_usuario)
        elif nombre == "Ver cargamentos":
            ModuloVerCargamentos(content_frame, self.sesion_usuario)
        elif nombre == "Entregas":
            ModuloEntregas(content_frame,self.sesion_usuario)
        elif nombre == "Vehiculos":
            ModuloVehiculos(content_frame, self.sesion_usuario)
        elif nombre == "Choferes":
            ModuloChoferes(content_frame, self.sesion_usuario)
        elif nombre == "Regiones":
            ModuloRegionesCiudades(content_frame)
        elif nombre == "Reporte de recoleccion":
            ModuloRecoleccion(content_frame)
        elif nombre == "Reporte de cargas":
            ReporteDeCargas(content_frame)
        elif nombre == "Rebotes y devoluciones":
            ModuloRebotesDevoluciones(content_frame, self.sesion_usuario)
        elif nombre == "Ver rebotes y devoluciones":
            ModuloVerRebotesYDevoluciones(content_frame, self.sesion_usuario)
        elif nombre == "Tipo 1":
            ModuloTipo1(content_frame)
        elif nombre == "Tipo 2":
            ModuloTipo2(content_frame)
        elif nombre == "Tipo 3":
            ModuloTipo3(content_frame)
        elif nombre == "Tipo 4":
            ModuloTipo4(content_frame)
        elif nombre == "Carteras":
           ModuloCarteras(content_frame,self.sesion_usuario)
        elif nombre == "Pedidos con imagenes":
            orderPDFGenerator(content_frame, self.sesion_usuario)
        elif nombre == "Usuarios":
            ModuloUsuarios(content_frame)
        elif nombre == "Permisos":
            ModuloAdministracion(content_frame, self.sesion_usuario)
        elif nombre == "Grupos":
            ModuloGruposUsuarios(content_frame)
        elif nombre == "Conferencia de Compras":
            OrderPdfApp(content_frame, self.sesion_usuario)
        elif nombre == "Generador de cargas":
            ExportadorDePedidos(content_frame)
        else:
            ctk.CTkLabel(
                content_frame,
                text=f"Área de trabajo para: {nombre}",
                font=("Arial", 16, "bold")
            ).pack(pady=20)

        self._mostrar_tab(nombre)

    def _mostrar_tab(self, nombre):
        """Muestra el contenido de la pestaña seleccionada."""
        for elementos in self.pestañas_abiertas.values():
            elementos["content_frame"].pack_forget()

        if nombre in self.pestañas_abiertas:
            self.pestañas_abiertas[nombre]["content_frame"].pack(fill="both", expand=True)

    def _cerrar_tab(self, nombre):
        """Cierra la pestaña seleccionada."""
        if nombre in self.pestañas_abiertas:
            # Destruir contenido y botones asociados
            self.pestañas_abiertas[nombre]["content_frame"].destroy()
            self.pestañas_abiertas[nombre]["tab_frame"].destroy()
            del self.pestañas_abiertas[nombre]

    def _crear_footer(self):
        """Crea el footer con información del usuario y fecha/hora de inicio."""
        footer_label = ctk.CTkLabel(
            self.footer,
            text=f"Bienvenido, {self.sesion_usuario['nombre']} {self.sesion_usuario['apellido']} | Fecha/Hora de inicio: {self.fecha_inicio}",
            font=("Arial", 10),
            anchor="w"  # Alinea el texto a la izquierda
        )
        footer_label.pack(side="left", fill="both", padx=10)

    def _cerrar_sesion(self):
        """Cierra la ventana principal y finaliza la sesión."""
        self.ventana.destroy()
        print("Sesión cerrada.")