import datetime

import flet as ft
import httpx

from washer.api_requests import BackendApi


class BookingPage:
    def __init__(
        self, page: ft.Page, car_wash: dict, username: str, cars: list
    ):
        self.page = page
        self.car_wash = car_wash
        self.username = username
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.selected_car_id = None
        self.selected_box_id = None
        self.selected_date = None
        self.selected_time = None
        self.available_times = []
        self.cars = cars
        self.car_price = 0

        # Индикатор загрузки
        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.page.adaptive = True
        self.page.scroll = 'adaptive'

        self.car_dropdown = ft.Dropdown(
            width=300,
            hint_text='Выберите автомобиль',
            options=self.load_user_cars(),
            on_change=self.on_car_select,
        )

        self.add_car_button = ft.ElevatedButton(
            text='Еще не добавили авто?',
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

        self.box_dropdown = ft.Dropdown(
            label='Выберите бокс',
            width=300,
            options=[],
            on_change=self.on_box_select,
        )

        self.time_dropdown_container = ft.Column()

        self.price_text = ft.Text(
            'Стоимость: ₸0',
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.WHITE,
        )

        self.back_button = ft.ElevatedButton(
            text='Назад',
            on_click=self.on_back_click,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.book_button = ft.ElevatedButton(
            text='Забронировать',
            on_click=self.on_booking_click,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
        )

        self.page.clean()
        self.page.add(self.create_booking_page())
        self.page.overlay.append(self.loading_overlay)

        self.load_boxes()

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def create_booking_page(self):
        return ft.Container(
            content=ft.ListView(
                controls=[
                    self.car_dropdown,
                    self.add_car_button,
                    self.box_dropdown,
                    self.date_picker_button,
                    self.time_dropdown_container,
                    self.price_text,
                    self.book_button,
                    self.back_button,
                ],
                padding=ft.padding.all(20),
                spacing=20,
            ),
            margin=ft.margin.only(top=100),
            expand=True,
        )

    def load_user_cars(self):
        access_token = self.page.client_storage.get('access_token')
        user_id = self.page.client_storage.get('user_id')

        if not access_token or not user_id:
            print('Access token или user_id не найдены.')
            return []

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        url = f'{self.api.url.rstrip("/")}/cars?user_id={user_id}&limit=100'

        print(f'Отправляем запрос на {url} с заголовками {headers}')

        try:
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                cars = response.json().get('data', [])
                print(f'Автомобили успешно загружены: {cars}')

                if not cars:
                    print('Список автомобилей пуст.')

                self.cars = cars

                car_options = [
                    ft.dropdown.Option(
                        text=car.get(
                            'name',
                            (
                                f"{car.get('brand', 'Неизвестный бренд')} "
                                f"{car.get('model', 'Неизвестная модель')}"
                            ),
                        ),
                        key=str(car.get('id')),
                    )
                    for car in cars
                    if car.get('id')
                ]

                return car_options

            else:
                print(
                    f'Ошибка при загрузке автомобилей: '
                    f'{response.status_code} - {response.text}'
                )
                return []

        except httpx.RequestError as e:
            print(f'Произошла ошибка при попытке выполнить запрос: {str(e)}')
            return []

    def on_car_select(self, e):
        self.selected_car_id = e.control.value
        print(f'Выбран автомобиль с ID: {self.selected_car_id}')

        if self.selected_box_id and self.selected_date and self.selected_time:
            self.show_loading()

        selected_car = next(
            (
                car
                for car in self.cars
                if str(car['id']) == self.selected_car_id
            ),
            None,
        )

        if selected_car:
            configuration_id = selected_car.get('configuration_id')
            print(
                f'Configuration ID для выбранного автомобиля: '
                f'{configuration_id}'
            )

            if configuration_id:
                if (
                    self.selected_box_id
                    and self.selected_date
                    and self.selected_time
                ):
                    self.load_body_type_id(
                        configuration_id, auto_update_price=True
                    )
                else:
                    self.load_body_type_id(configuration_id)
            else:
                print('Configuration ID для автомобиля не определен.')
        else:
            print(
                f'Автомобиль с ID {self.selected_car_id} не найден в списке.'
            )

    def load_body_type_id(self, configuration_id, auto_update_price=False):
        url = (
            f"{self.api.url.rstrip('/')}/cars/configurations"
            f"?configuration_id={configuration_id}&limit=10000"
        )

        headers = {
            'Authorization': (
                f'Bearer {self.page.client_storage.get("access_token")}'
            ),
            'Accept': 'application/json',
        }

        print(f'Отправляем запрос на {url} с заголовками {headers}')
        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json().get('data', [])
            print(
                f'Конфигурации успешно загружены. '
                f'Всего конфигураций: {len(data)}'
            )

            selected_config = next(
                (
                    config
                    for config in data
                    if config['id'] == configuration_id
                ),
                None,
            )

            if selected_config:
                body_type_id = selected_config.get('body_type_id')
                print(
                    f'Тип кузова для конфигурации '
                    f'{configuration_id}: {body_type_id}'
                )

                if body_type_id:
                    self.load_car_price(body_type_id, auto_update_price)
                else:
                    print('Тип кузова для конфигурации не найден.')
            else:
                print(f'Конфигурация с ID {configuration_id} не найдена.')
        else:
            print(f'Ошибка при запросе конфигурации: {response.text}')

    def load_car_price(self, body_type_id, auto_update_price=False):
        response = self.api.get_prices(self.car_wash['id'])

        if response.status_code == 200:
            prices = response.json().get('data', [])
            print(f'Цены: {prices}')

            price = next(
                (
                    price
                    for price in prices
                    if price['body_type_id'] == body_type_id
                ),
                None,
            )

            if price:
                self.car_price = price['price']
                print(
                    f'Цена для автомобиля с типом кузова '
                    f'{body_type_id}: {self.car_price}'
                )
                if auto_update_price:
                    self.show_price()
                    self.hide_loading()
            else:
                print(f'Цена для body_type_id {body_type_id} не найдена.')
                self.hide_loading()
        else:
            print(f'Ошибка загрузки цены автомобиля: {response.text}')
            self.hide_loading()

    def show_price(self):
        self.price_text.value = f'Стоимость: ₸{int(self.car_price)}'
        self.page.update()

    def on_box_select(self, e):
        self.selected_box_id = e.control.value
        print(f'Выбранный бокс: {self.selected_box_id}')

        self.time_dropdown_container.controls = []
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
        self.selected_date = e.control.value.strftime('%Y-%m-%d')
        print(f'Выбрана дата: {self.selected_date}')

        if self.selected_box_id:
            self.load_available_times()
        else:
            print('Выберите бокс для отображения доступного времени.')

        self.page.update()

    def on_date_dismiss(self, e):
        print('Выбор даты отменен.')

    def load_available_times(self):
        if self.selected_box_id and self.selected_date:
            response = self.api.get_available_times(
                self.car_wash['id'], self.selected_date
            )
            if response.status_code == 200:
                all_times = (
                    response.json()
                    .get('available_times', {})
                    .get(str(self.selected_box_id), [])
                )
                print(f'Доступное время: {all_times}')

                self.available_times = self.parse_available_times(all_times)
                print(f'Доступные временные интервалы: {self.available_times}')

                self.time_dropdown_container.controls = [
                    self.create_time_dropdown()
                ]
                self.page.update()
            else:
                print(f'Ошибка загрузки доступного времени: {response.text}')
        else:
            print('Выберите бокс и дату.')

    def parse_available_times(self, times):
        parsed_times = []
        for time_range in times:
            start_time = datetime.datetime.fromisoformat(time_range[0])
            end_time = datetime.datetime.fromisoformat(time_range[1])

            while start_time + datetime.timedelta(hours=1) <= end_time:
                parsed_times.append(start_time.isoformat())
                start_time += datetime.timedelta(hours=1)

        return parsed_times

    def create_time_dropdown(self):
        return ft.Dropdown(
            expand=True,
            hint_text='Выберите доступное время',
            options=[
                ft.dropdown.Option(self.format_time(time_slot))
                for time_slot in self.available_times
            ],
            on_change=self.on_time_select,
        )

    def format_time(self, time_str):
        time_obj = datetime.datetime.fromisoformat(time_str)
        return time_obj.strftime('%H:%M')

    def on_time_select(self, e):
        self.selected_time = e.control.value
        print(f'Выбрано время: {self.selected_time}')
        self.show_price()

    def on_booking_click(self, e):
        if (
            self.selected_box_id
            and self.selected_time
            and self.selected_car_id
        ):
            start_datetime = f'{self.selected_date}T{self.selected_time}:00'

            try:
                booking_data = {
                    'box_id': self.selected_box_id,
                    'user_car_id': self.selected_car_id,
                    'is_exception': False,
                    'start_datetime': start_datetime,
                    'end_datetime': (
                        datetime.datetime.fromisoformat(start_datetime)
                        + datetime.timedelta(hours=2)
                    ).isoformat(),
                }
                response = self.api.create_booking(booking_data)

                if response.status_code == 200:
                    print('Букинг успешно создан!')
                else:
                    print(f'Ошибка создания букинга: {response.text}')
            except ValueError as ve:
                print(f'Ошибка при создании букинга: {ve}')
        else:
            print('Выберите бокс, автомобиль и время для букинга.')

    def on_add_car_click(self, e):
        from washer.ui_components.select_car_page import SelectCarPage

        SelectCarPage(self.page, self.on_car_saved)

    def on_car_saved(self, car):
        self.cars.append(car)
        self.car_dropdown.options.append(
            ft.dropdown.Option(f"{car['brand']} {car['model']}", car['id'])
        )
        self.car_dropdown.value = car['id']
        self.page.update()

    def load_boxes(self):
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            all_boxes = response.json().get('data', [])
            if all_boxes:
                print(f'Боксы успешно загружены: {all_boxes}')
                box_options = [
                    ft.dropdown.Option(str(box['id']), box['name'])
                    for box in all_boxes
                ]
                self.box_dropdown.options = box_options
                self.page.update()
            else:
                print('Список боксов пуст.')
        else:
            print(f'Ошибка загрузки боксов: {response.text}')

    def on_back_click(self, e):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)
