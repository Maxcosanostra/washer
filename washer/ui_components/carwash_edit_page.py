import datetime
import io
import json

import flet as ft
import httpx

from washer.api_requests import BackendApi
from washer.ui_components.box_revenue_page import BoxRevenuePage


class CarWashEditPage:
    def __init__(self, page: ft.Page, car_wash, api_url):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url
        self.selected_image = None
        self.selected_image_bytes = None

        self.dates_storage = {}

        self.schedule_list_container = None

        self.body_type_dict = {}

        self.price_list = self.load_prices()

        self.load_body_types()

        self.page.adaptive = True

        # # Устанавливаем черный фон для всей страницы
        # self.page.theme_mode = ft.ThemeMode.LIGHT
        # self.page.bgcolor = None

        self.boxes_list = []
        self.schedule_list = []
        self.selected_days = []
        self.selected_boxes = []

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

        self.load_boxes()

        self.load_schedules()

        page.clean()
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

        self.schedule_list_container = ft.Container(
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

        return self.schedule_list_container

    def on_delete_schedule(self, schedule_id):
        self.show_loading()
        response = self.api.delete_schedule(schedule_id)
        if response.status_code == 200:
            print(f'Расписание с ID {schedule_id} успешно удалено.')
            self.load_schedules()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка при удалении расписания: {response.text}')
        self.hide_loading()

    def load_boxes(self):
        self.show_loading()
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            all_boxes = response.json().get('data', [])
            self.boxes_list = [
                box
                for box in all_boxes
                if box['car_wash_id'] == self.car_wash['id']
            ]
        else:
            print(f'Ошибка загрузки боксов: {response.text}')
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

    def create_boxes_checkboxes(self):
        checkboxes = []
        for box in self.boxes_list:
            checkbox = ft.Checkbox(
                label=f"Бокс {box['id']}",
                value=False,
                on_change=self.on_box_checked,
                data=box['id'],
            )
            checkboxes.append(checkbox)
        return checkboxes

    def on_box_checked(self, e: ft.ControlEvent):
        box_id = e.control.data
        if e.control.value:
            if box_id not in self.selected_boxes:
                self.selected_boxes.append(box_id)
        else:
            if box_id in self.selected_boxes:
                self.selected_boxes.remove(box_id)

    def select_all_boxes(self, e):
        self.selected_boxes = [box['id'] for box in self.boxes_list]
        for checkbox in self.create_boxes_checkboxes():
            checkbox.value = True
        self.page.update()

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
                ft.Container(
                    content=ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.icons.ARROW_BACK,
                                icon_size=30,
                                on_click=self.on_back_to_admin_page,
                            ),
                            ft.Text('Назад', size=16),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    expand=0,
                    padding=ft.padding.symmetric(vertical=20),
                ),
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
                        ft.IconButton(
                            icon=ft.icons.UPLOAD,
                            icon_size=30,
                            on_click=lambda _: self.image_picker.pick_files(
                                allow_multiple=False,
                                file_type=ft.FilePickerFileType.IMAGE,
                            ),
                            tooltip='Загрузить новое изображение',
                        ),
                        ft.IconButton(
                            icon=ft.icons.SAVE,
                            icon_size=30,
                            on_click=self.on_save_click,
                            tooltip='Сохранить изменения',
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Divider(),
                self.create_boxes_ui(),
                ft.Divider(),
                self.create_week_schedule_section(),
                ft.Divider(),
                self.create_manual_schedule_section(),
                ft.Divider(),
                self.create_schedule_list_section(),
                ft.Divider(),
                self.create_price_list_section(),
                ft.Divider(),
                self.create_add_price_section(),
                ft.ElevatedButton(
                    text='Перейти к тестовому букингу',
                    on_click=self.on_test_booking_click,
                ),
            ],
            spacing=20,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

    def on_test_booking_click(self, e):
        from washer.ui_components.test_booking_page import TestBookingPage

        TestBookingPage(self.page, self.car_wash, self.api_url)

    def create_boxes_ui(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Боксы', size=24, text_align=ft.TextAlign.CENTER),
                    ft.Column(
                        controls=[
                            self.create_box_item_ui(box)
                            for box in self.boxes_list
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=10,
                    ),
                    self.create_add_box_ui(),
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
        )

    def create_box_item_ui(self, box):
        box_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        box['name'],
                        size=16,
                        weight='bold',
                        text_align=ft.TextAlign.LEFT,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.icons.RECEIPT_LONG,
                        on_click=lambda _: self.open_box_revenue_page(box),
                        icon_size=20,
                        tooltip='Посмотреть выручку',
                    ),
                    ft.IconButton(
                        icon=ft.icons.EDIT,
                        on_click=lambda _: self.show_edit_name_modal(box),
                        icon_size=20,
                        tooltip='Редактировать имя',
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda _: self.on_delete_box(box['id']),
                        icon_size=20,
                        tooltip='Удалить бокс',
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=10),
            border_radius=ft.border_radius.all(8),
            bgcolor=ft.colors.GREY_900,
            shadow=ft.BoxShadow(
                offset=ft.Offset(0, 2),
                blur_radius=4,
                color=ft.colors.GREY_700,
            ),
            width=300,
        )
        return box_container

    def open_box_revenue_page(self, box):
        BoxRevenuePage(self.page, box, self.car_wash, self.api_url)

    def show_edit_name_modal(self, box):
        name_field = ft.TextField(
            label='Новое имя бокса',
            value=box['name'],
            width=300,
        )
        save_button = ft.ElevatedButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_box(box, name_field.value),
        )
        close_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Редактировать имя бокса', size=18),
                    name_field,
                    ft.Row(
                        controls=[save_button, close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            padding=ft.padding.all(10),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def close_modal(self, e=None):
        if self.modal_container in self.page.controls:
            self.page.controls.remove(self.modal_container)
        self.page.update()

    def create_add_box_ui(self):
        return ft.Container(
            content=ft.IconButton(
                icon=ft.icons.CREATE,
                icon_size=30,
                tooltip='Добавить новый бокс',
                on_click=self.show_add_box_field,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
        )

    def show_add_box_field(self, e):
        self.add_box_field = ft.TextField(
            label='Имя нового бокса', width=200, text_align=ft.TextAlign.CENTER
        )
        self.add_box_button = ft.TextButton(
            text='Сохранить', on_click=self.on_add_box_from_modal
        )
        self.close_button = ft.TextButton(
            text='Отмена', on_click=self.close_modal
        )

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            'Добавить новый бокс',
                            size=18,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=self.add_box_field,
                        alignment=ft.alignment.center,
                    ),
                    ft.Row(
                        controls=[self.add_box_button, self.close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(10),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def on_add_box_from_modal(self, e):
        self.show_loading()
        new_box_data = {
            'name': self.add_box_field.value,
            'car_wash_id': self.car_wash['id'],
            'user_id': 1,
        }

        response = self.api.create_box(new_box_data)
        if response.status_code == 200:
            print(f"Бокс '{self.add_box_field.value}' успешно добавлен.")
            self.close_modal(e)
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка добавления бокса: {response.text}')
        self.hide_loading()

    # def close_modal(self, e=None):
    #     if self.modal_container in self.page.controls:
    #         self.page.controls.remove(self.modal_container)
    #     self.page.update()

    def create_week_schedule_section(self):
        self.schedule_start_time = None
        self.schedule_end_time = None

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
                    f'Расписание на день {day_of_week} '
                    f'уже существует, пропускаем.'
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

        self.update_schedule_and_scroll()

    def update_schedule_and_scroll(self):
        self.show_loading()

        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            self.schedule_list = response.json().get('data', [])
            print(f'Загружено расписаний: {len(self.schedule_list)}')

        self.page.controls.clear()
        self.page.add(self.create_edit_page())
        self.page.update()

        self.hide_loading()

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
                    f'Ошибка создания расписания на день '
                    f'{day + 1}: {response.text}'
                )

        self.hide_loading()

        self.update_schedule_and_scroll()

    def on_delete_box(self, box_id):
        self.show_loading()
        response = self.api.delete_box(box_id)
        if response.status_code == 200:
            print(f'Бокс с ID {box_id} успешно удален.')
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка при удалении бокса: {response.text}')
        self.hide_loading()

    def on_save_box(self, box, new_name):
        self.show_loading()
        response = self.api.update_box(box['id'], new_name)
        if response.status_code == 200:
            print(f"Бокс с ID {box['id']} успешно обновлен.")
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка при обновлении бокса: {response.text}')
        self.hide_loading()

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
                # Оставляем радиус для круга
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

    def create_price_list_section(self):
        rows = []

        for price in self.price_list:
            body_type_name = self.body_type_dict.get(
                price['body_type_id'], 'Неизвестный тип кузова'
            )
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            f'{body_type_name}',
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            f"{price['price']} руб.",
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            tooltip='Редактировать цену',
                            on_click=lambda e,
                            p=price: self.on_edit_price_click(p),
                            icon_size=18,
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            tooltip='Удалить цену',
                            on_click=lambda e, p=price: self.on_delete_price(
                                p['id']
                            ),
                            icon_size=18,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Container(
            content=ft.Column(
                controls=[ft.Text('Текущие цены', size=24), *rows],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def create_add_price_section(self):
        existing_body_type_ids = [
            price['body_type_id'] for price in self.price_list
        ]
        available_body_types = [
            (id, name)
            for id, name in self.body_type_dict.items()
            if id not in existing_body_type_ids
        ]

        if not available_body_types:
            return ft.Container(
                content=ft.Text('Все типы кузовов уже имеют цену'),
                alignment=ft.alignment.center,
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
            )

        body_type_dropdown = ft.Dropdown(
            label='Выберите тип кузова',
            options=[
                ft.dropdown.Option(key=str(id), text=name)
                for id, name in available_body_types
            ],
            width=300,
        )

        price_field = ft.TextField(label='Цена', width=300)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Добавить цену',
                        size=24,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    body_type_dropdown,
                    price_field,
                    ft.ElevatedButton(
                        text='Создать цену',
                        on_click=lambda e: self.on_create_price_click(
                            body_type_dropdown.value, price_field.value
                        ),
                        width=150,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
        )

    def on_create_price_click(self, body_type_id, price):
        if not body_type_id or not price:
            print('Заполните все поля!')
            return

        price_data = {
            'car_wash_id': self.car_wash['id'],
            'body_type_id': int(body_type_id),
            'price': float(price),
        }

        response = self.api.create_price(price_data)
        if response.status_code == 200:
            print('Цена успешно добавлена')
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка добавления цены: {response.text}')

    def on_edit_price_click(self, price):
        price_field = ft.TextField(
            label='Цена', value=str(price['price']), width=200
        )
        save_button = ft.TextButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_price_click(
                price['id'], price_field.value
            ),
        )
        close_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        body_type = self.body_type_dict.get(
            price['body_type_id'], 'Неизвестный тип кузова'
        )

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f'Редактирование цены для {body_type}',
                        size=18,
                    ),
                    price_field,
                    ft.Row(
                        controls=[save_button, close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def on_save_price_click(self, price_id, new_price):
        if not new_price:
            print('Заполните поле цены!')
            return

        price_data = {'price': float(new_price)}

        response = self.api.update_price(price_id, price_data)
        if response.status_code == 200:
            print('Цена успешно обновлена')
            self.load_prices()
            self.close_modal()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка обновления цены: {response.text}')

    def on_delete_price(self, price_id):
        confirm_button = ft.TextButton(
            text='Подтвердить', on_click=lambda e: self.delete_price(price_id)
        )
        cancel_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Вы уверены, что хотите удалить эту цену?', size=18
                    ),
                    ft.Row(
                        controls=[confirm_button, cancel_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def delete_price(self, price_id):
        response = self.api.delete_price(price_id)
        if response.status_code == 200:
            print(f'Цена с ID {price_id} успешно удалена.')
            self.load_prices()
            self.close_modal()
            self.page.controls.clear()
            self.page.add(self.create_edit_page())
            self.page.update()
        else:
            print(f'Ошибка удаления цены: {response.text}')

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

    def load_prices(self):
        response = self.api.get_prices(self.car_wash['id'])
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f'Ошибка загрузки цен: {response.text}')
            return []

    def on_back_to_admin_page(self, e=None):
        from washer.ui_components.admin_page import AdminPage

        AdminPage(self.page)
