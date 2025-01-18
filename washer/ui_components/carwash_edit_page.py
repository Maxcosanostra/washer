import datetime
import io
from datetime import date

import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.archived_schedule_page import ArchivedSchedulePage
from washer.ui_components.schedule_management_page import (
    ScheduleManagementPage,
)


class CarWashEditPage:
    def __init__(self, page: ft.Page, car_wash, locations):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.locations = locations or self.fetch_locations()
        self.selected_image = None
        self.selected_image_bytes = None
        self.original_image = self.car_wash['image_link']
        self.body_type_dict = {}
        self.total_revenue = 0
        self.boxes_list = []
        self.show_change_button = False
        self.show_save_button = False
        self.show_cancel_button = False
        self.page.adaptive = True

        app_bar = ft.AppBar(
            leading=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.on_back_to_admin_page,
                        icon_color='#ef7b00',
                        padding=ft.padding.only(left=10),
                    ),
                    ft.Text('Назад', size=16, color='#ef7b00'),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=100,
        )

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.page.navigation_bar = self.create_navigation_bar()

        self.image_picker = ft.FilePicker(on_result=self.on_image_picked)
        self.page.overlay.append(self.image_picker)

        self.page.clean()
        self.page.add(app_bar)
        self.page.overlay.append(self.loading_overlay)

        self.show_loading()
        self.reset_data()
        self.load_boxes()
        self.load_body_types()
        self.load_schedules()
        self.load_total_revenue()

        if self.boxes_list:
            self.today_bookings = self.load_today_bookings()
        else:
            self.today_bookings = []

        self.hide_loading()

        self.page.add(self.create_edit_page())
        self.page.update()

    def create_navigation_bar(self):
        navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.ATTACH_MONEY,
                    selected_icon=ft.icons.ATTACH_MONEY_OUTLINED,
                    label='Цены',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.CALENDAR_TODAY,
                    selected_icon=ft.icons.CALENDAR_TODAY_OUTLINED,
                    label='График',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.HOME,
                    selected_icon=ft.icons.HOME_OUTLINED,
                    label='Главная',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.GARAGE,
                    selected_icon=ft.icons.GARAGE_OUTLINED,
                    label='Боксы',
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.VIEW_LIST,
                    selected_icon=ft.icons.VIEW_LIST_OUTLINED,
                    label='Букинги',
                ),
            ],
            selected_index=2,
            on_change=self.on_navigation_change,
            indicator_color='#ef7b00',
            label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
        )
        return navigation_bar

    def on_navigation_change(self, e):
        selected_index = e.control.selected_index
        print(
            f'[CarWashEditPage] NavigationBar selected index: {selected_index}'
        )
        if selected_index == 0:
            self.on_prices_button_click(None)
        elif selected_index == 1:
            self.on_schedule_button_click(None)
        elif selected_index == 2:
            return
        elif selected_index == 3:
            self.on_boxes_button_click(None)
        elif selected_index == 4:
            self.on_booking_button_click(None)

    def reset_data(self):
        self.boxes_list = []
        self.schedule_list = []
        self.dates_storage = {}
        self.today_bookings = []
        self.total_revenue = 0
        print(f'Данные сброшены для автомойки {self.car_wash["id"]}.')

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def fetch_locations(self):
        print('Загружаем данные о локациях через API...')
        response = self.api.get_locations()

        if response.status_code == 200:
            locations = response.json().get('data', [])
            print(f'Загруженные локации: {locations}')
            return {loc['id']: loc for loc in locations}
        else:
            print(f'Ошибка загрузки локаций: {response.text}')
            return {}

    def load_schedules(self):
        self.schedule_list = []
        self.dates_storage = {}
        print(f'Загрузка расписаний для автомойки {self.car_wash["id"]}')
        self.show_loading()
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            self.schedule_list = [
                schedule
                for schedule in response.json().get('data', [])
                if schedule['car_wash_id'] == self.car_wash['id']
            ]
            self.initialize_dates_for_schedule()
            print(
                f'Загружено расписаний: {len(self.schedule_list)} '
                f'для автомойки {self.car_wash["id"]}'
            )
        else:
            print(
                f'Ошибка загрузки расписаний для автомойки '
                f'{self.car_wash["id"]}: {response.text}'
            )
        self.hide_loading()

    def initialize_dates_for_schedule(self):
        current_date = datetime.date.today()
        self.dates_storage = {}
        for schedule in self.schedule_list:
            day_of_week = schedule['day_of_week']
            delta_days = (day_of_week - current_date.weekday()) % 7
            target_date = current_date + datetime.timedelta(days=delta_days)
            self.dates_storage[day_of_week] = target_date.strftime('%Y-%m-%d')

    def load_total_revenue(self):
        car_wash_id = None
        try:
            car_wash_id = self.car_wash['id']
            response = self.api.get_bookings(car_wash_id)
            if response and response.status_code == 200:
                bookings_data = response.json().get('data', [])
                current_date_str = datetime.date.today().strftime('%Y-%m-%d')
                total_revenue = 0
                for booking in bookings_data:
                    booking_date = booking.get('start_datetime', '')
                    status = booking.get('state', '').upper()

                    if status == 'COMPLETED' and booking_date.startswith(
                        current_date_str
                    ):
                        price = float(booking.get('total_price', 0))
                        total_revenue += price

                self.total_revenue = total_revenue
                print(
                    f'Общая выручка для автомойки '
                    f'{car_wash_id}: {self.total_revenue} ₸'
                )

                if hasattr(self, 'total_revenue_text'):
                    self.total_revenue_text.value = f'{self.total_revenue} ₸'
                    self.total_revenue_text.color = ft.colors.WHITE
                    self.total_revenue_text.update()
            else:
                print(
                    f'Ошибка загрузки букингов для автомойки {car_wash_id}: '
                    f'{response.status_code if response else "No response"}, '
                    f'{response.text if response else ""}'
                )
                self.total_revenue = 0
                if hasattr(self, 'total_revenue_text'):
                    self.total_revenue_text.value = '0 ₸'
                    self.total_revenue_text.color = ft.colors.WHITE
                    self.total_revenue_text.update()
        except Exception as e:
            print(
                f'Ошибка при загрузке букингов для автомойки '
                f'{car_wash_id}: {e}'
            )
            self.total_revenue = 0
            if hasattr(self, 'total_revenue_text'):
                self.total_revenue_text.value = '0 ₸'
                self.total_revenue_text.color = ft.colors.WHITE
                self.total_revenue_text.update()

    def load_today_bookings(self):
        car_wash_id = self.car_wash['id']
        response = self.api.get_bookings(car_wash_id)
        if response.status_code == 200:
            all_bookings = response.json().get('data', [])
            today = datetime.date.today().strftime('%Y-%m-%d')
            today_bookings = [
                booking
                for booking in all_bookings
                if booking['start_datetime'].startswith(today)
            ]
            for booking in today_bookings:
                box = next(
                    (
                        bx
                        for bx in self.boxes_list
                        if bx['id'] == booking['box_id']
                    ),
                    None,
                )
                booking['box_name'] = (
                    box['name'] if box else 'Неизвестный бокс'
                )
                if box is None:
                    print(f"Не удалось найти бокс с ID: {booking['box_id']}")
            return today_bookings
        else:
            print(
                f'Ошибка загрузки букингов для автомойки {car_wash_id}: '
                f'{response.status_code}, {response.text}'
            )
            return []

    def load_boxes(self):
        self.boxes_list = []
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            self.boxes_list = [
                box
                for box in response.json().get('data', [])
                if box['car_wash_id'] == self.car_wash['id']
            ]
            print(
                f'Боксы для автомойки {self.car_wash["id"]} успешно загружены.'
            )
        else:
            print(
                f'Ошибка загрузки боксов для автомойки '
                f'{self.car_wash["id"]}: {response.text}'
            )

    def create_edit_page(self):
        location_id = self.car_wash.get('location_id')
        location = self.locations.get(location_id, {})
        city = location.get('city', 'Неизвестный город')
        address = location.get('address', 'Неизвестный адрес')

        print(
            f'Создаем страницу редактирования '
            f'для города: {city}, адрес: {address}'
        )

        location_display = f'{city}, {address}'

        self.avatar_container = ft.Container(
            content=ft.Image(
                src=self.car_wash['image_link'],
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
            ),
            alignment=ft.alignment.center,
            on_click=self.on_avatar_click,
        )

        self.change_button = ft.TextButton(
            text='Изменить изображение',
            on_click=lambda _: self.image_picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE,
            ),
            visible=self.show_change_button,
        )
        self.save_button = ft.TextButton(
            text='Сохранить',
            on_click=self.on_save_click,
            style=ft.ButtonStyle(color=ft.colors.WHITE),
            visible=self.show_save_button,
        )
        self.cancel_button = ft.TextButton(
            text='Отменить',
            on_click=self.on_cancel_click,
            style=ft.ButtonStyle(color=ft.colors.RED),
            visible=self.show_cancel_button,
        )

        self.booking_status_dashboard = ft.Container(
            content=self.create_booking_status_dashboard(),
            padding=ft.padding.symmetric(vertical=10),
        )

        self.created_bookings_dashboard = ft.Container(
            content=self.create_created_bookings_section(),
            padding=ft.padding.symmetric(vertical=10),
        )

        self.total_revenue_text = ft.Text(
            f'{self.total_revenue} ₸',
            size=40,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.WHITE,
        )
        self.total_revenue_card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=self.total_revenue_text,
                    padding=ft.padding.all(20),
                    alignment=ft.alignment.center,
                ),
                elevation=2,
                width=300,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=10),
        )

        main_content = ft.ListView(
            controls=[
                ft.Container(height=10),
                self.avatar_container,
                ft.Row(
                    controls=[
                        self.change_button,
                        self.save_button,
                        self.cancel_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Text(
                        f"{self.car_wash['name']}",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.padding.only(top=5),
                ),
                ft.Container(
                    content=ft.Text(
                        f'{location_display}',
                        size=16,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY,
                    ),
                    padding=ft.padding.only(bottom=5),
                ),
                ft.Divider(),
                self.total_revenue_card,
                self.created_bookings_dashboard,
                ft.Divider(),
                self.booking_status_dashboard,
                ft.Divider(),
                self.create_schedule_list_section(),
                ft.Divider(),
                ft.TextButton(
                    text='Архив расписаний',
                    on_click=self.on_view_archived_schedule_click,
                    style=ft.ButtonStyle(color='#ef7b00'),
                    expand=True,
                ),
            ],
            spacing=5,
            padding=ft.padding.only(right=15),
            expand=True,
        )

        return ft.Container(
            content=main_content,
            margin=ft.margin.only(top=-10),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
        )

    def create_created_bookings_section(self):
        section_header = ft.Text(
            'Новые букинги', size=24, weight=ft.FontWeight.BOLD
        )
        bookings_container = ft.Column(controls=[], spacing=10, expand=True)
        created_bookings = [
            b for b in self.today_bookings if b.get('state') == 'CREATED'
        ]

        if not created_bookings:
            bookings_container.controls.append(
                ft.Text(
                    'Нет букингов',
                    size=16,
                    color=ft.colors.GREY,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        else:
            for booking in created_bookings:
                user_car = booking.get('user_car', {})
                user_info = user_car.get('user', {})
                first_name = user_info.get('first_name', 'Неизвестный')
                last_name = user_info.get('last_name', 'Клиент')
                full_name = f'{first_name} {last_name}'.strip()
                phone_number = user_info.get(
                    'phone_number', 'Неизвестный номер'
                )
                user_id = user_info.get('id', None)

                car_name = user_car.get('name', 'Неизвестный автомобиль')
                license_plate = user_car.get(
                    'license_plate', 'Неизвестный номер'
                )

                start_time = datetime.datetime.fromisoformat(
                    booking['start_datetime']
                ).strftime('%H:%M')
                end_time = datetime.datetime.fromisoformat(
                    booking['end_datetime']
                ).strftime('%H:%M')
                time_range = f'{start_time} - {end_time}'
                box_name = booking.get('box_name', 'Неизвестный бокс')
                total_price = booking.get('total_price', '0.00 ₸')
                notes = booking.get('notes', '').strip()

                confirm_button = ft.ElevatedButton(
                    text='Подтвердить',
                    on_click=lambda e,
                    b_id=booking['id']: self.show_confirmation_dialog(b_id),
                    bgcolor=ft.colors.ORANGE,
                    color=ft.colors.WHITE,
                )

                decline_button = ft.TextButton(
                    text='Отказать',
                    on_click=lambda e,
                    b_id=booking['id']: self.show_decline_dialog(b_id),
                    style=ft.ButtonStyle(color=ft.colors.RED),
                )

                buttons_column = ft.Column(
                    controls=[
                        confirm_button,
                        ft.Container(height=5),
                        decline_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                )

                booking_controls = [
                    ft.Text(
                        'Пользователь',
                        weight=ft.FontWeight.BOLD,
                        size=16,
                    ),
                    ft.Row(
                        [
                            ft.Icon(
                                ft.icons.PERSON,
                                size=20,
                                color=ft.colors.BLUE_600,
                            ),
                            ft.Text(
                                full_name,
                                width=200,
                                text_align=ft.TextAlign.LEFT,
                            ),
                        ]
                    ),
                ]

                if user_id != 1:
                    booking_controls.extend(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.PHONE,
                                        size=20,
                                        color=ft.colors.GREEN_600,
                                    ),
                                    ft.Text(
                                        phone_number,
                                        width=200,
                                        text_align=ft.TextAlign.LEFT,
                                    ),
                                ]
                            ),
                        ]
                    )

                booking_controls.extend(
                    [
                        ft.Divider(thickness=1, color=ft.colors.GREY_300),
                        ft.Text(
                            'Информация о записи',
                            weight=ft.FontWeight.BOLD,
                            size=16,
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.ACCESS_TIME,
                                    size=20,
                                    color=ft.colors.ORANGE_600,
                                ),
                                ft.Text(
                                    time_range,
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.INBOX,
                                    size=20,
                                    color=ft.colors.PURPLE_600,
                                ),
                                ft.Text(
                                    box_name,
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.ATTACH_MONEY,
                                    size=20,
                                    color=ft.colors.GREEN_600,
                                ),
                                ft.Text(
                                    f'{total_price}',
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ]
                        ),
                    ]
                )

                additions = booking.get('additions', [])
                if additions:
                    additional_services = ', '.join(
                        [addition['name'] for addition in additions]
                    )
                    booking_controls.extend(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.ADD,
                                        size=20,
                                        color=ft.colors.BLUE_600,
                                    ),
                                    ft.Text(
                                        additional_services,
                                        width=200,
                                        text_align=ft.TextAlign.LEFT,
                                    ),
                                ],
                                visible=True,
                            ),
                        ]
                    )

                booking_controls.extend(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.NOTE,
                                    size=20,
                                    color=ft.colors.RED_600,
                                ),
                                ft.Text(
                                    notes if notes else 'Нет',
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ],
                            visible=bool(notes),
                        ),
                        ft.Divider(thickness=1, color=ft.colors.GREY_300),
                        ft.Text(
                            'Автомобиль',
                            weight=ft.FontWeight.BOLD,
                            size=16,
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.DIRECTIONS_CAR,
                                    size=20,
                                    color=ft.colors.BLUE_GREY_600,
                                ),
                                ft.Text(
                                    car_name,
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ]
                        ),
                        ft.Row(
                            [
                                ft.Icon(
                                    ft.icons.NUMBERS,
                                    size=20,
                                    color=ft.colors.PINK_600,
                                ),
                                ft.Text(
                                    license_plate,
                                    width=200,
                                    text_align=ft.TextAlign.LEFT,
                                ),
                            ]
                        ),
                        buttons_column,
                    ]
                )

                booking_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=booking_controls,
                            spacing=10,
                        ),
                        padding=ft.padding.all(10),
                    ),
                    elevation=2,
                )
                bookings_container.controls.append(booking_card)

        return ft.Column(
            controls=[section_header, bookings_container],
            spacing=10,
        )

    def on_confirm_booking(self, booking_id):
        print(f'Подтверждение букинга ID: {booking_id}')
        self.show_loading()
        updated_data = {'state': 'ACCEPTED'}
        response = self.api.update_booking(booking_id, updated_data)

        if response and response.status_code == 200:
            for booking in self.today_bookings:
                if booking['id'] == booking_id:
                    booking['state'] = 'ACCEPTED'
                    break
            self.show_success_message(
                f'Букинг ID {booking_id} успешно подтвержден'
            )
            self.update_booking_status_dashboard()
            self.update_created_bookings_dashboard()
        else:
            print(
                f'Ошибка при подтверждении букинга ID '
                f'{booking_id}: {response.text if response else "No response"}'
            )
            self.show_error_message(
                f'Ошибка при подтверждении букинга ID {booking_id}'
            )

        self.hide_loading()
        self.page.update()

    def update_created_bookings_dashboard(self):
        print('Обновление таблицы новых букингов (CREATED)...')
        self.created_bookings_dashboard.content = (
            self.create_created_bookings_section()
        )
        self.created_bookings_dashboard.update()
        print('Таблица новых букингов обновлена.')

    def create_booking_status_dashboard(self):
        header = ft.Row(
            controls=[
                ft.Text(
                    'Время начала',
                    weight=ft.FontWeight.BOLD,
                    width=70,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Время окончания',
                    weight=ft.FontWeight.BOLD,
                    width=90,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Бокс',
                    weight=ft.FontWeight.BOLD,
                    width=70,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Статус',
                    weight=ft.FontWeight.BOLD,
                    width=150,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        rows = [header]

        filtered_bookings = [
            b for b in self.today_bookings if b.get('state') != 'CREATED'
        ]
        sorted_bookings = sorted(
            filtered_bookings, key=lambda b: b['start_datetime']
        )

        if not sorted_bookings:
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            'Записей на сегодня нет',
                            size=16,
                            color=ft.colors.GREY,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )
        else:
            for booking in sorted_bookings:
                booking_id = booking.get('id')
                start_time = datetime.datetime.fromisoformat(
                    booking['start_datetime']
                ).strftime('%H:%M')
                end_time = datetime.datetime.fromisoformat(
                    booking['end_datetime']
                ).strftime('%H:%M')
                state = booking.get('state', 'CREATED').upper()
                notes = booking.get('notes', '')
                box_name = booking.get('box_name', 'Неизвестный бокс')

                status_info = self.get_status_info(state)
                display_text = status_info['text']

                status_btn = ft.TextButton(
                    text=display_text,
                    style=ft.ButtonStyle(
                        color={ft.MaterialState.DEFAULT: status_info['color']},
                    ),
                    on_click=lambda e,
                    b_id=booking_id,
                    c_notes=notes,
                    st=state: self.create_radio_dialog(b_id, c_notes, st),
                )

                row = ft.Row(
                    controls=[
                        ft.Text(
                            start_time,
                            width=70,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            end_time, width=90, text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            box_name, width=70, text_align=ft.TextAlign.CENTER
                        ),
                        status_btn,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                rows.append(row)

                if state == 'STARTED':
                    progress_bar = ft.ProgressBar(
                        width=600,
                        height=10,
                        color=ft.colors.ORANGE,
                        bgcolor=ft.colors.TRANSPARENT,
                        value=None,
                    )
                    progress_container = ft.Container(
                        content=progress_bar,
                        padding=ft.padding.only(top=5, bottom=10),
                    )
                    rows.append(progress_container)

        return ft.Column(
            controls=[
                ft.Text('Статус букингов', size=24, weight=ft.FontWeight.BOLD)
            ]
            + rows,
            spacing=10,
        )

    def create_radio_dialog(self, booking_id, current_notes, current_state):
        radio_values = [
            ('CREATED', 'Новый'),
            ('ACCEPTED', 'Подтвержден'),
            ('STARTED', 'В процессе'),
            ('COMPLETED', 'Завершено'),
            ('EXCEPTION', 'Ошибка'),
        ]

        color_mapping = {
            'CREATED': '#40E0D0',  # Бирюзовый
            'ACCEPTED': '#87CEFA',  # Голубой
            'STARTED': '#FFA500',  # Оранжевый
            'COMPLETED': '#32CD32',  # Зеленый
            'EXCEPTION': '#FF0000',  # Красный
        }

        initial_value = None
        for val, _ in radio_values:
            if val == current_state:
                initial_value = val
                break

        def create_radio_line(value, label):
            text_color = color_mapping.get(value, '#808080')

            r = ft.Radio(value=value)
            t = ft.Text(label, size=20, color=text_color)

            def on_line_click(_):
                radio_group.value = value
                radio_group.update()

            return ft.Container(
                content=ft.Row(
                    controls=[r, t],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(vertical=5),
                on_click=on_line_click,
            )

        lines = [create_radio_line(val, lbl) for val, lbl in radio_values]

        radio_group = ft.RadioGroup(
            content=ft.Column(lines), value=initial_value
        )

        save_button = ft.ElevatedButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_radio_selection(
                e, booking_id, radio_group.value, current_notes
            ),
        )

        dialog = ft.AlertDialog(
            title=ft.Text('Выбор статуса'),
            content=ft.Column(
                controls=[ft.Container(height=10), radio_group],
                spacing=10,
            ),
            actions=[
                save_button,
                ft.TextButton(
                    'Отмена', on_click=lambda _: self.close_dialog()
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def on_save_radio_selection(self, e, booking_id, new_state, current_notes):
        print(
            f'[on_save_radio_selection] '
            f'booking_id={booking_id}, new_state={new_state}'
        )
        self.close_dialog()
        self.show_status_change_dialog(booking_id, new_state, current_notes)

    def get_status_info(self, state):
        status_mapping = {
            'CREATED': {'text': 'Новый', 'color': '#40E0D0'},
            'ACCEPTED': {'text': 'Подтвержден', 'color': '#87CEFA'},
            'STARTED': {'text': 'В процессе', 'color': '#FFA500'},
            'COMPLETED': {'text': 'Завершено', 'color': '#32CD32'},
            'EXCEPTION': {'text': 'Ошибка', 'color': '#FF0000'},
        }
        return status_mapping.get(
            state, {'text': 'Неизвестно', 'color': '#808080'}
        )

    def on_status_change(self, e, booking_id, current_notes):
        new_state = e.control.value
        self.show_status_change_dialog(booking_id, new_state, current_notes)

    def show_status_change_dialog(self, booking_id, new_state, current_notes):
        if new_state == 'COMPLETED':
            existing_notes_text = ft.Text(
                f'Существующие заметки: {current_notes}'
                if current_notes
                else 'Существующих заметок нет.',
                size=14,
                color=ft.colors.GREY,
                selectable=True,
            )
            notes_field = ft.TextField(
                label='Добавить заметки',
                hint_text='Введите дополнительные заметки...',
                multiline=True,
                width=300,
            )
            dialog_content = ft.Column(
                [
                    ft.Text(
                        f"Вы уверены, что хотите изменить статус "
                        f"на '{self.get_status_info(new_state)['text']}'?"
                    ),
                    existing_notes_text,
                    notes_field,
                ],
                spacing=10,
            )
        else:
            dialog_content = ft.Text(
                f"Вы уверены, что хотите изменить статус "
                f"на '{self.get_status_info(new_state)['text']}'?"
            )

        save_button = ft.ElevatedButton(
            text='Сохранить',
            on_click=lambda _: self.confirm_status_change(
                booking_id,
                new_state,
                notes_field.value if new_state == 'COMPLETED' else None,
            ),
        )
        cancel_button = ft.TextButton(
            text='Отмена',
            on_click=lambda _: self.close_dialog(),
        )
        dialog = ft.AlertDialog(
            title=ft.Text('Изменение статуса букинга'),
            content=dialog_content,
            actions=[save_button, cancel_button],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def close_dialog(self):
        if hasattr(self.page, 'dialog') and self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def confirm_status_change(self, booking_id, new_state, additional_notes):
        if new_state == 'COMPLETED' and additional_notes:
            existing_notes = next(
                (
                    booking['notes']
                    for booking in self.today_bookings
                    if booking['id'] == booking_id
                ),
                '',
            )
            if existing_notes:
                updated_notes = existing_notes + '\n' + additional_notes
            else:
                updated_notes = additional_notes
        else:
            existing_notes = next(
                (
                    booking['notes']
                    for booking in self.today_bookings
                    if booking['id'] == booking_id
                ),
                '',
            )
            updated_notes = existing_notes

        updated_data = {'state': new_state, 'notes': updated_notes}
        response = self.api.update_booking(booking_id, updated_data)

        if response and response.status_code == 200:
            for booking in self.today_bookings:
                if booking['id'] == booking_id:
                    booking['state'] = new_state
                    booking['notes'] = updated_notes
                    break
            self.close_dialog()
            self.show_success_message('Статус успешно обновлён')
            self.load_total_revenue()
            self.update_booking_status_dashboard()
            self.update_created_bookings_dashboard()
        else:
            self.close_dialog()
            self.show_error_message('Ошибка при обновлении статуса')
        self.page.update()

    def create_schedule_list_section(self):
        header = ft.Row(
            controls=[
                ft.Text(
                    'Дата',
                    weight=ft.FontWeight.BOLD,
                    width=80,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'День недели',
                    weight=ft.FontWeight.BOLD,
                    width=120,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Время',
                    weight=ft.FontWeight.BOLD,
                    width=120,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        rows = [header]
        sorted_schedules = sorted(
            self.schedule_list,
            key=lambda x: datetime.datetime.strptime(
                self.dates_storage.get(x['day_of_week'], '1970-01-01'),
                '%Y-%m-%d',
            ),
        )
        for schedule in sorted_schedules:
            day_of_week = schedule['day_of_week']
            schedule_date = datetime.datetime.strptime(
                self.dates_storage.get(day_of_week, '1970-01-01'), '%Y-%m-%d'
            ).strftime('%d.%m')
            day_name = self.get_day_name(day_of_week)
            start_time = datetime.datetime.strptime(
                schedule['start_time'], '%H:%M:%S'
            ).strftime('%H:%M')
            end_time = datetime.datetime.strptime(
                schedule['end_time'], '%H:%M:%S'
            ).strftime('%H:%M')

            row = ft.Row(
                controls=[
                    ft.Text(
                        schedule_date, width=80, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        day_name, width=120, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f'{start_time} - {end_time}',
                        width=120,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            rows.append(row)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Текущее расписание',
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                    *rows,
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(vertical=10),
        )

    def get_day_name(self, day_of_week):
        days_of_week_names = [
            'Понедельник',
            'Вторник',
            'Среда',
            'Четверг',
            'Пятница',
            'Суббота',
            'Воскресенье',
        ]
        return days_of_week_names[day_of_week]

    def on_schedule_button_click(self, e):
        self.page.navigation_bar.selected_index = 1
        self.page.update()
        ScheduleManagementPage(self.page, self.car_wash, self.locations)
        self.page.update()

    def on_boxes_button_click(self, e):
        from washer.ui_components.box_management_page import BoxManagementPage

        self.page.navigation_bar.selected_index = 3
        self.page.update()
        BoxManagementPage(self.page, self.car_wash, self.locations)

    def on_prices_button_click(self, e):
        from washer.ui_components.price_management_page import (
            PriceManagementPage,
        )

        self.page.navigation_bar.selected_index = 0
        self.page.update()
        prices = self.load_prices()
        PriceManagementPage(
            self.page,
            self.car_wash,
            self.body_type_dict,
            prices,
            self.locations,
        )

    def on_booking_button_click(self, e):
        from washer.ui_components.admin_booking_table import AdminBookingTable

        self.page.navigation_bar.selected_index = 4
        self.page.update()
        current_date = str(date.today())
        AdminBookingTable(
            self.page, self.car_wash, current_date, locations=self.locations
        )

    def load_prices(self):
        response = self.api.get_prices(self.car_wash['id'])
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f'Ошибка загрузки цен: {response.text}')
            return []

    def on_avatar_click(self, e):
        self.show_change_button = not self.show_change_button
        self.update_button_visibility(
            show_change=self.show_change_button,
            show_save=False,
            show_cancel=False,
        )

    def on_image_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.original_image = self.car_wash['image_link']
            self.selected_image = e.files[0].path
            if hasattr(e.files[0], 'bytes') and e.files[0].bytes:
                self.selected_image_bytes = e.files[0].bytes
            self.avatar_container.content = ft.Image(
                src=self.selected_image,
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
            )
            self.update_button_visibility(
                show_change=False, show_save=True, show_cancel=True
            )
            self.page.update()

    def on_cancel_click(self, e):
        self.avatar_container.content = ft.Image(
            src=self.original_image,
            width=150,
            height=150,
            fit=ft.ImageFit.COVER,
            border_radius=ft.border_radius.all(100),
        )
        self.update_button_visibility(
            show_change=False, show_save=False, show_cancel=False
        )
        self.page.update()

    def on_save_click(self, e):
        if self.selected_image or self.selected_image_bytes:
            self.show_loading()
            self.upload_image()
            self.update_button_visibility(
                show_change=False, show_save=False, show_cancel=False
            )
            self.hide_loading()
            self.page.update()

    def update_button_visibility(self, show_change, show_save, show_cancel):
        self.show_change_button = show_change
        self.show_save_button = show_save
        self.show_cancel_button = show_cancel
        self.change_button.visible = show_change
        self.save_button.visible = show_save
        self.cancel_button.visible = show_cancel
        self.page.update()

    def upload_image(self):
        files = None
        if self.selected_image_bytes:
            files = {
                'image': ('image.png', io.BytesIO(self.selected_image_bytes))
            }
        elif self.selected_image:
            try:
                with open(self.selected_image, 'rb') as img_file:
                    files = {'image': img_file}
            except FileNotFoundError:
                self.hide_loading()
                self.show_error_message('Файл изображения не найден.')
                return

        new_values = {
            'name': self.car_wash['name'],
            'location_id': self.car_wash['location_id'],
        }

        response = self.api.update_car_wash(
            self.car_wash['id'], new_values=new_values, files=files
        )
        if response and response.status_code == 200:
            self.car_wash['image_link'] = response.json().get(
                'image_link', self.car_wash['image_link']
            )
            self.avatar_container.content = ft.Image(
                src=self.car_wash['image_link'],
                width=150,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
            )
            self.page.update()
            self.show_success_message('Изображение успешно обновлено.')
        else:
            print(
                f'Ошибка при загрузке изображения: '
                f'{response.text if response else "No response"}'
            )
            self.show_error_message('Ошибка при загрузке изображения.')

        self.hide_loading()

    def load_body_types(self):
        response = self.api.get_body_types(limit=100)
        if response.status_code == 200:
            body_types = response.json().get('data', [])
            self.body_type_dict = {
                body_type['id']: body_type['name'] for body_type in body_types
            }
            print('Типы кузовов успешно загружены.')
        else:
            print(f'Ошибка загрузки типов кузовов: {response.text}')
            self.body_type_dict = {}

    def on_back_to_admin_page(self, e=None):
        from washer.ui_components.admin_page import AdminPage

        AdminPage.car_washes_cache = None
        AdminPage(self.page)

    def on_view_archived_schedule_click(self, e):
        ArchivedSchedulePage(self.page, self.car_wash, self.locations)

    def show_confirmation_dialog(self, booking_id):
        """
        Отображает модальное окно подтверждения для подтверждения букинга.
        """
        dialog = ft.AlertDialog(
            title=ft.Text('Подтверждение'),
            content=ft.Text('Вы уверены, что хотите подтвердить этот букинг?'),
            actions=[
                ft.TextButton(
                    text='Нет',
                    on_click=lambda e: self.close_dialog(),
                ),
                ft.ElevatedButton(
                    text='Да',
                    bgcolor=ft.colors.ORANGE,
                    color=ft.colors.WHITE,
                    on_click=lambda e: self.confirm_booking_and_close(
                        e, booking_id
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def confirm_booking_and_close(self, event, booking_id):
        """
        Закрывает диалог и выполняет подтверждение букинга.
        """
        # Закрываем диалог
        self.close_dialog()

        # Выполняем подтверждение букинга
        self.on_confirm_booking(booking_id)

    def show_success_message(self, message):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), open=True)
        self.page.snack_bar.open = True
        self.page.update()

    def update_booking_status_dashboard(self):
        print('Обновление таблицы статусов букингов...')

        # Перезагружаем / обновляем данные букингов
        self.today_bookings = self.load_today_bookings()

        # Заново создаём контент для booking_status_dashboard
        self.booking_status_dashboard.content = (
            self.create_booking_status_dashboard()
        )

        # Обновляем контейнер в UI
        self.booking_status_dashboard.update()
        print('Таблица статусов букингов обновлена.')

    def show_error_message(self, message):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.ERROR, color=ft.colors.RED),
                    ft.Text(
                        message, color=ft.colors.RED, weight=ft.FontWeight.BOLD
                    ),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=10,
            ),
            bgcolor=ft.colors.WHITE,
            action='Закрыть',
            action_color=ft.colors.RED,
            open=True,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_decline_dialog(self, booking_id):
        """
        Отображает модальное окно подтверждения для отказа от букинга.
        """
        dialog = ft.AlertDialog(
            title=ft.Text('Отказ от букинга'),
            content=ft.Text(
                'Вы уверены, что хотите отказаться от этого букинга?'
            ),
            actions=[
                ft.TextButton(
                    text='Нет',
                    on_click=lambda e: self.close_dialog(),
                ),
                ft.ElevatedButton(
                    text='Да',
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE,
                    on_click=lambda e: self.confirm_decline_booking(
                        booking_id
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def confirm_decline_booking(self, booking_id):
        self.close_dialog()
        self.show_loading()

        response = self.api.delete_booking(booking_id)

        if response and response.status_code == 200:
            self.today_bookings = [
                booking
                for booking in self.today_bookings
                if booking['id'] != booking_id
            ]
            self.show_success_message(
                f'Букинг ID {booking_id} успешно удалён.'
            )
            self.update_created_bookings_dashboard()
        else:
            print(
                f'Ошибка при удалении букинга ID {booking_id}: '
                f'{response.text if response else "No response"}'
            )
            self.show_error_message(
                f'Ошибка при удалении букинга ID {booking_id}.'
            )

        self.hide_loading()
        self.page.update()
