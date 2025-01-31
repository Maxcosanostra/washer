from typing import Optional

import flet as ft
from pydantic import ValidationError

from washer.api_requests import BackendApi
from washer.models.user import UserBasicInfo, UserPassword, UserRegistration
from washer.ui_components.add_car_prompt_page import AddCarPromptPage


class SignUpPage:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = BackendApi()

        self.user_basic_info: Optional[UserBasicInfo] = None
        self.user_password: Optional[UserPassword] = None
        self.user_registration: Optional[UserRegistration] = None
        self.phone_number: Optional[str] = None

        self.is_formatting = False

        self.first_name_field = self.create_first_name_field()
        self.last_name_field = self.create_last_name_field()
        self.username_field = self.create_username_field()

        self.password_field = self.create_password_field()
        self.confirm_password_field = self.create_confirm_password_field()
        self.phone_number_field = self.create_phone_number_field()

        self.image_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.image_picker)
        self.selected_image = None

        self.snack_bar = ft.SnackBar(
            content=ft.Text(
                '',
                text_align=ft.TextAlign.CENTER,
                size=16,
                color=ft.colors.WHITE,
            ),
            bgcolor=ft.colors.RED,
            duration=3000,
        )
        self.page.overlay.append(self.snack_bar)
        self.page.update()

        self.show_welcome_page()

    def create_first_name_field(self):
        return ft.TextField(
            label='Имя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_last_name_field(self):
        return ft.TextField(
            label='Фамилия',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_username_field(self):
        return ft.TextField(
            label='Имя пользователя',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
        )

    def create_password_field(self):
        return ft.TextField(
            label='Пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
        )

    def create_confirm_password_field(self):
        return ft.TextField(
            label='Подтвердите пароль',
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
        )

    def create_phone_number_field(self):
        phone_field = ft.TextField(
            label='Номер телефона',
            hint_text='(___) ___-__-__',
            value='+7',
            width=300,
            text_size=15,
            height=60,
            border_radius=ft.border_radius.all(30),
            content_padding=ft.Padding(left=20, top=5, right=10, bottom=5),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=self.format_phone_number,
        )
        return phone_field

    def format_phone_number(self, e):
        if self.is_formatting:
            return

        self.is_formatting = True

        raw_input = self.phone_number_field.value or ''
        digits = ''.join(c for c in raw_input if c.isdigit())

        formatted = ''

        if len(digits) >= 1:
            if digits[0] == '7':
                formatted += '+' + digits[0]
            else:
                formatted += digits[0]
        if len(digits) > 1:
            formatted += ' (' + digits[1:4]
        if len(digits) >= 4:
            formatted += ') ' + digits[4:7]
        if len(digits) >= 7:
            formatted += '-' + digits[7:9]
        if len(digits) >= 9:
            formatted += '-' + digits[9:11]

        if len(digits) < 11:
            if len(digits) < 10 and formatted.endswith('-'):
                formatted = formatted[:-1]
            if len(digits) < 7 and formatted.endswith(') '):
                formatted = formatted[:-2]
            if len(digits) < 4 and formatted.endswith(' ('):
                formatted = formatted[:-2]
            if len(digits) < 1 and formatted.startswith('+'):
                formatted = ''

        if len(formatted) > 18:
            formatted = formatted[:18]

        self.phone_number_field.value = formatted
        self.phone_number_field.update()

        self.is_formatting = False

    def show_welcome_page(self, e=None):
        image_size = 300

        self.page.clean()
        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                'wexy!',
                                size=180,
                                font_family='LavishlyYours',
                                # Применение пользовательского шрифта
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.Image(
                                src='http://77.73.66.191:9001/api/v1/buckets/general-bucket/objects/download?preview=true&prefix=Car%20wash-amico.png&version_id=null',
                                # src='https://drive.google.com/uc?export=view&id=1haBXQrQ_akd40ZAuIi7dr-apE8hWhi5h',
                                width=image_size,
                                height=image_size,
                            ),
                            margin=ft.margin.only(bottom=30),
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Лучшие автомойки в вашем кармане',
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.colors.GREY,
                            ),
                            margin=ft.margin.only(bottom=30),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Зарегистрироваться',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.show_step_1,
                                elevation=5,
                            ),
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.TextButton(
                            'Уже есть аккаунт? Войти',
                            on_click=self.open_sign_in_page,
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20),
                ),
                alignment=ft.alignment.center,
                expand=True,
            )
        )

    def show_step_1(self, e=None):
        self.page.clean()

        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(height=100),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=self.show_welcome_page,
                                ),
                                ft.TextButton(
                                    text='Назад',
                                    on_click=self.show_welcome_page,
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=ft.colors.BLACK,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Шаг 1', size=28, weight=ft.FontWeight.BOLD
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text('Введите ваши данные', size=18),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=self.first_name_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.last_name_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.username_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Далее',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.save_step_1,
                            ),
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=20, bottom=15),
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20, horizontal=20),
                ),
                expand=True,
                border_radius=ft.border_radius.all(12),
            )
        )

    def save_step_1(self, e=None):
        first_name = self.first_name_field.value.strip()
        last_name = self.last_name_field.value.strip()
        username = self.username_field.value.strip()

        try:
            self.user_basic_info = UserBasicInfo(
                username=username, first_name=first_name, last_name=last_name
            )
        except ValidationError as ve:
            self.display_validation_errors(ve)
            return

        self.show_step_2()

    def show_step_2(self, e=None):
        self.page.clean()

        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(height=100),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=self.show_step_1,
                                ),
                                ft.TextButton(
                                    text='Назад',
                                    on_click=self.show_step_1,
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=ft.colors.BLACK,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Шаг 2', size=28, weight=ft.FontWeight.BOLD
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text('Придумайте пароль', size=18),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=self.password_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.confirm_password_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Далее',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.save_step_2,
                            ),
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=20, bottom=15),
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20, horizontal=20),
                ),
                expand=True,
                border_radius=ft.border_radius.all(12),
            )
        )

    def save_step_2(self, e=None):
        password = self.password_field.value
        confirm_password = self.confirm_password_field.value

        try:
            self.user_password = UserPassword(
                password=password, confirm_password=confirm_password
            )
        except ValidationError as ve:
            error_messages = []
            for error in ve.errors():
                msg = error['msg']
                prefix = 'Value error, '
                if msg.startswith(prefix):
                    msg = msg[len(prefix) :]
                error_messages.append(msg)
            error_text = '\n'.join(error_messages)
            self.show_snack_bar(error_text, bgcolor=ft.colors.RED)
            return

        self.show_step_3_phone()

    def show_step_3_phone(self, e=None):
        self.page.clean()

        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(height=100),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=self.show_step_2,
                                ),
                                ft.TextButton(
                                    text='Назад',
                                    on_click=self.show_step_2,
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=ft.colors.BLACK,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Шаг 3', size=28, weight=ft.FontWeight.BOLD
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text('Введите номер телефона', size=18),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=self.phone_number_field,
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Далее',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.save_step_3_phone,
                            ),
                            width=300,
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=20, bottom=15),
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20, horizontal=20),
                ),
                expand=True,
                border_radius=ft.border_radius.all(12),
            )
        )

    def save_step_3_phone(self, e=None):
        phone = self.phone_number_field.value.strip()
        if not self.validate_phone_number(phone):
            self.show_snack_bar(
                'Некорректный номер телефона!', bgcolor=ft.colors.RED
            )
            return
        self.phone_number = phone

        self.show_step_4_image()

    def show_step_4_image(self, e=None):
        self.page.clean()

        self.page.add(
            ft.Container(
                content=ft.ListView(
                    controls=[
                        ft.Container(height=100),
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.ARROW_BACK,
                                    on_click=self.show_step_3_phone,
                                ),
                                ft.TextButton(
                                    text='Назад',
                                    on_click=self.show_step_3_phone,
                                    style=ft.ButtonStyle(
                                        padding=0,
                                        color=ft.colors.BLACK,
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(
                            content=ft.Text(
                                'Шаг 4', size=28, weight=ft.FontWeight.BOLD
                            ),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text('Выберите изображение', size=18),
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(
                            content=ft.Text('(опционально)', size=16),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=10),
                        ),
                        ft.Container(
                            content=ft.Text(
                                (
                                    'Вы можете загрузить изображение сейчас '
                                    'или сделать это позже.'
                                ),
                                size=16,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.Container(
                                width=100,
                                height=100,
                                border_radius=ft.border_radius.all(50),
                                bgcolor=ft.colors.GREY,
                                alignment=ft.alignment.center,
                                content=ft.Icon(ft.icons.PERSON, size=50),
                                on_click=(
                                    lambda e: self.image_picker.pick_files(
                                        allow_multiple=False,
                                        file_type=ft.FilePickerFileType.IMAGE,
                                    )
                                ),
                            ),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(bottom=20),
                        ),
                        ft.Container(
                            content=ft.ElevatedButton(
                                text='Зарегистрироваться',
                                bgcolor=ft.colors.PURPLE_ACCENT,
                                color=ft.colors.WHITE,
                                on_click=self.on_sign_up_click,
                            ),
                            width=300,
                            alignment=ft.alignment.center,
                        ),
                    ],
                    expand=True,
                    padding=ft.padding.symmetric(vertical=20, horizontal=20),
                ),
                expand=True,
                border_radius=ft.border_radius.all(12),
            )
        )

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image = e.files[0].path
            print(f'Выбрано изображение: {self.selected_image}')

    def on_sign_up_click(self, e=None):
        if (
            not self.user_basic_info
            or not self.user_password
            or not self.phone_number
        ):
            self.show_snack_bar(
                'Пожалуйста, завершите все шаги регистрации!',
                bgcolor=ft.colors.RED,
            )
            return

        try:
            self.user_registration = UserRegistration(
                username=self.user_basic_info.username,
                first_name=self.user_basic_info.first_name,
                last_name=self.user_basic_info.last_name,
                password=self.user_password.password,
                phone_number=self.phone_number,
                image=None,
            )
        except ValidationError as ve:
            self.display_validation_errors(ve)
            return

        if self.selected_image:
            try:
                with open(self.selected_image, 'rb') as img_file:
                    image_bytes = img_file.read()
                self.user_registration.image = image_bytes
            except Exception as ex:
                self.show_snack_bar(
                    f'Ошибка при чтении изображения: {ex}',
                    bgcolor=ft.colors.RED,
                )
                return

        response = self.api.register_user(user=self.user_registration)

        if response.status_code == 200:
            tokens = response.json()
            self.api.set_access_token(tokens['access_token'])
            self.api.refresh_token = tokens['refresh_token']  # Если необходимо

            print(f'Access token после установки: {self.api.access_token}')
            print(f'Refresh token после установки: {self.api.refresh_token}')

            self.page.client_storage.set(
                'access_token', tokens['access_token']
            )
            self.page.client_storage.set(
                'refresh_token', tokens['refresh_token']
            )
            self.page.client_storage.set(
                'username', self.user_basic_info.username
            )

            user_info = self.api.get_logged_user()
            if 'id' in user_info:
                self.page.client_storage.set('user_id', user_info['id'])

            AddCarPromptPage(
                page=self.page, username=self.user_basic_info.username
            )
        else:
            try:
                error_detail = response.json().get('detail', response.text)
            except ValueError:
                error_detail = response.text
            self.show_snack_bar(
                f'Ошибка: {error_detail}', bgcolor=ft.colors.RED
            )

    def display_validation_errors(self, ve: ValidationError):
        """
        Отображает ошибки валидации на странице с использованием SnackBar.
        """
        error_messages = []
        for error in ve.errors():
            msg = error['msg']
            print(f'Error message before processing: {msg}')  # Отладка
            prefix = 'Value error, '
            if msg.startswith(prefix):
                msg = msg[len(prefix) :]
            error_messages.append(msg)
        error_text = '\n'.join(error_messages)
        self.show_snack_bar(error_text, bgcolor=ft.colors.RED)

    def show_snack_bar(self, message: str, bgcolor: str = ft.colors.RED):
        print(f'Показываем сообщение: {message}')

        self.snack_bar.content.value = message
        self.snack_bar.bgcolor = bgcolor
        self.snack_bar.open = True

        self.page.update()

    def open_wash_selection_page(self):
        from washer.ui_components.wash_selection_page import WashSelectionPage

        WashSelectionPage(self.page, self.user_basic_info.username)

    def open_sign_in_page(self, e=None):
        from washer.ui_components.sign_in_page import SignInPage

        SignInPage(self.page)

    def validate_phone_number(self, phone: str) -> bool:
        import re

        pattern = (
            r'^(\+\d{1,3} \(\d{3}\) \d{3}-\d{2}-\d{2})|'
            r'(\d{1,3} \(\d{3}\) \d{3}-\d{2}-\d{2})$'
        )
        return re.match(pattern, phone) is not None
