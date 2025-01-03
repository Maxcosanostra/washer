import datetime
import locale

import flet as ft

from washer.api_requests import BackendApi


class AdminBookingTable:
    def __init__(
        self,
        page: ft.Page,
        car_wash,
        date,
        selected_date=None,
        locations=None,
    ):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.date = date
        self.selected_date = selected_date
        self.locations = locations
        self.schedule_data = []
        self.dates_storage = {}
        self.boxes_list = []
        self.available_times = {}
        self.bookings = []
        self.loaded_days = set()

        app_bar = ft.AppBar(
            leading=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.on_back_click,
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

        self.load_boxes()
        self.load_available_times(datetime.date.today())
        self.load_bookings()
        self.load_schedules()

        if self.selected_date and self.selected_date not in self.loaded_days:
            print(
                f'Обновляем доступные слоты '
                f'для выбранной даты {self.selected_date}'
            )
            self.load_available_times(self.selected_date)

        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_booking_page())

    def on_car_saved(self, car_data):
        print(f'Сохраненные данные автомобиля: {car_data}')

    def load_bookings(self):
        try:
            car_wash_id = self.car_wash['id']
            response = self.api.get_bookings(car_wash_id)
            if response and response.status_code == 200:
                bookings_data = response.json().get('data', [])

                self.bookings = bookings_data

                for booking in self.bookings:
                    if 'user_car_id' in booking:
                        car_name = self.get_car_name(booking['user_car_id'])
                        booking['car_name'] = (
                            car_name if car_name != 'Неизвестно' else ''
                        )

                print(
                    f"Загружено букингов: {len(self.bookings)} "
                    f"для автомойки {self.car_wash['id']}"
                )
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code if response else "No response"}, '
                    f'{response.text if response else ""}'
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

        if start_time == end_time:
            timeslots.append(end_time.strftime('%H:%M'))

        print(f'Сгенерированные временные слоты: {timeslots}')
        return timeslots

    def load_schedules(self):
        print(
            f"Загружаем расписание для автомойки с ID: {self.car_wash['id']}"
        )
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            self.schedule_data = [
                schedule
                for schedule in response.json().get('data', [])
                if schedule['car_wash_id'] == self.car_wash['id']
            ]
            if not self.schedule_data:
                print('Нет расписаний для данной автомойки.')
            else:
                self.initialize_dates_for_schedule()
                self.schedule_data.sort(
                    key=lambda x: self.dates_storage.get(x['day_of_week'])
                )
                print(f'Загружено расписаний: {len(self.schedule_data)}')
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
            # Фильтрация по текущей автомойке
            self.boxes_list = [
                box
                for box in response.json().get('data', [])
                if box['car_wash_id'] == self.car_wash['id']
            ]
            print(
                f'Загружено боксов: {len(self.boxes_list)} '
                f'для автомойки {self.car_wash["id"]}'
            )
        else:
            print(f'Ошибка загрузки боксов: {response.text}')

    def load_available_times(self, target_date):
        print(
            f"Загружаем доступное время для автомойки с ID: "
            f"{self.car_wash['id']} на дату {target_date}"
        )

        response = self.api.get_available_times(
            self.car_wash['id'], str(target_date)
        )

        if response.status_code == 200:
            daily_times = response.json().get('available_times', {})

            self.available_times[str(target_date)] = daily_times
            self.loaded_days.add(target_date)

            print(
                f'Доступное время загружено для '
                f'{target_date}: {self.available_times[str(target_date)]}'
            )
        else:
            print(
                f'Ошибка загрузки доступного времени для '
                f'{target_date}: {response.text}'
            )

    def create_booking_page(self):
        if not self.schedule_data:
            print('Нет расписаний для отображения.')
            return ft.Text(
                'Нет доступных расписаний.',
                size=18,
                text_align=ft.TextAlign.CENTER,
            )

        tabs = []
        selected_index = 0

        for i, schedule in enumerate(self.schedule_data):
            day_of_week = schedule.get('day_of_week')
            schedule_date = self.dates_storage.get(day_of_week)
            formatted_date = schedule_date.strftime('%d %B')
            day_name = self.get_day_name(day_of_week)
            day_with_date = f'{day_name} ({formatted_date})'

            if self.selected_date and schedule_date == self.selected_date:
                selected_index = i

            tab_content = (
                self.create_booking_table(
                    day_with_date,
                    schedule,
                    self.generate_timeslots(
                        schedule['start_time'], schedule['end_time']
                    ),
                )
                if i == selected_index
                else ft.Container()
            )

            tabs.append(ft.Tab(text=day_name, content=tab_content))

        if not tabs:
            print('Расписания есть, но вкладки не создались.')
            return ft.Text(
                'Ошибка создания вкладок.',
                size=18,
                text_align=ft.TextAlign.CENTER,
            )

        booking_tabs = ft.Tabs(
            tabs=tabs,
            selected_index=selected_index,
            expand=True,
            on_change=self.on_tab_change,
        )

        return booking_tabs

    def on_tab_change(self, e):
        booking_tabs = e.control
        selected_index = booking_tabs.selected_index

        if not booking_tabs.tabs or selected_index >= len(booking_tabs.tabs):
            print('Ошибка: Некорректный индекс вкладки.')
            return

        selected_tab = booking_tabs.tabs[selected_index]
        day_of_week = self.schedule_data[selected_index]['day_of_week']
        schedule_date = self.dates_storage[day_of_week]

        if schedule_date not in self.loaded_days:
            self.load_available_times(schedule_date)

        schedule = self.schedule_data[selected_index]
        day_with_date = (
            f"{self.get_day_name(day_of_week)} "
            f"({schedule_date.strftime('%d %B')})"
        )
        selected_tab.content = self.create_booking_table(
            day_with_date,
            schedule,
            self.generate_timeslots(
                schedule['start_time'], schedule['end_time']
            ),
        )
        self.page.update()

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
            height=50,
        )
        rows.append(header)

        box_names_row = [
            ft.Container(
                content=ft.Text(
                    '', weight='bold', text_align=ft.TextAlign.CENTER, size=14
                ),
                width=100,
                height=40,
                alignment=ft.alignment.center,
            )
        ]

        for box in self.boxes_list:
            box_names_row.append(
                ft.Container(
                    content=ft.Text(
                        box['name'],
                        weight='bold',
                        text_align=ft.TextAlign.CENTER,
                        size=14,
                    ),
                    expand=True,
                    height=40,
                    alignment=ft.alignment.center,
                )
            )

        rows.append(
            ft.Row(
                controls=box_names_row,
                spacing=5,
                height=40,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START,
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
                    color = ft.colors.GREY_500
                    text = 'Занято'

                    start_time = datetime.datetime.fromisoformat(
                        booking['start_datetime']
                    ).time()
                    end_time = datetime.datetime.fromisoformat(
                        booking['end_datetime']
                    ).time()
                    # в новом используется более удобный и "автоматический"
                    # метод datetime.datetime.fromisoformat, который позволяет
                    # обойтись без явного указания формата, если строка
                    # соответствует стандартному ISO-формату даты и времени.
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
                        color = ft.colors.BLUE
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

            row = ft.Row(controls=row_controls, spacing=5, height=50)
            rows.append(ft.Container(content=row))

        return ft.ListView(
            controls=rows, padding=ft.padding.all(10), expand=True
        )

    def get_car_name(self, user_car_id):
        response = self.api.get_car_by_id(user_car_id)
        if response.status_code == 200:
            car_data = response.json()
            return (
                car_data.get('name', '')
                if car_data.get('name', '') != 'Неизвестно'
                else ''
            )
        return ''

    def open_booking_details_dialog(self, booking):
        user_id = booking.get('user_id')
        car_name = booking.get('car_name', '')
        price = booking.get('price', 'Не указана')

        user_response = self.api.get_user_by_id(user_id)
        if user_response and user_response.status_code == 200:
            user_data = user_response.json()
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            full_name = f'{first_name} {last_name}'.strip()
        else:
            full_name = 'Неизвестен'

        def confirm_delete(e):
            self.page.close(confirm_dialog)
            self.delete_booking(booking['id'])

        def cancel_delete(e):
            self.page.close(confirm_dialog)

        def open_confirm_dialog(e):
            self.page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.page.update()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение удаления'),
            content=ft.Text('Вы уверены, что хотите удалить этот букинг?'),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        details_dialog = ft.AlertDialog(
            title=ft.Text('Детали букинга'),
            content=ft.Column(
                [
                    self.create_detail_row(ft.icons.PERSON, full_name),
                    self.create_detail_row(ft.icons.DIRECTIONS_CAR, car_name),
                    self.create_detail_row(ft.icons.MONEY, f'₸{price}'),
                    self.create_detail_row(ft.icons.PHONE, ''),
                ]
            ),
            actions=[
                ft.TextButton(
                    'Удалить',
                    on_click=open_confirm_dialog,
                    style=ft.ButtonStyle(color=ft.colors.RED),
                ),
                ft.TextButton(
                    'Закрыть',
                    on_click=lambda e: self.page.close(details_dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = details_dialog
        details_dialog.open = True
        self.page.update()

    def create_detail_row(self, icon, text):
        return ft.Row(
            controls=[
                ft.Icon(icon, size=20),
                ft.Text(text, size=16, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def delete_booking(self, booking_id: int):
        try:
            response = self.api.delete_booking(booking_id)
            if response.status_code == 200:
                self.bookings = [
                    b for b in self.bookings if b['id'] != booking_id
                ]
                print(f'Букинг с ID {booking_id} успешно удалён.')

                # Получаем активную вкладку
                booking_tabs = self.page.controls[
                    1
                ]  # Предполагается, что Tabs на позиции 1
                selected_index = booking_tabs.selected_index
                selected_tab = booking_tabs.tabs[selected_index]

                day_of_week = self.schedule_data[selected_index]['day_of_week']
                schedule_date = self.dates_storage[day_of_week]

                self.load_available_times(schedule_date)
                self.load_bookings()

                schedule = self.schedule_data[selected_index]
                timeslots = self.generate_timeslots(
                    schedule['start_time'], schedule['end_time']
                )
                selected_tab.content = self.create_booking_table(
                    f"{self.get_day_name(day_of_week)} "
                    f"({schedule_date.strftime('%d %B')})",
                    schedule,
                    timeslots,
                )
                self.page.update()
            else:
                print(f'Ошибка удаления букинга: {response.text}')
                self.show_error_message('Ошибка при удалении букинга.')
        except Exception as e:
            print(f'Ошибка при удалении букинга: {e}')
            self.show_error_message('Произошла ошибка при удалении букинга.')

    def show_error_message(self, message: str):
        error_snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.colors.WHITE),
            bgcolor=ft.colors.RED,
            duration=3000,
        )
        self.page.overlay.append(error_snack_bar)
        error_snack_bar.open = True
        self.page.update()

    def close_details_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def open_booking_page(self, box_id, date, time):
        from washer.ui_components.admin_car_selection_page import (
            AdminCarSelectionPage,
        )

        def on_car_selected(selected_car, car_price):
            from washer.ui_components.admin_booking_process_page import (
                AdminBookingProcessPage,
            )

            AdminBookingProcessPage(
                self.page,
                self.car_wash,
                box_id,
                date,
                time,
                selected_car,
                car_price,
            )

        AdminCarSelectionPage(
            self.page,
            on_car_selected,
            self.car_wash,
            box_id,
            date,
            time,
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
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.locations)
