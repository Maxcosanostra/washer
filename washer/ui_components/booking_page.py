import calendar
import re
from datetime import date, datetime, timedelta

import flet as ft

from washer.api_requests import BackendApi

date_class: dict[int, str] = {
    0: 'Пн',
    1: 'Вт',
    2: 'Ср',
    3: 'Чт',
    4: 'Пт',
    5: 'Сб',
    6: 'Вс',
}

month_class: dict[int, str] = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь',
}


class Settings:
    year: int = datetime.now().year
    month: int = datetime.now().month

    @staticmethod
    def get_year() -> int:
        return Settings.year

    @staticmethod
    def get_month() -> int:
        return Settings.month

    @staticmethod
    def get_date(delta: int):
        if delta == 1:
            if Settings.month + delta > 12:
                Settings.month = 1
                Settings.year += 1
            else:
                Settings.month += 1

        if delta == -1:
            if Settings.month + delta < 1:
                Settings.month = 12
                Settings.year -= 1
            else:
                Settings.month -= 1


date_box_style = {
    'width': 30,
    'height': 30,
    'alignment': ft.alignment.center,
    'shape': ft.BoxShape.RECTANGLE,
    'animate': ft.Animation(duration=400, curve=ft.AnimationCurve.EASE),
    'border_radius': 5,
}


class DateBox(ft.Container):
    def __init__(
        self,
        day: int,
        date_str: str = None,
        date_instance: ft.Column = None,
        on_date_selected=None,
        date_obj: date = None,
        disabled: bool = False,
        today: date = None,
    ):
        self.today = today
        if date_obj == self.today and not disabled:
            initial_bgcolor = None
            initial_border = ft.Border(
                left=ft.BorderSide(color='#4fadf9', width=1.5),
                right=ft.BorderSide(color='#4fadf9', width=1.5),
                top=ft.BorderSide(color='#4fadf9', width=1.5),
                bottom=ft.BorderSide(color='#4fadf9', width=1.5),
            )
            initial_text_color = ft.colors.BLUE
        else:
            initial_bgcolor = None
            initial_border = None
            initial_text_color = (
                ft.colors.GREY_500 if disabled else ft.colors.BLUE
            )

        super().__init__(
            **date_box_style,
            data=date_str,
            on_click=self.selected if not disabled else None,
            bgcolor=initial_bgcolor,
            border=initial_border,
        )

        self.day = day
        self.date_instance = date_instance
        self.on_date_selected = on_date_selected
        self.date_obj = date_obj
        self.disabled = disabled

        if isinstance(self.day, int) and self.day != 0:
            self.content = ft.Text(
                str(self.day),
                text_align=ft.TextAlign.CENTER,
                color=initial_text_color,
            )
        else:
            self.content = ft.Text('', text_align=ft.TextAlign.CENTER)

    def selected(self, e: ft.TapEvent):
        if self.date_instance:
            for row in self.date_instance.controls:
                if isinstance(row, ft.Row):
                    for date_box in row.controls:
                        if isinstance(date_box, DateBox):
                            if date_box == e.control:
                                date_box.bgcolor = ft.colors.BLUE
                                date_box.border = ft.Border(
                                    left=ft.BorderSide(
                                        color='#4fadf9', width=1.5
                                    ),
                                    right=ft.BorderSide(
                                        color='#4fadf9', width=1.5
                                    ),
                                    top=ft.BorderSide(
                                        color='#4fadf9', width=1.5
                                    ),
                                    bottom=ft.BorderSide(
                                        color='#4fadf9', width=1.5
                                    ),
                                )
                                date_box.content.color = ft.colors.WHITE
                            else:
                                if (
                                    date_box.date_obj == self.today
                                    and not date_box.disabled
                                ):
                                    date_box.bgcolor = None
                                    date_box.border = ft.Border(
                                        left=ft.BorderSide(
                                            color='#4fadf9', width=1.5
                                        ),
                                        right=ft.BorderSide(
                                            color='#4fadf9', width=1.5
                                        ),
                                        top=ft.BorderSide(
                                            color='#4fadf9', width=1.5
                                        ),
                                        bottom=ft.BorderSide(
                                            color='#4fadf9', width=1.5
                                        ),
                                    )
                                    date_box.content.color = ft.colors.BLUE
                                elif not date_box.disabled:
                                    date_box.bgcolor = None
                                    date_box.border = None
                                    date_box.content.color = ft.colors.BLUE
                                else:
                                    date_box.bgcolor = None
                                    date_box.border = None
                                    date_box.content.color = ft.colors.GREY_500

            self.date_instance.update()

            if self.on_date_selected and self.date_obj:
                self.on_date_selected(self.date_obj)


