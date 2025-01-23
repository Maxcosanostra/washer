import flet as ft

from washer.api_requests import BackendApi


class PasswordChangePage:
    def __init__(
        self,
        page: ft.Page,
        user_data: dict,
        on_change_callback,
        api: BackendApi,
    ):
        print('Initializing PasswordChangePage')
        self.page = page
        self.api = api
        self.user_data = user_data
        self.on_change_callback = on_change_callback

        self.current_password_field = self.create_current_password_field()
        self.new_password_field = self.create_new_password_field()
        self.confirm_password_field = self.create_confirm_password_field()

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
        print('SnackBar initialized and added to page overlay')

        self.show_password_change_page()

    def create_current_password_field(self):
        print('Creating current password field')
        return ft.TextField(
            label='Текущий пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_new_password_field(self):
        print('Creating new password field')
        return ft.TextField(
            label='Новый пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_confirm_password_field(self):
        print('Creating confirm password field')
        return ft.TextField(
            label='Подтвердите новый пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def show_password_change_page(self):
        print('Displaying PasswordChangePage')

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.go_back,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Смена пароля',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(height=150),
                        ft.Container(
                            content=self.current_password_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.new_password_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.confirm_password_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Сменить пароль',
                                bgcolor=ft.colors.GREEN,
                                color=ft.colors.WHITE,
                                on_click=self.change_password,
                                width=300,
                                height=50,
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20, horizontal=20),
                ),
                expand=True,
                alignment=ft.alignment.center,
            )
        )
        self.page.update()
        print('PasswordChangePage displayed successfully')

    def change_password(self, e=None):
        print('Attempting to change password')
        current_password = self.current_password_field.value.strip()
        new_password = self.new_password_field.value.strip()
        confirm_password = self.confirm_password_field.value.strip()

        print(f"Current password: {'*' * len(current_password)}")
        print(f"New password: {'*' * len(new_password)}")
        print(f"Confirm password: {'*' * len(confirm_password)}")

        if not current_password or not new_password or not confirm_password:
            print('One or more password fields are empty')
            self.show_error_message('Все поля обязательны для заполнения.')
            return

        if new_password != confirm_password:
            print('New password and confirmation do not match')
            self.show_error_message(
                'Новый пароль и подтверждение не совпадают.'
            )
            return

        print('Passwords validated successfully')

        new_values = {'password': new_password}

        print(f'New values to update for password: {new_values}')

        try:
            print('Sending request to update password')
            response = self.api.update_user_data(
                self.user_data['id'], new_values
            )
            print(f'Update password response: {response}')
        except Exception as ex:
            error_message = f'Ошибка при смене пароля: {str(ex)}'
            print(error_message)
            self.show_error_message(error_message)
            return

        if response and response.get('status_code') == 200:
            print('Пароль успешно изменен')
            self.show_success_message('Пароль успешно изменен.')
            if self.on_change_callback:
                print('Calling on_change_callback')
                self.on_change_callback()
        else:
            error_message = response.get('error', 'Неизвестная ошибка')
            print(f'Ошибка при смене пароля: {error_message}')
            self.show_error_message(
                f'Ошибка при смене пароля: {error_message}'
            )

    def go_back(self, e):
        print('Navigating back to AccountSettingsPage')
        from washer.ui_components.account_settings_page import (
            AccountSettingsPage,
        )

        AccountSettingsPage(self.page, self.api)

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.RED):
        print(f'Показываем сообщение в SnackBar: {message}')
        self.snack_bar.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True
        self.page.update()

    def show_success_message(self, message: str):
        print(f'Showing success message: {message}')
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        print(f'Showing error message: {message}')
        self.show_snack_bar(message, bgcolor=ft.colors.RED)
