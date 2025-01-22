import flet as ft

from washer.ui_components.select_car_page import SelectCarPage
from washer.ui_components.wash_selection_page import WashSelectionPage


class AddCarPromptPage:
    def __init__(self, page: ft.Page, username: str):
        self.page = page
        self.username = username

        self.page.clean()
        self.page.add(self.create_add_car_prompt_page())

        self.page.update()

    def create_add_car_prompt_page(self):
        return ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Container(height=40),
                    ft.Container(
                        content=ft.Image(
                            src='https://drive.google.com/uc?export=view&id=1C3y7ItCMgFDgVpZBquagTkFpVuGWMXue',
                            width=350,
                            height=350,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=ft.Text(
                            'Может, добавим сразу автомобиль?',
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=ft.Text(
                            'Добавление автомобиля поможет быстрее\n'
                            'оформлять записи и получать\n'
                            'персонализированные предложения.',
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.colors.GREY,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=40),
                    ),
                    ft.Column(
                        controls=[
                            ft.ElevatedButton(
                                text='Добавить',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.on_add_car_click,
                                width=230,
                                height=50,
                                style=ft.ButtonStyle(),
                            ),
                            ft.Container(height=10),
                            ft.ElevatedButton(
                                text='Позже',
                                bgcolor=ft.colors.GREY,
                                color=ft.colors.WHITE,
                                on_click=self.on_skip_click,
                                width=230,
                                height=50,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=1,
                    ),
                ],
                expand=True,
                padding=ft.padding.symmetric(vertical=20, horizontal=20),
            ),
            expand=True,
            border_radius=ft.border_radius.all(12),
        )

    def on_add_car_click(self, e):
        SelectCarPage(
            page=self.page,
            on_car_saved=self.on_car_saved,  # Callback для перенаправления
        )

    def on_skip_click(self, e):
        WashSelectionPage(self.page, username=self.username)

    def on_car_saved(self, car):
        WashSelectionPage(self.page, username=self.username)
