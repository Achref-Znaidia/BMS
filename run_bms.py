import flet as ft
from src.ui.main_app import BMSApp


def main(page: ft.Page):
    app = BMSApp()
    app.main(page)


if __name__ == "__main__":
    # Launch the Flet app using our themed BMSApp
    ft.app(target=main)
