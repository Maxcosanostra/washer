import flet as ft
from pydantic import ValidationError

from washer.api_requests import BackendApi
from washer.models.user import UserSignIn


class SignInPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()

        self.disable_navigation_drawer_and_appbar()

        self.username_field = self.create_username_field()
        self.password_field = self.create_password_field()

        page.clean()

        self.page.navigation_bar = None
        self.page.floating_action_button = None

        self.snack_bar = ft.SnackBar(
            content=ft.Text(
                '',
                text_align=ft.TextAlign.CENTER,
                size=16,
                color=ft.colors.WHITE,
            ),
            bgcolor=ft.colors.RED,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

        page.add(self.create_sign_in_container())

    def disable_navigation_drawer_and_appbar(self):
        """Отключает NavigationDrawer и AppBar, обновляет страницу."""
        self.page.drawer = None
        self.page.appbar = None

    def create_username_field(self):
        return ft.TextField(
            label='Имя пользователя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            autofocus=True,
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
        # input_field_width = 300

        return ft.Container(
            content=ft.ListView(
                controls=[
                    ft.Container(height=40),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=self.on_back_to_sign_up_click,
                            ),
                            ft.TextButton(
                                text='Назад на регистрацию',
                                on_click=self.on_back_to_sign_up_click,
                                style=ft.ButtonStyle(
                                    color=ft.colors.BLACK,
                                    padding=0,
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    ft.Container(height=0),
                    ft.Container(
                        content=ft.Image(
                            src='http://77.73.66.191:9001/api/v1/buckets/general-bucket/objects/download?preview=true&prefix=Sign%20in-pana.png&version_id=null',
                            width=300,
                            height=300,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=0),
                    ),
                    ft.Container(
                        content=ft.Text(
                            'Войти',
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=20),
                    ),
                    ft.Container(
                        content=ft.Text(
                            'Используйте учетную запись ниже для входа.',
                            size=12,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        margin=ft.margin.only(bottom=15),
                    ),
                    ft.Container(
                        content=self.username_field,
                        width=300,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=self.password_field,
                        width=300,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=10),
                    ),
                    ft.Container(
                        content=ft.ElevatedButton(
                            text='Войти',
                            bgcolor=ft.colors.PURPLE_ACCENT,
                            color=ft.colors.WHITE,
                            on_click=self.on_sign_in_click,
                            elevation=5,
                        ),
                        width=300,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=20, bottom=15),
                    ),
                    ft.TextButton(
                        'Забыли пароль?',
                        on_click=self.on_forgot_password_click,
                    ),
                ],
                expand=True,
                padding=ft.padding.symmetric(vertical=20, horizontal=20),
            ),
            expand=True,
            border_radius=ft.border_radius.all(12),
        )

    def on_sign_in_click(self, _: ft.ControlEvent):
        username = self.username_field.value
        password = self.password_field.value

        try:
            user_sign_in = UserSignIn(username=username, password=password)
        except ValidationError as ve:
            self.display_validation_errors(ve)
            return

        print(f'Пытаемся войти с пользователем: {user_sign_in.username}')
        tokens = self.api.login(user_sign_in.username, user_sign_in.password)

        if 'access_token' in tokens:
            self.page.client_storage.set(
                'access_token', tokens['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', tokens['refresh_token']
            )
            self.page.client_storage.set('username', user_sign_in.username)

            user_info = self.api.get_logged_user()
            if 'id' in user_info:
                self.page.client_storage.set('user_id', user_info['id'])

            if user_info['role']['name'] == 'admin':
                self.open_admin_page()
            else:
                self.open_wash_selection_page()
        else:
            self.show_snack_bar(
                'Неверный логин или пароль!', bgcolor=ft.colors.RED
            )

    def display_validation_errors(self, ve: ValidationError):
        """
        Отображает ошибки валидации на странице с использованием SnackBar.
        Убирает префикс "Value error, " из сообщений.
        """
        error_messages = []
        for error in ve.errors():
            msg = error['msg']
            prefix = 'Value error, '
            if msg.startswith(prefix):
                msg = msg[len(prefix) :]
            error_messages.append(msg)
        error_text = '\n'.join(error_messages)
        self.show_snack_bar(error_text, bgcolor=ft.colors.RED)

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.RED):
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def on_forgot_password_click(self, e):
        print('Переход на страницу восстановления пароля.')
        # Здесь можно добавить переход на соответствующую страницу
        # Например:
        # from washer.ui_components.forgot_password_page
        # import ForgotPasswordPage
        # ForgotPasswordPage(self.page)

    def open_admin_page(self):
        from washer.ui_components.admin_page import AdminPage

        AdminPage(self.page)

    def open_wash_selection_page(self):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page, self.username_field.value)

    def on_back_to_sign_up_click(self, _: ft.ControlEvent):
        from washer.ui_components.sign_up_page import SignUpPage

        SignUpPage(self.page)
