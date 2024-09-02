import flet as ft

from washer.ui_components.pages import SignInPage


def main(page: ft.Page):
    page.title = 'Sign In'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.adaptive = True

    SignInPage(page)


ft.app(target=main)
