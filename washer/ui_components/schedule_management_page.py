import datetime

import flet as ft

from washer.api_requests import BackendApi


class ScheduleManagementPage:
    def __init__(self, page: ft.Page, car_wash, api_url):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url

        self.schedule_list = []
        self.selected_days = []
        self.dates_storage = {}

        app_bar = ft.AppBar(
            leading=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.on_back_to_edit_page,
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

        self.schedule_start_time_picker = ft.TimePicker(
            confirm_text='Подтвердить',
            error_invalid_text='Неверное время',
            help_text='Выберите время начала',
            on_change=self.on_time_change,
        )

        self.schedule_end_time_picker = ft.TimePicker(
            confirm_text='Подтвердить',
            error_invalid_text='Неверное время',
            help_text='Выберите время окончания',
            on_change=self.on_time_change,
        )

        self.schedule_start_time_picker_manual = ft.TimePicker(
            confirm_text='Подтвердить',
            error_invalid_text='Неверное время',
            help_text='Выберите время начала (механическое)',
            on_change=self.on_time_change_manual,
        )

        self.schedule_end_time_picker_manual = ft.TimePicker(
            confirm_text='Подтвердить',
            error_invalid_text='Неверное время',
            help_text='Выберите время окончания (механическое)',
            on_change=self.on_time_change_manual,
        )

        self.days_of_week_checkboxes = self.create_day_of_week_checkboxes()
        self.load_schedules()

        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_schedule_management_page())
        self.page.overlay.append(self.loading_overlay)

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
        for schedule in self.schedule_list:
            day_of_week = schedule['day_of_week']
            delta_days = (day_of_week - current_date.weekday()) % 7
            target_date = current_date + datetime.timedelta(days=delta_days)
            self.dates_storage[day_of_week] = target_date.strftime('%Y-%m-%d')

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
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            on_click=lambda e,
                            s=schedule: self.on_delete_schedule(s['id']),
                            icon_size=18,
                            tooltip='Удалить расписание',
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Актуальное расписание', size=24),
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

    def on_delete_schedule(self, schedule_id):
        self.show_loading()
        response = self.api.delete_schedule(schedule_id)
        if response.status_code == 200:
            print(f'Расписание с ID {schedule_id} успешно удалено.')
            self.refresh_schedule_list()
        else:
            print(f'Ошибка при удалении расписания: {response.text}')
        self.hide_loading()

    def create_day_of_week_checkboxes(self):
        days_of_week = [
            'Понедельник',
            'Вторник',
            'Среда',
            'Четверг',
            'Пятница',
            'Суббота',
            'Воскресенье',
        ]
        checkboxes = []
        for i, day in enumerate(days_of_week):
            checkbox = ft.Checkbox(
                label=day,
                value=False,
                on_change=self.on_day_of_week_checked,
                data=i,
            )
            checkboxes.append(checkbox)
        return checkboxes

    def on_day_of_week_checked(self, e: ft.ControlEvent):
        day = e.control.data
        if e.control.value:
            if day not in self.selected_days:
                self.selected_days.append(day)
        else:
            if day in self.selected_days:
                self.selected_days.remove(day)

    def create_week_schedule_section(self):
        self.start_time_button = ft.ElevatedButton(
            text='Выбрать время начала',
            on_click=self.open_start_time_picker,
        )

        self.end_time_button = ft.ElevatedButton(
            text='Выбрать время окончания',
            on_click=self.open_end_time_picker,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Недельное расписание', size=24),
                    self.start_time_button,
                    self.end_time_button,
                    ft.ElevatedButton(
                        text='Создать недельное расписание',
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=50),
                            padding=ft.Padding(20, 15, 20, 15),
                        ),
                        on_click=self.create_week_schedule_for_all_boxes,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

    def open_start_time_picker(self, e):
        self.page.open(self.schedule_start_time_picker)

    def open_end_time_picker(self, e):
        self.page.open(self.schedule_end_time_picker)

    def on_time_change(self, e):
        if e.control == self.schedule_start_time_picker:
            selected_time = self.schedule_start_time_picker.value.strftime(
                '%H:%M'
            )
            self.start_time_button.text = f'Начало: {selected_time}'
            self.page.update()

        elif e.control == self.schedule_end_time_picker:
            selected_time = self.schedule_end_time_picker.value.strftime(
                '%H:%M'
            )
            self.end_time_button.text = f'Окончание: {selected_time}'
            self.page.update()

    def create_manual_schedule_section(self):
        self.start_time_button_manual = ft.ElevatedButton(
            text='Выбрать время начала',
            on_click=self.open_start_time_picker_manual,
        )

        self.end_time_button_manual = ft.ElevatedButton(
            text='Выбрать время окончания',
            on_click=self.open_end_time_picker_manual,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Механическое расписание', size=24),
                    self.start_time_button_manual,
                    self.end_time_button_manual,
                    ft.Text('Выберите дни недели:'),
                    ft.Container(
                        content=ft.Row(
                            controls=self.days_of_week_checkboxes,
                            scroll='auto',
                            spacing=10,
                        ),
                        padding=ft.padding.only(bottom=10),
                    ),
                    ft.ElevatedButton(
                        text='Добавить самостоятельно',
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE,
                            color=ft.colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=50),
                            padding=ft.Padding(20, 15, 20, 15),
                        ),
                        on_click=self.on_add_schedule,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=10),
        )

    def open_start_time_picker_manual(self, e):
        self.page.open(self.schedule_start_time_picker_manual)

    def open_end_time_picker_manual(self, e):
        self.page.open(self.schedule_end_time_picker_manual)

    def on_time_change_manual(self, e):
        if e.control == self.schedule_start_time_picker_manual:
            selected_time = (
                self.schedule_start_time_picker_manual.value.strftime('%H:%M')
            )
            self.start_time_button_manual.text = f'Начало: {selected_time}'
            self.page.update()

        elif e.control == self.schedule_end_time_picker_manual:
            selected_time = (
                self.schedule_end_time_picker_manual.value.strftime('%H:%M')
            )
            self.end_time_button_manual.text = f'Окончание: {selected_time}'
            self.page.update()

    def create_week_schedule_for_all_boxes(self, e):
        today = datetime.datetime.today()

        start_time = self.schedule_start_time_picker.value.strftime('%H:%M:%S')
        end_time = self.schedule_end_time_picker.value.strftime('%H:%M:%S')

        if not start_time or not end_time:
            print('Ошибка: Время начала или окончания не указано.')
            return

        self.show_loading()

        existing_schedules = {
            schedule['day_of_week']: schedule
            for schedule in self.schedule_list
        }

        for i in range(7):
            schedule_date = today + datetime.timedelta(days=i)
            day_of_week = schedule_date.weekday()

            if day_of_week in existing_schedules:
                print(
                    f'Расписание на день '
                    f'{day_of_week} уже существует, пропускаем.'
                )
                continue

            self.dates_storage[day_of_week] = schedule_date.strftime(
                '%Y-%m-%d'
            )

            new_schedule_data = {
                'car_wash_id': self.car_wash['id'],
                'day_of_week': day_of_week,
                'start_time': start_time,
                'end_time': end_time,
                'is_available': True,
            }

            response = self.api.create_schedule(new_schedule_data)
            if response.status_code == 200:
                print(
                    f"Создано расписание для "
                    f"{schedule_date.strftime('%Y-%m-%d')} "
                    f"на день {day_of_week}"
                )
            else:
                print(
                    f'Ошибка создания расписания для дня '
                    f'{day_of_week}: {response.text}'
                )

        self.hide_loading()
        self.refresh_schedule_list()  # Обновляем только список расписаний

    # def update_schedule_and_scroll(self):
    #     """Старый метод для обновления расписаний
    #     с полной перезагрузкой страницы."""
    #     self.show_loading()
    #
    #     response = self.api.get_schedules(self.car_wash['id'])
    #     if response.status_code == 200:
    #         self.schedule_list = response.json().get('data', [])
    #         print(f'Загружено расписаний: {len(self.schedule_list)}')
    #
    #     self.page.controls.clear()
    #     self.page.add(self.create_schedule_management_page())
    #     self.page.update()
    #
    #     self.hide_loading()

    def refresh_schedule_list(self):
        """Метод для обновления секции расписания
        без полной перезагрузки страницы
        """
        self.load_schedules()
        self.schedule_list_container.content = (
            self.create_schedule_list_section()
        )
        self.page.update()

    def on_add_schedule(self, e):
        if (
            self.schedule_start_time_picker_manual.value is None
            or self.schedule_end_time_picker_manual.value is None
        ):
            print('Ошибка: Время начала и окончания должно быть выбрано.')
            return

        start_time = self.schedule_start_time_picker_manual.value.strftime(
            '%H:%M:%S'
        )
        end_time = self.schedule_end_time_picker_manual.value.strftime(
            '%H:%M:%S'
        )

        self.show_loading()

        for day in self.selected_days:
            schedule_data = {
                'car_wash_id': self.car_wash['id'],
                'day_of_week': day,
                'start_time': start_time,
                'end_time': end_time,
                'is_available': True,
            }

            response = self.api.create_schedule(schedule_data)
            if response.status_code == 200:
                print(f'Расписание на день {day + 1} создано')
            else:
                print(
                    f'Ошибка создания расписания для дня {day + 1}: '
                    f'{response.text}'
                )

        self.hide_loading()
        self.refresh_schedule_list()

    def create_schedule_management_page(self):
        self.schedule_list_container = ft.Container(
            content=self.create_schedule_list_section(), expand=True
        )

        return ft.ListView(
            controls=[
                self.create_week_schedule_section(),
                ft.Divider(),
                self.create_manual_schedule_section(),
                ft.Divider(),
                self.schedule_list_container,
            ],
            spacing=20,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

    def on_back_to_edit_page(self, e=None):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api_url)
