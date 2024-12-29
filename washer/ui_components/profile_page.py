import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.account_settings_page import AccountSettingsPage
from washer.ui_components.my_finance_page import MyFinancePage


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(page.client_storage.get('access_token'))
        self.api_url = self.api.url
        self.username = self.page.client_storage.get('username')

        self.cars = []
        self.bookings = []
        self.completed_visible = False
        self.selected_image_bytes = None

        self.completed_bookings_container = ft.Container(visible=False)

        self.avatar_container = self.create_avatar_container()
        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        self.get_user_data()

        page.clean()

        if self.page.navigation_bar:
            self.page.navigation_bar.selected_index = 3

        self.page.floating_action_button = None
        self.page.update()

        page.add(self.create_profile_page())

    def on_login_success(self):
        self.get_user_data()
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def create_profile_card(self):
        return ft.Container(
            width=730,
            alignment=ft.alignment.center,
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.IconButton(
                                        icon=ft.icons.ARROW_BACK,
                                        on_click=self.on_back_click,
                                    ),
                                    ft.Container(expand=1),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(
                                content=self.avatar_container,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=-50),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    self.username,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=-10),
                            ),
                            ft.Container(
                                content=ft.ElevatedButton(
                                    icon=ft.icons.CAMERA_ALT,
                                    text='Изменить фото профиля',
                                    on_click=self.on_avatar_click,
                                    width=300,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=5),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            margin=ft.margin.only(bottom=20),
        )

    def create_profile_page(self):
        return ft.Container(
            width=730,
            alignment=ft.alignment.center,
            content=ft.ListView(
                controls=[
                    ft.Container(height=40),
                    self.create_profile_card(),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.ACCOUNT_CIRCLE,
                                    color=ft.colors.WHITE,
                                ),
                                ft.Text(
                                    'Учетная запись',
                                    color=ft.colors.WHITE,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_account_settings,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.icons.ATTACH_MONEY,
                                    color=ft.colors.WHITE,
                                ),
                                ft.Text(
                                    'Финансы',
                                    color=ft.colors.WHITE,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=5,
                        ),
                        on_click=self.open_finances_page,
                        width=300,
                        bgcolor=ft.colors.BLUE,
                        padding=ft.padding.symmetric(
                            vertical=10, horizontal=15
                        ),
                        border_radius=ft.border_radius.all(8),
                    ),
                    ft.Divider(height=1, color=ft.colors.GREY_400),
                    ft.Container(
                        content=ft.ElevatedButton(
                            text='Выйти из профиля',
                            bgcolor=ft.colors.RED,
                            color=ft.colors.WHITE,
                            on_click=self.on_logout_click,
                            elevation=5,
                        ),
                        width=300,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(top=20, bottom=15),
                    ),
                ],
                padding=ft.padding.all(0),
                spacing=15,
            ),
            margin=ft.margin.only(top=20),
            expand=True,
        )

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Icon(ft.icons.PERSON, size=100, color=ft.colors.GREY),
            alignment=ft.alignment.center,
            padding=20,
            on_click=self.on_avatar_click,
        )

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def on_avatar_click(self, e):
        self.file_picker.pick_files(allow_multiple=False)

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            with open(e.files[0].path, 'rb') as image_file:
                self.selected_image_bytes = image_file.read()
            self.avatar_container.content = ft.Image(
                src=e.files[0].path,
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(50),
            )
            self.page.update()
            self.upload_avatar_to_server()

    def upload_avatar_to_server(self):
        user_id = self.page.client_storage.get('user_id')
        username = self.username
        if not user_id or not self.selected_image_bytes:
            print('Необходимые данные отсутствуют для обновления аватара.')
            self.show_snackbar(
                'Необходимые данные отсутствуют для обновления аватара.',
                color=ft.colors.RED,
            )
            return

        new_values = {'username': username}
        response = self.api.update_user_with_avatar(
            user_id=user_id,
            new_values=new_values,
            image_bytes=self.selected_image_bytes,
        )
        if response and response.status_code == 200:
            print('Аватар успешно обновлен.')
            self.get_user_data()
            self.show_snackbar(
                'Аватар успешно обновлен!', color=ft.colors.GREEN
            )
        else:
            error_text = (
                response.text
                if response
                else 'Неизвестная ошибка при обновлении аватара.'
            )
            print(f'Ошибка при обновлении аватара: {error_text}')
            self.show_snackbar(
                f'Ошибка при обновлении аватара: {error_text}',
                color=ft.colors.RED,
            )

    def get_user_data(self):
        user_data = self.api.get_logged_user()
        if user_data and 'error' not in user_data:
            avatar_url = user_data.get('image_link')
            if avatar_url:
                self.avatar_container.content = ft.Image(
                    src=avatar_url,
                    width=100,
                    height=100,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(50),
                )
                self.page.update()
        else:
            error_message = user_data.get(
                'error',
                'Неизвестная ошибка при получении данных пользователя.',
            )
            print(error_message)
            self.show_snackbar(
                f'Ошибка при получении данных: {error_message}',
                color=ft.colors.RED,
            )

    def open_account_settings(self, e):
        self.page.clean()
        AccountSettingsPage(self.page)
        self.page.update()

    def open_finances_page(self, e):
        finance_page = MyFinancePage(self.page)
        finance_page.open()

    def return_to_profile(self, e):
        self.page.appbar = None
        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def on_back_click(self, e):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)

    def on_logout_click(self, e):
        self.page.client_storage.remove('access_token')
        self.page.client_storage.remove('refresh_token')
        self.page.client_storage.remove('username')
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

    def show_snackbar(self, message: str, color: str = ft.colors.RED):
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()
