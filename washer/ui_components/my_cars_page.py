import re

import flet as ft

from washer.api_requests import BackendApi


class MyCarsPage:
    def __init__(self, page, api_url, cars, on_car_saved_callback=None):
        self.page = page
        self.api = BackendApi()
        self.api.set_access_token(page.client_storage.get('access_token'))
        self.api_url = api_url
        self.cars = cars
        self.on_car_saved_callback = on_car_saved_callback

        self.page.floating_action_button = None
        # self.page.update()
        # При включении self.page.update() AppBar скидывается некрасиво
        # Но за то FAB скрывается красиво до загрузки страницы

    def open(self):
        self.load_user_cars_from_server()
        self.page.clean()
        self.page.add(self.create_cars_page())
        self.page.update()

    def create_cars_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_wash_selection,
                icon_color=ft.colors.WHITE,
                padding=ft.padding.only(left=10),
            ),
            title=ft.Text(
                'Мои автомобили',
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE,
            ),
            center_title=True,
            bgcolor=ft.colors.BLUE,
            leading_width=40,
        )

        car_blocks = [self.create_car_info_card(car) for car in self.cars]

        if not self.cars:
            empty_image = ft.Container(
                content=ft.Image(
                    src='https://drive.google.com/uc?id=122KNtdntfiTPaOB5eAA0b1N_IxCPMY3a',
                    width=300,
                    height=300,
                    fit=ft.ImageFit.COVER,
                ),
                padding=ft.padding.only(top=100),
            )
            empty_text = ft.Container(
                content=ft.Text(
                    'У вас пока нет добавленных автомобилей',
                    size=18,
                    color=ft.colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.only(top=20),
            )
            car_blocks = [empty_image, empty_text]

        add_car_button = ft.ElevatedButton(
            text='Добавить автомобиль',
            on_click=self.on_add_car_click,
            bgcolor=ft.colors.BLUE,
            color=ft.colors.WHITE,
            width=400,
        )

        return ft.Container(
            width=730,
            alignment=ft.alignment.center,
            content=ft.Column(
                controls=[
                    *car_blocks,
                    add_car_button,
                ],
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll='adaptive',
            ),
            padding=ft.padding.all(10),
        )

    def create_car_info_card(self, car):
        car_name = car.get('name', 'Название не указано')
        brand, model, generation, body_type = self.parse_car_name(car_name)

        car_details = [
            ('Бренд', brand),
            ('Модель', model),
            ('Поколение', generation),
            ('Тип кузова', body_type),
        ]

        car_info_column = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, weight=ft.FontWeight.BOLD, size=16),
                        ft.Text(value, color=ft.colors.GREY_600, size=16),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for label, value in car_details
            ],
            spacing=10,
        )

        delete_button = ft.TextButton(
            'Удалить автомобиль',
            on_click=lambda e, car_id=car['id']: self.on_delete_car(car_id),
            style=ft.ButtonStyle(
                color=ft.colors.RED_400,
                padding=ft.padding.symmetric(vertical=5),
            ),
        )

        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                'Информация об автомобиле',
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Divider(),
                            car_info_column,
                            ft.Divider(),
                            delete_button,
                        ],
                        spacing=10,
                    ),
                    padding=ft.padding.all(20),
                ),
                elevation=3,
            ),
            width=700,
            padding=ft.padding.all(5),
            margin=ft.margin.only(bottom=20),
        )

    def parse_car_name(self, name: str) -> tuple[str, str, str, str]:
        from typing import List, Tuple

        print(f'Parsing car name: {name}')

        body_types = [
            'внедорожник 5 дв',
            'внедорожник 3 дв',
            'седан 4 дв',
            'хэтчбек 5 дв',
            'хэтчбек 3 дв',
            'универсал 5 дв',
            'лифтбек 5 дв',
            'фастбек 3 дв',
            'купе 2 дв',
            'кабриолет 2 дв',
            'седан',
            'хэтчбек',
            'универсал',
            'внедорожник',
            'купе',
            'кабриолет',
            'минивэн',
            'пикап',
            'фургон',
            'лимузин',
            'тарга',
            'родстер',
            'комби',
            'фастбек',
            'лифтбек',
            'спортивный',
            'кроссовер',
            'вэн',
            'микроавтобус',
            'минивен',
            '4 дв',
            '5 дв',
            '3 дв',
        ]

        body_types.sort(key=lambda x: -len(x))

        numeric_generation_pattern = re.compile(
            r'\b(\d{4}-(?:\d{4}|present))\b', re.IGNORECASE
        )

        roman_generation_pattern = re.compile(
            r'\b([IVXLCDM]+(?:\s*\([^)]*\))*(?:\s*Рестайлинг(?:\s*\d+)?)?(?:\s*\(\d{4}-present\))?)\b',
            re.IGNORECASE,
        )

        words = name.split()
        print(f'Words: {words}')

        brand = words[0] if words else 'Бренд не указан'
        remaining_words = words[1:] if len(words) > 1 else []

        print(f'Brand: {brand}')
        print(f'Remaining words: {remaining_words}')

        generation = 'Поколение не указано'
        body_type = 'Тип кузова не указан'
        model = 'Модель не указана'

        MatchType = Tuple[int, int, str, str]

        matches: List[MatchType] = []
        for i in range(len(remaining_words)):
            for j in range(i + 1, min(i + 6, len(remaining_words) + 1)):
                potential_generation = ' '.join(remaining_words[i:j])
                if numeric_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'numeric'))
                elif roman_generation_pattern.fullmatch(potential_generation):
                    matches.append((j - i, i, potential_generation, 'roman'))

        if matches:
            matches.sort(key=lambda x: (-x[0], x[3]))
            _, generation_index, generation, generation_type = matches[0]
            print(f'Found generation: {generation} ({generation_type})')
            remaining_words = (
                remaining_words[:generation_index]
                + remaining_words[generation_index + matches[0][0] :]
            )
            print(
                f'Remaining words after generation extraction: '
                f'{remaining_words}'
            )
        else:
            print('Generation not found')

        matched_body_types = []
        for i in range(len(remaining_words), 0, -1):
            potential_body_type = (
                ' '.join(remaining_words[i - 1 :]).lower().rstrip('.')
            )
            print(f'Checking potential body type: {potential_body_type}')
            for bt in body_types:
                if potential_body_type == bt.lower():
                    matched_body_types.append((i - 1, bt))
        if matched_body_types:
            matched_body_types.sort(key=lambda x: x[0])
            body_type_index, body_type = matched_body_types[0]
            remaining_words = remaining_words[:body_type_index]
            print(f'Found body type: {body_type}')
            print(
                f'Remaining words after body type extraction: '
                f'{remaining_words}'
            )
        else:
            print('Body type not found')

        if remaining_words:
            model = ' '.join(remaining_words)
        else:
            model = 'Модель не указана'

        print(f'Model: {model}')
        print(f'Generation: {generation}')
        print(f'Body type: {body_type}')

        return brand, model, generation, body_type

    def load_user_cars_from_server(self):
        try:
            user_id = self.page.client_storage.get('user_id')
            if not user_id:
                print('User ID not found!')
                return

            response = self.api.get_user_cars(user_id=user_id)
            print(
                f'Ответ от сервера при загрузке автомобилей: {response.text}'
            )

            if response.status_code == 200:
                self.cars[:] = response.json().get('data', [])
            else:
                print(
                    f'Ошибка при загрузке автомобилей с сервера: '
                    f'{response.status_code} - {response.text}'
                )
        except Exception as e:
            print(f'Ошибка при запросе автомобилей с сервера: {e}')

    def on_add_car_click(self, e):
        from washer.ui_components.select_car_page import SelectCarPage

        SelectCarPage(
            page=self.page,
            on_car_saved=self.on_car_saved,
            redirect_to='my_cars_page',
        )

    def on_car_saved(self, car):
        if 'id' not in car and 'user_car_id' in car:
            car['id'] = car['user_car_id']
        self.cars.append(car)
        self.page.clean()
        self.page.add(self.create_cars_page())
        self.page.update()

    def on_delete_car(self, car_id):
        def confirm_delete(e):
            self.page.dialog.open = False
            self.page.update()
            self.delete_car_from_server(car_id)

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text('Подтверждение удаления'),
            content=ft.Text('Вы уверены, что хотите удалить этот автомобиль?'),
            actions=[
                ft.TextButton('Да', on_click=confirm_delete),
                ft.TextButton('Нет', on_click=cancel_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dlg_modal
        dlg_modal.open = True
        self.page.update()

    def delete_car_from_server(self, car_id):
        try:
            response = self.api.delete_user_car(car_id)
            if response.status_code == 200:
                self.cars[:] = [
                    car for car in self.cars if car['id'] != car_id
                ]
                self.page.clean()
                self.page.add(self.create_cars_page())
                self.page.update()
                print(f'Автомобиль с ID {car_id} успешно удален.')
            else:
                print(f'Ошибка при удалении автомобиля: {response.text}')
        except Exception as e:
            print(f'Ошибка при удалении автомобиля: {e}')

    def return_to_wash_selection(self, e):
        self.page.appbar = None

        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(
            self.page, username=self.page.client_storage.get('username')
        )
