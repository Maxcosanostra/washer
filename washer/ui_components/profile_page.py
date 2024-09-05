import flet as ft


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        self.avatar_container = self.create_avatar_container()
        self.name_field = self.create_name_field()
        self.surname_field = self.create_surname_field()
        self.brand_dropdown = self.create_brand_dropdown()
        self.save_button = self.create_save_button()

        page.clean()
        page.add(self.create_profile_container())

    def create_file_picker(self):
        return ft.FilePicker(on_result=self.on_picture_select)

    def create_avatar_container(self):
        return ft.Container(
            content=ft.Image(
                src='https://via.placeholder.com/100',
                width=100,
                height=100,
                border_radius=ft.border_radius.all(50),
            ),
            on_click=self.on_picture_click,
        )

    def create_name_field(self):
        return ft.TextField(
            label='Ваше имя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
        )

    def create_surname_field(self):
        return ft.TextField(
            label='Ваша фамилия',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
        )

    def create_brand_dropdown(self):
        return ft.Dropdown(
            label='Марка',
            options=[
                ft.dropdown.Option('Выберите марку'),
                ft.dropdown.Option('Audi'),
                ft.dropdown.Option('BMW'),
                ft.dropdown.Option('Skoda'),
            ],
            width=300,
            border_radius=ft.border_radius.all(30),
        )

    def create_save_button(self):
        return ft.ElevatedButton(
            text='Сохранить',
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )

    def create_profile_container(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=lambda e: self.open_sign_in(),
                            ),
                            ft.Text('Создайте профиль', size=24),
                        ]
                    ),
                    self.avatar_container,
                    self.name_field,
                    self.surname_field,
                    self.brand_dropdown,
                    self.save_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(10),
            width=350,
            alignment=ft.alignment.center,
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
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)
