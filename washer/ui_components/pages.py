import flet as ft

from washer.api_requests import BackendApi


class SignInPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.profile_page = ProfilePage
        self.api = BackendApi()

        self.username_field = ft.TextField(
            label='Имя пользователя',
            width=280,
            text_size=12,
            height=40,
        )

        self.password_field = ft.TextField(
            label='Пароль',
            password=True,
            can_reveal_password=True,
            width=280,
            text_size=12,
            height=40,
        )

        page.clean()
        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Image(
                                src='assets/logo.png', width=80, height=80
                            ),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Text('Войти', size=28, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(
                                'Используйте учетную запись ниже для входа.',
                                size=12,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            margin=ft.margin.only(bottom=15),
                        ),
                        self.username_field,
                        self.password_field,
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Войти',
                                width=180,
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.on_sign_in_click,
                            ),
                            margin=ft.margin.only(top=20, bottom=15),
                        ),
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
        )

    def on_sign_in_click(self, _: ft.ControlEvent):
        username = self.username_field.value
        password = self.password_field.value

        tokens = self.api.login(username, password)
        print(tokens)
        self.open_profile_page()

    def open_profile_page(self):
        self.profile_page(self.page)


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.sign_in_page = SignInPage
        self.file_picker = ft.FilePicker(on_result=self.on_picture_select)
        page.overlay.append(self.file_picker)

        self.avatar_container = ft.Container(
            content=ft.Image(
                src='https://via.placeholder.com/100',
                width=100,
                height=100,
                border_radius=ft.border_radius.all(50),
            ),
            on_click=self.on_picture_click,
        )

        name_field = ft.TextField(label='Ваше имя', width=300)
        city_field = ft.TextField(label='Ваша фамилия', width=300)
        state_dropdown = ft.Dropdown(
            label='Марка',
            options=[
                ft.dropdown.Option('Выберите марку'),
                ft.dropdown.Option('Audi'),
                ft.dropdown.Option('BMW'),
                ft.dropdown.Option('Skoda'),
            ],
            width=300,
        )
        bio_field = ft.TextField(
            label='Ваше био', multiline=True, width=300, height=100
        )
        save_button = ft.ElevatedButton(
            text='Сохранить',
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )

        page.clean()
        page.add(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=lambda e: self.open_sign_in(),
                                ),
                                ft.Text('Create your Profile', size=24),
                            ]
                        ),
                        self.avatar_container,
                        name_field,
                        city_field,
                        state_dropdown,
                        bio_field,
                        save_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                padding=ft.padding.all(20),
                border_radius=ft.border_radius.all(10),
                width=350,
                alignment=ft.alignment.center,
            )
        )

    def on_picture_click(self, _: ft.ControlEvent):
        self.file_picker.pick_files(allow_multiple=False)

    def on_picture_select(self, e: ft.FilePickerResultEvent):
        if e.files:
            img = ft.Image(
                src=e.files[0].path,
                width=100,
                height=100,
                border_radius=ft.border_radius.all(50),
            )
            self.avatar_container.content = img
            self.page.update()

    def open_sign_in(self):
        self.sign_in_page(self.page)
