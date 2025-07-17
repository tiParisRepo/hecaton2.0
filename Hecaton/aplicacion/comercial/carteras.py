# -*- coding: utf-8 -*-
"""
ModuloCarteras – carteras y asignación de empresas.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from turtle import right
import customtkinter as ctk
from typing import Any, List, Optional

from numpy import row_stack

try:
    from aplicacion.conectiondb.conexion import DBConnection         # type: ignore
except ImportError:                                                  # demo sin BD
    DBConnection = None


class ModuloCarteras:
    COLS_CARTERAS = ("ID", "Nombre", "VendedorID", "Vendedor")
    COLS_EMPRESAS = ("ID", "Nombre", "Ciudad")

    def __init__(self, master: tk.Widget, sesion_usuario: dict[str, Any]):
        self.master = master
        self.sesion_usuario = sesion_usuario
        self.db = DBConnection() if DBConnection else None

        self.frame_principal = ctk.CTkFrame(master)
        self.frame_principal.pack(expand=True, fill="both")

        self._estilos()
        self._ui()

    # ---------- estilos ----------
    def _estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background="#2b2b2b",
            foreground="#E9F0ED",
            rowheight=25,
            fieldbackground="#333333",
            font=("Arial", 12),
        )
        style.map("Custom.Treeview", background=[("selected", "#144870")])
        style.configure(
            "Custom.Treeview.Heading",
            background="#1F6AA5",
            foreground="#E9F0ED",
            font=("Arial", 13, "bold"),
            relief="flat",
        )
        style.map("Custom.Treeview.Heading", background=[("active", "#1F6AA5")])

    # ---------- interfaz ----------
    def _ui(self):
        self.tabview = ctk.CTkTabview(self.frame_principal)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        self.tab_carteras = self.tabview.add("Carteras")
        self.tab_empresas = self.tabview.add("Empresas")

        self._tab_carteras()
        self._tab_empresas()

    # ========== TAB CARTERAS ==========
    def _tab_carteras(self):
        frame = ctk.CTkFrame(self.tab_carteras)
        frame.pack(expand=True, fill="both")

        ctk.CTkLabel(frame, text="Carteras", font=("Arial", 14, "bold")).pack(pady=(10, 0))

        self.tree_carteras = ttk.Treeview(
            frame, style="Custom.Treeview", columns=self.COLS_CARTERAS, show="headings"
        )
        self.tree_carteras.pack(expand=True, fill="both", padx=10, pady=10)

        for col, txt, w in zip(
            self.COLS_CARTERAS, ("ID", "Nombre", "ID Vendedor", "Vendedor"), (70, 220, 100, 200)
        ):
            self.tree_carteras.heading(col, text=txt)
            self.tree_carteras.column(col, width=w, anchor="center")

        self.tree_carteras.bind("<Double-1>", self._modal_editar_cartera)
        self._llenar_treeview_carteras()

    def _llenar_treeview_carteras(self):
        self.tree_carteras.delete(*self.tree_carteras.get_children())
        if not self.db:
            return
        try:
            conn = self.db.connect_mysql()
            cur = conn.cursor()
            cur.execute(
                """SELECT c.id, c.nombre, u.identify, u.usuario
                   FROM carteras c
                   LEFT JOIN usuarios u ON u.identify = c.vendedor"""
            )
            for row in cur.fetchall():
                self.tree_carteras.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar carteras: {e}")

    def _modal_editar_cartera(self, *_):
        item = self.tree_carteras.focus()
        if item:
            EditarCarteraModal(
                self.master,
                self.tree_carteras.item(item, "values"),
                self._llenar_treeview_carteras,
                self.db,
            )

    # ========== TAB EMPRESAS ==========
    def _tab_empresas(self):
        c = ctk.CTkFrame(self.tab_empresas)
        c.pack(expand=True, fill="both")
        c.columnconfigure((0, 1, 2), weight=1)
        c.rowconfigure((1, 2), weight=1)

        # lista carteras
        ctk.CTkLabel(c, text="Carteras", font=("Arial", 13, "bold")).grid(row=0, column=0, pady=5)
        self.tv_emp_carteras = ttk.Treeview(
            c, style="Custom.Treeview", columns=("Nombre",), show="headings"
        )
        self.tv_emp_carteras.heading("Nombre", text="Nombre")
        self.tv_emp_carteras.column("Nombre", anchor="w", width=180)
        self.tv_emp_carteras.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(10, 5), pady=5)
        self.tv_emp_carteras.bind("<<TreeviewSelect>>", lambda *_: self._empresas_con())

        # empresas con cartera
        mid = ctk.CTkFrame(c)
        mid.grid(row=1, column=1, sticky="nsew",rowspan=2, padx=5, pady=5)
        mid.rowconfigure(2, weight=1)

        ctk.CTkLabel(mid, text="Empresas en cartera", font=("Arial", 13, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(5, 0)
        )

        self.filt_id = tk.StringVar()
        self.filt_nom = tk.StringVar()
        self.filt_ciudad = tk.StringVar()
        self._filtros(mid, self.filt_id, self.filt_nom, self.filt_ciudad, self._empresas_con)

        self.tv_emp_con = ttk.Treeview(mid, style="Custom.Treeview", columns=self.COLS_EMPRESAS, show="headings")
        for col in self.COLS_EMPRESAS:
            self.tv_emp_con.heading(col, text=col)
            self.tv_emp_con.column(col, anchor="center", width=120)
        self.tv_emp_con.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=5)

        # filtros + empresas sin cartera
                # empresas con cartera
        right = ctk.CTkFrame(c)
        right.grid(row=1, column=3, sticky="nsew",rowspan=2, padx=5, pady=5)
        right.rowconfigure(2, weight=1)

        ctk.CTkLabel(right, text="Sin cartera", font=("Arial", 13, "bold")).grid(row=0, column=2, pady=5)

        self.filt_id_sin = tk.StringVar()
        self.filt_nom_sin = tk.StringVar()
        self.filt_ciudad_sin = tk.StringVar()
        self._filtros(right, self.filt_id_sin, self.filt_nom_sin, self.filt_ciudad_sin, self._empresas_sin, row=1, col=2)

        self.tv_emp_sin = ttk.Treeview(right, style="Custom.Treeview", columns=self.COLS_EMPRESAS, show="headings")
        for col in self.COLS_EMPRESAS:
            self.tv_emp_sin.heading(col, text=col)
            self.tv_emp_sin.column(col, anchor="center", width=120)
        self.tv_emp_sin.grid(row=2, column=2, padx=(5, 10), pady=5)

        # botones flecha
        btnf = ctk.CTkFrame(c)
        btnf.grid(row=1, column=2, sticky="ns", rowspan=2, padx=0, pady=5)
        ctk.CTkButton(btnf, text="<-", width=40, command=self._asignar).pack(side='top', pady=5, padx=5)
        ctk.CTkButton(btnf, text="->", width=40, command=self._quitar).pack(side='top', pady=5, padx=5)

        self._llenar_carteras()
        self._empresas_sin()

    # ---------- filtros helper ----------
    @staticmethod
    def _filtros(parent, var_id, var_nom, var_ciu, callback, *, row=1, col=0):
        f = ctk.CTkFrame(parent)
        f.grid(row=row, column=col, sticky="ew", padx=5, pady=(2, 0))
        f.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        ctk.CTkLabel(f, text="ID").grid(row=0, column=0, padx=2)
        ctk.CTkEntry(f, textvariable=var_id, width=80).grid(row=0, column=1, padx=2)
        ctk.CTkLabel(f, text="Nombre").grid(row=0, column=2, padx=2)
        ctk.CTkEntry(f, textvariable=var_nom, width=120).grid(row=0, column=3, padx=2)
        ctk.CTkLabel(f, text="Ciudad").grid(row=0, column=4, padx=2)
        ctk.CTkEntry(f, textvariable=var_ciu, width=120).grid(row=0, column=5, padx=2)
        for v in (var_id, var_nom, var_ciu):
            v.trace_add("write", lambda *_: callback())

    # ---------- cargar listas ----------
    def _llenar_carteras(self):
        self.tv_emp_carteras.delete(*self.tv_emp_carteras.get_children())
        try:
            conn = self.db.connect_mysql()
            cur = conn.cursor()
            cur.execute("SELECT nombre FROM carteras")
            for (nombre,) in cur.fetchall():
                self.tv_emp_carteras.insert("", "end", values=(nombre,))
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar carteras: {e}")

    def _empresas_con(self):
        self.tv_emp_con.delete(*self.tv_emp_con.get_children())
        sel = self.tv_emp_carteras.focus()
        if not sel:
            return
        cartera = self.tv_emp_carteras.item(sel, "values")[0]
        f = (
            self.filt_id.get().strip(),
            self.filt_nom.get().strip(),
            self.filt_ciudad.get().strip(),
        )
        try:
            conn = self.db.connect_mysql()
            cur = conn.cursor()
            sql = """SELECT id, nombre, ciudad
                     FROM empresas
                     WHERE activo='S' AND cancelado IS NULL AND cartera=%s
                     AND id     LIKE %s
                     AND nombre LIKE %s
                     AND ciudad LIKE %s"""
            cur.execute(sql, (cartera, f"%{f[0]}%", f"%{f[1]}%", f"%{f[2]}%"))
            for row in cur.fetchall():
                self.tv_emp_con.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar empresas: {e}")

    def _empresas_sin(self):
        self.tv_emp_sin.delete(*self.tv_emp_sin.get_children())
        f = (
            self.filt_id_sin.get().strip(),
            self.filt_nom_sin.get().strip(),
            self.filt_ciudad_sin.get().strip(),
        )
        try:
            conn = self.db.connect_mysql()
            cur = conn.cursor()
            sql = """SELECT id, nombre, ciudad
                     FROM empresas
                     WHERE (cartera IS NULL OR cartera='') AND activo='S' AND cancelado IS NULL
                     AND id     LIKE %s
                     AND nombre LIKE %s
                     AND ciudad LIKE %s"""
            cur.execute(sql, (f"%{f[0]}%", f"%{f[1]}%", f"%{f[2]}%"))
            for row in cur.fetchall():
                self.tv_emp_sin.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar empresas sin cartera: {e}")

    # ---------- asignar / quitar ----------
    def _asignar(self):
        sel_cart = self.tv_emp_carteras.focus()
        if not sel_cart:
            messagebox.showwarning("", "Seleccione una cartera")
            return
        cartera = self.tv_emp_carteras.item(sel_cart, "values")[0]
        ids = [self.tv_emp_sin.item(i, "values")[0] for i in self.tv_emp_sin.selection()]
        self._actualizar(ids, cartera)

    def _quitar(self):
        ids = [self.tv_emp_con.item(i, "values")[0] for i in self.tv_emp_con.selection()]
        self._actualizar(ids, None)

    # ---------- actualizar BD ----------
    def _actualizar(self, ids: List[str], cartera: Optional[str]):
        if not ids:
            return
        try:
            mysql = self.db.connect_mysql()
            cur_m = mysql.cursor()
            if cartera is None:
                cur_m.execute(
                    "UPDATE empresas SET cartera=NULL WHERE id IN (%s)" % ",".join(["%s"] * len(ids)),
                    ids,
                )
            else:
                cur_m.execute(
                    "UPDATE empresas SET cartera=%s WHERE id IN (%s)"
                    % ("%s", ",".join(["%s"] * len(ids))),
                    [cartera] + ids,
                )
            mysql.commit()

            fb = self.db.connect_firebird()
            cur_f = fb.cursor()
            if cartera is None:
                cur_f.execute(
                    "UPDATE EMPRESAS SET PROFISSAO=NULL WHERE CODIGO IN (%s)" % ",".join(["?"] * len(ids)),
                    ids,
                )
            else:
                cur_f.execute(
                    "UPDATE EMPRESAS SET PROFISSAO=? WHERE CODIGO IN (%s)"
                    % ",".join(["?"] * len(ids)),
                    [cartera] + ids,
                )
            fb.commit()

            messagebox.showinfo("Éxito", "Actualización completa")
            self._empresas_con()
            self._empresas_sin()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar: {e}")


# ========= modales =========
class EditarCarteraModal(ctk.CTkToplevel):
    def __init__(self, master, datos, on_saved, db):
        super().__init__(master)
        self.title("Editar cartera")
        self.geometry("420x260")
        self.transient(master)
        self.grab_set()

        self.db = db
        self.on_saved = on_saved
        self.cartera_id, nombre, vendedor_id, vendedor_nom = datos

        self.var_nombre = tk.StringVar(value=nombre)
        self.var_vid = tk.StringVar(value=vendedor_id or "")
        self.var_vnom = tk.StringVar(value=vendedor_nom or "")

        self.columnconfigure(1, weight=1)
        pad = {"padx": 10, "pady": 5, "sticky": "ew"}

        ctk.CTkLabel(self, text="Nombre").grid(row=0, column=0, **pad)
        ctk.CTkEntry(self, textvariable=self.var_nombre).grid(row=0, column=1, **pad)

        ctk.CTkLabel(self, text="ID vendedor").grid(row=1, column=0, **pad)
        ctk.CTkEntry(self, textvariable=self.var_vid).grid(row=1, column=1, **pad)

        ctk.CTkLabel(self, text="Nombre vendedor").grid(row=2, column=0, **pad)
        ctk.CTkEntry(self, textvariable=self.var_vnom).grid(row=2, column=1, **pad)

        ctk.CTkButton(self, text="Seleccionar…", command=self._selector).grid(
            row=3, column=1, sticky="e", padx=10
        )

        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.grid(row=4, column=0, columnspan=2, pady=10)
        ctk.CTkButton(bf, text="Guardar", command=self._guardar).pack(side="right", padx=5)
        ctk.CTkButton(bf, text="Cancelar", command=self.destroy).pack(side="right", padx=5)

    def _selector(self):
        SelectorVendedorModal(self, lambda vid, vnom: (self.var_vid.set(vid), self.var_vnom.set(vnom)), self.db)

    def _guardar(self):
        nombre = self.var_nombre.get().strip()
        vid = self.var_vid.get().strip()
        if not nombre or not vid:
            messagebox.showwarning("", "Datos obligatorios")
            return
        try:
            mysql = self.db.connect_mysql()
            with mysql.cursor() as cur:
                cur.execute("UPDATE carteras SET nombre=%s, vendedor=%s WHERE id=%s", (nombre, vid, self.cartera_id))
            mysql.commit()

            fb = self.db.connect_firebird()
            fb.cursor().execute("UPDATE EMPRESAS SET PROFISSAO=?, VENDEDOR=? WHERE PROFISSAO=?", (nombre, vid, self.var_nombre.get()))
            fb.commit()

            messagebox.showinfo("Éxito", "Cartera actualizada")
            self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")


class SelectorVendedorModal(ctk.CTkToplevel):
    def __init__(self, master, callback, db):
        super().__init__(master)
        self.title("Seleccionar vendedor")
        self.geometry("360x420")
        self.transient(master)
        self.grab_set()

        self.callback = callback
        self.db = db

        self.var_filter = tk.StringVar()
        ctk.CTkEntry(self, textvariable=self.var_filter, placeholder_text="Filtrar…").pack(
            fill="x", padx=10, pady=(10, 0)
        )
        self.var_filter.trace_add("write", lambda *_: self._cargar())

        self.tree = ttk.Treeview(self, style="Custom.Treeview", columns=("ID", "Nombre"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.column("ID", width=70, anchor="center")
        self.tree.column("Nombre", width=220, anchor="w")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)
        self.tree.bind("<Double-1>", self._sel)

        self._cargar()

    def _cargar(self):
        term = self.var_filter.get().strip()
        self.tree.delete(*self.tree.get_children())
        try:
            conn = self.db.connect_mysql()
            cur = conn.cursor()
            sql = "SELECT identify, usuario FROM usuarios"
            params = None
            if term:
                sql += " WHERE usuario LIKE %s OR identify LIKE %s"
                params = (f"%{term}%", f"%{term}%")
            cur.execute(sql, params)
            for uid, uname in cur.fetchall():
                self.tree.insert("", "end", values=(uid, uname))
            conn.close()
        except Exception:
            pass

    def _sel(self, *_):
        item = self.tree.focus()
        if item:
            vid, vnom = self.tree.item(item, "values")
            self.callback(vid, vnom)
            self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.geometry("1200x650")
    ModuloCarteras(root, sesion_usuario={"id": 1})
    root.mainloop()
