import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.account_edit_page import AccountEditPage
from washer.ui_components.password_change_page import PasswordChangePage
from washer.ui_components.sign_in_page import SignInPage


class AccountSettingsPage:
    def __init__(self, page: ft.Page, api: BackendApi = None):
        self.page = page
        self.api = api if api else BackendApi()
        self.user_data = {}

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
        self.change_avatar_button = ft.ElevatedButton(
            text='Изменить фото профиля',
            icon=ft.icons.CAMERA_ALT,
            on_click=self.on_avatar_click,
            width=300,
            visible=True,
        )

        self.account_button = self.create_navigation_button(
            icon=ft.icons.ACCOUNT_CIRCLE,
            text='Учетная запись',
            on_click=self.open_account_edit_page,
            icon_bg_color=ft.colors.BLUE_200,
        )

        self.password_button = self.create_navigation_button(
            icon=ft.icons.LOCK,
            text='Пароль',
            on_click=self.open_password_change_page,
            icon_bg_color=ft.colors.ORANGE_300,
        )

        self.phone_button = self.create_navigation_button(
            icon=ft.icons.PHONE,
            text='Номер телефона',
            on_click=self.on_phone_click,
            icon_bg_color=ft.colors.GREEN_200,
        )

        self.about_button = self.create_navigation_button(
            icon=ft.icons.INFO,
            text='О приложении',
            on_click=self.open_about_page,
            icon_bg_color=ft.colors.GREEN_300,
        )

        self.delete_account_button = self.create_navigation_button(
            icon=ft.icons.DELETE,
            text='Удалить аккаунт',
            on_click=self.on_delete_account_click,
            icon_bg_color=ft.colors.RED,
        )

    def create_navigation_button(
        self, icon, text, on_click, icon_bg_color=ft.colors.WHITE
    ):
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, color=ft.colors.WHITE),
                        bgcolor=icon_bg_color,
                        width=25,
                        height=25,
                        border_radius=ft.border_radius.all(8),
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        text,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            on_click=on_click,
            width=700,
            bgcolor=ft.colors.TRANSPARENT,
            padding=ft.padding.symmetric(vertical=15, horizontal=20),
            border_radius=ft.border_radius.all(8),
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
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(50),
                )
            else:
                self.avatar_container.content = ft.Icon(
                    ft.icons.PERSON, size=100, color=ft.colors.GREY
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
            title=ft.Text(
                'Настройки аккаунта',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            actions=[],
        )

        profile_card = self.create_profile_card()

        buttons_card_1 = ft.Card(
            content=ft.Column(
                controls=[
                    self.account_button,
                    ft.Container(
                        content=ft.Divider(
                            height=1,
                            color=ft.colors.GREY,
                            thickness=1,
                        ),
                        margin=ft.margin.only(left=55),
                    ),
                    self.password_button,
                    ft.Container(
                        content=ft.Divider(
                            height=1,
                            color=ft.colors.GREY,
                            thickness=1,
                        ),
                        margin=ft.margin.only(left=55),
                    ),
                    self.phone_button,
                ],
                spacing=0,
            ),
            width=700,
            elevation=3,
        )

        buttons_card_2 = ft.Card(
            content=ft.Column(
                controls=[
                    self.about_button,
                    ft.Container(
                        content=ft.Divider(
                            height=1,
                            color=ft.colors.GREY,
                            thickness=1,
                        ),
                        margin=ft.margin.only(left=55),
                    ),
                    self.delete_account_button,
                ],
                spacing=0,
            ),
            width=700,
            elevation=3,
        )

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        profile_card,
                        ft.Container(height=20),
                        buttons_card_1,
                        ft.Container(height=15),
                        buttons_card_2,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                width=730,
                alignment=ft.alignment.center,
            )
        )

        self.page.update()

    def create_profile_card(self):
        return ft.Container(
            width=730,
            alignment=ft.alignment.center,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=self.avatar_container,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=50),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    self.user_data.get('username', ''),
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=10),
                            ),
                            ft.Container(
                                content=self.change_avatar_button,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=10),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=ft.padding.all(20),
                    height=250,
                ),
                elevation=3,
            ),
            margin=ft.margin.only(bottom=20),
        )

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Icon(ft.icons.PERSON, size=100, color=ft.colors.GREY),
            alignment=ft.alignment.center,
            margin=ft.margin.only(top=-50),
            on_click=self.on_avatar_click,
            width=100,
            height=100,
        )

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def on_avatar_click(self, e):
        self.file_picker.pick_files(
            allow_multiple=False, allowed_extensions=['png', 'jpg', 'jpeg']
        )

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            try:
                self.selected_image_bytes = file.content
                self.avatar_container.content = ft.Image(
                    src=ft.ImageSource.bytes(self.selected_image_bytes),
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(50),
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
                new_values={},
                image_bytes=self.selected_image_bytes,
            )
            if response and response.status_code == 200:
                print('Аватар успешно обновлен.')
                self.show_success_message('Аватар успешно обновлен!')
                self.load_user_data()
            else:
                error_text = (
                    response.text
                    or 'Неизвестная ошибка при обновлении аватара.'
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

    def open_account_edit_page(self, e):
        print('Opening AccountEditPage')
        AccountEditPage(
            self.page, self.user_data, self.on_account_updated, self.api
        )

    def on_account_updated(self):
        # Callback после обновления учетной записи
        self.load_user_data()

    def open_password_change_page(self, e):
        print('Opening PasswordChangePage')
        PasswordChangePage(
            self.page, self.user_data, self.on_password_changed, self.api
        )

    def on_password_changed(self):
        # Callback после смены пароля
        self.show_success_message('Пароль успешно изменен.')

    def on_phone_click(self, e):
        print("Кнопка 'Номер телефона' нажата")
        # Пока без логики, можно добавить заглушку или оставить пустым
        pass

    def on_logout_click(self, e):
        self.page.client_storage.clear()
        self.redirect_to_sign_in_page()

    def on_delete_account_click(self, e):
        print('Delete Account button clicked')
        # Логика удаления аккаунта будет добавлена позже
        self.show_error_message(
            'Функция удаления аккаунта пока не реализована.'
        )

    def open_about_page(self, e):
        print("Открыта кнопка 'О приложении'")
        # Пока без логики. В будущем можно добавить диалог или новую страницу.
        pass