class DateGrid(ft.Column):
    def __init__(
        self, year: int, month: int, on_date_selected=None, today: date = None
    ):
        super().__init__()
        self.year = year
        self.month = month
        self.on_date_selected = on_date_selected
        self.available_dates = []
        self.today = today

        self.date_text = ft.Text(
            f'{month_class[self.month]} {self.year}', color='white'
        )

        self.year_and_month = ft.Container(
            bgcolor='#20303e',
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.IconButton(
                        icon=ft.icons.CHEVRON_LEFT,
                        icon_size=24,
                        on_click=lambda e: self.update_date_grid(e, -1),
                        icon_color='white',
                    ),
                    ft.Container(
                        width=150,
                        content=self.date_text,
                        alignment=ft.alignment.center,
                    ),
                    ft.IconButton(
                        icon=ft.icons.CHEVRON_RIGHT,
                        icon_size=24,
                        on_click=lambda e: self.update_date_grid(e, 1),
                        icon_color='white',
                    ),
                ],
            ),
        )

        self.controls.append(self.year_and_month)

        week_days = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            controls=[
                ft.Text(
                    date_class[index],
                    text_align=ft.TextAlign.CENTER,
                    color=ft.colors.GREY_500,
                    weight=ft.FontWeight.BOLD,
                )
                for index in range(7)
            ],
        )

        self.controls.append(week_days)

        self.date_rows = ft.Column(
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.controls.append(self.date_rows)

        self.on_attach = self.initial_setup

    def initial_setup(self, e):
        self.populate_date_grid(self.year, self.month)
        self.update()

    def populate_date_grid(self, year: int, month: int):
        self.date_rows.controls.clear()

        print(f'Populating calendar for {month_class[month]} {year}')
        print(f'Available dates: {self.available_dates}')
        print(f'Today is: {self.today}')

        for week in calendar.monthcalendar(year, month):
            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=5
            )
            for day in week:
                if day != 0:
                    try:
                        date_obj = datetime(year, month, day).date()
                        is_today = date_obj == self.today
                        is_available = date_obj in self.available_dates
                        print(
                            f'Date: {date_obj}, Is Today: {is_today}, '
                            f'Available: {is_available}'
                        )
                    except ValueError:
                        date_obj = None
                        is_today = False
                        is_available = False
                        print(
                            f'Invalid date: '
                            f'Year={year}, Month={month}, Day={day}'
                        )

                    date_box = DateBox(
                        day,
                        date_str=self.format_date(day),
                        date_instance=self.date_rows,
                        on_date_selected=self.on_date_selected,
                        date_obj=date_obj,
                        disabled=not is_available,
                        today=self.today,
                    )

                    if is_today and is_available:
                        date_box.bgcolor = None
                        date_box.border = ft.Border(
                            left=ft.BorderSide(color='#4fadf9', width=1.5),
                            right=ft.BorderSide(color='#4fadf9', width=1.5),
                            top=ft.BorderSide(color='#4fadf9', width=1.5),
                            bottom=ft.BorderSide(color='#4fadf9', width=1.5),
                        )
                        date_box.content.color = ft.colors.BLUE

                    row.controls.append(date_box)
                else:
                    row.controls.append(
                        DateBox(day=0, disabled=True, today=self.today)
                    )
            self.date_rows.controls.append(row)

        self.update()

    def update_date_grid(self, e: ft.TapEvent, delta: int):
        Settings.get_date(delta)

        self.today = datetime.today().date()

        self.update_year_and_month(
            Settings.get_year(),
            Settings.get_month(),
        )

        self.populate_date_grid(
            Settings.get_year(),
            Settings.get_month(),
        )
        self.update()

    def update_year_and_month(self, year: int, month: int):
        self.year = year
        self.month = month
        self.date_text.value = f'{month_class[self.month]} {self.year}'
        print(f'Updated calendar to {month_class[self.month]} {year}')
        self.date_text.update()

    def format_date(self, day: int) -> str:
        return f'{month_class[self.month]} {day}, {self.year}'

    def set_available_dates(self, available_dates: list[date]):
        self.available_dates = available_dates
        print(f'Setting available_dates for DateGrid: {self.available_dates}')
        self.populate_date_grid(self.year, self.month)
        self.update()


