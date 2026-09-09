from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    available: Optional[bool] = None


class MenuItemOut(MenuItemCreate):
    id: int
    available: bool = True

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    menu_item_id: int
    qty: int = 1


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    notes: Optional[str] = None
    table_id: Optional[int] = None
    payment_method: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str
    payment_method: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    menu_item_id: int
    name: Optional[str] = None
    qty: int
    price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    status: str
    total: float
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    table_id: Optional[int] = None
    user_id: Optional[int] = None
    shift_id: Optional[int] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class TableCreate(BaseModel):
    number: Optional[str] = None
    name: Optional[str] = None
    seats: int = 4
    zone: Optional[str] = None


class TableUpdate(BaseModel):
    number: Optional[str] = None
    name: Optional[str] = None
    seats: Optional[int] = None
    zone: Optional[str] = None
    is_active: Optional[bool] = None


class TableOut(TableCreate):
    id: int
    is_active: bool = True

    class Config:
        from_attributes = True


class TableBookingCreate(BaseModel):
    table_id: int
    linked_table_id: Optional[int] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    guests: int = 1
    starts_at: datetime
    ends_at: Optional[datetime] = None
    note: Optional[str] = None


class TableBookingUpdate(BaseModel):
    table_id: Optional[int] = None
    linked_table_id: Optional[int] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    guests: Optional[int] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    note: Optional[str] = None
    status: Optional[str] = None


class TableBookingOut(TableBookingCreate):
    id: int
    status: str = "confirmed"
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShiftOpen(BaseModel):
    opening_balance: float = 0.0
    notes: Optional[str] = None


class ShiftClose(BaseModel):
    closing_balance: float = 0.0
    expected_cash: Optional[float] = None
    notes: Optional[str] = None


class ShiftOut(BaseModel):
    id: int
    user_id: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: str
    opening_balance: float = 0.0
    closing_balance: Optional[float] = None
    expected_cash: Optional[float] = None
    notes: Optional[str] = None
    orders_count: int = 0
    total_revenue: float = 0.0

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = 'waiter'


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class StaffProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    socials: dict = {}
    dashboard_preferences: dict = {}


class StaffProfileUpdate(StaffProfileBase):
    pass


class StaffProfileOut(StaffProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class DashboardPreferences(BaseModel):
    accent: Optional[str] = None
    density: Optional[str] = None
    radius: Optional[str] = None
    glass: Optional[bool] = None
    show_metrics: Optional[bool] = None
    show_activity: Optional[bool] = None


class SocialLinks(BaseModel):
    telegram: Optional[str] = None
    instagram: Optional[str] = None
    whatsapp: Optional[str] = None
    github: Optional[str] = None
    x: Optional[str] = None
    website: Optional[str] = None


class IngredientCreate(BaseModel):
    name: str
    unit: Optional[str] = None
    quantity: float = 0.0
    threshold: float = 0.0


class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[float] = None
    threshold: Optional[float] = None


class IngredientOut(IngredientCreate):
    id: int

    class Config:
        from_attributes = True
