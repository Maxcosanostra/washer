import datetime

import flet as ft

from washer.api_requests import BackendApi


class BookingPage:
    def __init__(
        self,
        page: ft.Page,
        car_wash: dict,
        username: str,
        cars: list,
        location_data: dict = None,
    ):
        self.page = page
        self.car_wash = car_wash
        self.username = username
        self.api = BackendApi()
        self.location_data = location_data or {}
        self.api.set_access_token(self.page.client_storage.get('access_token'))

        self.selected_car_id = None
        self.selected_box_id = None
        self.selected_date = None
        self.selected_time = None
        self.selected_time_iso = None
        self.available_times = []
        self.cars = cars
        self.car_price = 0

        self.boxes = []
        self.available_boxes = []
        self.schedule_list = []

        self.car_dropdown_disabled = False
        self.box_dropdown_disabled = True
        self.date_picker_button_disabled = True
        self.time_dropdown_container_disabled = True
        self.book_button_disabled = True

        self.create_elements()

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.page.adaptive = True
        self.page.scroll = 'adaptive'

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_click,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text('Бронирование', size=20, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        self.page.floating_action_button = None
        self.page.update()

        self.page.clean()
        self.page.add(self.create_booking_page())
        self.page.overlay.append(self.loading_overlay)

        self.snack_bar = ft.SnackBar(
            content=ft.Text(
                '',
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ft.colors.RED,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

        self.load_schedules()
        self.load_boxes()

    def create_elements(self):
        self.add_car_button = ft.ElevatedButton(
            text='Еще не добавили авто?',
            on_click=self.on_add_car_click,
            width=300,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )

        self.car_dropdown = ft.Dropdown(
            width=300,
            hint_text='Выберите автомобиль',
            options=self.load_user_cars(),
            on_change=self.on_car_select,
            disabled=self.car_dropdown_disabled,
        )

        self.box_dropdown = ft.Dropdown(
            label='Выберите бокс',
            width=300,
            options=[],
            on_change=self.on_box_select,
            disabled=self.box_dropdown_disabled,
        )

        self.date_picker_button = ft.ElevatedButton(
            text='Выбрать дату',
            icon=ft.icons.CALENDAR_MONTH,
            on_click=self.open_date_picker,
            width=300,
            disabled=self.date_picker_button_disabled,
        )

        self.time_dropdown_container = ft.Column(
            disabled=self.time_dropdown_container_disabled
        )

        self.complex_wash_checkbox = ft.Checkbox(
            label='Комплексная мойка',
            disabled=True,
            on_change=self.on_complex_wash_change,
        )

        self.price_text = ft.Text(
            'Стоимость: ₸0',
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY,
        )

        self.book_button = ft.ElevatedButton(
            text='Забронировать',
            on_click=self.on_book_click,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            disabled=self.book_button_disabled,
        )

        self.back_button = ft.ElevatedButton(
            text='Назад',
            on_click=self.on_back_click,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

    def create_booking_page(self):
        return ft.Container(
            width=730,
            alignment=ft.alignment.center,
            content=ft.ListView(
                controls=[
                    self.create_car_wash_card(),
                    ft.Divider(),
                    self.car_dropdown,
                    self.add_car_button,
                    ft.Divider(),
                    self.date_picker_button,
                    self.box_dropdown,
                    self.time_dropdown_container,
                    ft.Divider(),
                    self.complex_wash_checkbox,
                    self.price_text,
                    self.book_button,
                ],
                padding=ft.padding.all(0),
                spacing=20,
            ),
            margin=ft.margin.all(0),
            expand=True,
        )

    def create_car_wash_card(self):
        image_link = self.car_wash.get('image_link', 'assets/spa_logo.png')
        location_address = (
            f"{self.location_data['city']}, {self.location_data['address']}"
            if self.location_data
            else 'Address not available'
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Image(
                                    src=image_link,
                                    fit=ft.ImageFit.COVER,
                                    width=float('inf'),
                                ),
                                height=170,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                f"{self.car_wash['name']}",
                                weight=ft.FontWeight.BOLD,
                                size=24,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                location_address,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.GREY,
                                size=16,
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.all(8),
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            width=400,
        )

    def load_user_cars(self):
        user_id = self.page.client_storage.get('user_id')

        if not user_id:
            print('User ID не найден.')
            self.cars = []
            self.update_add_car_button()
            return []

        response = self.api.get_user_cars(user_id=user_id, limit=100)

        if response.status_code == 200:
            cars = response.json().get('data', [])
            print(f'Автомобили успешно загружены: {cars}')
            self.cars = cars
            self.update_add_car_button()
            return [
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
        else:
            print(
                f'Ошибка при загрузке автомобилей: '
                f'{response.status_code}, {response.text}'
            )
            self.cars = []
            self.update_add_car_button()
            return []

    def update_add_car_button(self):
        if not self.cars or len(self.cars) == 0:
            self.add_car_button.text = 'Еще не добавили авто?'
        else:
            self.add_car_button.text = 'Добавить еще автомобиль'
        self.page.update()

    def on_car_select(self, e):
        self.selected_car_id = e.control.value
        print(f'Выбран автомобиль с ID: {self.selected_car_id}')

        self.selected_date = None
        self.selected_time = None
        self.selected_time_iso = None
        self.date_picker_button.text = 'Выбрать дату'
        self.date_picker_button.disabled = False
        self.box_dropdown.value = None
        self.box_dropdown.disabled = True
        self.time_dropdown_container.controls = []
        self.time_dropdown_container.disabled = True
        self.book_button.disabled = True
        self.complex_wash_checkbox.value = False
        self.complex_wash_checkbox.disabled = True
        self.price_text.value = 'Стоимость: ₸0'

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
                self.load_body_type_id(configuration_id)
            else:
                print('Configuration ID для автомобиля не определен.')

        else:
            print(
                f'Автомобиль с ID {self.selected_car_id} не найден в списке.'
            )

        self.page.update()

    def load_body_type_id(self, configuration_id, auto_update_price=False):
        self.show_loading()

        response = self.api.get_configuration_by_id(
            configuration_id=configuration_id, limit=10000
        )

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
                    self.hide_loading()
            else:
                print(f'Конфигурация с ID {configuration_id} не найдена.')
                self.hide_loading()
        else:
            print(
                f'Ошибка при запросе конфигурации: '
                f'{response.status_code}, {response.text}'
            )
            self.hide_loading()

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
        if self.complex_wash_checkbox.value:
            self.price_text.value = f'Стоимость: ₸{int(self.car_price)}'
            self.price_text.color = None
            self.book_button.disabled = False
        else:
            self.price_text.value = 'Стоимость: ₸0'
            self.price_text.color = ft.colors.GREY
            self.book_button.disabled = True
        self.page.update()

    def on_box_select(self, e):
        self.selected_box_id = int(e.control.value)
        print(f'Выбранный бокс: {self.selected_box_id}')

        self.selected_time = None
        self.selected_time_iso = None
        self.time_dropdown_container.controls = []
        self.time_dropdown_container.disabled = False
        self.book_button.disabled = True
        self.complex_wash_checkbox.value = False
        self.complex_wash_checkbox.disabled = True
        self.price_text.value = 'Стоимость: ₸0'

        self.load_available_times_for_box()

        self.page.update()

    def open_date_picker(self, e):
        print(f'Загруженные расписания: {self.schedule_list}')

        current_date = datetime.datetime.today()
        available_dates = []

        for schedule in self.schedule_list:
            if 'day_of_week' in schedule:
                day_of_week = schedule['day_of_week']
                delta_days = (day_of_week - current_date.weekday()) % 7
                target_date = current_date + datetime.timedelta(
                    days=delta_days
                )
                available_dates.append(target_date)

        print(f'Доступные даты: {available_dates}')

        if available_dates:
            first_date = min(available_dates)
            last_date = max(available_dates)
        else:
            first_date = current_date
            last_date = first_date

        self.page.open(
            ft.DatePicker(
                first_date=first_date,
                last_date=last_date,
                on_change=self.on_date_change,
                on_dismiss=self.on_date_dismiss,
            )
        )

    def load_schedules(self):
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            data = response.json()
            print(
                f'Расписания успешно загружены для автомойки '
                f'{self.car_wash["name"]}: {data}'
            )
            self.schedule_list = data.get('data', [])
            self.available_dates = [
                datetime.datetime.strptime(schedule['date'], '%Y-%m-%d')
                for schedule in self.schedule_list
                if 'date' in schedule
            ]
        else:
            print(f'Ошибка загрузки расписаний: {response.text}')
            self.schedule_list = []
            self.available_dates = []

        self.page.update()

    def on_date_change(self, e):
        self.selected_date = e.control.value
        if self.selected_date:
            self.date_picker_button.text = (
                f"Выбранная дата: {self.selected_date.strftime('%d.%m.%Y')}"
            )
            self.box_dropdown.disabled = False
            self.load_available_boxes()
            self.time_dropdown_container.controls = []
            self.time_dropdown_container.disabled = True
            self.book_button.disabled = True
            self.complex_wash_checkbox.value = False
            self.complex_wash_checkbox.disabled = True
            self.price_text.value = 'Стоимость: ₸0'
        else:
            self.date_picker_button.text = 'Выбрать дату'
            self.box_dropdown.disabled = True
            self.time_dropdown_container.controls = []
            self.time_dropdown_container.disabled = True
            self.book_button.disabled = True
            self.complex_wash_checkbox.value = False
            self.complex_wash_checkbox.disabled = True
            self.price_text.value = 'Стоимость: ₸0'
        self.page.update()

    def on_date_dismiss(self, e):
        print('Выбор даты отменен.')

    def load_available_boxes(self):
        if self.selected_date:
            self.show_loading()
            date_str = self.selected_date.strftime('%Y-%m-%d')
            response = self.api.get_available_times(
                self.car_wash['id'], date_str
            )

            if response.status_code == 200:
                available_times_data = response.json().get(
                    'available_times', {}
                )
                print(f'Available times data: {available_times_data}')

                available_box_ids = list(map(int, available_times_data.keys()))
                available_boxes = [
                    box for box in self.boxes if box['id'] in available_box_ids
                ]

                self.available_boxes = available_boxes

                self.box_dropdown.options = [
                    ft.dropdown.Option(text=box['name'], key=str(box['id']))
                    for box in self.available_boxes
                ]

                if not self.available_boxes:
                    self.box_dropdown.disabled = True
                    self.show_snack_bar(
                        'На выбранную дату нет доступных боксов.'
                    )
                else:
                    self.box_dropdown.disabled = False

                self.hide_loading()
            else:
                print(f'Ошибка загрузки доступных времен: {response.text}')
                self.show_snack_bar(
                    'Не удалось загрузить доступные времена.', ft.colors.RED
                )
                self.hide_loading()
        else:
            print('Дата не выбрана.')
            self.show_snack_bar('Пожалуйста, выберите дату.', ft.colors.RED)

    def load_available_times_for_box(self):
        if self.selected_box_id and self.selected_date:
            self.show_loading()
            date_str = self.selected_date.strftime('%Y-%m-%d')
            response = self.api.get_available_times(
                self.car_wash['id'], date_str
            )

            if response.status_code == 200:
                available_times_data = response.json().get(
                    'available_times', {}
                )
                box_times = available_times_data.get(
                    str(self.selected_box_id), []
                )
                print(
                    f'Available times for box '
                    f'{self.selected_box_id}: {box_times}'
                )

                filtered_times = self.parse_available_times(box_times)

                if not filtered_times:
                    self.time_dropdown_container.controls = [
                        ft.Container(
                            content=ft.Text(
                                'К сожалению, мест не осталось',
                                color=ft.colors.RED,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Выберите другой бокс',
                                color=ft.colors.RED,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ]
                    self.time_dropdown_container.disabled = True
                else:
                    morning_slots = [
                        slot for slot in filtered_times if 6 <= slot.hour < 12
                    ]
                    day_slots = [
                        slot for slot in filtered_times if 12 <= slot.hour < 18
                    ]
                    evening_slots = [
                        slot
                        for slot in filtered_times
                        if 18 <= slot.hour <= 22
                    ]

                    controls = []
                    if morning_slots:
                        controls.append(
                            ft.Text('Утро', size=20, weight=ft.FontWeight.BOLD)
                        )
                        controls.append(self.create_time_grid(morning_slots))
                    if day_slots:
                        controls.append(
                            ft.Text('День', size=20, weight=ft.FontWeight.BOLD)
                        )
                        controls.append(self.create_time_grid(day_slots))
                    if evening_slots:
                        controls.append(
                            ft.Text(
                                'Вечер', size=20, weight=ft.FontWeight.BOLD
                            )
                        )
                        controls.append(self.create_time_grid(evening_slots))

                    self.time_dropdown_container.controls = controls

                self.hide_loading()
                self.page.update()
            else:
                print(f'Ошибка загрузки доступных времен: {response.text}')
                self.show_snack_bar(
                    'Не удалось загрузить доступные времена.', ft.colors.RED
                )
                self.hide_loading()
        else:
            print('Не выбрана дата или бокс.')
            self.show_snack_bar(
                'Пожалуйста, выберите дату и бокс.', ft.colors.RED
            )

    def create_time_grid(self, time_slots):
        grid = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=120,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=2.5,
        )

        for time_slot in time_slots:
            grid.controls.append(self.create_time_button(time_slot))

        return grid

    def on_time_select_grid(self, time_slot_iso):
        self.selected_time_iso = time_slot_iso
        self.selected_time = datetime.datetime.fromisoformat(time_slot_iso)
        print(f'Selected time: {self.selected_time}')

        if self.selected_time:
            self.complex_wash_checkbox.disabled = False
            self.complex_wash_checkbox.value = False
            self.price_text.value = 'Стоимость: ₸0'
            self.book_button.disabled = True
            self.page.update()

        self.refresh_time_grid()
        self.page.update()

    def on_complex_wash_change(self, e):
        if self.complex_wash_checkbox.value:
            self.show_price()
        else:
            self.price_text.value = 'Стоимость: ₸0'
            self.price_text.color = ft.colors.GREY
            self.book_button.disabled = True
            self.page.update()

    def create_time_button(self, time_slot: datetime.datetime):
        is_selected = self.selected_time_iso == time_slot.isoformat()
        return ft.ElevatedButton(
            text=self.format_time(time_slot),
            on_click=lambda e: self.on_time_select_grid(time_slot.isoformat()),
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE if is_selected else ft.colors.GREY,
                color=ft.colors.WHITE if is_selected else ft.colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding={'top': 5, 'bottom': 5, 'left': 10, 'right': 10},
            ),
        )

    def parse_available_times(self, times):
        parsed_times = []
        now = datetime.datetime.now()

        if not self.selected_date:
            return parsed_times

        is_today = self.selected_date.date() == now.date()

        if is_today:
            ceil_hour = (now + datetime.timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
        else:
            ceil_hour = None

        for time_range in times:
            try:
                start_time = datetime.datetime.fromisoformat(time_range[0])
                end_time = datetime.datetime.fromisoformat(time_range[1])

                while start_time + datetime.timedelta(hours=2) <= end_time:
                    if is_today:
                        if start_time >= ceil_hour:
                            parsed_times.append(start_time)
                    else:
                        parsed_times.append(start_time)
                    start_time += datetime.timedelta(hours=1)
            except ValueError as e:
                print(f'Invalid time range detected: {time_range}, Error: {e}')
                continue

        return parsed_times

    def format_time(self, time_obj):
        return time_obj.strftime('%H:%M')

    def refresh_time_grid(self):
        if not self.selected_box_id or not self.selected_date:
            return

        date_str = self.selected_date.strftime('%Y-%m-%d')
        response = self.api.get_available_times(self.car_wash['id'], date_str)

        if response.status_code == 200:
            available_times_data = response.json().get('available_times', {})
            box_times = available_times_data.get(str(self.selected_box_id), [])
            print(
                f'Available times for box {self.selected_box_id}: {box_times}'
            )

            filtered_times = self.parse_available_times(box_times)

            if not filtered_times:
                self.time_dropdown_container.controls = [
                    ft.Text(
                        'К сожалению, мест не осталось',
                        color=ft.colors.RED,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    )
                ]
                self.time_dropdown_container.disabled = True
            else:
                morning_slots = [
                    slot for slot in filtered_times if 6 <= slot.hour < 12
                ]
                day_slots = [
                    slot for slot in filtered_times if 12 <= slot.hour < 18
                ]
                evening_slots = [
                    slot for slot in filtered_times if 18 <= slot.hour <= 22
                ]

                controls = []
                if morning_slots:
                    controls.append(
                        ft.Text('Утро', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(morning_slots))
                if day_slots:
                    controls.append(
                        ft.Text('День', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(day_slots))
                if evening_slots:
                    controls.append(
                        ft.Text('Вечер', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(evening_slots))

                self.time_dropdown_container.controls = controls

        else:
            print(f'Ошибка загрузки доступных времен: {response.text}')
            self.show_snack_bar(
                'Не удалось загрузить доступные времена.', ft.colors.RED
            )

    def on_book_click(self, e):
        if (
            self.selected_box_id
            and self.selected_time
            and self.selected_car_id
            and self.selected_date
        ):
            if not self.complex_wash_checkbox.value:
                self.show_snack_bar(
                    'Пожалуйста, активируйте чекбокс "Комплексная мойка" '
                    'для отображения стоимости.'
                )
                return
            self.show_confirmation_page()
        else:
            print('Выберите бокс, автомобиль, дату и время для букинга.')
            self.show_snack_bar(
                'Пожалуйста, выберите бокс, автомобиль, дату и время.'
            )

    def on_confirm_booking(self, e):
        if (
            self.selected_box_id
            and self.selected_time
            and self.selected_car_id
            and self.selected_date
        ):
            if not self.complex_wash_checkbox.value:
                self.show_snack_bar(
                    'Пожалуйста, активируйте чекбокс "Комплексная мойка" '
                    'для отображения стоимости.'
                )
                return
            try:
                start_datetime = self.selected_time.isoformat()

                end_datetime = (
                    self.selected_time + datetime.timedelta(hours=2)
                ).isoformat()

                booking_data = {
                    'box_id': self.selected_box_id,
                    'user_car_id': self.selected_car_id,
                    'is_exception': False,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                }

                print(f'Данные для бронирования: {booking_data}')

                self.show_loading()
                response = self.api.create_booking(booking_data)
                self.hide_loading()

                if response.status_code == 200:
                    print('Букинг успешно создан!')
                    self.show_success_page()
                else:
                    error_detail = response.json().get('detail', '')
                    print(f'Ошибка создания букинга: {response.text}')

                    if error_detail == (
                        'Booking for these start_datetime and '
                        'end_datetime is not available'
                    ):
                        self.show_snack_bar('Упс.. Вас кто-то опередил')
                    else:
                        self.show_snack_bar(
                            'Произошла ошибка при бронировании. '
                            'Попробуйте позже.'
                        )
            except ValueError as ve:
                print(f'Ошибка при создании букинга: {ve}')
                self.show_snack_bar('Произошла ошибка при обработке данных.')
        else:
            print('Выберите бокс, автомобиль, дату и время для букинга.')
            self.show_snack_bar(
                'Пожалуйста, выберите бокс, автомобиль, дату и время.'
            )

    def on_add_car_click(self, e):
        from washer.ui_components.select_car_page import SelectCarPage

        self.page.client_storage.set('redirect_to', 'booking_page')
        self.page.client_storage.set('car_wash_data', self.car_wash)
        self.page.client_storage.set('username', self.username)
        self.page.client_storage.set('cars', self.cars)
        self.page.client_storage.set('location_data', self.location_data)

        SelectCarPage(
            page=self.page,
            on_car_saved=self.on_car_saved,
            redirect_to='booking_page',
        )

    def on_car_saved(self, car):
        if 'id' not in car and 'user_car_id' in car:
            car['id'] = car['user_car_id']

        self.cars.append(car)

        self.car_dropdown.options.append(
            ft.dropdown.Option(
                text=(
                    f"{car.get('brand', 'Неизвестный бренд')} "
                    f"{car.get('model', 'Неизвестная модель')}"
                ),
                key=str(car['id']),
            )
        )

        self.car_dropdown.value = str(car['id'])

        self.page.client_storage.set('cars', self.cars)

        self.update_add_car_button()
        self.page.update()

    def load_boxes(self):
        self.show_loading()

        try:
            response = self.api.get_boxes(self.car_wash['id'])
            if response.status_code == 200:
                all_boxes = response.json().get('data', [])
                print(
                    f'Боксы успешно загружены для автомойки '
                    f'{self.car_wash["name"]}: {all_boxes}'
                )
                self.boxes = all_boxes
            else:
                print(f'Ошибка загрузки боксов: {response.text}')
                self.boxes = []
        except Exception as e:
            print(f'Ошибка загрузки боксов: {str(e)}')
            self.boxes = []
        finally:
            self.hide_loading()
            self.page.update()

    def on_back_click(self, e):
        self.page.appbar = None
        self.page.clean()

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)

        self.page.update()

    def show_confirmation_page(self):
        if self.box_dropdown.value:
            selected_box_option = next(
                (
                    option
                    for option in self.box_dropdown.options
                    if option.key == str(self.box_dropdown.value)
                ),
                None,
            )
            box_name = (
                selected_box_option.text
                if selected_box_option
                else 'Не выбран'
            )
        else:
            box_name = 'Не выбран'

        formatted_date = (
            self.selected_date.strftime('%d.%m.%Y')
            if self.selected_date
            else 'Не выбрана'
        )
        formatted_time = (
            self.selected_time.strftime('%H:%M')
            if isinstance(self.selected_time, datetime.datetime)
            else self.selected_time or 'Не выбрано'
        )
        price = f'₸{int(self.car_price)}'

        booking_details = [
            ('Бокс', box_name),
            ('Дата', formatted_date),
            ('Время', formatted_time),
            ('Цена', price),
        ]

        booking_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in booking_details
            ],
            spacing=10,
        )

        car_info_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            'Информация о записи',
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        booking_info_column,
                    ],
                    spacing=10,
                ),
                padding=ft.padding.all(20),
            ),
            elevation=3,
            margin=ft.margin.only(bottom=20),
        )

        confirm_button = ft.ElevatedButton(
            text='Подтвердить букинг',
            on_click=self.on_confirm_booking,
            width=300,
            bgcolor=ft.colors.GREEN,
            color=ft.colors.WHITE,
        )

        back_button = ft.ElevatedButton(
            text='Изменить',
            on_click=self.on_back_to_booking_page,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_to_booking_page,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=None,
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            'Пожалуйста, подтвердите свои данные',
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        car_info_card,
                        confirm_button,
                        back_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=ft.padding.all(20),
            )
        )

        self.page.update()

    def show_success_page(self):
        self.page.appbar = None

        self.page.clean()
        self.page.scroll = 'adaptive'

        success_icon = ft.Icon(
            ft.icons.CHECK_CIRCLE,
            color=ft.colors.GREEN,
            size=100,
        )

        success_message = ft.Text(
            'Букинг успешно совершен!',
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        confirm_button = ft.ElevatedButton(
            text='Принято',
            on_click=self.redirect_to_my_bookings_page,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            width=200,
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        success_icon,
                        ft.Container(height=20),
                        success_message,
                        ft.Container(height=40),
                        confirm_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.top_center,
                expand=True,
                padding=ft.padding.all(20),
                margin=ft.margin.only(top=200),
            )
        )

        self.page.update()

    def redirect_to_my_bookings_page(self, e):
        from washer.config import config
        from washer.ui_components.my_bookings_page import MyBookingsPage

        my_bookings_page = MyBookingsPage(
            page=self.page,
            api_url=config.api_url,
            car_wash=self.car_wash,
            location_data=self.location_data,
        )
        my_bookings_page.open()

    def on_back_to_booking_page(self, e):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_click,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text('Бронирование', size=20, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        self.page.clean()
        self.page.add(self.create_booking_page())
        self.page.overlay.append(self.loading_overlay)
        self.page.overlay.append(self.snack_bar)
        self.page.update()

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.RED):
        """
        Отображает SnackBar с заданным сообщением и цветом фона.
        """
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def show_success_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()
