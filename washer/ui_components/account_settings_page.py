import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.sign_in_page import SignInPage


class AccountSettingsPage:
    def __init__(self, page):
        self.page = page
        self.api = BackendApi()
        self.user_data = {}

        self.setup_snack_bar()

        self.access_token = self.page.client_storage.get('access_token')
        if not self.access_token:
            print('Access token not found, redirecting to login.')
            self.redirect_to_sign_in_page()
            return

        self.api.set_access_token(self.access_token)

        self.load_user_data()

    def load_user_data(self):
        print(
            'Заголовки запроса для получения данных пользователя:',
            self.api.get_headers(),
        )

        self.user_data = self.api.get_logged_user()

        if 'error' not in self.user_data:
            print('Данные пользователя успешно загружены:', self.user_data)
            self.show_account_settings()
        else:
            error_message = self.user_data['error']
            print('Ошибка при загрузке данных пользователя:', error_message)
            self.page.clean()
            self.page.add(
                ft.Container(
                    content=ft.Text(
                        f'Ошибка при загрузке данных: {error_message}',
                        color=ft.colors.RED,
                        size=16,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.all(20),
                )
            )
            self.page.update()

    def show_account_settings(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Настройки аккаунта',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

        username_label = ft.Text(
            'ИМЯ ПОЛЬЗОВАТЕЛЯ',
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_800,
        )
        username_field = ft.TextField(
            value=self.user_data.get('username', ''),
            label='Имя пользователя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.PERSON,
            filled=True,
            border_color=ft.colors.GREY_300,
        )

        first_name_label = ft.Text(
            'ИМЯ', size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREY_800
        )
        first_name_field = ft.TextField(
            value=self.user_data.get('first_name', ''),
            label='Имя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.BADGE,
            filled=True,
            border_color=ft.colors.GREY_300,
        )

        last_name_label = ft.Text(
            'ФАМИЛИЯ',
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_800,
        )
        last_name_field = ft.TextField(
            value=self.user_data.get('last_name', ''),
            label='Фамилия',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.BADGE,
            filled=True,
            border_color=ft.colors.GREY_300,
        )

        password_label = ft.Text(
            'ПАРОЛЬ',
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_800,
        )
        password_field = ft.TextField(
            value='',
            label='Пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            icon=ft.icons.LOCK,
            filled=True,
            border_color=ft.colors.GREY_300,
            hint_text='Оставьте пустым, если не хотите менять',
            hint_style=ft.TextStyle(color=ft.colors.GREY_500),
        )

        save_button = ft.ElevatedButton(
            text='Сохранить изменения',
            icon=ft.icons.SAVE,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                padding=ft.padding.symmetric(horizontal=20, vertical=15),
            ),
            on_click=lambda e: self.update_user_data(
                username_field.value,
                first_name_field.value,
                last_name_field.value,
                password_field.value,
            ),
        )

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        username_label,
                        username_field,
                        first_name_label,
                        first_name_field,
                        last_name_label,
                        last_name_field,
                        password_label,
                        password_field,
                        ft.Container(height=20),
                        save_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=ft.padding.all(20),
                width=400,
                alignment=ft.alignment.center,
            )
        )
        self.page.update()

    def update_user_data(self, username, first_name, last_name, password):
        new_values = {
            'username': username or self.user_data.get('username'),
            'first_name': first_name or self.user_data.get('first_name'),
            'last_name': last_name or self.user_data.get('last_name'),
            'role_id': 2,
        }

        if password:
            new_values['password'] = password

        try:
            response = self.api.update_user_data(
                self.user_data['id'], new_values
            )
        except Exception as e:
            error_message = f'Ошибка при обновлении данных: {str(e)}'
            print(error_message)
            self.show_error_message(error_message)
            return

        if response and response.get('status_code') == 200:
            print('Данные успешно обновлены')
            self.show_success_message('Данные успешно обновлены')
            self.load_user_data()
        else:
            error_message = response.get('error', 'Неизвестная ошибка')
            print(f'Ошибка при обновлении данных: {error_message}')
            self.show_error_message(
                f'Ошибка при обновлении данных: {error_message}'
            )

    def return_to_profile(self, e):
        self.page.appbar = None
        from washer.ui_components.profile_page import ProfilePage

        ProfilePage(self.page)

    def redirect_to_sign_in_page(self):
        SignInPage(self.page)

    def setup_snack_bar(self):
        self.snack_bar = ft.SnackBar(
            content=ft.Text(''),
            bgcolor=ft.colors.GREEN,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

    def show_snack_bar(
        self,
        message: str,
        bgcolor: str = ft.colors.GREEN,
        text_color: str = ft.colors.WHITE,
    ):
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.content.color = text_color

        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def show_success_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.RED)
