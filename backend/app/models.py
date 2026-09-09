from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship, declarative_base
import enum
import datetime

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    admin = "admin"
    cashier = "cashier"
    waiter = "waiter"
    chef = "chef"


class OrderStatus(str, enum.Enum):
    new = "new"
    kitchen = "kitchen"
    ready = "ready"
    paid = "paid"
    cancelled = "cancelled"


class ShiftStatus(str, enum.Enum):
    open = "open"
    closed = "closed"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    card = "card"
    other = "other"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=RoleEnum.waiter.value)
    is_active = Column(Boolean, default=True)
    
    profile = relationship("StaffProfile", back_populates="user", uselist=False)
    shifts = relationship("Shift", back_populates="user", foreign_keys="Shift.user_id")


class StaffProfile(Base):
    __tablename__ = "staff_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    position = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    avatar = Column(String, nullable=True)
    socials = Column(Text, nullable=True, default="{}")
    dashboard_preferences = Column(Text, nullable=True, default="{}")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="profile")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String, index=True)
    image = Column(String, nullable=True)
    available = Column(Boolean, default=True)
    
    order_items = relationship("OrderItem", back_populates="menu_item")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default=OrderStatus.new.value, index=True)
    total = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=True, index=True)
    payment_method = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    items = relationship("OrderItem", back_populates="order", lazy="selectin")
    table = relationship("Table", back_populates="orders")
    user = relationship("User")
    shift = relationship("Shift", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    qty = Column(Integer, default=1)
    price = Column(Float, default=0.0)
    
    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")

    @property
    def name(self):
        if self.menu_item is not None:
            return self.menu_item.name
        return None


class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    seats = Column(Integer, default=4)
    zone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="table")
    bookings = relationship(
        "TableBooking",
        back_populates="table",
        foreign_keys="TableBooking.table_id",
        cascade="all, delete-orphan",
    )


class TableBooking(Base):
    __tablename__ = "table_bookings"
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False, index=True)
    linked_table_id = Column(Integer, ForeignKey("tables.id"), nullable=True, index=True)
    customer_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    guests = Column(Integer, default=1)
    starts_at = Column(DateTime, nullable=False, index=True)
    ends_at = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String, default="confirmed", index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    table = relationship("Table", primaryjoin="TableBooking.table_id==Table.id", back_populates="bookings")
    linked_table = relationship("Table", primaryjoin="TableBooking.linked_table_id==Table.id")


class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default=ShiftStatus.open.value, index=True)
    opening_balance = Column(Float, default=0.0)
    closing_balance = Column(Float, nullable=True)
    expected_cash = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User")
    orders = relationship("Order", back_populates="shift")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")


class Ingredient(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    unit = Column(String)
    quantity = Column(Float, default=0.0)
    threshold = Column(Float, default=0.0)
