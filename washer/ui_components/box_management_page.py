import datetime

import flet as ft

from washer.api_requests import BackendApi


class BoxManagementPage:
    def __init__(self, page: ft.Page, car_wash, locations):
        self.page = page
        self.car_wash = car_wash
        self.api = BackendApi()
        self.api.set_access_token(self.page.client_storage.get('access_token'))
        self.locations = locations
        self.boxes_list = []
        self.current_tab_index = 0
        self.tab_contents = {}
        self.setup_snack_bar()

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

        self.load_boxes()
        self.page.clean()
        self.page.add(app_bar)
        self.page.add(self.create_box_management_tabs())

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def load_boxes(self):
        try:
            response = self.api.get_boxes(self.car_wash['id'])
            if response.status_code == 200:
                self.boxes_list = [
                    box
                    for box in response.json().get('data', [])
                    if box['car_wash_id'] == self.car_wash['id']
                ]
                print(f'Успешно загружены боксы: {self.boxes_list}')
            else:
                print(
                    f'Ошибка загрузки боксов для автомойки '
                    f'{self.car_wash["id"]}: {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке боксов: {e}')

    def load_boxes_and_refresh(self):
        try:
            self.load_boxes()
            self.refresh_tabs()
        except Exception as e:
            print(f'Ошибка при загрузке боксов и обновлении вкладок: {e}')
        finally:
            self.hide_loading()

    def load_bookings(self, box):
        try:
            response = self.api.get_bookings(self.car_wash['id'])
            if response.status_code == 200:
                bookings_data = response.json().get('data', [])
                current_date = datetime.date.today()
                current_time = datetime.datetime.now()
                return [
                    booking
                    for booking in bookings_data
                    if booking['box_id'] == box['id']
                    and booking['start_datetime'].startswith(
                        current_date.strftime('%Y-%m-%d')
                    )
                    and datetime.datetime.fromisoformat(
                        booking['end_datetime']
                    )
                    < current_time
                ]
            else:
                print(
                    f'Ошибка загрузки букингов: '
                    f'{response.status_code}, {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при загрузке букингов: {e}')
        return []

    def create_box_management_tabs(self):
        self.tab_contents = {}

        tabs = [
            ft.Tab(
                text=box['name'],
                content=self.create_box_tab_content(box),
            )
            for box in self.boxes_list
        ]

        for i, box in enumerate(self.boxes_list):
            self.tab_contents[box['id']] = tabs[i].content

        tabs.append(
            ft.Tab(
                text='Добавить бокс',
                content=self.create_add_box_ui(),
            )
        )

        return ft.Tabs(
            tabs=tabs,
            expand=True,
            selected_index=self.current_tab_index,
            on_change=self.on_tab_change,
        )

    def create_box_tab_content(self, box):
        bookings = self.load_bookings(box)

        booking_rows = []
        total_revenue = 0

        for index, booking in enumerate(bookings, start=1):
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

        rows = [
            ft.Container(
                content=ft.Text(
                    f"Бокс: {box['name']}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.alignment.center,
                padding=ft.padding.only(bottom=10),
            ),
            *booking_rows,
            ft.Row(
                controls=[
                    ft.Text(
                        'Итого:',
                        weight=ft.FontWeight.BOLD,
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{total_revenue} ₸',
                        weight=ft.FontWeight.BOLD,
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        'Зарплата (40%):',
                        weight=ft.FontWeight.BOLD,
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{salary} ₸',
                        weight=ft.FontWeight.BOLD,
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                controls=[
                    ft.Text(
                        'Чистая прибыль:',
                        weight=ft.FontWeight.BOLD,
                        expand=2,
                        text_align=ft.TextAlign.LEFT,
                    ),
                    ft.Text(
                        f'{net_profit} ₸',
                        weight=ft.FontWeight.BOLD,
                        expand=1,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.EDIT,
                        on_click=lambda _: self.show_edit_name_modal(box),
                        icon_size=20,
                        tooltip='Редактировать имя',
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        on_click=lambda _: self.on_delete_box(box['id']),
                        icon_size=20,
                        tooltip='Удалить бокс',
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ]

        return ft.Container(
            content=ft.ListView(
                controls=rows,
                padding=ft.padding.all(10),
                spacing=5,
            ),
            expand=True,
            padding=ft.padding.symmetric(horizontal=20),
        )

    def update_tab_content(self, box):
        if box['id'] in self.tab_contents:
            self.tab_contents[box['id']].content = self.create_box_tab_content(
                box
            )
            self.tab_contents[box['id']].update()

    def refresh_tabs(self):
        while len(self.page.controls) > 1:
            self.page.controls.pop()

        tabs = self.create_box_management_tabs()
        self.page.add(tabs)
        self.page.update()

    def on_tab_change(self, e):
        self.current_tab_index = e.control.selected_index

    def create_add_box_ui(self):
        add_box_field = ft.TextField(
            label='Имя нового бокса',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.padding.only(
                left=20, top=5, right=10, bottom=5
            ),
            text_align=ft.TextAlign.CENTER,
            autofocus=True,
        )
        add_box_button = ft.TextButton(
            text='Сохранить',
            on_click=lambda e: self.on_add_box(add_box_field.value),
        )

        content = ft.Column(
            controls=[
                ft.Text(
                    'Добавить новый бокс',
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                add_box_field,
                ft.Row(
                    controls=[add_box_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Container(
            content=content,
            alignment=ft.alignment.center,
            padding=ft.padding.all(20),
        )

    def on_add_box(self, box_name):
        self.show_loading()
        new_box_data = {
            'name': box_name,
            'car_wash_id': self.car_wash['id'],
            'user_id': 1,
        }

        response = self.api.create_box(new_box_data)
        if response.status_code == 200:
            print(f"Бокс '{box_name}' успешно добавлен.")
            new_box = response.json().get('data', {})

            if not new_box:
                print('Сервер вернул пустой ответ. Обновляем список боксов...')
                self.load_boxes_and_refresh()
            else:
                self.boxes_list.append(new_box)
                self.add_new_tab(new_box)
        else:
            print(f'Ошибка добавления бокса: {response.text}')
        self.hide_loading()

    def add_new_tab(self, box):
        try:
            new_tab_content = self.create_box_tab_content(box)
            self.tab_contents[box['id']] = new_tab_content

            tabs_control = self.page.controls[-1]
            if isinstance(tabs_control, ft.Tabs):
                tabs_control.tabs.insert(
                    len(tabs_control.tabs) - 1,
                    ft.Tab(
                        text=box['name'],
                        content=new_tab_content,
                    ),
                )
                tabs_control.update()
        except KeyError as e:
            print(f'Ошибка при создании вкладки: отсутствует ключ {e}')

    def refresh_page(self):
        self.page.clean()
        self.page.add(self.create_box_management_tabs())
        self.page.update()

    def on_delete_box(self, box_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_box_from_server(box_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                'Подтверждение удаления',
                text_align=ft.TextAlign.CENTER,
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Text(
                'Вы уверены, что хотите удалить этот бокс?',
                text_align=ft.TextAlign.CENTER,
                size=14,
            ),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(dlg_modal)

    def delete_box_from_server(self, box_id):
        self.show_loading()
        response = self.api.delete_box(box_id)
        if response.status_code == 200:
            print(f'Бокс с ID {box_id} успешно удалён.')
            self.boxes_list = [
                box for box in self.boxes_list if box['id'] != box_id
            ]
            self.refresh_tabs()
            self.show_snack_bar(
                'Бокс успешно удалён!', bgcolor=ft.colors.GREEN
            )
        elif response.status_code == 400:
            error_message = response.json().get(
                'detail', 'Невозможно удалить бокс.'
            )
            print(f'Ошибка при удалении бокса: {error_message}')
            self.show_snack_bar(
                f'Ошибка: {error_message}\nУдалите '
                f'записи перед удалением бокса.',
                bgcolor=ft.colors.RED,
            )
        else:
            print(f'Ошибка при удалении бокса: {response.text}')
            self.show_snack_bar(
                'На данном боксе зарегистрирована история записей.',
                bgcolor=ft.colors.RED,
            )
        self.hide_loading()

    def setup_snack_bar(self):
        self.snack_bar = ft.SnackBar(
            content=ft.Container(
                content=ft.Text('', text_align=ft.TextAlign.CENTER),
                alignment=ft.alignment.center,
            ),
            bgcolor=ft.colors.GREEN,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.GREEN):
        self.snack_bar.content.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True
        self.page.update()

    def show_edit_name_modal(self, box):
        name_field = ft.TextField(
            label='Новое имя бокса',
            value=box['name'],
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.padding.only(
                left=20, top=5, right=10, bottom=5
            ),
            text_align=ft.TextAlign.CENTER,
            autofocus=True,
        )

        save_button = ft.ElevatedButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_box(box, name_field.value),
        )
        close_button = ft.TextButton(
            text='Отмена',
            on_click=self.close_modal,
        )

        modal_content = ft.Column(
            controls=[
                ft.Text(
                    'Редактировать имя бокса',
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                name_field,
                ft.Row(
                    controls=[save_button, close_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20,
                ),
            ],
            spacing=20,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.modal_container = ft.Container(
            content=modal_content,
            alignment=ft.alignment.bottom_center,
            padding=ft.padding.all(20),
            margin=ft.margin.only(top=250),
            bgcolor='rgba(0, 0, 0, 0.5)',
            expand=False,
        )

        self.loading_overlay = ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            visible=False,
            expand=True,
        )

        self.page.overlay.append(self.modal_container)
        self.page.overlay.append(self.loading_overlay)
        self.page.update()

    def close_modal(self, e=None):
        if (
            hasattr(self, 'modal_container')
            and self.modal_container in self.page.overlay
        ):
            self.page.overlay.remove(self.modal_container)
        self.page.update()

    def on_save_box(self, box, new_name):
        if new_name.strip():
            self.show_loading()
            box['name'] = new_name
            response = self.api.update_box(box['id'], new_name)
            if response.status_code == 200:
                print(f"Бокс с ID {box['id']} успешно обновлён.")
                self.refresh_tabs()
            else:
                print(f'Ошибка при обновлении бокса: {response.text}')
            self.hide_loading()
        self.close_modal()

    def on_back_to_edit_page(self, e=None):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api.url, self.locations)
