"""
Bienvenido a tu IDE de DuckDB potenciado por Reflex.
"""
import reflex as rx
import pandas as pd
import duckdb
from typing import List, Dict, Any, Tuple
import os

# --- Estilos para la UI ---
# Se emula la paleta de colores y el layout de la UI de DuckDB.
SIDEBAR_STYLE = {
    "width": "300px",
    "padding": "1.5em", # Aumentado para mejor aspecto visual
    "background_color": "#f8f9fa",
    "border_right": "1px solid #dee2e6",
    "height": "100vh",
    "overflow_y": "auto",
}

MAIN_CONTENT_STYLE = {
    "padding": "2em",
    "width": "100%",
    "height": "100vh",
    "overflow_y": "auto",
}

TEXT_AREA_STYLE = {
    "height": "40vh",
    "width": "100%",
    "font_family": "monospace",
    "font_size": "14px",
    "border": "1px solid #ced4da",
    "border_radius": "6px",
    "padding": "1em",
    "margin_bottom": "1em",
}

# --- Estado de la Aplicación ---
# Aquí se maneja la lógica y los datos de la aplicación.
class AppState(rx.State):
    """
    El estado principal de la aplicación.
    Maneja la consulta SQL, la ejecución y los resultados.
    """
    # La consulta SQL que el usuario escribe en el editor.
    sql_query: str = "SELECT '¡Bienvenido!' AS Mensaje;"
    
    # Los datos del resultado de la consulta.
    result_df: pd.DataFrame = pd.DataFrame()
    
    # Indicador de carga para mostrar mientras se ejecuta la consulta.
    is_loading: bool = False

    # Mensajes de error para mostrar al usuario.
    error_message: str = ""

    # Ruta actual del explorador de archivos.
    current_path: str = "."

    # Variable para forzar la actualización del explorador de archivos.
    refresh_trigger: int = 0

    @rx.var
    def directory_contents(self) -> List[Tuple[str, bool]]:
        """
        Devuelve una lista de tuplas (nombre, es_directorio) para la ruta actual.
        """
        # Esta dependencia asegura que la variable computada se recalcule cuando refresh_trigger cambie.
        _ = self.refresh_trigger 
        try:
            items = []
            for item in sorted(os.listdir(self.current_path)):
                # Ignora archivos ocultos
                if item.startswith('.'):
                    continue
                full_path = os.path.join(self.current_path, item)
                is_dir = os.path.isdir(full_path)
                items.append((item, is_dir))
            # Ordena para que las carpetas aparezcan primero
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            return items
        except FileNotFoundError:
            self.current_path = "."
            return []

    def refresh_file_list(self):
        """
        Incrementa el trigger para forzar la actualización de la lista de archivos.
        """
        self.refresh_trigger += 1

    def change_directory(self, dir_name: str):
        """
        Cambia el directorio actual del explorador de archivos.
        """
        if dir_name == "..":
            # Sube un nivel en el directorio
            self.current_path = os.path.dirname(self.current_path)
        else:
            # Entra a un subdirectorio
            self.current_path = os.path.join(self.current_path, dir_name)

    def copy_to_clipboard(self, file_name: str):
        """
        Copia la ruta relativa del archivo al portapapeles.
        """
        full_path = os.path.join(self.current_path, file_name)
        return rx.set_clipboard(full_path)

    def run_query(self):
        """
        Ejecuta la consulta SQL usando DuckDB y actualiza el estado con los resultados.
        """
        self.is_loading = True
        self.error_message = ""
        self.result_df = pd.DataFrame() # Limpia resultados anteriores
        try:
            con = duckdb.connect(database=':memory:')
            self.result_df = con.execute(self.sql_query).fetchdf()
            con.close()
        except Exception as e:
            self.error_message = f"Error al ejecutar la consulta: {e}"
            
        self.is_loading = False

# --- Componentes de la UI ---
# Aquí se definen las piezas visuales de la aplicación.
def file_explorer_item(item: rx.Var[Tuple[str, bool]]) -> rx.Component:
    """
    Renderiza una fila para un archivo o carpeta en el explorador.
    """
    # *** CORRECCIÓN AQUÍ ***
    # Se accede a los elementos de la tupla Var usando índices.
    name = item[0]
    is_dir = item[1]
    
    return rx.cond(
        is_dir,
        rx.button(
            rx.hstack(
                rx.icon("folder", size=16),
                rx.text(name, size="2"),
                spacing="2",
                align="center",
            ),
            on_click=lambda: AppState.change_directory(name),
            variant="ghost",
            width="100%",
            justify_content="start",
        ),
        rx.hstack(
            rx.icon("file", size=16),
            rx.text(name, size="2", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
            rx.spacer(),
            rx.icon_button(
                rx.icon("copy", size=16),
                on_click=lambda: AppState.copy_to_clipboard(name),
                variant="ghost",
                size="1",
            ),
            spacing="2",
            width="100%",
            align="center",
        )
    )


def sidebar() -> rx.Component:
    """
    La barra lateral de la aplicación con el explorador de archivos mejorado.
    """
    return rx.box(
        rx.vstack(
            rx.heading("DuckDB IDE", size="6"),
            rx.divider(),
            rx.hstack(
                rx.heading("Explorador", size="4"),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("refresh-cw", size=16),
                    on_click=AppState.refresh_file_list,
                    variant="ghost",
                    size="1",
                ),
                width="100%",
                align="center",
                margin_top="1em",
            ),
            rx.text(AppState.current_path, size="1", color_scheme="gray"),
            rx.vstack(
                rx.cond(
                    AppState.current_path != ".",
                    rx.button(
                        rx.hstack(
                            rx.icon("arrow-up", size=16),
                            rx.text("..", size="2"),
                            spacing="2",
                            align="center",
                        ),
                        on_click=lambda: AppState.change_directory(".."),
                        variant="ghost",
                        width="100%",
                        justify_content="start",
                    )
                ),
                rx.foreach(AppState.directory_contents, file_explorer_item),
                spacing="1",
                width="100%",
                align_items="left",
                margin_top="0.5em",
            ),
        ), 
        style=SIDEBAR_STYLE,
    )

def main_content() -> rx.Component:
    """
    El área principal donde el usuario escribirá y verá los resultados de las consultas.
    """
    return rx.box(
        rx.heading("Celda de Código SQL", size="5"),
        rx.text_area(
            value=AppState.sql_query,
            on_change=AppState.set_sql_query,
            style=TEXT_AREA_STYLE,
            placeholder="Escribe tu consulta SQL aquí...",
        ),
        rx.button(
            "Ejecutar Consulta",
            on_click=AppState.run_query,
            is_loading=AppState.is_loading,
            size="3",
            variant="solid",
        ),
        rx.divider(margin_y="2em"),
        rx.heading("Resultados", size="5"),
        rx.cond(
            AppState.error_message,
            rx.callout(
                AppState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                role="alert",
                width="100%",
            )
        ),
        rx.data_table(
            data=AppState.result_df,
            pagination=True,
            search=True,
            sort=True,
            resizable=True,
        ),
        style=MAIN_CONTENT_STYLE
    )

def index() -> rx.Component:
    """
    La página principal de la aplicación.
    """
    return rx.flex(
        sidebar(),
        main_content(),
        direction="row",
        width="100%",
    )

app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="blue",
    )
)

app.add_page(index)
