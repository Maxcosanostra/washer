import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.sign_in_page import SignInPage


class AccountSettingsPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()
        self.user_data = {}
        self.edit_mode = False

        self.setup_snack_bar()

        self.access_token = self.page.client_storage.get('access_token')
        if not self.access_token:
            print('Access token не найден, перенаправление на страницу входа.')
            self.redirect_to_sign_in_page()
            return

        self.api.set_access_token(self.access_token)

        self.selected_image_bytes = None
        self.avatar_container = self.create_avatar_container()
        self.file_picker = self.create_file_picker()
        self.page.overlay.append(self.file_picker)

        self.initialize_controls()

        self.load_user_data()

    def initialize_controls(self):
        self.username_text = ft.Text(
            self.user_data.get('username', ''),
            size=30,
            weight=ft.FontWeight.BOLD,
            color=None,
            text_align=ft.TextAlign.CENTER,
        )

        self.username_label = ft.Text(
            'Имя пользователя',
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_700,
            visible=False,
        )

        self.username_field = ft.TextField(
            value=self.user_data.get('username', ''),
            width=300,
            text_size=15,
            height=40,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.PERSON,
            filled=True,
            border_color=ft.colors.GREY_300,
            visible=False,
        )

        self.first_name_label = ft.Text(
            'ИМЯ',
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_700,
            visible=False,
        )
        self.first_name_field = ft.TextField(
            value=self.user_data.get('first_name', ''),
            width=300,
            text_size=15,
            height=40,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.BADGE,
            filled=True,
            border_color=ft.colors.GREY_300,
            read_only=True,
        )

        self.last_name_label = ft.Text(
            'ФАМИЛИЯ',
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_700,
            visible=False,
        )
        self.last_name_field = ft.TextField(
            value=self.user_data.get('last_name', ''),
            width=300,
            text_size=15,
            height=40,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            icon=ft.icons.BADGE,
            filled=True,
            border_color=ft.colors.GREY_300,
            read_only=True,
        )

        self.password_label = ft.Text(
            'Пароль',
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_700,
            visible=False,
        )

        self.password_field = ft.TextField(
            value='',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=40,
            border_radius=ft.border_radius.all(30),
            icon=ft.icons.LOCK,
            filled=True,
            border_color=ft.colors.GREY_300,
            hint_text='Оставьте пустым, если не хотите менять',
            hint_style=ft.TextStyle(color=ft.colors.GREY_500),
            read_only=True,
        )

        self.cancel_button = ft.TextButton(
            text='Отмена',
            icon=ft.icons.CANCEL,
            on_click=self.cancel_edit_mode,
            visible=False,
        )

        self.change_avatar_button = ft.ElevatedButton(
            text='Изменить фото профиля',
            icon=ft.icons.CAMERA_ALT,
            on_click=self.on_avatar_click,
            width=300,
            visible=False,
        )

    def load_user_data(self):
        print(
            'Заголовки запроса для получения данных пользователя:',
            self.api.get_headers(),
        )

        self.user_data = self.api.get_logged_user()

        if 'error' not in self.user_data:
            print('Данные пользователя успешно загружены:', self.user_data)
            avatar_url = self.user_data.get('image_link')
            if avatar_url:
                self.avatar_container.content = ft.Image(
                    src=avatar_url,
                    width=200,
                    height=200,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(100),
                )
            else:
                self.avatar_container.content = ft.Icon(
                    ft.icons.PERSON, size=200, color=ft.colors.GREY
                )
            self.show_account_settings()
        else:
            error_message = self.user_data['error']
            print('Ошибка при загрузке данных пользователя:', error_message)
            self.page.clean()
            self.page.drawer = None
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
        self.page.drawer = None
        self.page.floating_action_button = None
        if self.page.navigation_bar:
            self.page.navigation_bar.selected_index = 3
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10, top=5, bottom=5),
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
            actions=[
                ft.IconButton(
                    icon=ft.icons.EDIT
                    if not self.edit_mode
                    else ft.icons.CHECK,
                    on_click=self.save_changes
                    if self.edit_mode
                    else self.toggle_edit_mode,
                    icon_color=ft.colors.WHITE,
                    tooltip='Сохранить' if self.edit_mode else 'Редактировать',
                    padding=ft.padding.only(top=5, bottom=5, right=10),
                )
            ],
        )

        avatar_section = ft.Column(
            controls=[
                self.avatar_container,
                self.change_avatar_button,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        avatar_section,
                        self.username_text,
                        self.username_label,
                        self.username_field,
                        ft.Container(height=10),
                        self.first_name_label,
                        self.first_name_field,
                        self.last_name_label,
                        self.last_name_field,
                        self.password_label,
                        self.password_field,
                        ft.Container(height=10),
                        ft.Row(
                            controls=[
                                self.cancel_button,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=ft.padding.all(20),
                width=400,
                alignment=ft.alignment.center,
            )
        )

        self.update_controls()
        self.page.update()

    def update_controls(self):
        if (
            not self.page.appbar
            or not self.page.appbar.actions
            or len(self.page.appbar.actions) == 0
        ):
            print('AppBar или его действия не установлены.')
            return

        self.username_text.value = self.user_data.get('username', '')
        self.username_field.value = self.user_data.get('username', '')
        self.first_name_field.value = self.user_data.get('first_name', '')
        self.last_name_field.value = self.user_data.get('last_name', '')
        self.password_field.value = ''

        self.username_label.visible = self.edit_mode
        self.password_label.visible = self.edit_mode
        self.first_name_label.visible = self.edit_mode
        self.last_name_label.visible = self.edit_mode

        self.username_text.visible = not self.edit_mode
        self.username_field.visible = self.edit_mode

        self.first_name_field.read_only = not self.edit_mode
        self.last_name_field.read_only = not self.edit_mode
        self.password_field.read_only = not self.edit_mode

        self.change_avatar_button.visible = self.edit_mode
        self.cancel_button.visible = self.edit_mode

        if self.edit_mode:
            self.page.appbar.actions[0].icon = ft.icons.CHECK
            self.page.appbar.actions[0].tooltip = 'Сохранить'
        else:
            self.page.appbar.actions[0].icon = ft.icons.EDIT
            self.page.appbar.actions[0].tooltip = 'Редактировать'

        print(f'Update Controls: edit_mode={self.edit_mode}')
        print(f'username_label.visible={self.username_label.visible}')
        print(f'password_label.visible={self.password_label.visible}')
        print(f'first_name_label.visible={self.first_name_label.visible}')
        print(f'last_name_label.visible={self.last_name_label.visible}')

        self.page.update()

    def toggle_edit_mode(self, e):
        self.edit_mode = not self.edit_mode
        print(
            f'Режим редактирования: '
            f'{"ВКЛЮЧЕН" if self.edit_mode else "ВЫКЛЮЧЕН"}'
        )
        self.update_controls()

    def save_changes(self, e=None):
        print('Сохранение изменений через AppBar.')
        self.update_user_data(
            self.username_field.value,
            self.first_name_field.value,
            self.last_name_field.value,
            self.password_field.value,
        )
        self.edit_mode = False
        self.update_controls()

    def cancel_edit_mode(self, e):
        print('Отмена режима редактирования.')
        self.edit_mode = False
        self.update_controls()
        self.load_user_data()

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

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Icon(ft.icons.PERSON, size=200, color=ft.colors.GREY),
            alignment=ft.alignment.center,
            padding=20,
            on_click=self.on_avatar_click,
            width=200,
            height=200,
        )

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def on_avatar_click(self, e):
        if self.edit_mode:
            self.file_picker.pick_files(
                allow_multiple=False, allowed_extensions=['png', 'jpg', 'jpeg']
            )
        else:
            self.show_error_message(
                'Сначала нажмите на иконку редактирования.'
            )

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            try:
                self.selected_image_bytes = file.content
                self.avatar_container.content = ft.Image(
                    src=ft.ImageSource.bytes(self.selected_image_bytes),
                    width=200,
                    height=200,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(100),
                )
                self.page.update()
                self.upload_avatar_to_server()
            except Exception as ex:
                error_message = f'Ошибка при обработке файла: {str(ex)}'
                print(error_message)
                self.show_error_message(error_message)

    def upload_avatar_to_server(self):
        user_id = self.user_data.get('id')
        if not user_id or not self.selected_image_bytes:
            print('Необходимые данные отсутствуют для обновления аватара.')
            self.show_error_message(
                'Необходимые данные отсутствуют для обновления аватара.'
            )
            return

        try:
            response = self.api.update_user_with_avatar(
                user_id=user_id,
                image_bytes=self.selected_image_bytes,
            )
            if response and response.get('status_code') == 200:
                print('Аватар успешно обновлен.')
                self.show_success_message('Аватар успешно обновлен!')
                self.load_user_data()
            else:
                error_text = response.get(
                    'error', 'Неизвестная ошибка при обновлении аватара.'
                )
                print(f'Ошибка при обновлении аватара: {error_text}')
                self.show_error_message(
                    f'Ошибка при обновлении аватара: {error_text}'
                )
        except Exception as e:
            error_message = f'Ошибка при обновлении аватара: {str(e)}'
            print(error_message)
            self.show_error_message(error_message)

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
