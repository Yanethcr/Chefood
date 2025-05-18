import reflex as rx
import os
import json
from unidecode import unidecode

# ------------------------ CARGAR RECETAS ------------------------

def cargar_recetas_desde_json():
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_json = os.path.join(directorio_actual, "recetas.json")
        print(f"Buscando recetas.json en: {ruta_json}")
        
        with open(ruta_json, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error cargando recetas: {e}")
        return []

# Cargar recetas una sola vez al inicio
RECETAS_JSON = cargar_recetas_desde_json()

# ------------------------ FUNCIONES DE BÚSQUEDA POR BACKTRACKING ------------------------

def normalizar(ingrediente):
    """Normaliza un ingrediente para comparaciones (quita acentos, minúsculas)."""
    if not ingrediente:
        return ""
    return unidecode(ingrediente.strip().lower())

def generar_recetas_backtracking(ingredientes_usuario):
    """Busca recetas usando backtracking simplificado."""
    resultados = []
    
    # Normalizar los ingredientes del usuario
    ingr_usuario_normalizados = [normalizar(i) for i in ingredientes_usuario if i.strip()]
    ingr_usuario_set = set(ingr_usuario_normalizados)
    
    # Para cada receta, verificar coincidencias
    for receta in RECETAS_JSON:
        # Normalizar los ingredientes de la receta
        ingr_receta_normalizados = [normalizar(i) for i in receta["ingredientes"]]
        ingr_receta_set = set(ingr_receta_normalizados)
        
        # Calcular faltantes
        faltantes = list(ingr_receta_set - ingr_usuario_set)
        
        # Permitir la receta si faltan 0, 1 o 2 ingredientes
        if len(faltantes) <= 2:
            # Crear una versión plana para el estado (evita objetos anidados)
            resultados.append({
                "nombre": receta["nombre"],
                "ingredientes_texto": ", ".join(receta["ingredientes"]),
                "ingredientes_lista": receta["ingredientes"],
                "preparacion": receta["preparacion"],
                "faltantes_texto": ", ".join(faltantes) if faltantes else "Ninguno",
                "color_faltantes": "green" if not faltantes else "red",  # Poner el color directamente aquí
                "imagen": receta.get("imagen", "")
            })
    
    return resultados

# ------------------------ ESTADO ------------------------

class Estado(rx.State):
    # Variables simples (evitamos estructuras anidadas complejas)
    ingredientes: list[str] = ["", "", "", "", ""]
    recetas_encontradas: list[dict] = []
    
    # Variables para la receta seleccionada (aplanadas)
    receta_nombre: str = ""
    receta_ingredientes: list[str] = []
    receta_preparacion: list[str] = []
    receta_faltantes: str = ""
    receta_color_faltantes: str = "red"  # Valor por defecto
    receta_imagen: str = ""
    
    # Contador para identificar cambios
    total_recetas: int = 0
    
    def set_ingrediente(self, valor: str, index: int):
        """Actualiza un ingrediente en la posición especificada."""
        self.ingredientes[index] = valor
    
    def agregar_campo(self):
        """Agrega un nuevo campo de ingrediente."""
        self.ingredientes.append("")
    
    def buscar_recetas(self):
        """Busca recetas usando el algoritmo de backtracking."""
        # Filtrar ingredientes no vacíos
        ingredientes_validos = [i for i in self.ingredientes if i.strip()]
        
        # Buscar recetas usando backtracking
        resultados = generar_recetas_backtracking(ingredientes_validos)
        
        # Actualizar estado
        self.recetas_encontradas = resultados
        self.total_recetas = len(resultados)
        
        # Redirigir a la página de resultados
        return rx.redirect("/recetas")
    
    def seleccionar_receta(self, indice: int):
        """Selecciona una receta por su índice y guarda sus detalles."""
        if 0 <= indice < len(self.recetas_encontradas):
            receta = self.recetas_encontradas[indice]
            
            # Guardar datos de manera plana (evitando objetos anidados)
            self.receta_nombre = receta["nombre"]
            self.receta_ingredientes = receta["ingredientes_lista"]
            self.receta_preparacion = receta["preparacion"]
            self.receta_faltantes = receta["faltantes_texto"]
            self.receta_color_faltantes = receta["color_faltantes"]
            self.receta_imagen = receta.get("imagen", "")
            
            # Redirigir a la página de detalles
            return rx.redirect("/detalle_receta")

# ------------------------ PÁGINAS ------------------------

def index():
    """Página principal para ingresar ingredientes."""
    return rx.center(
        rx.vstack(
            rx.heading("Chefood - Ingresa tus ingredientes 🍅🥕🧅", size="1"),
            rx.text("Ingresa los ingredientes que tienes disponibles:"),
            
            # Lista de campos de ingredientes
            rx.foreach(
                Estado.ingredientes,
                lambda ingrediente, i: rx.input(
                    placeholder=f"Ingrediente {i + 1}",
                    value=ingrediente,
                    on_change=lambda e, index=i: Estado.set_ingrediente(e, index),
                    width="100%",
                    margin_bottom="0.5em"
                )
            ),
            
            # Botones
            rx.hstack(
                rx.button(
                    "Agregar otro ingrediente", 
                    on_click=Estado.agregar_campo,
                    variant="outline"
                ),
                rx.button(
                    "Buscar recetas", 
                    on_click=Estado.buscar_recetas, 
                    color_scheme="green"
                ),
                width="100%",
                justify="between",
                margin_top="1em"
            ),
            
            width="100%",
            max_width="600px",
            spacing="4",
            padding="2em",
            border="1px solid #eaeaea",
            border_radius="lg",
            box_shadow="lg"
        ),
        padding="3em",
        width="100%"
    )

def recetas():
    """Página que muestra las recetas encontradas."""
    return rx.center(
        rx.vstack(
            rx.heading("Recetas encontradas", size="1"),
            
            # Mensaje informativo
            rx.text(f"Se encontraron {Estado.total_recetas} recetas con tus ingredientes"),
            
            # Lista de recetas
            rx.cond(
                Estado.total_recetas > 0,
                rx.vstack(
                    rx.foreach(
                        Estado.recetas_encontradas,
                        lambda receta, i: rx.box(
                            rx.vstack(
                                rx.heading(receta["nombre"], size="3"),
                                rx.text(f"Ingredientes: {receta['ingredientes_texto']}"),
                                # Ya no usamos condicionales, el color viene predeterminado
                                rx.text(
                                    f"Faltantes: {receta['faltantes_texto']}",
                                    color=receta["color_faltantes"],
                                    font_weight="bold"
                                ),
                                rx.button(
                                    "Ver receta completa",
                                    on_click=Estado.seleccionar_receta(i),
                                    color_scheme="blue",
                                    width="100%"
                                ),
                                width="100%",
                                align_items="start",
                                padding="1em",
                                spacing="3"
                            ),
                            width="100%",
                            border="1px solid #eaeaea",
                            border_radius="md",
                            margin_bottom="1em",
                            overflow="hidden"
                        )
                    ),
                    width="100%"
                ),
                rx.box(
                    rx.text(
                        "No se encontraron recetas con esos ingredientes. Intenta agregar más ingredientes o modificar tu búsqueda.",
                        color="gray",
                        font_style="italic"
                    ),
                    padding="2em",
                    border="1px dashed #eaeaea",
                    border_radius="md",
                    width="100%",
                    text_align="center"
                )
            ),
            
            # Botón para volver
            rx.button(
                "Volver a buscar", 
                on_click=lambda: rx.redirect("/"),
                variant="outline",
                margin_top="1em"
            ),
            
            width="100%",
            max_width="800px",
            spacing="4",
            padding="2em",
            align_items="start"
        ),
        padding="3em",
        width="100%"
    )

def detalle_receta():
    """Página de detalle de una receta seleccionada."""
    return rx.center(
        rx.vstack(
            # Título principal
            rx.heading(Estado.receta_nombre, size="1"),
            
            # Imagen de la receta (nuevo componente)
            rx.cond(
                Estado.receta_imagen != "",
                rx.image(
                    src=Estado.receta_imagen,
                    width="100%",
                    height="300px",
                    object_fit="cover",
                    border_radius="md",
                    margin_bottom="1.5em"
                ),
                rx.box(
                    rx.text("No hay imagen disponible para esta receta", font_style="italic"),
                    padding="1em",
                    background="rgba(0,0,0,0.05)",
                    border_radius="md",
                    width="100%",
                    text_align="center",
                    margin_bottom="1.5em"
                )
            ),
            
            # Sección de ingredientes
            rx.box(
                rx.vstack(
                    rx.heading("Ingredientes", size="3"),
                    rx.foreach(
                        Estado.receta_ingredientes,
                        lambda ingrediente: rx.text(f"• {ingrediente}", text_align="left")
                    ),
                    # Ya no usamos condicionales, el color viene directamente del estado
                    rx.text(
                        f"Ingredientes faltantes: {Estado.receta_faltantes}",
                        color=Estado.receta_color_faltantes,
                        font_weight="bold",
                        margin_top="0.5em"
                    ),
                    width="100%",
                    align_items="start",
                    padding="1.5em",
                    spacing="2"
                ),
                width="100%",
                border="1px solid #eaeaea",
                border_radius="md",
                margin_bottom="1.5em",
                background="rgba(0,0,0,0.01)"
            ),
            
            # Sección de preparación
            rx.box(
                rx.vstack(
                    rx.heading("Preparación", size="3"),
                    rx.foreach(
                        Estado.receta_preparacion,
                        lambda paso, i: rx.hstack(
                            rx.text(f"{i+1}.", font_weight="bold", margin_right="0.5em"),
                            rx.text(paso),
                            width="100%",
                            align_items="start",
                            spacing="2"
                        )
                    ),
                    width="100%",
                    align_items="start",
                    padding="1.5em",
                    spacing="3"
                ),
                width="100%",
                border="1px solid #eaeaea",
                border_radius="md",
                background="rgba(0,0,0,0.01)"
            ),
            
            # Botones de navegación
            rx.hstack(
                rx.button(
                    "Volver a recetas", 
                    on_click=lambda: rx.redirect("/recetas"),
                    variant="outline"
                ),
                rx.button(
                    "Buscar otra receta", 
                    on_click=lambda: rx.redirect("/"),
                    color_scheme="green"
                ),
                rx.button(
                    "Ver backtraking", 
                    #on_click=lambda: rx.redirect("/"),
                    color_scheme="blue"
                ),
                width="100%",
                justify="between",
                margin_top="2em"
            ),
            
            width="100%",
            max_width="800px",
            spacing="4",
            padding="2em",
            align_items="start",
            border="1px solid #eaeaea",
            border_radius="lg",
            box_shadow="lg"
        ),
        padding="3em",
        width="100%"
    )

# ------------------------ CONFIGURACIÓN DE LA APP ------------------------

app = rx.App()
app.add_page(index, route="/")
app.add_page(recetas, route="/recetas")
app.add_page(detalle_receta, route="/detalle_receta")
