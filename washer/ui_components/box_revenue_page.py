import datetime

import flet as ft
import httpx

from washer.api_requests import BackendApi


class BoxRevenuePage:
    def __init__(self, page: ft.Page, box, car_wash, api_url):
        self.page = page
        self.box = box
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.api_url = api_url

        self.current_date = datetime.date.today()
        self.bookings = []

        self.load_bookings()

        page.clean()
        page.add(self.create_revenue_page())

    def load_bookings(self):
        try:
            access_token = self.page.client_storage.get('access_token')
            car_wash_id = self.car_wash['id']
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }
            url = (
                f"{self.api_url.rstrip('/')}/car_washes/bookings"
                f"?car_wash_id={car_wash_id}&limit=1000"
            )
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                bookings_data = response.json().get('data', [])
                self.bookings = [
                    booking
                    for booking in bookings_data
                    if booking['box_id'] == self.box['id']
                    and booking['start_datetime'].startswith(
                        self.current_date.strftime('%Y-%m-%d')
                    )
                ]
                print('Полученные бронирования:', self.bookings)
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code}, {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке букингов: {e}')

    def create_revenue_page(self):
        header = ft.Container(
            content=ft.Text(
                f"Отчет о прибылях и убытках за "
                f"{self.current_date.strftime('%d.%m.%Y')} - "
                f"бокс {self.box['name']}",
                size=24,
                weight='bold',
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=20),
        )

        back_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_size=24,
                        on_click=self.on_back,
                    ),
                    ft.Text('Назад', size=16),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.only(bottom=10),
        )

        booking_rows = []
        total_revenue = 0

        for index, booking in enumerate(self.bookings, start=1):
            print('Данные бронирования:', booking)
            service_name = booking.get('service_name', 'Не указано')
            price = round(float(booking.get('price', 0)))
            time = datetime.datetime.strptime(
                booking.get('start_datetime', 'Не указано'),
                '%Y-%m-%dT%H:%M:%S',
            ).strftime('%H:%M')
            total_revenue += price

            booking_rows.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            f'{index}. {time}',
                            expand=1,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            service_name,
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            f'{price} ₸',
                            expand=1,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        salary = round(total_revenue * 0.4)
        net_profit = total_revenue - salary

        total_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        'Итого:',
                        weight='bold',
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{total_revenue} ₸',
                        weight='bold',
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(top=10),
        )

        salary_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        'Зарплата (40%):',
                        weight='bold',
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{salary} ₸',
                        weight='bold',
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(top=10),
        )

        net_profit_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        'Чистая прибыль:',
                        weight='bold',
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{net_profit} ₸',
                        weight='bold',
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.only(top=10),
        )

        content = ft.Container(
            content=ft.Column(
                controls=[
                    back_button,
                    header,
                    *booking_rows,
                    total_row,
                    salary_row,
                    net_profit_row,
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
        )

        return content

    def on_back(self, e):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api_url)
