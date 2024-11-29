import flet as ft
import httpx

from washer.ui_components.select_car_page import SelectCarPage


class MyCarsPage:
    def __init__(self, page, api_url, cars, on_car_saved_callback):
        self.page = page
        self.api_url = api_url
        self.cars = cars
        self.on_car_saved_callback = on_car_saved_callback

    def open(self):
        self.load_user_cars_from_server()
        self.page.clean()
        self.page.add(self.create_cars_page())
        self.page.update()

    def create_cars_page(self):
        self.page.appbar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                on_click=self.return_to_profile,
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

        car_blocks = [self.create_car_display(car) for car in self.cars]

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

        return ft.Container(
            content=ft.Column(
                controls=[
                    *car_blocks,
                    ft.ElevatedButton(
                        text='Добавить автомобиль',
                        on_click=self.on_add_car_click,
                        bgcolor=ft.colors.BLUE,
                        color=ft.colors.WHITE,
                    ),
                ],
                spacing=15,
                scroll='adaptive',
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(20),
        )

    def create_car_display(self, car):
        car_name = car.get('name', 'Название не указано')
        parts = car_name.split(' ')
        brand = parts[0] if len(parts) > 0 else 'Бренд не указан'
        model = (
            ' '.join(parts[1:-1]) if len(parts) > 2 else 'Модель не указана'
        )
        generation = parts[-1] if len(parts) > 1 else 'Поколение не указано'

        car_details = [
            ('Модель', model),
            ('Поколение', generation),
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
            on_click=lambda e: self.on_delete_car(car['id']),
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
                            ft.Container(
                                content=ft.Text(
                                    brand,
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                alignment=ft.alignment.center,
                                padding=ft.padding.only(bottom=10),
                            ),
                            car_info_column,
                            ft.Divider(),
                            delete_button,
                        ],
                        spacing=15,
                    ),
                    padding=ft.padding.all(15),
                ),
                elevation=3,
            ),
            width=370,
            margin=ft.margin.only(bottom=20),
        )

    def load_user_cars_from_server(self):
        """Загрузка автомобилей пользователя с сервера"""
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
                f'{self.api_url.rstrip("/")}/cars?user_id={user_id}&limit=100'
            )
            response = httpx.get(url, headers=headers)

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
        SelectCarPage(self.page, self.on_car_saved_callback)

    def on_delete_car(self, car_id):
        def confirm_delete(e):
            self.page.close(dlg_modal)
            self.delete_car_from_server(car_id)

        def cancel_delete(e):
            self.page.close(dlg_modal)

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

        self.page.open(dlg_modal)

    def delete_car_from_server(self, car_id):
        access_token = self.page.client_storage.get('access_token')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
        }
        url = f'{self.api_url.rstrip("/")}/cars/{car_id}'
        print(f'Отправка DELETE запроса на {url}')

        response = httpx.delete(url, headers=headers)

        if response.status_code == 200:
            self.cars[:] = [car for car in self.cars if car['id'] != car_id]
            self.page.clean()
            self.page.add(self.create_cars_page())
            self.page.update()
            print(f'Автомобиль с ID {car_id} успешно удалён.')
        else:
            print(f'Ошибка при удалении автомобиля: {response.text}')

    def return_to_profile(self, e):
        self.page.appbar = None  # Сбрасываем AppBar
        from washer.ui_components.profile_page import ProfilePage

        profile_page = ProfilePage(self.page)
        profile_page.return_to_profile(e)
