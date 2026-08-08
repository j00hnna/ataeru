"""
نماذج Pydantic للمصادقة.
"""
from pydantic import BaseModel, EmailStr, Field, validator

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company_name: str = Field(..., min_length=2, max_length=255)
    commercial_register: str | None = Field(None, max_length=100)
    tax_number: str | None = Field(None, max_length=100)

    @validator("password")
    def password_must_contain_number_and_letter(cls, v):
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("كلمة المرور يجب أن تحتوي على حرف ورقم على الأقل")
        return v

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"