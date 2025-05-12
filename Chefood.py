import reflex as rx
import sqlite3
import os
import json
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

# ------------------------ CARGAR RECETAS DESDE JSON ------------------------

def cargar_recetas_desde_json():
    with open("recetas.json", "r", encoding="utf-8") as file:
        return json.load(file)

RECETAS_JSON = cargar_recetas_desde_json()

# ------------------------ BACKTRACKING PARA GENERAR RECETAS ------------------------

def normalizar(ingrediente):
    return unidecode(ingrediente.strip().lower())

def generar_recetas_backtracking(ingredientes_usuario, recetas, combinacion_actual, indice, resultados):
    # Caso base: si hemos procesado todas las recetas
    if indice == len(recetas):
        return

    receta = recetas[indice]
    ingredientes_receta = set(normalizar(i) for i in receta["ingredientes"])
    ingredientes_usuario_set = set(ingredientes_usuario)

    # Calcular los ingredientes faltantes
    faltantes = list(ingredientes_receta - ingredientes_usuario_set)

    # Permitir la receta si faltan 0, 1 o 2 ingredientes
    if len(faltantes) <= 2:
        receta_con_faltantes = receta.copy()
        receta_con_faltantes["faltantes"] = faltantes
        resultados.append(receta_con_faltantes)

    # Continuar con la siguiente receta
    generar_recetas_backtracking(ingredientes_usuario, recetas, combinacion_actual, indice + 1, resultados)

def buscar_combinaciones_recetas(ingredientes_usuario):
    recetas = RECETAS_JSON
    ingredientes_usuario = [normalizar(i) for i in ingredientes_usuario if i.strip()]
    resultados = []
    generar_recetas_backtracking(ingredientes_usuario, recetas, [], 0, resultados)
    print("Recetas generadas:", resultados)  # Depuración
    return resultados

# ------------------------ ESTADO ------------------------

class Estado(rx.State):
    ingredientes: list[str] = [""] * 5
    recetas_generadas: list[dict] = []  # Se define el tipo explícitamente como lista de diccionarios

    def set_ingrediente(self, valor: str, index: int):
        self.ingredientes[index] = valor

    def agregar_campo(self):
        self.ingredientes.append("")

    def enviar_recetas(self):
        lista = [normalizar(i) for i in self.ingredientes if i.strip()]
        self.recetas_generadas = buscar_combinaciones_recetas(lista)
        print("Estado.recetas_generadas:", self.recetas_generadas)  # Depuración

    def ir_a_recetas(self):
        return rx.redirect("/recetas")

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
        rx.button("Enviar", on_click=[Estado.enviar_recetas, Estado.ir_a_recetas], color_scheme="green"),
        spacing="4",
        padding="2em"
    )

def recetas():
    return rx.center(
        rx.vstack(
            rx.heading("Recetas generadas"),
            rx.foreach(
                Estado.recetas_generadas,
                lambda receta: rx.vstack(
                    rx.heading(receta.get("nombre", "Receta sin nombre")),
                    rx.text(
                        ", ".join(receta.get("ingredientes", [])) if isinstance(receta.get("ingredientes", []), list) else "Ingredientes no disponibles",
                        font_size="1em"
                    ),
                    rx.cond(
                        receta.get("faltantes") is not None,
                        rx.text(
                            f"Faltantes: {', '.join(receta.get('faltantes', [])) if isinstance(receta.get('faltantes', []), list) else 'No disponible'}",
                            font_size="0.9em",
                            color="red"
                        )
                    ),
                    rx.image(src=receta.get("imagen", ""), width="300px"),
                    spacing="2"
                )
            ),
            rx.button("Volver", on_click=lambda: rx.redirect("/")),
            spacing="4",
        ),
        padding="3em"
    )

# ------------------------ APP ------------------------

app = rx.App()
app.add_page(index, route="/")
app.add_page(recetas, route="/recetas")