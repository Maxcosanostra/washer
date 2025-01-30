import datetime
import locale
import re
from typing import List, Tuple

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

        # Если selected_car пришёл с уже готовыми полями brand, model и т.д.,
        # они уже будут в self.selected_car.
        # Но если этого нет, ниже можно сделать проверку, чтобы подставить их.
        self.parse_car_if_needed()  # <-- вот эта часть

        self.show_confirmation_page()

    def parse_car_if_needed(self):
        """
        Если у self.selected_car не заданы поля brand, model, generation,
        body_type, то распарсить их из 'name' и заполнить вручную.
        """
        if not self.selected_car:
            return

        # Проверяем, есть ли уже brand. Если нет — парсим name
        if not self.selected_car.get('brand'):
            name_str = self.selected_car.get('name', '')
            if name_str:
                brand, model, generation, body_type = self.parse_car_name(
                    name_str
                )
                self.selected_car['brand'] = brand
                self.selected_car['model'] = model
                self.selected_car['generation'] = generation
                self.selected_car['body_type'] = body_type

    def parse_car_name(self, name: str) -> tuple[str, str, str, str]:
        print(f'Parsing car name: {name}')

        body_types = [
            'внедорожник 5 дв',
            'внедорожник 3 дв',
            'седан 4 дв',
            'хэтчбек 5 дв',
            'хэтчбек 3 дв',
            'универсал 5 дв',
            'лифтбек 5 дв',
            'фастбек 3 дв',
            'купе 2 дв',
            'кабриолет 2 дв',
            'седан',
            'хэтчбек',
            'универсал',
            'внедорожник',
            'купе',
            'кабриолет',
            'минивэн',
            'пикап',
            'фургон',
            'лимузин',
            'тарга',
            'родстер',
            'комби',
            'фастбек',
            'лифтбек',
            'спортивный',
            'кроссовер',
            'вэн',
            'микроавтобус',
            'минивен',
            '4 дв',
            '5 дв',
            '3 дв',
        ]
        body_types.sort(key=lambda x: -len(x))

        numeric_generation_pattern = re.compile(
            r'\b(\d{4}-(?:\d{4}|present))\b', re.IGNORECASE
        )

        roman_generation_pattern = re.compile(
            r'\b([IVXLCDM]+(?:\s*\([^)]*\))*(?:\s*Рестайлинг(?:\s*\d+)?)?(?:\s*\(\d{4}-present\))?)\b',
            re.IGNORECASE,
        )

        words = name.split()
        print(f'Words: {words}')

        brand = words[0] if words else 'Бренд не указан'
        remaining_words = words[1:] if len(words) > 1 else []

        print(f'Brand: {brand}')
        print(f'Remaining words: {remaining_words}')

        generation = 'Поколение не указано'
        body_type = 'Тип кузова не указан'
        model = 'Модель не указана'

        # Явная аннотация типа для списка matches
        matches: List[Tuple[int, int, str, str]] = []
        for i in range(len(remaining_words)):
            for j in range(i + 1, min(i + 6, len(remaining_words) + 1)):
                potential_generation = ' '.join(remaining_words[i:j])
                if numeric_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'numeric'))
                elif roman_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'roman'))

        if matches:
            # Сортируем, чтобы взять самое длинное совпадение
            matches.sort(key=lambda x: (-x[0], x[3]))
            _, generation_index, generation, generation_type = matches[0]
            print(f'Found generation: {generation} ({generation_type})')
            # Убираем найденный кусок из remaining_words
            remaining_words = (
                remaining_words[:generation_index]
                + remaining_words[generation_index + matches[0][0] :]
            )
        else:
            print('Generation not found')

        matched_body_types = []
        # Ищем тип кузова
        # (забираем самые последние слова, сравниваем с body_types)
        for i in range(len(remaining_words), 0, -1):
            potential_body_type = (
                ' '.join(remaining_words[i - 1 :]).lower().rstrip('.')
            )
            for bt in body_types:
                if potential_body_type == bt.lower():
                    matched_body_types.append((i - 1, bt))
        if matched_body_types:
            matched_body_types.sort(key=lambda x: x[0])
            body_type_index, body_type = matched_body_types[0]
            remaining_words = remaining_words[:body_type_index]
            print(f'Found body type: {body_type}')
        else:
            print('Body type not found')

        if remaining_words:
            model = ' '.join(remaining_words)
        else:
            model = 'Модель не указана'

        print(f'Model: {model}')
        print(f'Generation: {generation}')
        print(f'Body type: {body_type}')

        return brand, model, generation, body_type

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
        """
        Метод вызывается, когда пользователь выбрал автомобиль
        (либо создал, либо выбрал из ClientsPage).
        """
        self.selected_car = car
        self.car_price = price
        print(f'Сохраненные данные автомобиля: {car}')

        # Если у автомобиля нет brand/model/generation/body_type,
        # попробуем их получить из parse_car_name
        self.parse_car_if_needed()  # <-- вот эта часть

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
            and (
                self.selected_car.get('id')
                or self.selected_car.get('user_car_id')
            )
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

        user_car_id = self.selected_car.get(
            'user_car_id'
        ) or self.selected_car.get('id')
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

        # Если у self.selected_car нет brand/model/generation/body_type,
        # ещё раз убеждаемся, что мы их пропарсили:
        if not self.selected_car.get('brand'):
            self.parse_car_if_needed()

        # Формируем структуру данных для отображения
        car_details = [
            ('Бренд', self.selected_car.get('brand', '---')),
            ('Модель', self.selected_car.get('model', '---')),
            (
                'Поколение',
                self.selected_car.get('generation', 'Не указано'),
            ),
            (
                'Тип кузова',
                self.selected_car.get('body_type', 'Не указано'),
            ),
            (
                'Номер автомобиля',
                self.selected_car.get('license_plate', '---'),
            ),
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
