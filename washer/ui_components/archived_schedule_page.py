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
                    ft.TextButton(
                        text='Назад',
                        on_click=self.on_back_click,
                        style=ft.ButtonStyle(
                            padding=0,
                            color='#ef7b00',
                        ),
                    ),
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

                    user_car = booking.get('user_car')
                    if user_car:
                        booking['car_name'] = user_car.get(
                            'name', 'Неизвестно'
                        )
                        booking['license_plate'] = user_car.get(
                            'license_plate', '---'
                        )
                    else:
                        booking['car_name'] = 'Неизвестно'
                        booking['license_plate'] = '---'
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
            padding=ft.padding.only(bottom=10, left=20),
            width=200,
            height=80,
        )

        table_header = ft.Row(
            controls=[
                ft.Text(
                    'Бокс',
                    weight=ft.FontWeight.BOLD,
                    width=70,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Время',
                    weight=ft.FontWeight.BOLD,
                    width=130,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Автомобиль',
                    weight=ft.FontWeight.BOLD,
                    width=180,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    'Цена',
                    weight=ft.FontWeight.BOLD,
                    width=70,
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
            license_plate = booking.get('license_plate', '---')
            price = booking.get('total_price', 0)

            total_price += float(price) if price else 0

            car_display = f'{car_name} ({license_plate})'

            row = ft.Row(
                controls=[
                    ft.Text(
                        box_name, width=70, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f'{start_time} - {end_time}',
                        width=130,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        car_display, width=180, text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f'₸{price}', width=70, text_align=ft.TextAlign.CENTER
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
                    width=70,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text('', width=130),
                ft.Text('', width=180),
                ft.Text(
                    f'₸{int(total_price)}',
                    weight=ft.FontWeight.BOLD,
                    width=70,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        )
        rows.append(total_row)

        def on_delete_click(e, date=date):
            self.confirm_delete_bookings(date)

        delete_button = ft.Container(
            content=ft.ElevatedButton(
                text='Удалить из истории',
                on_click=on_delete_click,
                bgcolor=ft.colors.RED,
                color=ft.colors.WHITE,
                width=200,
            ),
            padding=ft.padding.only(top=10, left=20),
        )

        rows.append(delete_button)

        return ft.Container(
            width=700,
            margin=ft.margin.only(left=-15),
            content=ft.ListView(
                controls=rows, padding=ft.padding.all(10), spacing=5
            ),
        )

    def confirm_delete_bookings(self, date):
        def confirm_delete(e):
            self.page.dialog.open = False
            self.page.update()
            self.delete_bookings_by_date(date)

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение удаления'),
            content=ft.Text(
                f'Вы уверены, что хотите удалить букинги за {date}?'
            ),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dlg_modal
        dlg_modal.open = True
        self.page.update()

    def delete_bookings_by_date(self, date):
        bookings_to_delete = [
            booking['id']
            for booking in self.bookings
            if booking['start_datetime'].startswith(date)
        ]

        success_deletions = []
        failed_deletions = []

        for booking_id in bookings_to_delete:
            response = self.api.delete_booking(booking_id)
            if response.status_code == 200:
                success_deletions.append(booking_id)
            else:
                failed_deletions.append(booking_id)
                print(
                    f'Ошибка при удалении букинга '
                    f'{booking_id}: {response.text}'
                )

        if success_deletions:
            print(f'Букинги {success_deletions} успешно удалены.')
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f'Букинги за {date} успешно удалены.'),
                open=True,
            )

        if failed_deletions:
            self.page.snack_bar = ft.SnackBar(
                ft.Text(f'Не удалось удалить некоторые букинги за {date}.'),
                open=True,
                bgcolor=ft.colors.RED_200,
            )

        self.page.update()

        self.load_bookings()
        self.page.controls[-1] = self.create_archived_schedule_page()
        self.page.update()

    def on_back_click(self, e):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.locations)
