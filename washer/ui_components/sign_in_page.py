import flet as ft

from washer.api_requests import BackendApi


class SignInPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()

        self.username_field = self.create_username_field()
        self.password_field = self.create_password_field()

        page.clean()
        page.add(self.create_sign_in_container())

    def create_username_field(self):
        return ft.TextField(
            label='Имя пользователя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_password_field(self):
        return ft.TextField(
            label='Пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
        )

    def create_sign_in_container(self):
        return ft.Container(
            content=ft.Column(
                [
                    self.create_back_button(),
                    self.create_logo_container(),
                    ft.Text('Войти', size=28, weight=ft.FontWeight.BOLD),
                    self.create_description_container(),
                    self.username_field,
                    self.password_field,
                    self.create_sign_in_button_container(),
                    ft.TextButton('Забыли пароль?'),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            ),
            width=350,
            height=720,
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(12),
        )

    def create_logo_container(self):
        return ft.Container(
            content=ft.Image(src='assets/logo.png', width=80, height=80),
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=20),
        )

    def create_description_container(self):
        return ft.Container(
            content=ft.Text(
                'Используйте учетную запись ниже для входа.',
                size=12,
                text_align=ft.TextAlign.CENTER,
            ),
            margin=ft.margin.only(bottom=15),
        )

    def create_sign_in_button_container(self):
        return ft.Container(
            content=ft.ElevatedButton(
                text='Войти',
                width=180,
                bgcolor=ft.colors.PURPLE_ACCENT,
                color=ft.colors.WHITE,
                on_click=self.on_sign_in_click,
            ),
            margin=ft.margin.only(top=20, bottom=15),
        )

    def create_back_button(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=30,
                        on_click=self.on_back_to_sign_up_click,
                    ),
                    ft.Text('Назад на регистрацию', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            margin=ft.margin.only(bottom=15),
        )

    def on_sign_in_click(self, _: ft.ControlEvent):
        username = self.username_field.value
        password = self.password_field.value

        if not username or not password:
            self.page.add(ft.Text('Заполните все поля!', color=ft.colors.RED))
            return

        tokens = self.api.login(username, password)

        if 'access_token' in tokens:
            self.page.client_storage.set(
                'access_token', tokens['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', tokens['refresh_token']
            )
            self.page.client_storage.set('username', username)

            print(
                "Tokens saved: "
                f"{self.page.client_storage.get('access_token')}, "
                f"{self.page.client_storage.get('refresh_token')}"
            )

            self.open_wash_selection_page()
        else:
            self.page.add(ft.Text('Ошибка авторизации!', color=ft.colors.RED))

    def open_wash_selection_page(self):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page, self.username_field.value)

    def on_back_to_sign_up_click(self, _: ft.ControlEvent):
        from washer.ui_components.sign_up_page import SignUpPage

        SignUpPage(self.page)
