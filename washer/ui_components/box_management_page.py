import flet as ft

from washer.ui_components.box_revenue_page import BoxRevenuePage


class BoxManagementPage:
    def __init__(self, page: ft.Page, car_wash, api_url, api, locations):
        self.page = page
        self.car_wash = car_wash
        self.api_url = api_url
        self.api = api
        self.locations = locations
        self.boxes_list = []

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
        self.page.add(self.create_box_management_page())
        self.page.overlay.append(self.loading_overlay)

    def show_loading(self):
        self.loading_overlay.visible = True
        self.page.update()

    def hide_loading(self):
        self.loading_overlay.visible = False
        self.page.update()

    def load_boxes(self):
        self.show_loading()
        response = self.api.get_boxes(self.car_wash['id'])
        if response.status_code == 200:
            all_boxes = response.json().get('data', [])
            self.boxes_list = [
                box
                for box in all_boxes
                if box['car_wash_id'] == self.car_wash['id']
            ]
        else:
            print(f'Ошибка загрузки боксов: {response.text}')
        self.hide_loading()

    def create_box_management_page(self):
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
                ft.Text(
                    'Управление боксами', size=24, weight=ft.FontWeight.BOLD
                ),
                ft.Column(
                    controls=[
                        self.create_box_item_ui(box) for box in self.boxes_list
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                self.create_add_box_ui(),
            ],
            spacing=20,
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

    def create_box_item_ui(self, box):
        box_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        box['name'],
                        size=16,
                        weight='bold',
                        text_align=ft.TextAlign.LEFT,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.icons.RECEIPT_LONG,
                        on_click=lambda _: self.open_box_revenue_page(box),
                        icon_size=20,
                        tooltip='Посмотреть выручку',
                    ),
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
            padding=ft.padding.all(10),
            margin=ft.margin.only(bottom=10),
            border_radius=ft.border_radius.all(8),
            bgcolor=ft.colors.GREY_900,
            shadow=ft.BoxShadow(
                offset=ft.Offset(0, 2),
                blur_radius=4,
                color=ft.colors.GREY_700,
            ),
            width=300,
        )
        return box_container

    def open_box_revenue_page(self, box):
        BoxRevenuePage(self.page, box, self.car_wash, self.api_url)

    def show_edit_name_modal(self, box):
        name_field = ft.TextField(
            label='Новое имя бокса',
            value=box['name'],
            width=300,
        )
        save_button = ft.ElevatedButton(
            text='Сохранить',
            on_click=lambda e: self.on_save_box(box, name_field.value),
        )
        close_button = ft.TextButton(text='Отмена', on_click=self.close_modal)

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text('Редактировать имя бокса', size=18),
                    name_field,
                    ft.Row(
                        controls=[save_button, close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.alignment.center,
            ),
            padding=ft.padding.all(10),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def close_modal(self, e=None):
        if self.modal_container in self.page.controls:
            self.page.controls.remove(self.modal_container)
        self.page.update()

    def create_add_box_ui(self):
        return ft.Container(
            content=ft.IconButton(
                icon=ft.icons.CREATE,
                icon_size=30,
                tooltip='Добавить новый бокс',
                on_click=self.show_add_box_field,
            ),
            alignment=ft.alignment.center,
            padding=ft.padding.all(10),
        )

    def show_add_box_field(self, e):
        self.add_box_field = ft.TextField(
            label='Имя нового бокса', width=200, text_align=ft.TextAlign.CENTER
        )
        self.add_box_button = ft.TextButton(
            text='Сохранить', on_click=self.on_add_box_from_modal
        )
        self.close_button = ft.TextButton(
            text='Отмена', on_click=self.close_modal
        )

        self.modal_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            'Добавить новый бокс',
                            size=18,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(
                        content=self.add_box_field,
                        alignment=ft.alignment.center,
                    ),
                    ft.Row(
                        controls=[self.add_box_button, self.close_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(10),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.GREY_900,
        )

        self.page.controls.append(self.modal_container)
        self.page.update()

    def on_add_box_from_modal(self, e):
        self.show_loading()
        new_box_data = {
            'name': self.add_box_field.value,
            'car_wash_id': self.car_wash['id'],
            'user_id': 1,
        }

        response = self.api.create_box(new_box_data)
        if response.status_code == 200:
            print(f"Бокс '{self.add_box_field.value}' успешно добавлен.")
            self.close_modal(e)
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_box_management_page())
            self.page.update()
        else:
            print(f'Ошибка добавления бокса: {response.text}')
        self.hide_loading()

    def on_delete_box(self, box_id):
        self.show_loading()
        response = self.api.delete_box(box_id)
        if response.status_code == 200:
            print(f'Бокс с ID {box_id} успешно удален.')
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_box_management_page())
            self.page.update()
        else:
            print(f'Ошибка при удалении бокса: {response.text}')
        self.hide_loading()

    def on_save_box(self, box, new_name):
        self.show_loading()
        response = self.api.update_box(box['id'], new_name)
        if response.status_code == 200:
            print(f"Бокс с ID {box['id']} успешно обновлен.")
            self.load_boxes()
            self.page.controls.clear()
            self.page.add(self.create_box_management_page())
            self.page.update()
        else:
            print(f'Ошибка при обновлении бокса: {response.text}')
        self.hide_loading()

    def on_back_to_edit_page(self, e=None):
        from washer.ui_components.carwash_edit_page import CarWashEditPage

        CarWashEditPage(self.page, self.car_wash, self.api_url, self.locations)
