import datetime

import flet as ft

from washer.api_requests import BackendApi

BODY_TYPES = [
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
]
BODY_TYPES.sort(key=len, reverse=True)


def remove_body_type_suffix(car_name: str) -> str:
    """
    Удаляет из конца строки любой тип кузова из BODY_TYPES, если найдётся.
    Возвращает «очищенное» название без типа кузова.
    """
    name_cleaned = car_name.strip().rstrip('.').rstrip()
    lowered = name_cleaned.lower()

    for bt in BODY_TYPES:
        if lowered.endswith(bt):
            cut_len = len(bt)
            name_without_bt = name_cleaned[: len(name_cleaned) - cut_len]
            return name_without_bt.strip().rstrip('.').rstrip()

    return car_name


class MyBookingsPage:
    def __init__(self, page, api_url, car_wash, location_data):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url
        self.car_wash = car_wash
        self.location_data = location_data
        self.bookings = []
        self.completed_visible = False

        self.state_messages = {
            'CREATED': 'Ожидаем приемки администратором',
            'ACCEPTED': 'Ваша запись принята. Будем ждать Вас!',
            'STARTED': 'Ваш автомобиль моется',
            'COMPLETED': 'Запись завершена',
            'EXCEPTION': 'Произошла ошибка при обработке записи',
        }

        self.state_colors = {
            'CREATED': ft.colors.GREY_500,
            'ACCEPTED': ft.colors.BLUE,
            'STARTED': ft.colors.ORANGE,
            'COMPLETED': ft.colors.GREEN,
            'EXCEPTION': ft.colors.RED,
        }

        self.car_washes_dict = {}
        self.boxes_dict = {}

        if self.page.navigation_bar:
            self.page.navigation_bar.selected_index = 0

        self.page.floating_action_button = None

    def _create_large_image_container(self, image_src, width=300, height=300):
        """
        Создаёт контейнер с большим изображением для пустого состояния.
        """
        return ft.Container(
            content=ft.Image(
                src=image_src,
                fit=ft.ImageFit.COVER,
                width=width,
                height=height,
            ),
            width=width,
            height=height,
            alignment=ft.alignment.center,
        )

    def _create_avatar_image_container(self, image_src, size=60):
        return ft.Container(
            content=ft.Image(
                src=image_src,
                fit=ft.ImageFit.COVER,
                width=size,
                height=size,
            ),
            width=size,
            height=size,
            border_radius=ft.border_radius.all(size / 2),
            alignment=ft.alignment.center,
        )

    def format_price(self, price_str):
        try:
            price = float(price_str)
            return f'₸{price:,.2f}'.replace(',', ' ')
        except ValueError:
            return '₸0.00'

    def format_datetime(self, datetime_str):
        try:
            dt = datetime.datetime.fromisoformat(
                datetime_str.replace('Z', '+00:00')
            )

            months = [
                'января',
                'февраля',
                'марта',
                'апреля',
                'мая',
                'июня',
                'июля',
                'августа',
                'сентября',
                'октября',
                'ноября',
                'декабря',
            ]
            weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

            day = dt.day
            month = months[dt.month - 1]
            weekday = weekdays[dt.weekday()]
            time_str = dt.strftime('%H:%M')

            return f'{day} {month} ({weekday}) в {time_str}'
        except Exception as e:
            print(f'Ошибка при форматировании даты и времени: {e}')
            return datetime_str

    def fetch_boxes(self):
        response = self.api.get_boxes(car_wash_id=self.car_wash['id'])
        if response and response.status_code == 200:
            data = response.json().get('data', [])
            self.boxes_dict = {box['id']: box['name'] for box in data}
            print(f'Получено боксов: {self.boxes_dict}')
        else:
            status = response.status_code if response else 'No Response'
            error_text = response.text if response else 'No Response'
            print(f'Ошибка при получении боксов: {status} - {error_text}')
            self.boxes_dict = {}

    def fetch_car_washes(self):
        page = 1
        # limit = 100
        while True:
            response = self.api.get_car_washes(page=page)
            if response and response.status_code == 200:
                data = response.json().get('data', [])
                if not data:
                    break
                for car_wash in data:
                    car_wash_id = car_wash.get('id')
                    name = car_wash.get('name', 'Без названия')
                    image_link = car_wash.get('image_link', '')
                    phone_number = car_wash.get('phone_number', '')
                    self.car_washes_dict[car_wash_id] = {
                        'name': name,
                        'image_link': image_link,
                        'phone_number': phone_number,
                    }
                if response.json().get('next') is None:
                    break
                page += 1
            else:
                status = response.status_code if response else 'No Response'
                error_text = response.text if response else 'No Response'
                print(
                    f'Ошибка при получении автомоек: {status} - {error_text}'
                )
                break

    def open(self):
        self.page.drawer = None
        self.completed_visible = False
        self.fetch_boxes()
        self.fetch_car_washes()
        self.load_user_bookings_from_server()
        self.page.clean()
        self.page.add(self.create_bookings_page())
        self.page.update()

    def create_bookings_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_wash_selection,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Мои записи',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.PURPLE,
            leading_width=40,
            actions=[
                ft.IconButton(
                    icon=ft.icons.AUTO_MODE_ROUNDED,
                    tooltip='Показать завершенные записи'
                    if not self.completed_visible
                    else 'Скрыть завершенные записи',
                    on_click=self.toggle_completed_visibility,
                    icon_color=ft.colors.WHITE,
                    padding=ft.padding.only(right=10),
                )
            ],
        )

        completed_states = ['COMPLETED']

        booking_content = []

        if self.completed_visible:
            filtered_bookings = [
                booking
                for booking in self.bookings
                if booking.get('state', '').upper() in completed_states
            ]
            booking_content = [
                self.create_booking_display(booking, active=False)
                for booking in filtered_bookings
            ]

            if not booking_content:
                empty_image = ft.Container(
                    content=self._create_large_image_container(
                        'https://drive.google.com/uc?id=11B4mRtzpx2TjtO6X4t-nc5gdf_fHHEoK',
                        width=300,
                        height=300,
                    ),
                    padding=ft.padding.only(top=100),  # Верхний отступ
                    alignment=ft.alignment.center,
                )
                empty_text = ft.Container(
                    content=ft.Text(
                        'У вас пока нет завершённых записей',
                        size=18,
                        color=ft.colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=20),
                )
                booking_content = [empty_image, empty_text]
        else:
            active_bookings = [
                booking
                for booking in self.bookings
                if booking.get('state', '').upper() not in completed_states
            ]
            booking_content = [
                self.create_booking_display(booking, active=True)
                for booking in active_bookings
            ]

            if not booking_content:
                empty_image = ft.Container(
                    content=self._create_large_image_container(
                        'https://drive.google.com/uc?id=11B4mRtzpx2TjtO6X4t-nc5gdf_fHHEoK',
                        width=300,
                        height=300,
                    ),
                    padding=ft.padding.only(top=100),
                    alignment=ft.alignment.center,
                )
                empty_text = ft.Container(
                    content=ft.Text(
                        'У вас пока нет активных записей',
                        size=18,
                        color=ft.colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=20),
                )
                booking_content = [empty_image, empty_text]

                add_booking_button = ft.Container(
                    content=ft.ElevatedButton(
                        text='Давайте запишемся!',
                        on_click=self.redirect_to_booking_page,
                        bgcolor=ft.colors.PURPLE,
                        color=ft.colors.WHITE,
                        width=400,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=20, bottom=20),
                )
                booking_content.append(add_booking_button)

        main_list_view = ft.ListView(
            controls=[ft.Container(height=10), *booking_content],
            spacing=15,
            expand=True,
            padding=ft.padding.all(0),
        )

        return ft.Container(
            content=main_list_view,
            margin=ft.margin.only(top=-10),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
        )

    def create_booking_display(self, booking, active=True):
        loc = booking.get('location', {})
        city = loc.get('city', 'Город не указан')
        addr = loc.get('address', 'Адрес не указан')

        user_car = booking.get('user_car', {})
        raw_car_name = user_car.get('name', 'Автомобиль не указан')
        car_name = remove_body_type_suffix(raw_car_name)

        license_plate = user_car.get('license_plate', '—')

        total_price = self.format_price(booking.get('total_price', '0.00'))
        notes = booking.get('notes') or ''

        state = booking.get('state', 'CREATED').upper()
        additional_message_text = self.state_messages.get(
            state, 'Неизвестное состояние записи'
        )

        car_wash_id = booking.get('car_wash_id')
        if not car_wash_id:
            car_wash_id = loc.get('id')

        car_wash_info = self.car_washes_dict.get(
            car_wash_id,
            {
                'name': 'Автомойка не указана',
                'image_link': '',
                'phone_number': '',
            },
        )
        car_wash_name = car_wash_info.get('name', 'Автомойка не указана')
        image_link = car_wash_info.get('image_link', '')
        phone_number = car_wash_info.get('phone_number', '')

        print(f"Booking ID: {booking.get('id')}, Image Link: {image_link}")

        if image_link:
            image_src = image_link
        else:
            image_src = 'https://via.placeholder.com/50'

        box_id = booking.get('box_id')
        box_name = self.boxes_dict.get(box_id, f'Бокс #{box_id}')

        booking_details = [
            (
                'Дата и время',
                self.format_datetime(booking.get('start_datetime', '')),
            ),
            ('Выбранный бокс', box_name),
            ('Автомобиль', car_name),
            ('Госномер', license_plate),
            ('Цена', f'{total_price}'),
        ]

        additions = booking.get('additions', [])
        if additions:
            additional_services = ', '.join(
                [addition['name'] for addition in additions]
            )
            booking_details.append(('Доп.услуги', additional_services))

        message_color = self.state_colors.get(state, ft.colors.GREY_500)

        avatar_container = self._create_avatar_image_container(
            image_src, size=60
        )

        booking_info_controls = [
            ft.Row(
                [
                    ft.Text(
                        car_wash_name,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.LEFT,
                        expand=True,
                    ),
                    avatar_container,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(
                content=ft.Text(
                    f'{city}, {addr}',
                    size=16,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center_left,
                padding=ft.padding.only(top=-20),
            ),
            ft.Divider(color=ft.colors.GREY_300, height=20),
        ]

        for label, value in booking_details:
            row = ft.Row(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(value, color=ft.colors.GREY_600, size=16),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            booking_info_controls.append(row)

        if notes:
            display_notes = notes if len(notes) <= 100 else notes[:100] + '...'
            show_more = len(notes) > 100

            notes_text = ft.Text(
                f'Заметки: {display_notes}',
                size=16,
                color=ft.colors.GREY_700,
                text_align=ft.TextAlign.LEFT,
            )

            if show_more:

                def toggle_notes(
                    e,
                    notes=notes,
                    display_notes=display_notes,
                    notes_text=notes_text,
                ):
                    if notes_text.value.endswith('...'):
                        notes_text.value = f'Заметки: {notes}'
                        toggle_button.text = 'Скрыть'
                    else:
                        notes_text.value = f'Заметки: {display_notes}'
                        toggle_button.text = 'Показать больше'
                    notes_text.update()
                    toggle_button.update()

                toggle_button = ft.TextButton(
                    text='Показать больше',
                    on_click=toggle_notes,
                    style=ft.ButtonStyle(
                        color=ft.colors.BLUE,
                        padding=ft.padding.symmetric(vertical=5),
                    ),
                )
                booking_info_controls.append(notes_text)
                booking_info_controls.append(toggle_button)
            else:
                booking_info_controls.append(notes_text)

        booking_info_controls.append(
            ft.Container(
                content=ft.Text(
                    additional_message_text,
                    size=18,
                    color=message_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center,
            )
        )

        if state == 'STARTED':
            loading_indicator = ft.ProgressBar(
                width=200,
                height=10,
                color=ft.colors.ORANGE,
                bgcolor=ft.colors.TRANSPARENT,
            )
            loading_container = ft.Container(
                content=loading_indicator,
                alignment=ft.alignment.center,
                padding=ft.padding.only(top=10),
            )
            booking_info_controls.append(loading_container)

        if active:
            booking_info_controls.append(
                ft.TextButton(
                    'Остались вопросы? Позвонить',
                    on_click=lambda e,
                    phone=phone_number: self.call_phone_number(phone),
                    style=ft.ButtonStyle(
                        color=ft.colors.BLUE,
                        padding=ft.padding.symmetric(vertical=5),
                    ),
                )
            )

            booking_id = booking.get('id', 'Неизвестен')
            booking_info_controls.append(
                ft.Text(
                    f'ID записи: {booking_id}',
                    size=12,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        elif state == 'COMPLETED':
            booking_id = booking.get('id', 'Неизвестен')
            booking_info_controls.append(
                ft.Text(
                    f'ID записи: {booking_id}',
                    size=12,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                )
            )

        booking_info_column = ft.Column(
            controls=booking_info_controls,
            spacing=10,
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=booking_info_column,
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=700,
            margin=ft.margin.only(bottom=20),
        )

    def toggle_completed_visibility(self, e):
        self.completed_visible = not self.completed_visible

        new_tooltip = (
            'Скрыть завершенные записи'
            if self.completed_visible
            else 'Показать завершенные записи'
        )

        for action in self.page.appbar.actions:
            if isinstance(action, ft.IconButton):
                action.tooltip = new_tooltip
                break

        self.page.clean()
        self.page.add(self.create_bookings_page())
        self.page.update()

    def load_user_bookings_from_server(self):
        try:
            response = self.api.get_all_bookings(
                page=1, limit=100, order_by='id'
            )
            if response is None:
                print('Не удалось получить ответ от сервера (None).')
                return

            print(f'Ответ от сервера при загрузке букингов: {response.text}')

            if response.status_code == 200:
                all_bookings = response.json().get('data', [])

                user_id = self.page.client_storage.get('user_id')
                if user_id:
                    try:
                        user_id = int(user_id)
                        all_bookings = [
                            b
                            for b in all_bookings
                            if b.get('user_car', {}).get('user', {}).get('id')
                            == user_id
                        ]
                    except ValueError:
                        pass

                self.bookings = all_bookings
            else:
                print(
                    f'Ошибка при загрузке букингов с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе букингов с сервера: {e}')

    def redirect_to_booking_page(self, e):
        self.page.appbar = None
        self.page.clean()

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(
            self.page, username=self.page.client_storage.get('username')
        )

    def return_to_wash_selection(self, e):
        self.page.appbar = None

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(
            self.page, username=self.page.client_storage.get('username')
        )

    def call_phone_number(self, phone_number):
        if phone_number:
            tel_url = f'tel:{phone_number}'
            try:
                self.page.launch_url(tel_url)
            except Exception:
                self.page.snackbar = ft.SnackBar(
                    content=ft.Text('Не удалось открыть звонилку.'), open=True
                )
                self.page.update()
        else:
            self.page.snackbar = ft.SnackBar(
                content=ft.Text('Номер телефона не указан.'), open=True
            )
            self.page.update()
