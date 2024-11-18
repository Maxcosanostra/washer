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

        app_bar = ft.AppBar(
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

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            bgcolor='rgba(0, 0, 0, 0.8)',
            expand=True,
        )
        self.page.overlay.append(self.loading_overlay)

        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_price_management_page())
        self.page.overlay.append(self.loading_overlay)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def close_modal(self, e=None):
        if (
            hasattr(self, 'modal_container')
            and self.modal_container in self.page.controls
        ):
            self.page.controls.remove(self.modal_container)
            self.page.update()

    def refresh_price_list(self):
        """Метод для обновления секции цен без полной перезагрузки страницы."""
        self.price_list = self.load_prices()
        self.price_list_container.content = self.create_price_list_content()
        self.page.update()

    def load_prices(self):
        response = self.api.get_prices(self.car_wash['id'])
        if response.status_code == 200:
            return response.json().get('data', [])
        else:
            print(f'Ошибка загрузки цен: {response.text}')
            return []

    def create_price_management_page(self):
        self.price_list_container = ft.Container(
            content=self.create_price_list_content()
        )
        return ft.ListView(
            controls=[
                # ft.Container(
                #     content=ft.Row(
                #         [
                #             ft.IconButton(
                #                 icon=ft.icons.ARROW_BACK,
                #                 icon_size=30,
                #                 on_click=self.on_back_to_edit_page,
                #             ),
                #             ft.Text('Назад', size=16),
                #         ],
                #         alignment=ft.MainAxisAlignment.START,
                #     ),
                #     expand=0,
                #     padding=ft.padding.symmetric(vertical=20),
                # ),
                self.price_list_container,  # Секция со списком цен
                self.create_add_price_section(),
            ],
            spacing=20,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

    def create_price_list_content(self):
        rows = []
        for price in self.price_list:
            body_type_name = self.body_type_dict.get(
                price['body_type_id'], 'Неизвестный тип кузова'
            )
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(
                            f'{body_type_name}',
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.Text(
                            f"{price['price']} ₸",
                            expand=2,
                            text_align=ft.TextAlign.LEFT,
                        ),
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            tooltip='Редактировать цену',
                            on_click=lambda e,
                            p=price: self.on_edit_price_click(p),
                            icon_size=18,
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            tooltip='Удалить цену',
                            on_click=lambda e, p=price: self.on_delete_price(
                                p['id']
                            ),
                            icon_size=18,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        return ft.Column(
            controls=[ft.Text('Текущие цены', size=24), *rows],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
        price_field = ft.TextField(label='Цена', width=300)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Добавить цену',
                        size=24,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    body_type_dropdown,
                    price_field,
                    ft.ElevatedButton(
                        text='Создать цену',
                        on_click=lambda e: self.on_create_price_click(
                            body_type_dropdown.value, price_field.value
                        ),
                        width=150,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            expand=True,
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
            self.refresh_price_list()
        else:
            print(f'Ошибка добавления цены: {response.text}')

    def on_edit_price_click(self, price):
        price_field = ft.TextField(
            label='Цена', value=str(price['price']), width=200
        )
        save_button = ft.TextButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_price_click(
                price['id'], price_field.value
            ),
        )
        close_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        body_type = self.body_type_dict.get(
            price['body_type_id'], 'Неизвестный тип кузова'
        )

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f'Редактирование цены для {body_type}',
                        size=18,
                    ),
                    price_field,
                    ft.Row(
                        controls=[save_button, close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def on_save_price_click(self, price_id, new_price):
        if not new_price:
            print('Заполните поле цены!')
            return

        price_data = {'price': float(new_price)}

        response = self.api.update_price(price_id, price_data)
        if response.status_code == 200:
            print('Цена успешно обновлена')
            self.refresh_price_list()
            self.close_modal()
        else:
            print(f'Ошибка обновления цены: {response.text}')

    def on_delete_price(self, price_id):
        confirm_button = ft.TextButton(
            text='Подтвердить', on_click=lambda e: self.delete_price(price_id)
        )
        cancel_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        'Вы уверены, что хотите удалить эту цену?', size=18
                    ),
                    ft.Row(
                        controls=[confirm_button, cancel_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def delete_price(self, price_id):
        response = self.api.delete_price(price_id)
        if response.status_code == 200:
            print(f'Цена с ID {price_id} успешно удалена.')
            self.refresh_price_list()
            self.close_modal()
        else:
            print(f'Ошибка удаления цены: {response.text}')

    def on_back_to_edit_page(self, e=None):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api_url, self.locations)
