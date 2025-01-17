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

        self.booking_colors = {}

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
        self.assign_colors_to_created_bookings()
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

    def handle_booking_click(self, e, booking):
        self.open_booking_details_dialog(booking)

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
                    user_car = booking.get('user_car')
                    if user_car:
                        booking['car_name'] = user_car.get(
                            'name', 'Неизвестно'
                        )
                        booking['license_plate'] = user_car.get(
                            'license_plate', '---'
                        )
                        user = user_car.get('user', {})
                        booking['first_name'] = user.get(
                            'first_name', 'Неизвестен'
                        )
                        booking['last_name'] = user.get('last_name', '')
                        booking['phone_number'] = user.get(
                            'phone_number', '---'
                        )
                    else:
                        booking['car_name'] = 'Неизвестно'
                        booking['license_plate'] = '---'
                        booking['first_name'] = 'Неизвестен'
                        booking['last_name'] = ''
                        booking['phone_number'] = '---'

                    # Корректное присвоение состояния букинга
                    booking['state'] = booking.get('state', 'CREATED').upper()

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

    def assign_colors_to_created_bookings(self):
        """Назначает цвета букингам со статусом CREATED,"""
        """чередуя между GREY_500 и GREY_400."""
        self.booking_colors = {}
        created_bookings = [
            b for b in self.bookings if b['state'] == 'CREATED'
        ]
        for i, booking in enumerate(created_bookings):
            color = ft.colors.GREY_500 if i % 2 == 0 else ft.colors.GREY_400
            self.booking_colors[booking['id']] = color
        print(
            f'Назначено цветов для '
            f'{len(self.booking_colors)} букингов со статусом CREATED.'
        )

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

            tabs.append(
                ft.Tab(
                    text=self.get_day_name(day_of_week), content=tab_content
                )
            )

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

        black_border_bottom = ft.border.Border(
            bottom=ft.border.BorderSide(width=1, color=ft.colors.BLACK),
        )

        header = ft.Container(
            content=ft.Text(
                day_with_date,
                size=28,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(bottom=10),
            height=60,
        )
        rows.append(header)

        box_names_row = [
            ft.Container(
                content=ft.Text(
                    '',  # Пустой заголовок
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    size=16,
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
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        size=16,
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
            row_controls = [
                ft.Text(
                    time,
                    weight=ft.FontWeight.BOLD,
                    width=100,
                    height=40,
                    size=16,
                )
            ]
            current_date = self.dates_storage[schedule['day_of_week']]

            for box in self.boxes_list:
                box_id = box['id']

                if box_id in skip_slots:
                    booking, occupied_color = skip_slots[box_id]

                    booking_state = booking.get('state', 'CREATED').upper()
                    if booking_state == 'CREATED':
                        occupied_color = self.booking_colors.get(
                            booking['id'], ft.colors.GREY_500
                        )
                    else:
                        status_info = self.get_status_info(booking_state)
                        occupied_color = status_info['color']

                    additions = booking.get('additions', [])
                    if additions:
                        additional_services = ', '.join(
                            [addition['name'] for addition in additions]
                        )
                    else:
                        additional_services = None

                    notes = booking.get('notes', '').strip()
                    has_notes = bool(notes)

                    cell_content = [
                        ft.Text(
                            f"₸{booking.get('total_price', '0')}",
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ]

                    if additional_services:
                        cell_content.append(
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.ADD,
                                        size=16,
                                        color=ft.colors.BLUE_600,
                                    ),
                                    ft.Text(
                                        additional_services,
                                        size=14,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        expand=True,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=5,
                            )
                        )

                    if has_notes:
                        cell_content.append(
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.NOTE,
                                        size=16,
                                        color=ft.colors.RED_600,
                                    ),
                                    ft.Text(
                                        notes,
                                        size=14,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        expand=True,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=5,
                            )
                        )

                    row_controls.append(
                        ft.Container(
                            content=ft.Column(
                                cell_content,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                            ),
                            bgcolor=occupied_color,
                            padding=ft.padding.all(5),
                            alignment=ft.alignment.center,
                            expand=True,
                            height=80,
                            border=black_border_bottom,
                            on_click=lambda e,
                            b=booking: self.handle_booking_click(e, b),
                        )
                    )

                    del skip_slots[box_id]
                    continue

                current_time_slot = f'{current_date}T{time}:00'

                booking = next(
                    (
                        b
                        for b in self.bookings
                        if b['box_id'] == box_id
                        and b['start_datetime']
                        <= current_time_slot
                        < b['end_datetime']
                    ),
                    None,
                )

                if booking:
                    booking_state = booking.get('state', 'CREATED').upper()

                    if booking_state == 'CREATED':
                        occupied_color = self.booking_colors.get(
                            booking['id'], ft.colors.GREY_500
                        )
                    else:
                        status_info = self.get_status_info(booking_state)
                        occupied_color = status_info['color']

                    user_full_name = (
                        f"{booking.get('first_name', '')} "
                        f"{booking.get('last_name', '')}"
                    ).strip()
                    car_info = f"{booking.get('car_name', '')}"
                    license_plate = f"({booking.get('license_plate', '---')})"

                    row_controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        user_full_name,
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        car_info,
                                        size=14,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        license_plate,
                                        size=14,
                                        text_align=ft.TextAlign.CENTER,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                            ),
                            bgcolor=occupied_color,
                            padding=ft.padding.all(5),
                            alignment=ft.alignment.center,
                            expand=True,
                            height=80,
                            on_click=lambda e,
                            b=booking: self.handle_booking_click(e, b),
                        )
                    )

                    start_time = datetime.datetime.fromisoformat(
                        booking['start_datetime']
                    ).time()
                    end_time = datetime.datetime.fromisoformat(
                        booking['end_datetime']
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
                    if duration_slots > 1:
                        skip_slots[box_id] = (booking, occupied_color)

                else:
                    box_times = self.available_times.get(
                        str(current_date), {}
                    ).get(str(box_id), [])
                    is_available = any(
                        start_time <= current_time_slot < end_time
                        for start_time, end_time in box_times
                    )

                    if is_available:
                        color = ft.colors.BLUE
                        row_controls.append(
                            ft.Container(
                                content=ft.Text(
                                    'Свободно',
                                    size=14,
                                    text_align=ft.TextAlign.CENTER,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                bgcolor=color,
                                padding=ft.padding.all(5),
                                alignment=ft.alignment.center,
                                expand=True,
                                height=80,
                                border=black_border_bottom,
                                on_click=lambda e,
                                b_id=box_id,
                                t_slot=time,
                                d=current_date: self.open_booking_page(
                                    b_id, d, t_slot
                                ),
                            )
                        )
                    else:
                        color = ft.colors.TRANSPARENT
                        row_controls.append(
                            ft.Container(
                                content=ft.Text(
                                    'Не актуально',
                                    size=14,
                                    text_align=ft.TextAlign.CENTER,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                bgcolor=color,
                                padding=ft.padding.all(5),
                                alignment=ft.alignment.center,
                                expand=True,
                                height=80,
                                border=black_border_bottom,
                                on_click=lambda e,
                                b=None: self.handle_booking_click(e, b)
                                if b
                                else None,
                            )
                        )

            row = ft.Row(controls=row_controls, spacing=5, height=80)
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
        first_name = booking.get('first_name', 'Неизвестен')
        last_name = booking.get('last_name', '')
        phone_number = booking.get('phone_number', '---')
        car_name = booking.get('car_name', 'Неизвестно')
        price = booking.get('total_price', 'Не указана')
        additions = booking.get('additions', [])
        notes = booking.get('notes', '').strip()

        full_name = (
            f'{first_name} {last_name}'.strip() if last_name else first_name
        )

        additional_services = (
            ', '.join([addition['name'] for addition in additions])
            if additions
            else None
        )
        has_notes = bool(notes)

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

        details_controls = [
            self.create_detail_row(ft.icons.PERSON, full_name),
            self.create_detail_row(ft.icons.DIRECTIONS_CAR, car_name),
            self.create_detail_row(ft.icons.MONEY, f'₸{price}'),
            self.create_detail_row(ft.icons.PHONE, phone_number),
        ]

        if additional_services:
            details_controls.append(
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.ADD,
                            size=20,
                            color=ft.colors.BLUE_600,
                        ),
                        ft.Text(
                            additional_services,
                            size=16,
                            text_align=ft.TextAlign.LEFT,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            expand=True,
                            max_lines=None,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                    visible=True,
                )
            )

        if has_notes:
            details_controls.append(
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.NOTE,
                            size=20,
                            color=ft.colors.RED_600,
                        ),
                        ft.Text(
                            notes,
                            size=16,
                            text_align=ft.TextAlign.LEFT,
                            overflow=ft.TextOverflow.CLIP,
                            expand=True,
                            max_lines=None,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                    visible=True,
                )
            )

        details_dialog = ft.AlertDialog(
            content=ft.Column(details_controls),
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

                self.assign_colors_to_created_bookings()

                booking_tabs = self.page.controls[
                    1
                ]  # Предполагается, что Tabs на позиции 1
                selected_index = booking_tabs.selected_index
                selected_tab = booking_tabs.tabs[selected_index]

                day_of_week = self.schedule_data[selected_index]['day_of_week']
                schedule_date = self.dates_storage[day_of_week]

                self.load_available_times(schedule_date)
                self.load_bookings()
                self.assign_colors_to_created_bookings()

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

    def get_status_info(self, state):
        status_mapping = {
            'ACCEPTED': {'text': 'Подтвержден', 'color': '#87CEFA'},
            'STARTED': {'text': 'В процессе', 'color': '#FFA500'},
            'COMPLETED': {'text': 'Завершено', 'color': '#32CD32'},
            'EXCEPTION': {'text': 'Ошибка', 'color': '#FF0000'},
        }
        return status_mapping.get(
            state, {'text': 'Неизвестно', 'color': '#808080'}
        )
