import datetime
import io
import json
from datetime import date

import flet as ft
import httpx

from washer.api_requests import BackendApi
from washer.ui_components.archived_schedule_page import ArchivedSchedulePage
from washer.ui_components.box_revenue_page import BoxRevenuePage
from washer.ui_components.schedule_management_page import (
    ScheduleManagementPage,
)


class CarWashEditPage:
    def __init__(self, page: ft.Page, car_wash, api_url):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url
        self.selected_image = None
        self.selected_image_bytes = None
        self.body_type_dict = {}
        self.total_revenue = 0

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

        self.image_picker = ft.FilePicker(on_result=self.on_image_picked)
        self.page.overlay.append(self.image_picker)

        self.image_element = ft.Image(
            src=self.car_wash['image_link'],
            width=300,
            height=200,
            fit=ft.ImageFit.COVER,
        )

        self.load_body_types()
        self.load_schedules()
        self.load_total_revenue()

        page.clean()
        page.add(app_bar)
        page.add(self.create_edit_page())
        page.overlay.append(self.loading_overlay)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def load_schedules(self):
        self.show_loading()
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            self.schedule_list = response.json().get('data', [])
            self.initialize_dates_for_schedule()
            print(f'Загружено расписаний: {len(self.schedule_list)}')
        else:
            print(f'Ошибка загрузки расписаний: {response.text}')
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
        try:
            access_token = self.page.client_storage.get('access_token')
            car_wash_id = self.car_wash['id']
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            url = (
                f"{self.api_url.rstrip('/')}/car_washes/bookings"
                f"?car_wash_id={car_wash_id}&limit=1000"
            )
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                bookings_data = response.json().get('data', [])
                current_date_str = datetime.date.today().strftime('%Y-%m-%d')
                total_revenue = 0
                for booking in bookings_data:
                    booking_date = booking.get('start_datetime', '')
                    if booking_date.startswith(current_date_str):
                        price = float(booking.get('price', 0))
                        total_revenue += price
                self.total_revenue = total_revenue
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code}, {response.text}'
                )
                self.total_revenue = 0
        except Exception as e:
            print(f'Ошибка при загрузке букингов: {e}')
            self.total_revenue = 0

    def create_edit_page(self):
        self.avatar_container = ft.Container(
            content=ft.Image(
                src=self.car_wash['image_link'],
                width=200,
                height=200,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
            ),
            alignment=ft.alignment.center,
        )

        return ft.ListView(
            controls=[
                self.avatar_container,
                ft.Container(
                    content=ft.Text(
                        f"{self.car_wash['name']}",
                        size=24,
                        weight='bold',
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.padding.only(top=10),
                ),
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                ft.icons.UPLOAD, size=30, color='#ef7b00'
                            ),
                            on_click=lambda _: self.image_picker.pick_files(
                                allow_multiple=False,
                                file_type=ft.FilePickerFileType.IMAGE,
                            ),
                            tooltip='Загрузить новое изображение',
                        ),
                        ft.Container(
                            content=ft.Icon(
                                ft.icons.SAVE, size=30, color='#ef7b00'
                            ),
                            on_click=self.on_save_click,
                            tooltip='Сохранить изменения',
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.icons.DIRECTIONS_CAR,
                                            size=50,
                                            color='#ef7b00',
                                        ),
                                        on_click=self.on_boxes_button_click,
                                    ),
                                    ft.Text(
                                        'Боксы',
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=80,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.icons.ATTACH_MONEY,
                                            size=50,
                                            color='#ef7b00',
                                        ),
                                        on_click=self.on_prices_button_click,
                                    ),
                                    ft.Text(
                                        'Цены',
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=80,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.icons.CALENDAR_TODAY,
                                            size=50,
                                            color='#ef7b00',
                                        ),
                                        on_click=self.on_schedule_button_click,
                                    ),
                                    ft.Text(
                                        'Расписание',
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=80,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(
                                            ft.icons.VIEW_LIST,
                                            size=50,
                                            color='#ef7b00',
                                        ),
                                        on_click=self.on_booking_button_click,
                                    ),
                                    ft.Text(
                                        'Букинги',
                                        size=12,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                width=80,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=10,
                    ),
                    padding=ft.padding.only(left=0, right=15),
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Text(
                                f'{self.total_revenue} ₸',
                                size=40,
                                weight='bold',
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
                self.create_schedule_list_section(),
                ft.Divider(),
                ft.TextButton(
                    text='Архив расписаний',
                    on_click=self.on_view_archived_schedule_click,
                    style=ft.ButtonStyle(
                        color='#ef7b00',
                    ),
                    expand=True,
                ),
            ],
            spacing=20,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

    def on_view_archived_schedule_click(self, e):
        ArchivedSchedulePage(self.page, self.car_wash, self.api_url)

    def create_booking_button(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        name=ft.icons.CALENDAR_VIEW_MONTH,
                        size=50,
                    ),
                    ft.Text(
                        'Посмотреть букинги',
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            on_click=self.on_booking_button_click,
            padding=ft.padding.symmetric(vertical=20),
            alignment=ft.alignment.center,
        )

    def on_booking_button_click(self, e):
        from washer.ui_components.admin_booking_table import AdminBookingTable

        current_date = str(date.today())
        AdminBookingTable(self.page, self.car_wash, self.api_url, current_date)

    def create_schedule_list_section(self):
        rows = []

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

            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            f'{schedule_date}',
                            expand=1,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            f'{day_name}',
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            f'{start_time} - {end_time}',
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Текущее расписание', size=24),
                    ft.Row(
                        controls=[
                            ft.Text(
                                'Дата',
                                weight='bold',
                                expand=1,
                                text_align=ft.TextAlign.LEFT,
                            ),
                            ft.Text(
                                'День недели',
                                weight='bold',
                                expand=2,
                                text_align=ft.TextAlign.LEFT,
                            ),
                            ft.Text(
                                'Время',
                                weight='bold',
                                expand=2,
                                text_align=ft.TextAlign.LEFT,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ]
                + rows,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            key='schedule_list_section',
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

    def create_schedule_button(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        name=ft.icons.CALENDAR_TODAY,
                        size=50,
                    ),
                    ft.Text(
                        'Расписание',
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            on_click=self.on_schedule_button_click,
            padding=ft.padding.symmetric(vertical=20),
            alignment=ft.alignment.center,
        )

    def on_schedule_button_click(self, e):
        ScheduleManagementPage(self.page, self.car_wash, self.api_url)

    def create_boxes_button(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        name=ft.icons.GARAGE,
                        size=50,
                    ),
                    ft.Text(
                        'Боксы',
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            on_click=self.on_boxes_button_click,
            padding=ft.padding.symmetric(vertical=20),
            alignment=ft.alignment.center,
        )

    def on_boxes_button_click(self, e):
        from washer.ui_components.box_management_page import BoxManagementPage

        BoxManagementPage(self.page, self.car_wash, self.api_url, self.api)

    def create_prices_button(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(
                        name=ft.icons.ATTACH_MONEY,
                        size=50,
                    ),
                    ft.Text(
                        'Цены',
                        text_align=ft.TextAlign.CENTER,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            on_click=self.on_prices_button_click,
            padding=ft.padding.symmetric(vertical=20),
            alignment=ft.alignment.center,
        )

    def load_prices(self):
        response = self.api.get_prices(self.car_wash['id'])
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f'Ошибка загрузки цен: {response.text}')
            return []

    def on_prices_button_click(self, e):
        from washer.ui_components.price_management_page import (
            PriceManagementPage,
        )

        prices = self.load_prices()
        PriceManagementPage(
            self.page, self.car_wash, self.api_url, self.body_type_dict, prices
        )

    def open_box_revenue_page(self, box):
        BoxRevenuePage(self.page, box, self.car_wash, self.api_url)

    def on_image_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image = e.files[0].path
            if hasattr(e.files[0], 'bytes') and e.files[0].bytes:
                self.selected_image_bytes = e.files[0].bytes
            else:
                self.selected_image = e.files[0].path

            self.avatar_container.content = ft.Image(
                src=self.selected_image,
                width=200,
                height=200,
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(100),
            )
            self.page.update()

    def on_save_click(self, e):
        if self.selected_image or self.selected_image_bytes:
            self.show_loading()
            self.upload_image()

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

        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }

        api_url = (
            f"{self.api_url.rstrip('/')}/car_washes/{self.car_wash['id']}"
        )

        response = httpx.patch(
            api_url,
            files=files,
            data={'new_values': json.dumps(new_values)},
            headers=headers,
        )

        if response.status_code == 200:
            self.car_wash['image_link'] = response.json().get(
                'image_link', self.car_wash['image_link']
            )
            self.image_element.src = self.car_wash['image_link']
            self.page.update()

            self.page.clean()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка при загрузке изображения: {response.text}')

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

        AdminPage(self.page)
