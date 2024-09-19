import datetime

import flet as ft


class BookingPage:
    def __init__(
        self, page: ft.Page, car_wash: dict, username: str, cars: list
    ):
        self.page = page
        self.car_wash = car_wash
        self.username = username
        self.cars = cars

        self.car_wash_image = ft.Container(
            width=300,
            height=200,
            bgcolor=ft.colors.GREY_200,
            content=ft.Text(
                'Фото автомойки', size=20, color=ft.colors.GREY_500
            ),
            alignment=ft.alignment.center,
            border_radius=ft.border_radius.all(10),
        )

        self.car_dropdown = ft.Dropdown(
            width=300,
            hint_text='Выберите автомобиль',
            options=self.load_user_cars(),
        )

        self.add_car_button = ft.ElevatedButton(
            text='Еще не добавили автомобиль?',
            on_click=self.on_add_car_click,
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )

        self.date_picker_button = ft.ElevatedButton(
            text='Выбрать дату',
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            width=300,
        )

        self.back_button = ft.ElevatedButton(
            text='Назад',
            on_click=self.on_back_click,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.page.clean()
        self.page.add(self.create_booking_page())

    def create_booking_page(self):
        return ft.Container(
            content=ft.Column(
                [
                    self.car_wash_image,
                    self.car_dropdown,
                    self.add_car_button,
                    self.date_picker_button,
                    self.back_button,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
            ),
            width=350,
            padding=ft.padding.all(20),
        )

    def load_user_cars(self):
        car_options = [
            ft.dropdown.Option(f"{car['brand']} {car['model']}")
            for car in self.cars
        ]
        return car_options

    def on_add_car_click(self, e):
        from washer.ui_components.select_car_page import SelectCarPage

        SelectCarPage(self.page, self.on_car_saved)

    def on_car_saved(self, car):
        self.cars.append(car)
        self.car_dropdown.options.append(
            ft.dropdown.Option(f"{car['brand']} {car['model']}")
        )
        self.car_dropdown.value = f"{car['brand']} {car['model']}"
        self.page.update()

    def open_date_picker(self, e):
        self.page.open(
            ft.DatePicker(
                first_date=datetime.datetime(year=2023, month=10, day=1),
                last_date=datetime.datetime(year=2024, month=10, day=1),
                on_change=self.on_date_change,
                on_dismiss=self.on_date_dismiss,
            )
        )

    def on_date_change(self, e):
        print(f'Выбрана дата: {e.data}')
        self.page.add(ft.Text(f'Вы выбрали дату: {e.data}'))
        self.page.update()

    def on_date_dismiss(self, e):
        print('Календарь закрыт без выбора даты.')

    def on_back_click(self, e):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)
