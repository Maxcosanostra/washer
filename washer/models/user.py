from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserBasicInfo(BaseModel):
    username: str = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)

    @field_validator('username')
    def validate_username(cls, v):
        if not v:
            raise ValueError('Имя пользователя обязательно для заполнения')
        if len(v) < 3:
            raise ValueError(
                'Имя пользователя должно содержать не менее 3 символов'
            )
        if len(v) > 10:
            raise ValueError(
                'Имя пользователя должно содержать не более 10 символов'
            )
        return v

    @field_validator('first_name')
    def validate_first_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Имя обязательно для заполнения')
        if len(v) > 50:
            raise ValueError('Имя должно содержать не более 50 символов')
        return v

    @field_validator('last_name')
    def validate_last_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Фамилия обязательна для заполнения')
        if len(v) > 50:
            raise ValueError('Фамилия должна содержать не более 50 символов')
        return v


class UserPassword(BaseModel):
    password: str = Field(...)
    confirm_password: str

    @field_validator('password')
    def validate_password_length(cls, v):
        if not v:
            raise ValueError('Пароль обязателен для заполнения')
        if len(v) < 6:
            raise ValueError('Пароль должен содержать не менее 6 символов')
        return v

    @field_validator('confirm_password')
    def validate_passwords_match(cls, v, info):
        password = info.data.get('password')
        if not v:
            raise ValueError('Подтверждение пароля обязательно для заполнения')
        if password and v != password:
            raise ValueError('Пароли не совпадают')
        return v


class UserRegistration(BaseModel):
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = Field(None, alias='phone_number')
    image: Optional[bytes] = None

    @field_validator('username')
    def validate_username(cls, v):
        if not v:
            raise ValueError('Имя пользователя обязательно для заполнения')
        if len(v) < 3:
            raise ValueError(
                'Имя пользователя должно содержать не менее 3 символов'
            )
        if len(v) > 50:
            raise ValueError(
                'Имя пользователя должно содержать не более 50 символов'
            )
        return v

    @field_validator('first_name')
    def validate_first_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Имя обязательно для заполнения')
        if len(v) > 50:
            raise ValueError('Имя должно содержать не более 50 символов')
        return v

    @field_validator('last_name')
    def validate_last_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Фамилия обязательна для заполнения')
        if len(v) > 50:
            raise ValueError('Фамилия должна содержать не более 50 символов')
        return v

    @field_validator('password')
    def validate_password_length(cls, v):
        if not v:
            raise ValueError('Пароль обязателен для заполнения')
        if len(v) < 6:
            raise ValueError('Пароль должен содержать не менее 6 символов')
        return v


class UserSignIn(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

    @field_validator('username')
    def validate_username(cls, v):
        if not v:
            raise ValueError('Имя пользователя обязательно для заполнения')
        if len(v) < 3:
            raise ValueError(
                'Имя пользователя должно содержать не менее 3 символов'
            )
        if len(v) > 10:
            raise ValueError(
                'Имя пользователя должно содержать не более 10 символов'
            )
        return v

    @field_validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Пароль обязателен для заполнения')
        if len(v) < 6:
            raise ValueError('Пароль должен содержать не менее 6 символов')
        return v
