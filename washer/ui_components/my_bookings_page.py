from datetime import datetime

import flet as ft
import httpx


class MyBookingsPage:
    def __init__(self, page, api_url, car_wash, location_data):
        self.page = page
        self.api_url = api_url
        self.car_wash = car_wash
        self.location_data = location_data
        self.bookings = []
        self.completed_visible = False
        self.completed_bookings_container = ft.Container(visible=False)

    def open(self):
        self.load_user_bookings_from_server()
        self.page.clean()
        self.page.add(self.create_bookings_page())
        self.page.update()

    def create_bookings_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
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
        )

        active_bookings = [
            booking
            for booking in self.bookings
            if datetime.fromisoformat(booking['start_datetime'])
            > datetime.now()
        ]

        booking_content = [
            self.create_booking_display(booking, active=True)
            for booking in active_bookings
        ]

        completed_bookings = [
            self.create_booking_display(booking, active=False)
            for booking in self.bookings
            if datetime.fromisoformat(booking['start_datetime'])
            <= datetime.now()
        ]

        if not booking_content:
            empty_image = ft.Container(
                content=ft.Image(
                    src='https://drive.google.com/uc?id=11B4mRtzpx2TjtO6X4t-nc5gdf_fHHEoK',
                    width=300,
                    height=300,
                    fit=ft.ImageFit.COVER,
                ),
                padding=ft.padding.only(top=130),
            )
            empty_text = ft.Container(
                content=ft.Text(
                    'У вас пока нет активных записей',
                    size=18,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.only(top=20),
            )
            booking_content = [empty_image, empty_text]

            booking_content.append(
                ft.ElevatedButton(
                    text='Давайте запишемся!',
                    on_click=self.redirect_to_booking_page,
                    bgcolor=ft.colors.PURPLE,
                    color=ft.colors.WHITE,
                    width=400,
                )
            )

        toggle_button = ft.TextButton(
            text='Показать завершенные записи'
            if not self.completed_visible
            else 'Скрыть завершенные записи',
            on_click=self.toggle_completed_visibility,
        )
        booking_content.append(toggle_button)

        self.completed_bookings_container.content = ft.Column(
            controls=completed_bookings,
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        booking_content.append(self.completed_bookings_container)

        return ft.Container(
            content=ft.Column(
                controls=booking_content,
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll='adaptive',
            ),
            padding=ft.padding.all(10),
        )

    def create_booking_display(self, booking, active=True):
        car_wash_name = self.car_wash.get('name', 'Автомойка не указана')
        address = (
            f"{self.location_data.get('city', 'Город не указан')}, "
            f"{self.location_data.get('address', 'Адрес не указан')}"
        )

        booking_details = [
            (
                'Дата и время',
                f"{booking['start_datetime'].split('T')[0]} в "
                f"{booking['start_datetime'].split('T')[1][:5]}",
            ),
            ('Выбранный бокс', f"Бокс №{booking['box_id']}"),
            ('Автомойка', car_wash_name),
            ('Адрес', address),
            ('Цена', f"₸{booking['price']}"),
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

        additional_message = (
            ft.Text(
                'Мы ждем вас!' if active else '',
                size=18,
                color=ft.colors.GREY_500,
                text_align=ft.TextAlign.CENTER,
            )
            if active
            else None
        )

        cancel_button = (
            ft.TextButton(
                'Отменить букинг',
                on_click=lambda e: self.on_delete_booking(booking['id']),
                style=ft.ButtonStyle(
                    color=ft.colors.RED_400,
                    padding=ft.padding.symmetric(vertical=5),
                ),
            )
            if active
            else None
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [booking_info_column, ft.Divider()]
                        + ([additional_message] if additional_message else [])
                        + ([cancel_button] if cancel_button else []),
                        spacing=15,
                    ),
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=400,
            padding=ft.padding.all(5),
            margin=ft.margin.only(bottom=20),
        )

    def toggle_completed_visibility(self, e):
        self.completed_visible = not self.completed_visible

        e.control.text = (
            'Скрыть завершенные'
            if self.completed_visible
            else 'Показать завершенные'
        )

        self.completed_bookings_container.visible = self.completed_visible

        e.control.update()
        self.page.update()

    def load_user_bookings_from_server(self):
        try:
            access_token = self.page.client_storage.get('access_token')
            user_id = self.page.client_storage.get('user_id')

            if not user_id:
                print('User ID not found!')
                return

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
            }

            url = (
                f"{self.api_url.rstrip('/')}/car_washes/bookings"
                f"?user_id={user_id}&limit=100"
            )
            response = httpx.get(url, headers=headers)

            if response.status_code == 200:
                self.bookings = response.json().get('data', [])
            else:
                print(
                    f'Ошибка при загрузке букингов: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе букингов с сервера: {e}')

    def on_delete_booking(self, booking_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_booking_from_server(booking_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение отмены'),
            content=ft.Text('Вы уверены, что хотите отменить этот букинг?'),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg_modal)

    def delete_booking_from_server(self, booking_id):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        url = f"{self.api_url.rstrip('/')}/car_washes/bookings/{booking_id}"
        print(f'Отправка DELETE запроса на {url}')

        response = httpx.delete(url, headers=headers)

        if response.status_code == 200:
            self.bookings = [b for b in self.bookings if b['id'] != booking_id]
            self.page.clean()
            self.page.add(self.create_bookings_page())
            self.page.update()
            print(f'Букинг с ID {booking_id} успешно удален.')
        else:
            print(f'Ошибка при удалении букинга: {response.text}')

    def redirect_to_booking_page(self, e):
        self.page.appbar = None
        self.page.clean()

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(
            self.page, username=self.page.client_storage.get('username')
        )

    def return_to_profile(self, e):
        from washer.ui_components.profile_page import ProfilePage

        self.page.appbar = None
        ProfilePage(self.page)
