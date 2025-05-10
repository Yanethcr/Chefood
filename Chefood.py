import reflex as rx
import sqlite3
import os
import difflib
from unidecode import unidecode

DB_PATH = "chefood.db"

# ------------------------ BASE DE DATOS ------------------------

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS productos (id INTEGER PRIMARY KEY, nombre TEXT)")
        conn.commit()
        conn.close()

init_db()

def insertar_producto(nombre):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO productos (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()

# ------------------------ RECETAS EN MEMORIA ------------------------

RECETAS = [
    {
        "nombre": "Ensalada fresca",
        "ingredientes": ["lechuga", "tomate", "pepino", "aceite", "limon"],
        "instrucciones": "Lava y corta las verduras. Mezcla todo en un bol, agrega aceite y jugo de limón al gusto.",
        "imagen": "https://www.recetasgratis.net/files/receta/8241-ensalada-fresca-facil.jpg"
    },
    {
        "nombre": "Tortilla de papas",
        "ingredientes": ["papas", "huevos", "cebolla", "aceite"],
        "instrucciones": "Fríe las papas y la cebolla en aceite. Bate los huevos y mézclalos con las papas cocidas. Cocina en sartén hasta dorar.",
        "imagen": "https://www.recetasnestle.com.mx/sites/default/files/styles/recipe_detail_desktop/public/srh_recipes/ff232bbc59dd4b30a1788a4f0f56b93e.jpg"
    },
    {
        "nombre": "Panqueques",
        "ingredientes": ["harina", "leche", "huevos", "azucar"],
        "instrucciones": "Mezcla todos los ingredientes hasta tener una masa homogénea. Cocina en una sartén por ambos lados.",
        "imagen": "https://assets.elgourmet.com/wp-content/uploads/2023/01/panqueques-dulces.jpg"
    },
    {
        "nombre": "Guacamole",
        "ingredientes": ["aguacate", "tomate", "cebolla", "limon", "sal"],
        "instrucciones": "Tritura el aguacate y mezcla con los demás ingredientes picados. Ajusta sal y limón al gusto.",
        "imagen": "https://www.pequerecetas.com/wp-content/uploads/2021/07/receta-de-guacamole.jpg"
    }
]

def cargar_recetas():
    return RECETAS

def normalizar(ingrediente):
    return unidecode(ingrediente.strip().lower())

def buscar_receta(ingredientes_usuario):
    recetas = cargar_recetas()
    ingredientes_usuario = [normalizar(i) for i in ingredientes_usuario if i.strip()]
    print("Ingredientes normalizados del usuario:", ingredientes_usuario)

    recetas_normalizadas = []
    for receta in recetas:
        receta_ingredientes = [normalizar(i) for i in receta["ingredientes"]]
        recetas_normalizadas.append((receta, receta_ingredientes))

    # Búsqueda exacta
    for receta, receta_ingredientes in recetas_normalizadas:
        if set(receta_ingredientes).issubset(set(ingredientes_usuario)):
            return receta

    # Búsqueda con 1 ingrediente faltante
    for receta, receta_ingredientes in recetas_normalizadas:
        faltantes = set(receta_ingredientes) - set(ingredientes_usuario)
        if len(faltantes) == 1:
            return {
                "nombre": f"{receta['nombre']} (faltando 1 ingrediente)",
                "ingredientes": receta["ingredientes"],
                "instrucciones": "Falta un ingrediente para ver los pasos completos.",
                "imagen": "https://cdn-icons-png.flaticon.com/512/2748/2748558.png"
            }

    # Búsqueda aproximada
    for receta, receta_ingredientes in recetas_normalizadas:
        coincidencias = 0
        for ingrediente in receta_ingredientes:
            similares = difflib.get_close_matches(ingrediente, ingredientes_usuario, n=1, cutoff=0.8)
            if similares:
                coincidencias += 1
        if coincidencias >= len(receta_ingredientes) - 1:
            return {
                "nombre": f"{receta['nombre']} (coincidencia aproximada)",
                "ingredientes": receta["ingredientes"],
                "instrucciones": receta["instrucciones"],
                "imagen": receta["imagen"]
            }

    return {
        "nombre": "Sin resultados",
        "instrucciones": "No se encontraron recetas con esos ingredientes.",
        "imagen": "https://cdn-icons-png.flaticon.com/512/751/751463.png"
    }

# ------------------------ ESTADO ------------------------

class Estado(rx.State):
    ingredientes: list[str] = [""] * 5
    receta_generada: dict = {}

    def set_ingrediente(self, valor: str, index: int):
        self.ingredientes[index] = valor

    def agregar_campo(self):
        self.ingredientes.append("")

    def enviar_receta(self):
        lista = [normalizar(i) for i in self.ingredientes if i.strip()]
        self.receta_generada = buscar_receta(lista)

    def ir_a_receta(self):
        return rx.redirect("/receta")

# ------------------------ INTERFAZ ------------------------

def index():
    return rx.vstack(
        rx.heading("Chefood - Ingresa tus ingredientes 🍅🥕🧅"),
        rx.foreach(
            Estado.ingredientes,
            lambda ingrediente, i: rx.input(
                placeholder=f"Ingrediente {i + 1}",
                value=ingrediente,
                on_change=lambda e, index=i: Estado.set_ingrediente(e, index),
                width="50%"
            )
        ),
        rx.button("Agregar otro ingrediente", on_click=Estado.agregar_campo),
        rx.button("Enviar", on_click=[Estado.enviar_receta, Estado.ir_a_receta], color_scheme="green"),
        spacing="4",
        padding="2em"
    )

def receta():
    return rx.center(
        rx.vstack(
            rx.heading(Estado.receta_generada.get("nombre", "Receta")),
            rx.image(src=Estado.receta_generada.get("imagen", ""), width="300px"),
            rx.text(Estado.receta_generada.get("instrucciones", ""), font_size="1.2em"),
            rx.button("Volver", on_click=lambda: rx.redirect("/")),
            spacing="4",
        ),
        padding="3em"
    )

# ------------------------ APP ------------------------

app = rx.App()
app.add_page(index, route="/")
app.add_page(receta, route="/receta")
