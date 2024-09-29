import flet as ft

from washer.api_requests import BackendApi


class SignUpPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()

        self.username_field = self.create_username_field()
        self.password_field = self.create_password_field()
        self.confirm_password_field = self.create_confirm_password_field()
        self.first_name_field = self.create_first_name_field()
        self.last_name_field = self.create_last_name_field()

        self.image_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.image_picker)

        self.selected_image = None

        page.clean()

        page.add(self.create_sign_up_container())

        page.add(
            ft.TextButton(
                'Уже есть аккаунт? Войти',
                on_click=self.open_sign_in_page,
            )
        )

    def create_username_field(self):
        return ft.TextField(
            label='Имя пользователя',
            width=280,
            text_size=12,
            height=50,
            border_radius=ft.border_radius.all(25),
            content_padding=ft.Padding(left=10, top=5, right=10, bottom=5),
        )

    def create_password_field(self):
        return ft.TextField(
            label='Пароль',
            password=True,
            can_reveal_password=True,
            width=280,
            text_size=12,
            height=50,
            border_radius=ft.border_radius.all(25),
            content_padding=ft.Padding(left=10, top=5, right=10, bottom=5),
        )

    def create_confirm_password_field(self):
        return ft.TextField(
            label='Подтвердите пароль',
            password=True,
            can_reveal_password=True,
            width=280,
            text_size=12,
            height=50,
            border_radius=ft.border_radius.all(25),
            content_padding=ft.Padding(left=10, top=5, right=10, bottom=5),
        )

    def create_first_name_field(self):
        return ft.TextField(
            label='Имя',
            width=280,
            text_size=12,
            height=50,
            border_radius=ft.border_radius.all(25),
            content_padding=ft.Padding(left=10, top=5, right=10, bottom=5),
        )

    def create_last_name_field(self):
        return ft.TextField(
            label='Фамилия',
            width=280,
            text_size=12,
            height=50,
            border_radius=ft.border_radius.all(25),
            content_padding=ft.Padding(left=10, top=5, right=10, bottom=5),
        )

    def create_sign_up_container(self):
        return ft.Container(
            content=ft.Column(
                [
                    self.create_logo_container(),
                    ft.Text('Регистрация', size=28, weight=ft.FontWeight.BOLD),
                    self.create_description_container(),
                    self.first_name_field,
                    self.last_name_field,
                    self.username_field,
                    self.password_field,
                    self.confirm_password_field,
                    ft.TextButton(
                        'Выбрать изображение профиля',
                        on_click=lambda _: self.image_picker.pick_files(
                            allow_multiple=False,
                            file_type=ft.FilePickerFileType.IMAGE,
                        ),
                    ),
                    self.create_sign_up_button_container(),
                    ft.TextButton(
                        'Уже есть аккаунт? Войти',
                        on_click=self.open_sign_in_page,
                    ),
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
                'Введите данные для регистрации.',
                size=12,
                text_align=ft.TextAlign.CENTER,
            ),
            margin=ft.margin.only(bottom=15),
        )

    def create_sign_up_button_container(self):
        return ft.Container(
            content=ft.ElevatedButton(
                text='Зарегистрироваться',
                width=300,
                bgcolor=ft.colors.PURPLE_ACCENT,
                color=ft.colors.WHITE,
                on_click=self.on_sign_up_click,
            ),
            margin=ft.margin.only(top=20, bottom=15),
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image = e.files[0].path
            print(f'Выбрано изображение: {self.selected_image}')

    def on_sign_up_click(self, _: ft.ControlEvent):
        username = self.username_field.value
        password = self.password_field.value
        first_name = self.first_name_field.value
        last_name = self.last_name_field.value
        confirm_password = self.confirm_password_field.value

        if password != confirm_password:
            self.page.add(ft.Text('Пароли не совпадают!', color=ft.colors.RED))
            return

        data = {
            'username': username,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
        }

        files = None
        if self.selected_image:
            files = {'image': open(self.selected_image, 'rb')}

        response = self.api.register_user(data, files)

        if response.status_code == 200:
            tokens = response.json()
            print(
                f"Токены: {tokens['access_token']}, {tokens['refresh_token']}"
            )

            self.page.client_storage.set(
                'access_token', tokens['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', tokens['refresh_token']
            )
            self.page.client_storage.set('username', username)

            user_info = self.api.get_logged_user()

            if 'id' in user_info:
                self.page.client_storage.set('user_id', user_info['id'])
                print(f"User ID получен: {user_info['id']}")
            else:
                print('User ID не был получен')

            self.open_wash_selection_page()
        else:
            print(f'Ошибка регистрации: {response.text}')
            self.page.add(
                ft.Text(f'Ошибка: {response.text}', color=ft.colors.RED)
            )

    def open_wash_selection_page(self):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page, self.username_field.value)

    def open_sign_in_page(self, e=None):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)
