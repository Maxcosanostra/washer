import flet as ft

from washer.ui_components.sign_up_page import SignUpPage


def main(page: ft.Page):
    page.title = 'User Registration'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.adaptive = True

    SignUpPage(page)


ft.app(target=main)
