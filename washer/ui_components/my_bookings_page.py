from datetime import datetime

import flet as ft

from washer.api_requests import BackendApi


class MyBookingsPage:
    def __init__(self, page, api_url, car_wash, location_data):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(page.client_storage.get('access_token'))
        self.api_url = api_url
        self.car_wash = car_wash
        self.location_data = location_data
        self.bookings = []
        self.completed_visible = False
        self.completed_bookings_container = ft.Container(visible=False)

        self.page.floating_action_button = None
        # self.page.update()
        # При включении self.page.update() AppBar скидывается некрасиво
        # Но за то FAB скрывается красиво до загрузки страницы

    def open(self):
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
            'Скрыть завершенные записи'
            if self.completed_visible
            else 'Показать завершенные записи'
        )

        self.completed_bookings_container.visible = self.completed_visible

        e.control.update()
        self.page.update()

    def load_user_bookings_from_server(self):
        try:
            user_id = self.page.client_storage.get('user_id')
            if not user_id:
                print('User ID не найден!')
                return

            response = self.api.get_user_bookings(user_id=user_id, limit=100)
            if response is None:
                print('Не удалось получить ответ от сервера.')
                return

            print(f'Ответ от сервера при загрузке букингов: {response.text}')

            if response.status_code == 200:
                self.bookings = response.json().get('data', [])
            else:
                print(
                    f'Ошибка при загрузке букингов с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе букингов с сервера: {e}')

    def on_delete_booking(self, booking_id):
        def confirm_delete(e):
            self.page.dialog.open = False
            self.page.update()
            self.delete_booking_from_server(booking_id)

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

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

        self.page.dialog = dlg_modal
        dlg_modal.open = True
        self.page.update()

    def delete_booking_from_server(self, booking_id):
        try:
            response = self.api.delete_booking(booking_id)
            if response is None:
                print('Не удалось получить ответ от сервера.')
                return

            if response.status_code == 200:
                self.bookings = [
                    b for b in self.bookings if b['id'] != booking_id
                ]
                self.page.clean()
                self.page.add(self.create_bookings_page())
                self.page.update()
                print(f'Букинг с ID {booking_id} успешно удален.')
            else:
                print(f'Ошибка при удалении букинга: {response.text}')
        except Exception as e:
            print(f'Ошибка при удалении букинга: {e}')

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
