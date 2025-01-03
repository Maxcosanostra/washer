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
                    label='Расписание',
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
                current_time = datetime.datetime.now()
                for booking in bookings_data:
                    booking_date = booking.get('start_datetime', '')
                    end_time_str = booking.get('end_datetime', '')
                    if end_time_str:
                        end_time = datetime.datetime.fromisoformat(
                            end_time_str
                        )
                        if (
                            booking_date.startswith(current_date_str)
                            and end_time < current_time
                        ):
                            price = float(booking.get('price', 0))
                            total_revenue += price
                self.total_revenue = total_revenue
                print(
                    f'Общая выручка для автомойки '
                    f'{car_wash_id}: {self.total_revenue} ₸'
                )
            else:
                print(
                    f'Ошибка загрузки букингов для автомойки {car_wash_id}: '
                    f'{response.status_code if response else "No response"}, '
                    f'{response.text if response else ""}'
                )
                self.total_revenue = 0
        except Exception as e:
            print(
                f'Ошибка при загрузке букингов '
                f'для автомойки {car_wash_id}: {e}'
            )
            self.total_revenue = 0

    def create_edit_page(self):
        location_id = self.car_wash.get('location_id')
        location = self.locations.get(location_id, {})
        city = location.get('city', 'Неизвестный город')
        address = location.get('address', 'Неизвестный адрес')

        print(
            f'Создаем страницу редактирования для города: '
            f'{city}, адрес: {address}'
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
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Text(
                                f'{self.total_revenue} ₸',
                                size=40,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            padding=ft.padding.all(20),
                            alignment=ft.alignment.center,
                        ),
                        elevation=2,
                        width=300,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=10),
                ),
                self.create_booking_status_dashboard(),
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

    def load_today_bookings(self):
        car_wash_id = None
        try:
            car_wash_id = self.car_wash['id']
            response = self.api.get_bookings(car_wash_id)
            if response and response.status_code == 200:
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
                        print(
                            f"Не удалось найти бокс с ID: {booking['box_id']}"
                        )

                return today_bookings
            else:
                print(
                    f'Ошибка загрузки букингов для автомойки {car_wash_id}: '
                    f'{response.status_code if response else "No response"}, '
                    f'{response.text if response else ""}'
                )
                return []
        except Exception as e:
            print(
                f'Ошибка при загрузке букингов '
                f'для автомойки {car_wash_id}: {e}'
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
                    width=90,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        rows = [header]
        current_time = datetime.datetime.now()
        sorted_bookings = sorted(
            getattr(self, 'today_bookings', []),
            key=lambda b: b['start_datetime'],
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
                start_time = datetime.datetime.fromisoformat(
                    booking['start_datetime']
                )
                end_time = datetime.datetime.fromisoformat(
                    booking['end_datetime']
                )

                if current_time < start_time:
                    status = 'В ожидании'
                    color = '#FFD700'
                elif start_time <= current_time <= end_time:
                    status = 'В процессе'
                    color = '#FFA500'
                else:
                    status = 'Завершено'
                    color = '#32CD32'

                box_name = booking.get('box_name', 'Неизвестный бокс')

                row = ft.Row(
                    controls=[
                        ft.Text(
                            start_time.strftime('%H:%M'),
                            width=70,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            end_time.strftime('%H:%M'),
                            width=90,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            box_name, width=70, text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            status,
                            width=90,
                            text_align=ft.TextAlign.CENTER,
                            color=color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                rows.append(row)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Статус букингов', size=24, weight=ft.FontWeight.BOLD
                    ),
                    *rows,
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(vertical=10),
        )

    def on_view_archived_schedule_click(self, e):
        ArchivedSchedulePage(self.page, self.car_wash, self.locations)

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
                show_change=False,
                show_save=True,
                show_cancel=True,
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
            show_change=False,
            show_save=False,
            show_cancel=False,
        )
        self.page.update()

    def on_save_click(self, e):
        if self.selected_image or self.selected_image_bytes:
            self.show_loading()
            self.upload_image()
            self.update_button_visibility(
                show_change=False,
                show_save=False,
                show_cancel=False,
            )

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
                files = {'image': open(self.selected_image, 'rb')}
            except FileNotFoundError:
                self.hide_loading()
                return
        new_values = {
            'name': self.car_wash['name'],
            'location_id': self.car_wash['location_id'],
        }

        response = self.api.update_car_wash(
            self.car_wash['id'],
            new_values=new_values,
            files=files,
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
        else:
            print(
                f'Ошибка при загрузке изображения: '
                f'{response.text if response else "No response"}'
            )

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
