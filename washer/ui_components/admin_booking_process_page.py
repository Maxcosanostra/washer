import datetime
import locale

import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.admin_car_selection_page import AdminCarSelectionPage


class AdminBookingProcessPage:
    def __init__(
        self,
        page: ft.Page,
        car_wash,
        box_id,
        date,
        time,
        selected_car,
        car_price,
    ):
        self.page = page
        self.car_wash = car_wash
        self.box_id = box_id
        self.date = date
        self.time = time
        self.selected_car = selected_car
        self.car_price = car_price

        self.api = BackendApi()
        access_token = self.page.client_storage.get('access_token')
        if access_token:
            self.api.set_access_token(access_token)

        self.snack_bar = None

        self.confirm_button = ft.ElevatedButton(
            text='Подтвердить букинг',
            on_click=self.on_confirm_booking,
            width=300,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            disabled=False,
        )

        self.notes_field = ft.TextField(
            label=(
                'Например: оставил вещи в салоне. '
                'Переложите, пожалуйста, в багажник и тд..'
            ),
            hint_text='',
            multiline=True,
            width=300,
            height=100,
            border_radius=ft.border_radius.all(10),
        )

        self.setup_snack_bar()
        self.show_confirmation_page()

    def setup_snack_bar(self):
        self.snack_bar = ft.SnackBar(
            content=ft.Text(''),
            bgcolor=ft.colors.GREEN,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

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

    def on_car_selected(self, car, price):
        self.selected_car = car
        self.car_price = price
        print(f'Сохраненные данные автомобиля: {car}')

        if (
            self.selected_car
            and self.selected_car.get('configuration_id')
            and self.car_price
            and self.box_id
            and self.date
            and self.time
        ):
            self.confirm_button.disabled = False
        else:
            self.confirm_button.disabled = True

        self.page.update()
        self.show_confirmation_page()

    def on_confirm_booking(self, e):
        if not (
            self.selected_car
            and self.selected_car.get('user_car_id')
            and self.car_price
            and self.box_id
            and self.date
            and self.time
        ):
            self.show_error_message(
                'Пожалуйста, выберите все необходимые данные.'
            )
            return

        start_datetime = f'{self.date}T{self.time}:00'
        end_datetime = (
            datetime.datetime.fromisoformat(start_datetime)
            + datetime.timedelta(hours=2)
        ).isoformat()

        user_car_id = self.selected_car.get('user_car_id')
        if user_car_id is None:
            self.show_error_message('ID выбранного автомобиля недоступен.')
            return

        # Получаем значение заметок из текстового поля
        notes = (
            self.notes_field.value.strip() if self.notes_field.value else ''
        )

        booking_data = {
            'box_id': self.box_id,
            'user_car_id': user_car_id,
            'state': 'CREATED',
            'addition_ids': [],
            'notes': notes,
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
        }

        try:
            response = self.api.create_booking(booking_data)
            if response.status_code == 200:
                print('Букинг успешно создан!')
                self.show_success_message('Букинг успешно создан!')
                self.confirm_button.disabled = True
                self.page.update()

                from washer.ui_components.admin_booking_table import (
                    AdminBookingTable,
                )

                AdminBookingTable(
                    self.page,
                    self.car_wash,
                    self.date,
                    selected_date=self.date,
                )

            else:
                print(f'Ошибка создания букинга: {response.text}')
                self.show_error_message(
                    f'Ошибка создания букинга: {response.text}'
                )
        except Exception as ex:
            print(f'Ошибка: {str(ex)}')
            self.show_error_message(f'Ошибка: {str(ex)}')

    def show_car_selection_page(self):
        self.page.clean()
        AdminCarSelectionPage(
            page=self.page,
            on_car_selected=self.on_car_selected,
            car_wash=self.car_wash,
            box_id=self.box_id,
            date=self.date,
            time=self.time,
        )

    def show_confirmation_page(self):
        self.page.clean()

        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        date_obj = (
            self.date
            if isinstance(self.date, datetime.date)
            else datetime.datetime.strptime(self.date, '%Y-%m-%d').date()
        )
        formatted_date = date_obj.strftime('%d %B')
        day_of_week = date_obj.strftime('%a')
        day_of_week_translated = {
            'Mon': 'Пн',
            'Tue': 'Вт',
            'Wed': 'Ср',
            'Thu': 'Чт',
            'Fri': 'Пт',
            'Sat': 'Сб',
            'Sun': 'Вс',
        }.get(day_of_week, day_of_week)
        date_with_day = f'{formatted_date} ({day_of_week_translated})'

        car_details = [
            ('Бренд', self.selected_car.get('brand')),
            ('Модель', self.selected_car.get('model')),
            ('Поколение', self.selected_car.get('generation') or 'Не указано'),
            ('Тип кузова', self.selected_car.get('body_type')),
        ]

        car_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in car_details
            ],
            spacing=10,
        )

        car_info_card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'Информация об автомобиле',
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Divider(),
                            car_info_column,
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(20),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

        booking_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text('Дата', weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(
                            date_with_day, color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text(
                            'Номер бокса', weight=ft.FontWeight.BOLD, size=16
                        ),
                        ft.Text(
                            str(self.box_id), color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text('Время', weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(
                            self.time[:5], color=ft.colors.GREY_600, size=16
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text(
                            'Стоимость', weight=ft.FontWeight.BOLD, size=16
                        ),
                        ft.Text(
                            f'₸{int(self.car_price)}',
                            color=ft.colors.GREY_600,
                            size=16,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=10,
        )

        booking_info_card = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'Информация о букинге',
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
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

        wishes_header = ft.Text(
            'Есть пожелания или комментарии? Добавьте ниже',
            size=18,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
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
            on_click=lambda e: self.show_car_selection_page(),
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=lambda e: self.show_car_selection_page(),
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=None,
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        main_content = ft.Column(
            [
                ft.Text(
                    'Пожалуйста, подтвердите свои данные',
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                booking_info_card,
                car_info_card,
                wishes_header,
                ft.Container(
                    content=self.notes_field,
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=10),
                ),
                confirm_button,
                back_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        confirmation_container = ft.Container(
            content=ft.ListView(
                controls=[
                    main_content,
                ],
                spacing=20,
                padding=ft.padding.all(20),
            ),
            expand=True,
        )

        self.page.add(confirmation_container)
        self.page.update()
