import flet as ft

from washer.config import config
from washer.ui_components.select_car_page import SelectCarPage


class ProfilePage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api_url = config.api_url
        self.username = self.page.client_storage.get('username')

        self.cars = self.page.client_storage.get('cars') or []
        self.bookings = self.page.client_storage.get('bookings') or []

        self.avatar_container = self.create_avatar_container()

        self.file_picker = self.create_file_picker()
        page.overlay.append(self.file_picker)

        page.clean()
        page.add(self.create_profile_page())

    def create_tabs(self):
        return ft.Tabs(
            tabs=[
                ft.Tab(
                    text='Мои автомобили',
                    content=ft.Container(
                        content=ft.Column(
                            controls=self.create_car_blocks()
                            + [
                                ft.ElevatedButton(
                                    text='Добавить автомобиль',
                                    on_click=self.on_add_car_click,
                                    bgcolor=ft.colors.PURPLE,
                                    color=ft.colors.WHITE,
                                )
                            ],
                            spacing=15,
                            scroll='adaptive',
                        ),
                        height=400,
                    ),
                ),
                ft.Tab(
                    text='Мои записи',
                    content=ft.Container(
                        content=ft.Column(
                            controls=self.create_booking_blocks()
                            or [
                                ft.Text(
                                    'Тут будут отображаться ваши записи...',
                                    size=14,
                                    color=ft.colors.GREY_500,
                                    weight=ft.FontWeight.NORMAL,
                                )
                            ],
                            spacing=15,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        height=400,
                    ),
                ),
            ],
            expand=True,
            animation_duration=300,
        )

    def create_profile_card(self):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                on_click=self.on_back_click,
                            ),
                            ft.Container(expand=1),
                            ft.IconButton(
                                icon=ft.icons.LOGOUT,
                                on_click=self.on_logout_click,
                            ),
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
                            self.username, size=20, weight=ft.FontWeight.BOLD
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
            bgcolor=ft.colors.GREY_900,
            padding=ft.padding.all(10),
            border_radius=ft.border_radius.all(20),
            height=250,
        )

    def create_profile_page(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.create_profile_card(),
                    self.create_tabs(),
                ],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                expand=True,
            ),
            width=350,
            height=720,
            padding=ft.padding.all(20),
            border_radius=ft.border_radius.all(12),
        )

    def create_car_blocks(self):
        car_blocks = []
        for index, car in enumerate(self.cars):
            print(f'Отображаем автомобиль: {car}')

            car_block = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"Марка: {car['brand']}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(f"Модель: {car['model']}"),
                                        ft.Text(
                                            f"Поколение: {car['generation']}"
                                        ),
                                        ft.Text(
                                            f"Тип кузова: "
                                            f"{car['body_type'] or
                                               'Не указан'}"
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                width=240,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e, i=index: self.on_delete_car(
                                    i
                                ),
                                icon_color=ft.colors.RED,
                                padding=ft.padding.only(left=10, bottom=35),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=ft.border_radius.all(15),
                ),
                width=300,
                elevation=2,
            )
            car_blocks.append(car_block)
        return car_blocks

    def create_booking_blocks(self):
        booking_blocks = []
        for index, booking in enumerate(self.bookings):
            booking_block = ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            f"Дата записи: {booking['date']}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"Место: {booking['location']}"
                                        ),
                                        ft.Text(
                                            f"Услуга: {booking['service']}"
                                        ),
                                    ],
                                    spacing=5,
                                ),
                                width=240,
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                on_click=lambda e,
                                i=index: self.on_delete_booking(i),
                                icon_color=ft.colors.RED,
                                padding=ft.padding.only(left=10, bottom=35),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    padding=ft.padding.all(10),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=ft.border_radius.all(15),
                ),
                width=300,
                elevation=2,
            )
            booking_blocks.append(booking_block)
        return booking_blocks

    def create_avatar_container(self):
        avatar_url = self.page.client_storage.get('avatar_url') or None

        if avatar_url:
            avatar_content = ft.Image(
                src=avatar_url,
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(50),
            )
        else:
            avatar_content = ft.Icon(
                ft.icons.PERSON,
                size=100,
                color=ft.colors.GREY,
            )

        self.avatar_image = avatar_content

        return ft.Container(
            content=self.avatar_image,
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
            avatar_url = e.files[0].path
            self.page.client_storage.set('avatar_url', avatar_url)

            self.avatar_container.content = ft.Image(
                src=avatar_url,
                width=100,
                height=100,
                fit=ft.ImageFit.COVER,  # Применяем обрезку сразу
                border_radius=ft.border_radius.all(50),
            )
            self.page.update()

    def on_delete_avatar_click(self, e):
        self.page.client_storage.remove('avatar_url')

        self.avatar_container.content = ft.Icon(
            ft.icons.PERSON, size=100, color=ft.colors.GREY
        )
        self.page.update()

    def on_add_car_click(self, e):
        SelectCarPage(self.page, self.on_car_saved)

    def on_car_saved(self, car):
        self.cars.append(car)
        self.page.client_storage.set('cars', self.cars)

        self.page.clean()
        self.page.add(self.create_profile_page())
        self.page.update()

    def on_delete_car(self, index):
        del self.cars[index]
        self.page.client_storage.set('cars', self.cars)

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
        self.page.client_storage.remove('avatar_url')
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)
