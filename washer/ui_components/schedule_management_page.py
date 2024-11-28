import datetime

import flet as ft

from washer.api_requests import BackendApi


class ScheduleManagementPage:
    def __init__(self, page: ft.Page, car_wash, api_url, locations):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url
        self.locations = locations

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
        self.setup_snack_bar()
        self.load_schedules()

        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_schedule_management_page())
        self.page.overlay.append(self.loading_overlay)
        self.page.overlay.append(self.snack_bar)

    def setup_snack_bar(self):
        self.snack_bar = ft.SnackBar(
            content=ft.Text(''),
            bgcolor=ft.colors.GREEN,
            duration=3000,
        )

    def show_snack_bar(
        self,
        message: str,
        bgcolor: str = ft.colors.GREEN,
        text_color: str = ft.colors.WHITE,
    ):
        print(f'Показываем сообщение: {message}')
        self.snack_bar.content.value = message
        self.snack_bar.content.color = text_color
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True
        self.page.update()

    def show_success_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_error_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.RED)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

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
                        ft.Container(
                            content=ft.Text(
                                f'{schedule_date}',
                                text_align=ft.TextAlign.CENTER,
                            ),
                            expand=2,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f'{day_name}',
                                text_align=ft.TextAlign.CENTER,
                            ),
                            expand=4,
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text(
                                f'{start_time} - {end_time}',
                                text_align=ft.TextAlign.CENTER,
                            ),
                            expand=4,
                            alignment=ft.alignment.center,
                        ),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    on_click=lambda e,
                                    s=schedule: self.on_edit_schedule(s),
                                    icon_size=16,
                                    tooltip='Редактировать расписание',
                                    padding=ft.padding.all(0),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    on_click=lambda e,
                                    s=schedule: self.on_delete_schedule(
                                        s['id']
                                    ),
                                    icon_size=16,
                                    tooltip='Удалить расписание',
                                    padding=ft.padding.all(0),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=0,
                            width=60,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    'Дата',
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                expand=2,
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    'День недели',
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                expand=4,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(left=5),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    'Время',
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                expand=4,
                                alignment=ft.alignment.center,
                                # padding=ft.padding.only(left=5),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    'Опции',
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                width=60,
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(left=10),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ]
                + rows,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            key='schedule_list_section',
        )

    def on_edit_schedule(self, schedule):
        self.current_edit_schedule = schedule
        self.show_start_time_modal()

    def show_start_time_modal(self):
        self.start_time_input = ft.TextField(
            label='Введите время начала (формат ЧЧ:ММ)',
            hint_text='Например: 08:00',
            expand=True,
        )

        modal = ft.AlertDialog(
            title=ft.Text('Редактировать время начала'),
            content=self.start_time_input,
            actions=[
                ft.ElevatedButton(
                    text='Подтвердить',
                    on_click=self.on_confirm_start_time,
                ),
                ft.TextButton(
                    text='Отмена',
                    on_click=lambda e: self.close_modal(),
                ),
            ],
            modal=True,
        )
        self.page.dialog = modal
        self.page.dialog.open = True
        self.page.update()

    def on_confirm_start_time(self, e):
        start_time = self.start_time_input.value.strip()
        try:
            datetime.datetime.strptime(start_time, '%H:%M')
            self.current_start_time = start_time + ':00'
            self.close_modal()
            self.show_end_time_modal()
        except ValueError:
            print('Ошибка: Неверный формат времени. Используйте ЧЧ:ММ.')

    def show_end_time_modal(self):
        self.end_time_input = ft.TextField(
            label='Введите время окончания (формат ЧЧ:ММ)',
            hint_text='Например: 18:00',
            expand=True,
        )

        modal = ft.AlertDialog(
            title=ft.Text('Редактировать время окончания'),
            content=self.end_time_input,
            actions=[
                ft.ElevatedButton(
                    text='Подтвердить',
                    on_click=self.on_confirm_end_time,
                ),
                ft.TextButton(
                    text='Отмена',
                    on_click=lambda e: self.close_modal(),
                ),
            ],
            modal=True,
        )
        self.page.dialog = modal
        self.page.dialog.open = True
        self.page.update()

    def on_confirm_end_time(self, e):
        end_time = self.end_time_input.value.strip()
        try:
            datetime.datetime.strptime(end_time, '%H:%M')
            self.current_end_time = end_time + ':00'
            self.close_modal()

            updated_schedule = {
                'start_time': self.current_start_time,
                'end_time': self.current_end_time,
            }

            self.show_loading()
            response = self.api.update_schedule(
                self.current_edit_schedule['id'], updated_schedule
            )
            if response.status_code == 200:
                message = (
                    f'Время расписания обновлено: '
                    f'{self.current_start_time} - {self.current_end_time}.'
                )
                print(message)
                self.show_success_message(message)
                self.refresh_schedule_list()
            else:
                error_message = (
                    f'Ошибка обновления расписания: {response.text}'
                )
                print(error_message)
                self.show_error_message(error_message)
            self.hide_loading()
        except ValueError:
            error_message = (
                'Ошибка: Неверный формат времени. Используйте ЧЧ:ММ.'
            )
            print(error_message)
            self.show_error_message(error_message)

    def close_modal(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    def on_delete_schedule(self, schedule_id):
        confirmation_dialog = ft.AlertDialog(
            title=ft.Text('Подтверждение удаления'),
            content=ft.Text(
                'Вы уверены, что хотите удалить этот день из расписания?'
            ),
            actions=[
                ft.TextButton(
                    text='Отмена',
                    on_click=lambda e: self.close_modal(),
                ),
                ft.ElevatedButton(
                    text='Подтвердить',
                    on_click=lambda e: self.confirm_delete_schedule(
                        schedule_id
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.RED,
                        color=ft.colors.WHITE,
                    ),
                ),
            ],
            modal=True,
        )
        self.page.dialog = confirmation_dialog
        self.page.dialog.open = True
        self.page.update()

    def confirm_delete_schedule(self, schedule_id):
        self.close_modal()
        self.show_loading()
        response = self.api.delete_schedule(schedule_id)
        if response.status_code == 200:
            message = 'Расписание успешно удалено.'
            print(message)
            self.show_success_message(message)
            self.refresh_schedule_list()
        else:
            error_message = f'Ошибка при удалении расписания: {response.text}'
            print(error_message)
            self.show_error_message(error_message)
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
            error_message = 'Ошибка: Время начала или окончания не указано.'
            print(error_message)
            self.show_error_message(error_message)
            return

        self.show_loading()
        success_count = 0
        for i in range(7):
            schedule_date = today + datetime.timedelta(days=i)
            day_of_week = schedule_date.weekday()
            new_schedule_data = {
                'car_wash_id': self.car_wash['id'],
                'day_of_week': day_of_week,
                'start_time': start_time,
                'end_time': end_time,
                'is_available': True,
            }
            response = self.api.create_schedule(new_schedule_data)
            if response.status_code == 200:
                success_count += 1
            else:
                print(
                    f'Ошибка создания расписания для дня {day_of_week}: '
                    f'{response.text}'
                )

        self.hide_loading()
        if success_count > 0:
            message = f'Создано расписаний: {success_count} из 7.'
            self.show_success_message(message)
        else:
            error_message = 'Ошибка создания недельного расписания.'
            self.show_error_message(error_message)
        self.refresh_schedule_list()

    # Обновляем только список расписаний

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
            error_message = (
                'Ошибка: Время начала и окончания должно быть выбрано.'
            )
            print(error_message)
            self.show_error_message(error_message)
            return

        start_time = self.schedule_start_time_picker_manual.value.strftime(
            '%H:%M:%S'
        )
        end_time = self.schedule_end_time_picker_manual.value.strftime(
            '%H:%M:%S'
        )
        self.show_loading()
        success_count = 0

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
                success_count += 1
            else:
                print(
                    f'Ошибка создания расписания для дня {day + 1}: '
                    f'{response.text}'
                )

        self.hide_loading()
        if success_count > 0:
            message = (
                f'Создано расписаний: {success_count} из '
                f'{len(self.selected_days)}.'
            )
            self.show_success_message(message)
        else:
            error_message = 'Ошибка создания механического расписания.'
            self.show_error_message(error_message)
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

        CarWashEditPage(self.page, self.car_wash, self.api_url, self.locations)
