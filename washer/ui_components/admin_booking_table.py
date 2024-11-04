import datetime
import locale

import flet as ft
import httpx

from washer.api_requests import BackendApi
from washer.ui_components.admin_page import AdminPage


class AdminBookingTable:
    def __init__(self, page: ft.Page, car_wash, api_url, date):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url
        self.date = date
        self.schedule_data = []
        self.dates_storage = {}
        self.boxes_list = []
        self.available_times = {}
        self.bookings = []

        self.load_boxes()
        self.load_available_times()
        self.load_bookings()
        self.load_schedules()

    def on_car_saved(self, car_data):
        print(f'Сохраненные данные автомобиля: {car_data}')

    def load_bookings(self):
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
                for booking in bookings_data:
                    if 'user_car_id' in booking:
                        car_name = self.get_car_name(booking['user_car_id'])
                        booking['car_name'] = car_name
                self.bookings = bookings_data
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code}, {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке букингов: {e}')

    def generate_timeslots(self, start_time_str, end_time_str):
        start_time = datetime.datetime.strptime(
            start_time_str, '%H:%M:%S'
        ).time()
        end_time = datetime.datetime.strptime(end_time_str, '%H:%M:%S').time()
        timeslots = []

        while start_time < end_time:
            timeslots.append(start_time.strftime('%H:%M'))
            start_time = (
                datetime.datetime.combine(datetime.date.today(), start_time)
                + datetime.timedelta(hours=1)
            ).time()
        return timeslots

    def load_schedules(self):
        print(
            f"Загружаем расписание для автомойки с ID: {self.car_wash['id']}"
        )
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            self.schedule_data = response.json().get('data', [])
            self.initialize_dates_for_schedule()
            self.schedule_data.sort(
                key=lambda x: self.dates_storage.get(x['day_of_week'])
            )
            print(f'Загружено расписаний: {len(self.schedule_data)}')
            self.page.clean()
            self.page.add(self.create_booking_page())
            self.page.update()
        else:
            print(f'Ошибка загрузки расписаний: {response.text}')

    def initialize_dates_for_schedule(self):
        current_date = datetime.date.today()
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        for schedule in self.schedule_data:
            day_of_week = schedule['day_of_week']
            delta_days = (day_of_week - current_date.weekday()) % 7
            target_date = current_date + datetime.timedelta(days=delta_days)
            self.dates_storage[day_of_week] = target_date

    def load_boxes(self):
        print(f"Загружаем боксы для автомойки с ID: {self.car_wash['id']}")
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            self.boxes_list = response.json().get('data', [])
            print(f'Загружено боксов: {len(self.boxes_list)}')
        else:
            print(f'Ошибка загрузки боксов: {response.text}')

    def load_available_times(self):
        print(
            f"Загружаем доступное время для автомойки с ID: "
            f"{self.car_wash['id']} на неделю"
        )

        current_date = datetime.date.today()

        for i in range(7):
            target_date = current_date + datetime.timedelta(days=i)
            response = self.api.get_available_times(
                self.car_wash['id'], str(target_date)
            )

            if response.status_code == 200:
                daily_times = response.json().get('available_times', {})
                self.available_times[str(target_date)] = daily_times
                print(
                    f'Доступное время загружено для '
                    f'{target_date}: {daily_times}'
                )
            else:
                print(
                    f'Ошибка загрузки доступного времени для '
                    f'{target_date}: {response.text}'
                )

    def create_booking_page(self):
        rows = []

        for schedule in self.schedule_data:
            day_of_week = schedule.get('day_of_week')
            day_name = self.get_day_name(day_of_week)
            schedule_date = self.dates_storage.get(day_of_week)
            formatted_date = schedule_date.strftime('%d %B')
            day_with_date = f'{day_name} ({formatted_date})'

            timeslots = self.generate_timeslots(
                schedule['start_time'], schedule['end_time']
            )
            rows.append(
                self.create_booking_table(day_with_date, schedule, timeslots)
            )

        back_button = ft.ElevatedButton(
            text='Назад',
            on_click=self.on_back_click,
            width=200,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        scrollable_content = ft.Column(
            controls=rows,
            spacing=20,
            scroll='auto',
            expand=True,
        )

        return ft.Column(
            controls=[
                scrollable_content,
                ft.Container(
                    content=back_button, alignment=ft.alignment.center
                ),
            ],
            expand=True,
        )

    def create_booking_table(self, day_with_date, schedule, timeslots):
        rows = []

        header = ft.Container(
            content=ft.Text(
                day_with_date,
                size=24,
                weight='bold',
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(bottom=10),
            bgcolor=ft.colors.GREY_900,
            height=50,
        )
        rows.append(header)

        box_header = ft.Row(
            controls=[ft.Text('', width=100)]
            + [
                ft.Text(
                    box['name'],
                    weight='bold',
                    text_align=ft.TextAlign.CENTER,
                    expand=True,
                )
                for box in self.boxes_list
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5,
        )
        rows.append(
            ft.Container(
                content=box_header,
                bgcolor=ft.colors.GREY_800,
                padding=ft.padding.all(5),
            )
        )

        skip_slots = {}
        for time in timeslots:
            row_controls = [ft.Text(time, weight='bold', width=100, height=40)]

            current_date = self.dates_storage[schedule['day_of_week']]

            for box in self.boxes_list:
                if skip_slots.get(box['id'], 0) > 0:
                    skip_slots[box['id']] -= 1
                    row_controls.append(
                        ft.Container(
                            content=ft.Text(
                                '', size=12, text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor=ft.colors.TRANSPARENT,
                            padding=ft.padding.all(5),
                            alignment=ft.alignment.center,
                            expand=True,
                            height=40,
                        )
                    )
                    continue

                current_time_slot = f'{current_date}T{time}:00'

                booking = next(
                    (
                        b
                        for b in self.bookings
                        if b['box_id'] == box['id']
                        and b['start_datetime']
                        <= current_time_slot
                        < b['end_datetime']
                    ),
                    None,
                )

                if booking:
                    car_name = (
                        self.get_car_name(booking['user_car_id'])
                        if booking.get('user_car_id')
                        else 'Неизвестно'
                    )
                    color = ft.colors.GREY_500
                    price = booking.get('price', 'Не указана')
                    text = f'Занято\n{car_name}\n₸{price}'

                    start_time = datetime.datetime.strptime(
                        booking['start_datetime'], '%Y-%m-%dT%H:%M:%S'
                    ).time()
                    end_time = datetime.datetime.strptime(
                        booking['end_datetime'], '%Y-%m-%dT%H:%M:%S'
                    ).time()
                    duration_slots = int(
                        (
                            datetime.datetime.combine(
                                datetime.date.today(), end_time
                            )
                            - datetime.datetime.combine(
                                datetime.date.today(), start_time
                            )
                        ).seconds
                        / 3600
                    )
                    skip_slots[box['id']] = duration_slots - 1

                    row_controls.append(
                        ft.Container(
                            content=ft.Text(
                                text, size=12, text_align=ft.TextAlign.CENTER
                            ),
                            bgcolor=color,
                            padding=ft.padding.all(5),
                            alignment=ft.alignment.center,
                            expand=True,
                            height=40,
                            border_radius=ft.border_radius.all(15),
                            on_click=lambda e,
                            booking=booking: self.open_booking_details_dialog(
                                booking
                            ),
                        )
                    )

                else:
                    box_times = self.available_times.get(
                        str(current_date), {}
                    ).get(str(box['id']), [])
                    is_available = any(
                        start_time <= current_time_slot < end_time
                        for start_time, end_time in box_times
                    )

                    if is_available:
                        color = ft.colors.GREEN
                        text = 'Свободно'
                        row_controls.append(
                            ft.Container(
                                content=ft.Text(
                                    text,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                bgcolor=color,
                                padding=ft.padding.all(5),
                                alignment=ft.alignment.center,
                                expand=True,
                                height=40,
                                border_radius=ft.border_radius.all(15),
                                on_click=lambda e,
                                box_id=box['id'],
                                time_slot=time,
                                date=current_date: self.open_booking_page(
                                    box_id, date, time_slot
                                ),
                            )
                        )
                    else:
                        color = ft.colors.GREY_600
                        text = 'Не актуально'
                        row_controls.append(
                            ft.Container(
                                content=ft.Text(
                                    text,
                                    size=12,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                bgcolor=color,
                                padding=ft.padding.all(5),
                                alignment=ft.alignment.center,
                                expand=True,
                                height=40,
                                border_radius=ft.border_radius.all(15),
                            )
                        )

            row = ft.Row(controls=row_controls, spacing=5)
            rows.append(ft.Container(content=row))

        return ft.Container(
            content=ft.Column(controls=rows, spacing=5),
            padding=ft.padding.all(10),
            expand=True,
        )

    def get_car_name(self, user_car_id):
        response = self.api.get_car_by_id(user_car_id)
        if response.status_code == 200:
            car_data = response.json()
            return car_data.get('name', 'Неизвестно')
        return 'Неизвестно'

    def open_booking_details_dialog(self, booking):
        car_name = booking.get('car_name', 'Неизвестно')
        price = booking.get('price', 'Не указана')

        details_dialog = ft.AlertDialog(
            title=ft.Text('Детали букинга'),
            content=ft.Column(
                [
                    ft.Text(f'Автомобиль: {car_name}', size=16),
                    ft.Text(f'Цена: ₸{price}', size=16),
                ]
            ),
            actions=[
                ft.TextButton(
                    'Закрыть', on_click=lambda e: self.close_details_dialog()
                )
            ],
        )
        self.page.dialog = details_dialog
        details_dialog.open = True
        self.page.update()

    def close_details_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def open_booking_page(self, box_id, date, time):
        from washer.ui_components.admin_booking_page import AdminSelectCarPage

        AdminSelectCarPage(
            self.page, self.on_car_saved, self.car_wash, box_id, date, time
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

    def on_back_click(self, e):
        AdminPage(self.page)
