import flet as ft

from washer.api_requests import BackendApi
from washer.ui_components.sign_up_page import SignUpPage


def main(page: ft.Page):
    page.fonts = {
        'LavishlyYours': 'http://77.73.66.191:9001/api/v1/buckets/general-bucket/objects/download?preview=true&prefix=LavishlyYours-Regular.ttf&version_id=null'
        # 'LavishlyYours': 'https://drive.google.com/uc?export=view&id=17uMDY7jYszJZS3td3pLzhnPbeKIXnZTD'
    }

    page.api = BackendApi()

    page.title = 'User Registration'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.adaptive = True

    SignUpPage(page)


ft.app(target=main)
