import flet as ft


class ConfirmationPage:
    def __init__(
        self,
        page: ft.Page,
        booking_data: dict,
        car_data: dict,
        price: int,
        additions_list: list[str] = None,
        on_confirm=None,
        on_cancel=None,
        notes_label: str = None,
    ):
        self.page = page
        self.booking_data = booking_data or {}
        self.car_data = car_data or {}
        self.price = price
        self.additions_list = additions_list or []
        self.on_confirm = on_confirm  # Callback "Подтвердить"
        self.on_cancel = on_cancel  # Callback "Изменить/Назад"
        self.notes_label = notes_label or (
            'Например: оставил вещи в салоне. '
            'Переложите, пожалуйста, в багажник и т.д.'
        )

        self.wishes_field = ft.TextField(
            label=self.notes_label,
            multiline=True,
            width=500,
            height=100,
            border_radius=ft.border_radius.all(10),
        )

    def open(self):
        self.page.clean()

        self.page.adaptive = True
        # Не устанавливаем self.page.scroll, пусть скроллит ListView

        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self._on_cancel_click,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Подтверждение',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.PURPLE,
            leading_width=40,
        )

        main_list_view = ft.ListView(
            spacing=10,
            expand=True,
            controls=[
                ft.Container(height=10),
                self._create_header_text(),
                self._create_booking_info_card(),
                self._create_car_info_card(),
                self._create_wishes_section(),
                self._create_buttons_row(),
            ],
        )

        # Оборачиваем ListView в контейнер, чтобы при прокрутке
        # был эффект «прижатия» под AppBar (margin.top=-10)
        main_container = ft.Container(
            content=main_list_view,
            margin=ft.margin.only(top=-10),
            expand=True,
            width=730,
            alignment=ft.alignment.center,
        )

        self.page.add(main_container)
        self.page.update()

    def _create_header_text(self) -> ft.Text:
        return ft.Text(
            'Пожалуйста, подтвердите свои данные',
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

    def _create_booking_info_card(self) -> ft.Card:
        box_name = self.booking_data.get('box_name', 'Не выбран')
        date_str = self.booking_data.get('date_str', 'Не выбрана')
        time_str = self.booking_data.get('time_str', 'Не выбрано')
        price_str = f'₸{int(self.price)}'
        service_str = 'Комплексная мойка'

        details = [
            ('Бокс', box_name),
            ('Дата', date_str),
            ('Время', time_str),
            ('Цена', price_str),
            ('Услуга', service_str),
        ]

        if self.additions_list:
            additions_str = ', '.join(self.additions_list)
            details.append(('Дополнительно', additions_str))

        info_rows = []
        for label, value in details:
            row = ft.Row(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(value, color=ft.colors.GREY_600, size=16),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            info_rows.append(row)

        info_column = ft.Column(info_rows, spacing=10)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            'Информация о записи',
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        info_column,
                    ],
                    spacing=10,
                ),
                padding=ft.padding.all(20),
            ),
            elevation=3,
            margin=ft.margin.only(bottom=20),
        )

    def _create_car_info_card(self) -> ft.Card:
        brand = self.car_data.get('brand', 'Не указано')
        model = self.car_data.get('model', 'Не указано')
        generation = self.car_data.get('generation', 'Не указано')
        body_type = self.car_data.get('body_type', 'Не указано')

        car_info_details = [
            ('Бренд', brand),
            ('Модель', model),
            ('Поколение', generation),
            ('Тип кузова', body_type),
        ]

        info_rows = []
        for label, value in car_info_details:
            row = ft.Row(
                [
                    ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                    ft.Text(value, color=ft.colors.GREY_600, size=16),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            info_rows.append(row)

        info_column = ft.Column(info_rows, spacing=10)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            'Информация об автомобиле',
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        info_column,
                    ],
                    spacing=10,
                ),
                padding=ft.padding.all(20),
            ),
            elevation=3,
            margin=ft.margin.only(bottom=20),
        )

    def _create_wishes_section(self) -> ft.Column:
        wishes_header = ft.Text(
            'Есть пожелания или комментарии? Добавьте ниже',
            size=18,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        wishes_container = ft.Container(
            content=self.wishes_field,
            alignment=ft.alignment.center,
            padding=ft.padding.symmetric(vertical=10),
        )

        return ft.Column(
            [wishes_header, wishes_container],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _create_buttons_row(self) -> ft.Column:
        confirm_button = ft.ElevatedButton(
            text='Подтвердить букинг',
            on_click=self._on_confirm_click,
            width=300,
            bgcolor=ft.colors.GREEN,
            color=ft.colors.WHITE,
        )

        cancel_button = ft.ElevatedButton(
            text='Изменить',
            on_click=self._on_cancel_click,
            width=300,
            bgcolor=ft.colors.GREY_700,
            color=ft.colors.WHITE,
        )

        return ft.Column(
            [confirm_button, cancel_button],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def _on_confirm_click(self, e):
        notes = self.wishes_field.value.strip()
        if self.on_confirm:
            self.on_confirm(notes)
        else:
            print('Нет on_confirm callback - ничего не делаем.')

    def _on_cancel_click(self, e):
        if self.on_cancel:
            self.on_cancel(e)
        else:
            print('Нет on_cancel callback - ничего не делаем.')
