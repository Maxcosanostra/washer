import flet as ft

from washer.api_requests import BackendApi


class AccountEditPage:
    def __init__(
        self, page: ft.Page, user_data: dict, on_save_callback, api: BackendApi
    ):
        self.page = page
        self.api = api
        self.user_data = user_data
        self.on_save_callback = on_save_callback

        self.first_name_field = self.create_first_name_field()
        self.last_name_field = self.create_last_name_field()
        self.username_field = self.create_username_field()

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
        self.show_account_edit_page()

    def create_first_name_field(self):
        return ft.TextField(
            label='Имя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            value=self.user_data.get('first_name', ''),
        )

    def create_last_name_field(self):
        return ft.TextField(
            label='Фамилия',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            value=self.user_data.get('last_name', ''),
        )

    def create_username_field(self):
        return ft.TextField(
            label='Имя пользователя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            value=self.user_data.get('username', ''),
        )

    def show_account_edit_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.go_back,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Учетная запись',
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
                            content=self.username_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.first_name_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.last_name_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Сохранить',
                                bgcolor=ft.colors.GREEN,
                                color=ft.colors.WHITE,
                                on_click=self.save_changes,
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

    def save_changes(self, e=None):
        print('Saving account changes')
        updated_username = self.username_field.value.strip()
        updated_first_name = self.first_name_field.value.strip()
        updated_last_name = self.last_name_field.value.strip()

        print(f'Updated username: {updated_username}')
        print(f'Updated first name: {updated_first_name}')
        print(f'Updated last name: {updated_last_name}')

        new_values = {
            'username': updated_username or self.user_data.get('username'),
            'first_name': updated_first_name
            or self.user_data.get('first_name'),
            'last_name': updated_last_name or self.user_data.get('last_name'),
            'role_id': 2,
        }

        print(f'New values to update: {new_values}')

        try:
            print('Sending request to update user data')
            response = self.api.update_user_data(
                self.user_data['id'], new_values
            )
            print(f'Update user data response: {response}')
        except Exception as ex:
            error_message = f'Ошибка при обновлении данных: {str(ex)}'
            print(error_message)
            self.show_error_message(error_message)
            return

        if response and response.get('status_code') == 200:
            print('Данные успешно обновлены')
            self.show_success_message('Данные успешно обновлены')
            if self.on_save_callback:
                print('Calling on_save_callback')
                self.on_save_callback()
        else:
            error_message = response.get('error', 'Неизвестная ошибка')
            print(f'Ошибка при обновлении данных: {error_message}')
            self.show_error_message(
                f'Ошибка при обновлении данных: {error_message}'
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
