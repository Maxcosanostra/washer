import datetime

import flet as ft

from washer.api_requests import BackendApi


class ArchivedSchedulePage:
    def __init__(self, page: ft.Page, car_wash, locations):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.locations = locations
        self.schedule_data = []
        self.boxes_list = []
        self.bookings = []

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
        self.load_bookings()

        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_archived_schedule_page())

    def load_boxes(self):
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            self.boxes_list = response.json().get('data', [])
        else:
            print(f'Ошибка загрузки боксов: {response.text}')

    def load_bookings(self):
        try:
            car_wash_id = self.car_wash['id']
            response = self.api.get_bookings(car_wash_id)

            if response.status_code == 200:
                all_bookings = response.json().get('data', [])
                today = datetime.date.today()
                self.bookings = [
                    booking
                    for booking in all_bookings
                    if datetime.date.fromisoformat(
                        booking['start_datetime'][:10]
                    )
                    < today
                ]
                for booking in self.bookings:
                    box = next(
                        (
                            box
                            for box in self.boxes_list
                            if box['id'] == booking['box_id']
                        ),
                        None,
                    )
                    booking['box_name'] = (
                        box['name'] if box else 'Неизвестный бокс'
                    )
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code}, {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке букингов: {e}')

    def create_archived_schedule_page(self):
        if not self.bookings:
            return ft.Text(
                'Данные для завершенных дней отсутствуют.',
                size=20,
                weight=ft.FontWeight.BOLD,
            )

        tabs = []
        grouped_bookings = {}

        for booking in self.bookings:
            date = booking['start_datetime'][:10]
            if date not in grouped_bookings:
                grouped_bookings[date] = []
            grouped_bookings[date].append(booking)

        for date, bookings in sorted(grouped_bookings.items()):
            tab_content = self.create_booking_table(date, bookings)
            tabs.append(ft.Tab(text=date, content=tab_content))

        return ft.Tabs(tabs=tabs, expand=True)

    def create_booking_table(self, date, bookings):
        header = ft.Container(
            content=ft.Text(
                f'Сводка букингов за\n{date}',
                size=24,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                overflow=ft.TextOverflow.CLIP,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.only(bottom=10, left=30),
            width=250,
            height=80,
        )

        table_header = ft.Row(
            controls=[
                ft.Text(
                    'Бокс',
                    weight=ft.FontWeight.BOLD,
                    width=80,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Время',
                    weight=ft.FontWeight.BOLD,
                    width=100,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Автомобиль',
                    weight=ft.FontWeight.BOLD,
                    width=120,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Цена',
                    weight=ft.FontWeight.BOLD,
                    width=80,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )

        rows = [header, table_header]
        total_price = 0

        for booking in bookings:
            box_name = booking['box_name']
            start_time = datetime.datetime.fromisoformat(
                booking['start_datetime']
            ).strftime('%H:%M')
            end_time = datetime.datetime.fromisoformat(
                booking['end_datetime']
            ).strftime('%H:%M')
            car_name = booking.get('car_name', 'Неизвестно')
            price = booking.get('price', 0)

            total_price += float(price) if price else 0

            row = ft.Row(
                controls=[
                    ft.Text(
                        box_name, width=80, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f'{start_time} - {end_time}',
                        width=100,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        car_name, width=120, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f'₸{price}', width=80, text_align=ft.TextAlign.CENTER
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            )
            rows.append(row)

        rows.append(
            ft.Container(
                height=10,
            )
        )

        total_row = ft.Row(
            controls=[
                ft.Text(
                    'Итого',
                    weight=ft.FontWeight.BOLD,
                    width=80,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text('', width=100),
                ft.Text('', width=120),
                ft.Text(
                    f'₸{int(total_price)}',
                    weight=ft.FontWeight.BOLD,
                    width=80,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )
        rows.append(total_row)

        delete_button = ft.Container(
            content=ft.ElevatedButton(
                text='Удалить из истории',
                on_click=lambda e: self.delete_bookings_by_date(date),
                bgcolor=ft.colors.RED,
                color=ft.colors.WHITE,
                width=250,
            ),
            padding=ft.padding.only(top=10, left=30),
        )

        rows.append(delete_button)

        return ft.Container(
            width=400,
            margin=ft.margin.only(left=-30),
            content=ft.ListView(
                controls=rows, padding=ft.padding.all(10), spacing=5
            ),
        )

    def delete_bookings_by_date(self, date):
        bookings_to_delete = [
            booking['id']
            for booking in self.bookings
            if booking['start_datetime'].startswith(date)
        ]

        for booking_id in bookings_to_delete:
            response = self.api.delete_booking(booking_id)
            if response.status_code == 200:
                print(f'Букинг {booking_id} успешно удален.')
            else:
                print(
                    f'Ошибка при удалении букинга '
                    f'{booking_id}: {response.text}'
                )

        self.load_bookings()
        self.page.controls[-1] = self.create_archived_schedule_page()
        self.page.update()

    def on_back_click(self, e):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.locations)
