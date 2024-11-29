import flet as ft


class MyFinancePage:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.clean()
        self.page.appbar = self.create_appbar()
        self.page.add(self.create_finances_page())
        self.page.update()

    def create_appbar(self):
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Финансы',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

    def create_finances_page(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Финансовая информация будет здесь',
                        size=20,
                        color=ft.colors.GREY_700,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            padding=ft.padding.all(20),
        )

    def return_to_profile(self, e):
        from washer.ui_components.profile_page import ProfilePage

        self.page.appbar = None
        ProfilePage(self.page)
