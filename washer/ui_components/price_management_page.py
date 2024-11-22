import flet as ft

from washer.api_requests import BackendApi


class PriceManagementPage:
    def __init__(
        self,
        page: ft.Page,
        car_wash,
        api_url,
        body_type_dict,
        prices,
        locations,
    ):
        self.page = page
        self.car_wash = car_wash
        self.api_url = api_url
        self.body_type_dict = body_type_dict
        self.price_list = prices
        self.locations = locations

        self.api = BackendApi()
        access_token = self.page.client_storage.get('access_token')
        self.api.set_access_token(access_token)

        self.load_prices_from_server()

        self.page.clean()
        self.page.add(self.create_price_management_page())

    def load_prices_from_server(self):
        response = self.api.get_prices(self.car_wash['id'])
        if response.status_code == 200:
            self.price_list = response.json().get('data', [])
        else:
            print(f'Ошибка загрузки цен: {response.text}')
            self.price_list = []

    def create_price_management_page(self):
        self.price_list_container = ft.Container(
            content=ft.ListView(
                controls=[
                    *[
                        self.create_price_display(price)
                        for price in self.price_list
                    ],
                    self.create_add_price_section(),
                ],
                padding=ft.padding.all(20),
            ),
            expand=True,
        )

        self.page.appbar = ft.AppBar(
            leading=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=self.on_back_to_edit_page,
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

        return self.price_list_container

    def create_price_display(self, price):
        body_type_name = self.body_type_dict.get(
            price['body_type_id'], 'Неизвестный тип кузова'
        )

        price_info = ft.Column(
            controls=[
                ft.Row(
                    [
                        ft.Text(
                            'Тип кузова', weight=ft.FontWeight.BOLD, size=14
                        ),
                        ft.Text(
                            body_type_name, size=14, color=ft.colors.GREY_600
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text('Цена', weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(
                            f"{price['price']} ₸",
                            size=14,
                            color=ft.colors.GREY_600,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=5,
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        controls=[
                            price_info,
                            ft.Divider(),
                            ft.Row(
                                controls=[
                                    ft.TextButton(
                                        'Редактировать',
                                        on_click=(
                                            lambda e: self.on_edit_price_click(
                                                price
                                            )
                                        ),
                                        style=ft.ButtonStyle(
                                            color=ft.colors.BLUE
                                        ),
                                    ),
                                    ft.TextButton(
                                        'Удалить',
                                        on_click=(
                                            lambda e: self.on_delete_price(
                                                price['id']
                                            )
                                        ),
                                        style=ft.ButtonStyle(
                                            color=ft.colors.RED_400
                                        ),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=2,
                    ),
                    padding=ft.padding.all(10),
                ),
                elevation=3,
            ),
            margin=ft.margin.only(bottom=10),
            width=400,
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
        price_field = ft.TextField(
            label='Введите цену',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

        add_button = ft.ElevatedButton(
            text='Добавить цену',
            on_click=lambda e: self.on_create_price_click(
                body_type_dropdown.value, price_field.value
            ),
            width=250,
            bgcolor='#ef7b00',
            color=ft.colors.WHITE,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Добавить новую цену',
                        size=24,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    body_type_dropdown,
                    price_field,
                    add_button,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
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
            self.load_prices_from_server()
            self.page.clean()
            self.page.add(self.create_price_management_page())
        else:
            print(f'Ошибка добавления цены: {response.text}')

    def on_edit_price_click(self, price):
        def save_changes(e):
            new_price = price_field.value
            if not new_price:
                print('Поле цены не может быть пустым!')
                return

            try:
                new_price_value = float(new_price)
            except ValueError:
                print('Введите корректное значение для цены!')
                return

            response = self.api.update_price(
                price['id'], {'price': new_price_value}
            )
            if response.status_code == 200:
                print('Цена успешно обновлена.')
                self.load_prices_from_server()
                self.refresh_price_list()
                self.page.close(dlg_modal)
            else:
                print(f'Ошибка обновления цены: {response.text}')

        def cancel_edit(e):
            self.page.close(dlg_modal)

        price_field = ft.TextField(
            label='Новая цена',
            value=str(price['price']),
            width=300,
            text_size=15,
            height=40,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                'Редактирование цены',
                text_align=ft.TextAlign.CENTER,
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=price_field,
                        padding=ft.padding.only(top=20),
                    ),
                ],
            ),
            actions=[
                ft.TextButton('Сохранить', on_click=save_changes),
                ft.TextButton('Отмена', on_click=cancel_edit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg_modal)

    def refresh_price_list(self):
        """Обновляет список цен без полной перезагрузки страницы."""
        self.price_list_container.content = ft.ListView(
            controls=[
                *[
                    self.create_price_display(price)
                    for price in self.price_list
                ],
                self.create_add_price_section(),
            ],
            padding=ft.padding.all(20),
        )
        self.page.update()

    def on_delete_price(self, price_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_price(price_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Container(
                content=ft.Text(
                    'Подтверждение удаления',
                    text_align=ft.TextAlign.CENTER,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                ),
                margin=ft.margin.only(bottom=7),
            ),
            content=ft.Container(
                content=ft.Text(
                    'Вы уверены, что хотите удалить эту цену?',
                    text_align=ft.TextAlign.CENTER,
                    size=14,
                ),
                alignment=ft.alignment.center,
            ),
            actions=[
                ft.TextButton(
                    content=ft.Text('Да'),
                    on_click=confirm_delete,
                ),
                ft.TextButton(
                    content=ft.Text('Нет', color=ft.colors.RED),
                    on_click=cancel_delete,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        self.page.open(dlg_modal)

    def delete_price(self, price_id):
        response = self.api.delete_price(price_id)
        if response.status_code == 200:
            print(f'Цена с ID {price_id} успешно удалена.')
            self.load_prices_from_server()
            self.page.clean()
            self.page.add(self.create_price_management_page())
        else:
            print(f'Ошибка удаления цены: {response.text}')

    def on_back_to_edit_page(self, e=None):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api_url, self.locations)