class BookingPage:
    def __init__(
        self,
        page: ft.Page,
        car_wash: dict,
        username: str,
        cars: list,
        location_data: dict = None,
    ):
        self.page = page
        self.car_wash = car_wash
        self.username = username
        self.api = BackendApi()
        self.location_data = location_data or {}
        self.api.set_access_token(self.page.client_storage.get('access_token'))

        self.selected_car_id = None
        self.selected_box_id = None
        self.selected_date = None
        self.today = datetime.today().date()
        self.selected_time = None
        self.selected_time_iso = None
        self.available_times = []
        self.cars = cars
        self.car_price = 0

        self.boxes = []
        self.available_boxes = []
        self.schedule_list = []
        self.available_dates = []

        self.car_dropdown_disabled = False
        self.box_dropdown_disabled = True
        self.time_dropdown_container_disabled = True
        self.book_button_disabled = True

        self.expanded_panels = [True, False, False]

        self.updating_panels = False

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )

        self.snack_bar = ft.SnackBar(
            content=ft.Text(
                '',
                text_align=ft.TextAlign.CENTER,
            ),
            bgcolor=ft.colors.RED,
            duration=3000,
        )
        self.page.overlay.append(self.loading_overlay)
        self.page.overlay.append(self.snack_bar)
        self.nearest_time_selected = False
        self.create_elements()

        self.page.adaptive = True
        self.page.scroll = 'adaptive'

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_click,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text('Бронирование', size=20, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        self.page.floating_action_button = None
        self.page.update()

        self.panels = [
            ft.ExpansionPanel(
                header=ft.ListTile(
                    title=ft.Text(
                        '1. Выбор автомобиля', weight=ft.FontWeight.BOLD
                    )
                ),
                content=ft.Container(
                    padding=ft.padding.all(10),
                    content=ft.Column(
                        [
                            self.car_dropdown,
                            self.add_car_button,
                        ],
                        spacing=10,
                    ),
                ),
                can_tap_header=True,
                expanded=self.expanded_panels[0],
            ),
            ft.ExpansionPanel(
                header=ft.ListTile(
                    title=ft.Text(
                        '2. Выбор даты, бокса и времени',
                        weight=ft.FontWeight.BOLD,
                    )
                ),
                content=ft.Container(
                    padding=ft.padding.all(10),
                    content=ft.Column(
                        [
                            self.calendar,
                            self.select_nearest_time_button,  # Новая кнопка
                            self.or_text,
                            self.box_dropdown,
                            self.time_dropdown_container,
                        ],
                        spacing=10,
                    ),
                ),
                can_tap_header=True,
                expanded=self.expanded_panels[1],
            ),
            ft.ExpansionPanel(
                header=ft.ListTile(
                    title=ft.Text('3. Выбор услуги', weight=ft.FontWeight.BOLD)
                ),
                content=ft.Container(
                    padding=ft.padding.all(10),
                    content=ft.Column(
                        [
                            self.service_image_container,
                            self.complex_wash_section,
                            self.price_text,
                        ],
                        spacing=10,
                    ),
                ),
                can_tap_header=True,
                expanded=self.expanded_panels[2],
            ),
        ]

        self.expansion_panel_list = ft.ExpansionPanelList(
            expand_icon_color=ft.colors.AMBER,
            elevation=8,
            divider_color=ft.colors.AMBER,
            on_change=self.on_panel_change,
            controls=self.panels,
            spacing=10,
        )

        self.main_container = ft.Container(
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    self.car_wash_card,
                    self.expansion_panel_list,
                    ft.Container(
                        content=self.book_button,
                        alignment=ft.alignment.center,
                    ),
                ],
                spacing=20,
            ),
            margin=ft.margin.all(0),
            width=730,
            expand=True,
        )

        self.page.clean()
        self.page.add(self.main_container)
        self.page.update()

        self.load_schedules()
        self.load_boxes()

    def create_car_wash_card(self):
        image_link = self.car_wash.get('image_link', 'assets/spa_logo.png')
        location_address = (
            f"{self.location_data.get('city', 'Неизвестный город')}, "
            f"{self.location_data.get('address', 'Адрес не указан')}"
            if self.location_data
            else 'Адрес недоступен'
        )

        car_wash_name = self.car_wash.get('name', 'Автомойка')

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Stack(
                        [
                            ft.Container(
                                content=ft.Image(
                                    src=image_link,
                                    fit=ft.ImageFit.COVER,
                                    width=float('inf'),
                                ),
                                height=170,
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    car_wash_name,
                                    weight=ft.FontWeight.BOLD,
                                    size=24,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=170),
                            ),
                            ft.Container(
                                content=ft.Text(
                                    location_address,
                                    text_align=ft.TextAlign.CENTER,
                                    color=ft.colors.GREY,
                                    size=16,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(top=200),
                            ),
                        ]
                    ),
                    padding=ft.padding.all(8),
                    width=float('inf'),
                ),
                elevation=3,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(0),
            expand=True,
        )

    def create_elements(self):
        self.add_car_button = ft.ElevatedButton(
            text='Добавить ещё автомобиль',
            on_click=self.on_add_car_click,
            width=700,
            bgcolor=ft.colors.PURPLE,
            color=ft.colors.WHITE,
        )

        self.car_dropdown = ft.Dropdown(
            width=700,
            hint_text='Выберите автомобиль',
            options=self.load_user_cars(),
            on_change=self.on_car_select,
            disabled=self.car_dropdown_disabled,
        )

        self.box_dropdown = ft.Dropdown(
            label='Выберите бокс',
            width=700,
            options=[],
            on_change=self.on_box_select,
            disabled=self.box_dropdown_disabled,
        )

        self.calendar = DateGrid(
            year=Settings.get_year(),
            month=Settings.get_month(),
            on_date_selected=self.handle_date_selected,
            today=self.today,
        )

        self.select_nearest_time_button = ft.OutlinedButton(
            text='Выбрать ближайшее время',
            on_click=self.on_select_nearest_time_click,
            width=700,
            disabled=True,
            style=self.get_nearest_time_button_style(),
        )

        self.or_text = ft.Container(
            content=ft.Text(
                'или',
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.GREY_700,
                text_align=ft.TextAlign.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=10),
            visible=True,  # Сделать видимым по умолчанию
        )

        self.time_dropdown_container = ft.Column(
            disabled=self.time_dropdown_container_disabled,
            width=700,
        )

        self.complex_wash_checkbox = ft.Checkbox(
            label='',
            disabled=True,
            on_change=self.on_complex_wash_change,
            value=False,
        )

        self.complex_wash_text = ft.Text(
            'Комплексная автомойка',
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_600,
        )

        self.complex_wash_section = ft.Column(
            [
                ft.Row(
                    [
                        self.complex_wash_text,
                        self.complex_wash_checkbox,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
                ft.Row(
                    [
                        ft.Icon(
                            ft.icons.ACCESS_TIME, color=ft.colors.GREY_600
                        ),
                        ft.Text(
                            '1,5 - 2 часа',
                            color=ft.colors.GREY_600,
                            size=16,
                            weight=ft.FontWeight.NORMAL,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                ),
                ft.Text(
                    'Наружная часть автомобиля: '
                    '1 фаза - бесконтактный шампунь, '
                    '2 фаза - ручная мойка "hydro shampoo", '
                    'чернение шин силиконом.\n'
                    'Внутренняя часть автомобиля: '
                    'уборка салона с помощью торнадора и пылесоса, '
                    'ароматизация, '
                    'бумажные полики.',
                    size=14,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.LEFT,
                ),
            ],
            spacing=10,
        )

        self.price_text = ft.Text(
            'Стоимость: ₸0',
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY,
        )

        self.book_button = ft.ElevatedButton(
            text='Забронировать',
            on_click=self.on_book_click,
            width=300,  # Ширина кнопки оставлена без изменений
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            disabled=self.book_button_disabled,
        )

        self.back_button = ft.ElevatedButton(
            text='Назад',
            on_click=self.on_back_click,
            width=300,  # Ширина кнопки оставлена без изменений
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.service_image_container = ft.Container(
            content=ft.Image(
                src='https://drive.google.com/uc?export=view&id=1j8oXQLe8WXS96vE3U32zieRVGq0knqyQ',
                fit=ft.ImageFit.COVER,
                width=float('inf'),
                height=200,
            ),
            border_radius=ft.border_radius.all(12),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.alignment.center,
        )

        self.car_wash_card = self.create_car_wash_card()

    def parse_car_name(self, name: str) -> tuple[str, str, str, str]:
        from typing import List, Tuple

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

        # Сортируем body_types по убыванию длины строк для корректного поиска
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

        MatchType = Tuple[int, int, str, str]

        matches: List[MatchType] = []
        for i in range(len(remaining_words)):
            for j in range(i + 1, min(i + 6, len(remaining_words) + 1)):
                potential_generation = ' '.join(remaining_words[i:j])
                if numeric_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'numeric'))
                elif roman_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'roman'))

        if matches:
            matches.sort(key=lambda x: (-x[0], x[3]))
            _, generation_index, generation, generation_type = matches[0]
            print(f'Found generation: {generation} ({generation_type})')
            remaining_words = (
                remaining_words[:generation_index]
                + remaining_words[generation_index + matches[0][0] :]
            )
            print(
                f'Remaining words after generation extraction: '
                f'{remaining_words}'
            )
        else:
            print('Generation not found')

        matched_body_types = []
        for i in range(len(remaining_words), 0, -1):
            potential_body_type = (
                ' '.join(remaining_words[i - 1 :]).lower().rstrip('.')
            )
            print(f'Checking potential body type: {potential_body_type}')
            for bt in body_types:
                if potential_body_type == bt.lower():
                    matched_body_types.append((i - 1, bt))
        if matched_body_types:
            # Сортируем по индексу вхождения
            matched_body_types.sort(key=lambda x: x[0])
            body_type_index, body_type = matched_body_types[0]
            remaining_words = remaining_words[:body_type_index]
            print(f'Found body type: {body_type}')
            print(
                f'Remaining words after body type extraction: '
                f'{remaining_words}'
            )
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

    def show_confirmation_page(self):
        if self.box_dropdown.value:
            selected_box_option = next(
                (
                    option
                    for option in self.box_dropdown.options
                    if option.key == str(self.box_dropdown.value)
                ),
                None,
            )
            box_name = (
                selected_box_option.text
                if selected_box_option
                else 'Не выбран'
            )
        else:
            box_name = 'Не выбран'

        selected_car = next(
            (
                car
                for car in self.cars
                if str(car.get('id')) == str(self.selected_car_id)
            ),
            None,
        )

        if selected_car:
            car_name = (
                selected_car.get('name')
                or f"{selected_car.get('brand', 'Неизвестный бренд')} "
                f"{selected_car.get('model', 'Неизвестная модель')}"
            )
            brand, model, generation, body_type = self.parse_car_name(car_name)

        else:
            car_name = 'Не выбран'
            brand, model, generation, body_type = (
                'Не указано',
                'Не указано',
                'Не указано',
                'Не указано',
            )

        if self.selected_date:
            day_of_week = date_class[self.selected_date.weekday()]
            formatted_date = (
                f"{self.selected_date.strftime('%d.%m.%Y')} ({day_of_week})"
            )
        else:
            formatted_date = 'Не выбрана'

        formatted_time = (
            self.selected_time.strftime('%H:%M')
            if isinstance(self.selected_time, datetime)
            else self.selected_time or 'Не выбрано'
        )
        price = f'₸{int(self.car_price)}'

        booking_details = [
            ('Бокс', box_name),
            ('Дата', formatted_date),
            ('Время', formatted_time),
            ('Цена', price),
            ('Услуга', 'Комплексная мойка'),
        ]

        booking_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in booking_details
            ],
            spacing=10,
        )

        booking_info_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            'Информация о записи',
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
            margin=ft.margin.only(bottom=20),
        )

        car_info_details = [
            ('Бренд', brand),
            ('Модель', model),
            ('Поколение', generation),
            ('Тип кузова', body_type),
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
                for label, value in car_info_details
            ],
            spacing=10,
        )

        car_info_card = ft.Card(
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
            margin=ft.margin.only(bottom=20),
        )

        wishes_header = ft.Text(
            'Есть пожелания или комментарии? Добавьте ниже',
            size=18,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        wishes_field = ft.TextField(
            label=(
                'Например: оставил вещи в салоне. '
                'Переложите, пожалуйста, в багажник и тд..'
            ),
            hint_text='',
            # multiline=True,
            width=500,
            height=100,
            border_radius=ft.border_radius.all(10),
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
            on_click=self.on_back_to_booking_page,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_to_booking_page,
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
                wishes_field,
                confirm_button,
                back_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        confirmation_container = ft.Container(
            content=main_content,
            alignment=ft.alignment.center,
            expand=True,
            width=730,
        )

        self.page.clean()
        self.page.add(confirmation_container)
        self.page.update()

    def on_panel_change(self, e: ft.ControlEvent):
        if self.updating_panels:
            return

        index_str = e.data
        print(f'Panel change event: {index_str}')

        try:
            index = int(index_str)
        except ValueError:
            print(f'Invalid panel index: {index_str}')
            return

        self.updating_panels = True
        try:
            if self.expanded_panels[index]:
                self.expanded_panels = [False] * len(self.expanded_panels)
            else:
                self.expanded_panels = [False] * len(self.expanded_panels)
                self.expanded_panels[index] = True
            self.update_expansion_panel_list()
        finally:
            self.updating_panels = False

        print(f'Updated expanded_panels: {self.expanded_panels}')

        self.expansion_panel_list.update()
        self.page.update()

    def load_user_cars(self):
        user_id = self.page.client_storage.get('user_id')

        if not user_id:
            print('User ID не найден.')
            self.cars = []
            self.update_add_car_button()
            return []

        response = self.api.get_user_cars(user_id=user_id, limit=100)

        if response.status_code == 200:
            cars = response.json().get('data', [])
            print(f'Автомобили успешно загружены: {cars}')
            self.cars = cars
            self.update_add_car_button()
            return [
                ft.dropdown.Option(
                    text=car.get(
                        'name',
                        (
                            f"{car.get('brand', 'Неизвестный бренд')} "
                            f"{car.get('model', 'Неизвестная модель')}"
                        ),
                    ),
                    key=str(car.get('id')),
                )
                for car in cars
                if car.get('id')
            ]
        else:
            print(
                f'Ошибка при загрузке автомобилей: '
                f'{response.status_code}, {response.text}'
            )
            self.cars = []
            self.update_add_car_button()
            return []

    def update_add_car_button(self):
        if not self.cars or len(self.cars) == 0:
            self.add_car_button.text = 'Еще не добавили авто?'
        else:
            self.add_car_button.text = 'Добавить ещё автомобиль'
        self.page.update()

    def on_car_select(self, e):
        self.selected_car_id = e.control.value
        print(f'Выбран автомобиль с ID: {self.selected_car_id}')

        self.selected_date = None
        self.selected_time = None
        self.selected_time_iso = None
        self.reset_calendar_selection()
        self.box_dropdown.value = None
        self.box_dropdown.disabled = True
        self.time_dropdown_container.controls = []
        self.time_dropdown_container.disabled = True
        self.book_button.disabled = True
        self.complex_wash_checkbox.value = False
        self.complex_wash_checkbox.disabled = True
        self.price_text.value = 'Стоимость: ₸0'
        self.select_nearest_time_button.disabled = True

        selected_car = next(
            (
                car
                for car in self.cars
                if str(car['id']) == str(self.selected_car_id)
            ),
            None,
        )

        if selected_car:
            configuration_id = selected_car.get('configuration_id')
            print(
                f'Configuration ID для выбранного автомобиля: '
                f'{configuration_id}'
            )

            if configuration_id:
                self.load_body_type_id(configuration_id)
            else:
                print('Configuration ID для автомобиля не определен.')

        else:
            print(
                f'Автомобиль с ID {self.selected_car_id} не найден в списке.'
            )

        self.updating_panels = True
        try:
            self.expanded_panels = [False, True, False]
            self.update_expansion_panel_list()
        finally:
            self.updating_panels = False

        self.page.update()

    def reset_calendar_selection(self):
        for row in self.calendar.date_rows.controls:
            for date_box in row.controls:
                if isinstance(date_box, DateBox):
                    if (
                        date_box.date_obj == self.today
                        and not date_box.disabled
                    ):
                        date_box.bgcolor = None
                        date_box.border = ft.Border(
                            left=ft.BorderSide(color='#4fadf9', width=1.5),
                            right=ft.BorderSide(color='#4fadf9', width=1.5),
                            top=ft.BorderSide(color='#4fadf9', width=1.5),
                            bottom=ft.BorderSide(color='#4fadf9', width=1.5),
                        )
                        date_box.content.color = ft.colors.BLUE
                    else:
                        date_box.bgcolor = None
                        date_box.border = None
                        date_box.content.color = (
                            ft.colors.BLUE
                            if not date_box.disabled
                            else ft.colors.GREY_500
                        )
        self.calendar.update()

    def load_body_type_id(self, configuration_id, auto_update_price=False):
        self.show_loading()

        response = self.api.get_configuration_by_id(
            configuration_id=configuration_id, limit=10000
        )

        if response.status_code == 200:
            data = response.json().get('data', [])
            print(
                f'Конфигурации успешно загружены. '
                f'Всего конфигураций: {len(data)}'
            )

            selected_config = next(
                (
                    config
                    for config in data
                    if config['id'] == configuration_id
                ),
                None,
            )

            if selected_config:
                body_type_id = selected_config.get('body_type_id')
                print(
                    f'Тип кузова для конфигурации '
                    f'{configuration_id}: {body_type_id}'
                )

                if body_type_id:
                    self.load_car_price(body_type_id, auto_update_price)
                else:
                    print('Тип кузова для конфигурации не найден.')
                    self.hide_loading()
            else:
                print(f'Конфигурация с ID {configuration_id} не найдена.')
                self.hide_loading()
        else:
            print(
                f'Ошибка при запросе конфигурации: '
                f'{response.status_code}, {response.text}'
            )
            self.hide_loading()

    def load_car_price(self, body_type_id, auto_update_price=False):
        response = self.api.get_prices(self.car_wash['id'])

        if response.status_code == 200:
            prices = response.json().get('data', [])
            print(f'Цены: {prices}')

            price = next(
                (
                    price
                    for price in prices
                    if price['body_type_id'] == body_type_id
                ),
                None,
            )

            if price:
                self.car_price = price['price']
                print(
                    f'Цена для автомобиля с типом кузова '
                    f'{body_type_id}: {self.car_price}'
                )
                if auto_update_price:
                    self.show_price()
                self.hide_loading()
            else:
                print(f'Цена для body_type_id {body_type_id} не найдена.')
                self.hide_loading()
        else:
            print(f'Ошибка загрузки цены автомобиля: {response.text}')
            self.hide_loading()

    def show_price(self):
        if self.complex_wash_checkbox.value:
            self.price_text.value = f'Стоимость: ₸{int(self.car_price)}'
            self.price_text.color = None
            self.book_button.disabled = False
        else:
            self.price_text.value = 'Стоимость: ₸0'
            self.price_text.color = ft.colors.GREY
            self.book_button.disabled = True
        self.page.update()

    def on_box_select(self, e):
        if self.nearest_time_selected:
            self.nearest_time_selected = False
            self.select_nearest_time_button.text = 'Выбрать ближайшее время'
            self.update_nearest_time_button_style()
            self.show_snack_bar(
                'Автоматический выбор ближайшего времени отменен.',
                bgcolor=ft.colors.RED,
            )
            self.or_text.visible = True
            self.or_text.update()

        self.selected_box_id = int(e.control.value)
        print(f'Выбранный бокс: {self.selected_box_id}')

        self.selected_time = None
        self.selected_time_iso = None
        self.time_dropdown_container.controls = []
        self.time_dropdown_container.disabled = False
        self.book_button.disabled = True
        self.complex_wash_checkbox.value = False
        self.complex_wash_checkbox.disabled = True
        self.price_text.value = 'Стоимость: ₸0'
        self.select_nearest_time_button.disabled = False

        self.load_available_times_for_box()

        self.updating_panels = True
        try:
            self.expanded_panels = [False, True, False]
            self.update_expansion_panel_list()
        finally:
            self.updating_panels = False

        self.page.update()

    def handle_date_selected(self, selected_date):
        """
        Callback-функция для обработки выбранной даты из календаря.
        """
        self.selected_date = selected_date
        print(f'Выбрана дата: {self.selected_date}')

        if self.nearest_time_selected:
            self.nearest_time_selected = False
            self.select_nearest_time_button.text = 'Выбрать ближайшее время'
            self.update_nearest_time_button_style()
            self.or_text.visible = True
            self.or_text.update()
            print(
                'Состояние ближайшего времени сброшено из-за изменения даты.'
            )

        if self.selected_date:
            self.load_available_boxes()
            self.selected_time = None
            self.selected_time_iso = None
            self.book_button.disabled = True
            self.complex_wash_checkbox.value = False
            self.complex_wash_checkbox.disabled = True
            self.price_text.value = 'Стоимость: ₸0'
            self.select_nearest_time_button.disabled = False
        else:
            self.selected_box_id = None
            self.box_dropdown.value = None
            self.box_dropdown.disabled = True
            self.time_dropdown_container.controls = []
            self.time_dropdown_container.disabled = True
            self.book_button.disabled = True
            self.complex_wash_checkbox.value = False
            self.complex_wash_checkbox.disabled = True
            self.price_text.value = 'Стоимость: ₸0'
            self.select_nearest_time_button.disabled = True

        if self.selected_date:
            self.updating_panels = True
            try:
                self.expanded_panels = [False, True, False]
                self.update_expansion_panel_list()
            finally:
                self.updating_panels = False
        else:
            self.updating_panels = True
            try:
                self.expanded_panels = [False, False, False]
                self.update_expansion_panel_list()
            finally:
                self.updating_panels = False

        self.page.update()

    def update_expansion_panel_list(self):
        """
        Обновляет список панелей в ExpansionPanelList
        на основе текущего состояния expanded_panels.
        """
        for i, panel in enumerate(self.panels):
            if i < len(self.expanded_panels):
                panel.expanded = self.expanded_panels[i]
            else:
                panel.expanded = False
        self.expansion_panel_list.update()

    def load_schedules(self):
        response = self.api.get_schedules(self.car_wash['id'])
        if response.status_code == 200:
            data = response.json()
            print(
                f'Расписания успешно загружены для автомойки '
                f'{self.car_wash["name"]}:'
            )
            import pprint

            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(data)

            self.schedule_list = [
                schedule
                for schedule in data.get('data', [])
                if schedule.get('car_wash_id') == self.car_wash['id']
            ]

            if not self.schedule_list:
                print('Нет расписаний для выбранной автомойки.')
            else:
                print(
                    f'Количество расписаний для автомойки: '
                    f'{len(self.schedule_list)}'
                )

            available_days_of_week = [
                schedule['day_of_week']
                for schedule in self.schedule_list
                if schedule.get('is_available', False)
                and 'day_of_week' in schedule
            ]
            print(f'Available days of week: {available_days_of_week}')

            available_days_of_week = list(set(available_days_of_week))
            print(f'Unique available days of week: {available_days_of_week}')

            today_date = datetime.today().date()

            available_dates = [
                today_date + timedelta(days=i)
                for i in range(7)
                if (today_date + timedelta(days=i)).weekday()
                in available_days_of_week
            ]
            print(f'Computed available_dates: {available_dates}')

            self.available_dates = available_dates
            print(
                f'Список доступных дат после обработки: '
                f'{self.available_dates}'
            )

        else:
            print(
                f'Ошибка загрузки расписаний: '
                f'{response.status_code}, {response.text}'
            )
            self.schedule_list = []
            self.available_dates = []

        if hasattr(self.calendar, 'set_available_dates'):
            self.calendar.set_available_dates(self.available_dates)
        else:
            print('Календарь не имеет метода set_available_dates.')
        self.page.update()

    def load_available_boxes(self):
        if self.selected_date:
            self.show_loading()
            date_str = self.selected_date.strftime('%Y-%m-%d')
            response = self.api.get_available_times(
                self.car_wash['id'], date_str
            )

            if response.status_code == 200:
                available_times_data = response.json().get(
                    'available_times', {}
                )
                print(f'Available times data: {available_times_data}')

                available_box_ids = list(map(int, available_times_data.keys()))
                available_boxes = [
                    box for box in self.boxes if box['id'] in available_box_ids
                ]

                self.available_boxes = available_boxes

                self.box_dropdown.options = [
                    ft.dropdown.Option(text=box['name'], key=str(box['id']))
                    for box in self.available_boxes
                ]

                if not self.available_boxes:
                    self.box_dropdown.disabled = True
                    self.box_dropdown.value = None
                    self.selected_box_id = None
                    self.show_snack_bar(
                        'На выбранную дату нет доступных боксов.'
                    )
                    self.time_dropdown_container.controls = []
                    self.time_dropdown_container.disabled = True
                    self.select_nearest_time_button.disabled = True
                else:
                    self.box_dropdown.disabled = False
                    if self.selected_box_id is not None:
                        if self.selected_box_id in available_box_ids:
                            self.box_dropdown.value = str(self.selected_box_id)
                            self.load_available_times_for_box()
                        else:
                            self.box_dropdown.value = None
                            self.selected_box_id = None
                            self.time_dropdown_container.controls = []
                            self.time_dropdown_container.disabled = True
                            self.show_snack_bar(
                                'Выбранный бокс недоступен на выбранную дату.'
                            )
                    else:
                        self.box_dropdown.value = None
                        self.time_dropdown_container.controls = []
                        self.time_dropdown_container.disabled = True

                    self.select_nearest_time_button.disabled = False

                self.hide_loading()
                self.page.update()
            else:
                print(f'Ошибка загрузки доступных времен: {response.text}')
                self.show_snack_bar(
                    'Не удалось загрузить доступные времена.',
                    bgcolor=ft.colors.RED,
                )
                self.hide_loading()
        else:
            print('Дата не выбрана.')
            self.show_snack_bar(
                'Пожалуйста, выберите дату.', bgcolor=ft.colors.RED
            )

    def load_available_times_for_box(self):
        if self.selected_box_id and self.selected_date:
            self.show_loading()
            date_str = self.selected_date.strftime('%Y-%m-%d')
            response = self.api.get_available_times(
                self.car_wash['id'], date_str
            )

            if response.status_code == 200:
                available_times_data = response.json().get(
                    'available_times', {}
                )
                box_times = available_times_data.get(
                    str(self.selected_box_id), []
                )
                print(
                    f'Available times for box '
                    f'{self.selected_box_id}: {box_times}'
                )

                filtered_times = self.parse_available_times(box_times)

                if not filtered_times:
                    self.time_dropdown_container.controls = [
                        ft.Container(
                            content=ft.Text(
                                'К сожалению, мест не осталось',
                                color=ft.colors.RED,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Выберите другой бокс',
                                color=ft.colors.RED,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                        ),
                    ]
                    self.time_dropdown_container.disabled = True
                    self.book_button.disabled = True
                else:
                    morning_slots = [
                        slot for slot in filtered_times if 2 <= slot.hour < 12
                    ]
                    day_slots = [
                        slot for slot in filtered_times if 12 <= slot.hour < 18
                    ]
                    evening_slots = [
                        slot
                        for slot in filtered_times
                        if 18 <= slot.hour <= 22
                    ]

                    controls = []
                    if morning_slots:
                        controls.append(
                            ft.Text('Утро', size=20, weight=ft.FontWeight.BOLD)
                        )
                        controls.append(self.create_time_grid(morning_slots))
                    if day_slots:
                        controls.append(
                            ft.Text('День', size=20, weight=ft.FontWeight.BOLD)
                        )
                        controls.append(self.create_time_grid(day_slots))
                    if evening_slots:
                        controls.append(
                            ft.Text(
                                'Вечер', size=20, weight=ft.FontWeight.BOLD
                            )
                        )
                        controls.append(self.create_time_grid(evening_slots))

                    self.time_dropdown_container.controls = controls
                    self.time_dropdown_container.disabled = False
                    self.book_button.disabled = True

                self.hide_loading()
                self.page.update()
            else:
                print(f'Ошибка загрузки доступных времен: {response.text}')
                self.show_snack_bar(
                    'Не удалось загрузить доступные времена.',
                    bgcolor=ft.colors.RED,
                )
                self.hide_loading()
        else:
            print('Не выбрана дата или бокс.')
            self.show_snack_bar(
                'Пожалуйста, выберите дату и бокс.', bgcolor=ft.colors.RED
            )

    def create_time_grid(self, time_slots):
        grid = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=120,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=2.5,
        )

        for time_slot in time_slots:
            grid.controls.append(self.create_time_button(time_slot))

        return grid

    def on_time_select_grid(self, time_slot_iso):
        self.nearest_time_selected = False
        self.select_nearest_time_button.text = 'Выбрать ближайшее время'
        self.update_nearest_time_button_style()

        self.selected_time_iso = time_slot_iso
        self.selected_time = datetime.fromisoformat(time_slot_iso)

        print(f'Selected time: {self.selected_time}')

        if self.selected_time:
            self.complex_wash_checkbox.disabled = False
            self.complex_wash_checkbox.value = False
            self.price_text.value = 'Стоимость: ₸0'
            self.book_button.disabled = True
            self.select_nearest_time_button.disabled = True
            self.page.update()

        self.updating_panels = True
        try:
            self.expanded_panels = [False, False, True]
            self.update_expansion_panel_list()
        finally:
            self.updating_panels = False

        self.page.update()

        self.refresh_time_grid()
        self.page.update()

        self.show_snack_bar(
            f'Выбран бокс {self.selected_box_id} на '
            f'{self.selected_time.strftime("%H:%M")}.',
            bgcolor=ft.colors.GREEN,
        )

    def on_complex_wash_change(self, e):
        if self.complex_wash_checkbox.value:
            self.complex_wash_text.color = ft.colors.BLUE
            self.show_price()
        else:
            self.complex_wash_text.color = None
            self.price_text.value = 'Стоимость: ₸0'
            self.book_button.disabled = True
        self.page.update()

    def create_time_button(self, time_slot: datetime):
        is_selected = self.selected_time_iso == time_slot.isoformat()
        return ft.ElevatedButton(
            text=self.format_time(time_slot),
            on_click=lambda e: self.on_time_select_grid(time_slot.isoformat()),
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE if is_selected else ft.colors.GREY,
                color=ft.colors.WHITE if is_selected else ft.colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=20),
                padding={'top': 5, 'bottom': 5, 'left': 10, 'right': 10},
            ),
        )

    def parse_available_times(self, times):
        parsed_times = []
        now = datetime.now()

        if not self.selected_date:
            return parsed_times

        is_today = self.selected_date == now.date()

        if is_today:
            ceil_hour = (now + timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
            print(f'Сегодня: {is_today}, ceil_hour: {ceil_hour}')
        else:
            ceil_hour = None

        for time_range in times:
            try:
                start_datetime_full = datetime.fromisoformat(time_range[0])
                end_datetime_full = datetime.fromisoformat(time_range[1])

                if start_datetime_full.date() != self.selected_date:
                    print(
                        f'Date mismatch: '
                        f'{start_datetime_full.date()} != {self.selected_date}'
                    )
                    continue

                start_time = start_datetime_full.time()
                end_time = end_datetime_full.time()

                start_datetime = datetime.combine(
                    self.selected_date, start_time
                )
                end_datetime = datetime.combine(self.selected_date, end_time)

                while start_datetime + timedelta(hours=2) <= end_datetime:
                    if is_today:
                        if start_datetime >= ceil_hour:
                            parsed_times.append(start_datetime)
                            print(f'Добавлено время: {start_datetime}')
                    else:
                        parsed_times.append(start_datetime)
                        print(f'Добавлено время: {start_datetime}')
                    start_datetime += timedelta(hours=1)  # Шаг 1 час

            except (ValueError, TypeError) as e:
                print(f'Invalid time range detected: {time_range}, Error: {e}')
                continue

        return parsed_times

    def format_time(self, time_obj):
        return time_obj.strftime('%H:%M')

    def refresh_time_grid(self):
        if not self.selected_box_id or not self.selected_date:
            return

        date_str = self.selected_date.strftime('%Y-%m-%d')
        response = self.api.get_available_times(self.car_wash['id'], date_str)

        if response.status_code == 200:
            available_times_data = response.json().get('available_times', {})
            box_times = available_times_data.get(str(self.selected_box_id), [])
            print(
                f'Available times for box {self.selected_box_id}: {box_times}'
            )

            filtered_times = self.parse_available_times(box_times)

            if not filtered_times:
                self.time_dropdown_container.controls = [
                    ft.Text(
                        'К сожалению, мест не осталось',
                        color=ft.colors.RED,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    )
                ]
                self.time_dropdown_container.disabled = True
            else:
                morning_slots = [
                    slot for slot in filtered_times if 6 <= slot.hour < 12
                ]
                day_slots = [
                    slot for slot in filtered_times if 12 <= slot.hour < 18
                ]
                evening_slots = [
                    slot for slot in filtered_times if 18 <= slot.hour <= 22
                ]

                controls = []
                if morning_slots:
                    controls.append(
                        ft.Text('Утро', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(morning_slots))
                if day_slots:
                    controls.append(
                        ft.Text('День', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(day_slots))
                if evening_slots:
                    controls.append(
                        ft.Text('Вечер', size=20, weight=ft.FontWeight.BOLD)
                    )
                    controls.append(self.create_time_grid(evening_slots))

                self.time_dropdown_container.controls = controls

        self.page.update()

    def on_book_click(self, e):
        if (
            self.selected_box_id
            and self.selected_time
            and self.selected_car_id
            and self.selected_date
        ):
            if not self.complex_wash_checkbox.value:
                self.show_snack_bar(
                    'Пожалуйста, активируйте чекбокс "Комплексная мойка" '
                    'для отображения стоимости.'
                )
                return
            self.show_confirmation_page()
        else:
            print('Выберите бокс, автомобиль, дату и время для букинга.')
            self.show_snack_bar(
                'Пожалуйста, выберите бокс, автомобиль, дату и время.'
            )

    def on_confirm_booking(self, e):
        if (
            self.selected_box_id
            and self.selected_time
            and self.selected_car_id
            and self.selected_date
        ):
            if not self.complex_wash_checkbox.value:
                self.show_snack_bar(
                    'Пожалуйста, активируйте чекбокс "Комплексная мойка" '
                    'для отображения стоимости.'
                )
                return
            try:
                start_datetime = self.selected_time.isoformat()

                end_datetime = (
                    self.selected_time + timedelta(hours=2)  # Исправлено
                ).isoformat()

                booking_data = {
                    'box_id': self.selected_box_id,
                    'user_car_id': self.selected_car_id,
                    'is_exception': False,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                }

                print(f'Данные для бронирования: {booking_data}')

                self.show_loading()
                response = self.api.create_booking(booking_data)
                self.hide_loading()

                if response.status_code == 200:
                    print('Букинг успешно создан!')
                    self.show_success_page()
                else:
                    error_detail = response.json().get('detail', '')
                    print(f'Ошибка создания букинга: {response.text}')

                    if error_detail == (
                        'Booking for these start_datetime and '
                        'end_datetime is not available'
                    ):
                        self.show_snack_bar('Упс.. Вас кто-то опередил')
                    else:
                        self.show_snack_bar(
                            'Произошла ошибка при бронировании. '
                            'Попробуйте позже.'
                        )
            except ValueError as ve:
                print(f'Ошибка при создании букинга: {ve}')
                self.show_snack_bar('Произошла ошибка при обработке данных.')
        else:
            print('Выберите бокс, автомобиль, дату и время для букинга.')
            self.show_snack_bar(
                'Пожалуйста, выберите бокс, автомобиль, дату и время.'
            )

    def on_add_car_click(self, e):
        from washer.ui_components.select_car_page import SelectCarPage

        self.page.client_storage.set('redirect_to', 'booking_page')
        self.page.client_storage.set('car_wash_data', self.car_wash)
        self.page.client_storage.set('username', self.username)
        self.page.client_storage.set('cars', self.cars)
        self.page.client_storage.set('location_data', self.location_data)

        SelectCarPage(
            page=self.page,
            on_car_saved=self.on_car_saved,
            redirect_to='booking_page',
        )

    def on_car_saved(self, car):
        if 'id' not in car and 'user_car_id' in car:
            car['id'] = car['user_car_id']

        self.cars.append(car)

        self.car_dropdown.options.append(
            ft.dropdown.Option(
                text=(
                    f"{car.get('brand', 'Неизвестный бренд')} "
                    f"{car.get('model', 'Неизвестная модель')}"
                ),
                key=str(car['id']),
            )
        )
        self.car_dropdown.value = str(car['id'])

        self.page.client_storage.set('cars', self.cars)

        self.update_add_car_button()
        self.page.update()

    def load_boxes(self):
        self.show_loading()

        try:
            response = self.api.get_boxes(self.car_wash['id'])
            if response.status_code == 200:
                all_boxes = response.json().get('data', [])
                print(
                    f'Боксы успешно загружены для автомойки '
                    f'{self.car_wash["name"]}: {all_boxes}'
                )
                self.boxes = all_boxes
            else:
                print(f'Ошибка загрузки боксов: {response.text}')
                self.boxes = []
        except Exception as e:
            print(f'Ошибка загрузки боксов: {str(e)}')
            self.boxes = []
        finally:
            self.hide_loading()
            self.page.update()

    def on_back_click(self, e):
        self.page.appbar = None
        self.page.clean()

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page)

        self.page.update()

    def show_success_page(self):
        self.page.appbar = None

        self.page.clean()
        self.page.scroll = 'adaptive'

        success_icon = ft.Icon(
            ft.icons.CHECK_CIRCLE,
            color=ft.colors.GREEN,
            size=100,
        )

        success_message = ft.Text(
            'Букинг успешно совершен!',
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

        confirm_button = ft.ElevatedButton(
            text='Принято',
            on_click=self.redirect_to_my_bookings_page,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            width=200,
        )

        self.page.add(
            ft.Container(
                content=ft.Column(
                    [
                        success_icon,
                        ft.Container(height=20),
                        success_message,
                        ft.Container(height=40),
                        confirm_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                alignment=ft.alignment.top_center,
                expand=True,
                padding=ft.padding.all(20),
                margin=ft.margin.only(top=200),
            )
        )

        self.page.update()

    def redirect_to_my_bookings_page(self, e):
        from washer.config import config
        from washer.ui_components.my_bookings_page import MyBookingsPage

        my_bookings_page = MyBookingsPage(
            page=self.page,
            api_url=config.api_url,
            car_wash=self.car_wash,
            location_data=self.location_data,
        )
        my_bookings_page.open()

    def on_back_to_booking_page(self, e):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.on_back_click,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text('Бронирование', size=20, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            leading_width=40,
        )

        self.update_expansion_panel_list()
        self.page.clean()
        self.page.add(self.main_container)
        self.page.overlay.append(self.loading_overlay)
        self.page.overlay.append(self.snack_bar)
        self.page.update()

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.RED):
        """
        Отображает SnackBar с заданным сообщением и цветом фона.
        """
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def show_success_message(self, message: str):
        self.show_snack_bar(message, bgcolor=ft.colors.GREEN)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def on_select_nearest_time_click(self, e):
        if self.nearest_time_selected:
            self.nearest_time_selected = False
            self.select_nearest_time_button.text = 'Выбрать ближайшее время'
            self.update_nearest_time_button_style()
            self.show_snack_bar(
                'Автоматический выбор ближайшего времени отменен.',
                bgcolor=ft.colors.RED,
            )
            self.or_text.visible = True
            self.or_text.update()
            return

        if not self.selected_date:
            self.show_snack_bar('Пожалуйста, выберите дату.')
            return

        self.show_loading()

        date_str = self.selected_date.strftime('%Y-%m-%d')
        response = self.api.get_available_times(self.car_wash['id'], date_str)

        if response.status_code == 200:
            available_times_data = response.json().get('available_times', {})
            available_slots = []

            for box_id, time_ranges in available_times_data.items():
                parsed_times = self.parse_available_times(time_ranges)
                for slot_datetime in parsed_times:
                    available_slots.append((slot_datetime, int(box_id)))
                    print(f'Добавлено время: {slot_datetime}, бокс: {box_id}')

            if available_slots:
                available_slots.sort(key=lambda x: x[0])
                earliest_time, selected_box_id = available_slots[0]
                print(
                    f'Самый ранний слот: {earliest_time} '
                    f'в боксе {selected_box_id}'
                )

                self.selected_box_id = selected_box_id
                self.selected_time = earliest_time
                self.selected_time_iso = earliest_time.isoformat()

                self.box_dropdown.value = str(self.selected_box_id)
                self.box_dropdown.update()

                self.time_dropdown_container.controls = [
                    self.create_time_grid([self.selected_time])
                ]
                self.time_dropdown_container.disabled = False
                self.book_button.disabled = True
                self.complex_wash_checkbox.disabled = False
                self.complex_wash_checkbox.value = False
                self.price_text.value = 'Стоимость: ₸0'

                self.nearest_time_selected = True
                self.select_nearest_time_button.text = (
                    'Выбрано ближайшее время'
                )
                self.update_nearest_time_button_style()

                self.calendar.update()

                self.or_text.visible = False
                self.or_text.update()

                self.updating_panels = True
                try:
                    self.expanded_panels = [False, False, True]
                    self.update_expansion_panel_list()
                finally:
                    self.updating_panels = False

                self.page.update()
                self.hide_loading()
                self.show_snack_bar(
                    f'Выбран бокс {selected_box_id} на '
                    f'{earliest_time.strftime("%H:%M")}.',
                    bgcolor=ft.colors.GREEN,
                )
            else:
                self.hide_loading()
                self.show_snack_bar(
                    'На выбранную дату нет доступных боксов и времени.'
                )
        else:
            self.hide_loading()
            self.show_snack_bar(
                'Не удалось загрузить доступные времена.',
                bgcolor=ft.colors.RED,
            )

        self.update_nearest_time_button_style()
        self.page.update()

    def get_nearest_time_button_style(self):
        if self.nearest_time_selected:
            return ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.Padding(left=10, right=10, top=5, bottom=5),
                bgcolor=ft.colors.BLUE,
                color=ft.colors.WHITE,
                overlay_color=ft.colors.BLUE_200,
                animation_duration=200,
            )
        else:
            return ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.Padding(left=10, right=10, top=5, bottom=5),
                side=ft.BorderSide(color=ft.colors.BLUE, width=1),
                color=ft.colors.BLUE,
                bgcolor=ft.colors.TRANSPARENT,
                overlay_color=ft.colors.BLUE_200,
                animation_duration=200,
            )

    def update_nearest_time_button_style(self):
        self.select_nearest_time_button.style = (
            self.get_nearest_time_button_style()
        )
        self.select_nearest_time_button.update()
