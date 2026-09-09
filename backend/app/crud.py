import json
import os
import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
import redis.asyncio as aioredis
from passlib.context import CryptContext
from sqlalchemy.orm import selectinload
from . import realtime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def _publish_redis(channel: str, payload: str):
    """Publish a payload to Redis, closing the client to avoid connection leaks."""
    client = None
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(redis_url)
        await client.publish(channel, payload)
    except Exception:
        pass
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass


async def list_menu_items(db: AsyncSession):
    q = await db.execute(select(models.MenuItem))
    return q.scalars().all()


async def delete_menu_item(db: AsyncSession, item_id: int):
    item = await db.get(models.MenuItem, item_id)
    if not item:
        return False
    from app.models import OrderItem
    for oi in (await db.execute(select(OrderItem).where(OrderItem.menu_item_id == item_id))).scalars().all():
        await db.delete(oi)
    await db.delete(item)
    await db.commit()
    return True


async def create_menu_item(db: AsyncSession, item: schemas.MenuItemCreate, image_path: Optional[str] = None):
    data = item.dict()
    if image_path:
        data['image'] = image_path
    db_item = models.MenuItem(**data)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def update_menu_item(db: AsyncSession, item_id: int, item: schemas.MenuItemUpdate, image_path: Optional[str] = None):
    db_item = await db.get(models.MenuItem, item_id)
    if not db_item:
        return None
    data = item.dict(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            setattr(db_item, k, v)
    if image_path:
        old = db_item.image
        db_item.image = image_path
        if old:
            try:
                old_file = old.lstrip('/')
                if os.path.exists(old_file):
                    os.remove(old_file)
            except Exception:
                pass
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def create_order(db: AsyncSession, order_in: schemas.OrderCreate, user_id: Optional[int] = None):
    items = order_in.items
    total = 0.0
    order = models.Order(total=0.0, notes=order_in.notes, table_id=order_in.table_id, user_id=user_id)
    db.add(order)
    await db.flush()

    # auto-bind to active shift of user if present
    if user_id:
        shift = await active_shift_for_user(db, user_id)
        if shift:
            order.shift_id = shift.id

    for it in items:
        menu = await db.get(models.MenuItem, it.menu_item_id)
        if not menu:
            await db.rollback()
            raise HTTPException(status_code=404, detail=f"Позиция меню {it.menu_item_id} не найдена")
        price = menu.price if menu else 0.0
        oi = models.OrderItem(order_id=order.id, menu_item_id=it.menu_item_id, qty=it.qty, price=price)
        total += price * it.qty
        db.add(oi)
    order.total = total

    if order_in.payment_method:
        order.status = models.OrderStatus.paid.value
        order.payment_method = order_in.payment_method
        order.paid_at = datetime.datetime.utcnow()
        order.closed_at = datetime.datetime.utcnow()

    await db.commit()
    # Re-fetch with items (and their menu items) eagerly loaded for response serialization
    order = await get_order(db, order.id)

    await add_audit_log(db, user_id, "order_create", "order", order.id, f"Создан заказ №{order.id} на сумму {total}")

    # broadcast to connected websocket clients (in-process)
    try:
        await realtime.broadcast(json.dumps({"order_id": order.id, "status": order.status, "total": order.total}, ensure_ascii=False))
    except Exception:
        pass

    # publish to redis
    try:
        await _publish_redis("orders", json.dumps({"order_id": order.id, "status": order.status, "total": order.total}))
    except Exception:
        pass

    return order


async def list_orders(db: AsyncSession, limit: int = 100, offset: int = 0, statuses: Optional[list[str]] = None, table_id: Optional[int] = None):
    q = select(models.Order)
    if statuses:
        q = q.where(models.Order.status.in_(statuses))
    if table_id is not None:
        q = q.where(models.Order.table_id == table_id)
    q = (
        q.options(selectinload(models.Order.items).selectinload(models.OrderItem.menu_item))
        .order_by(models.Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    return res.scalars().all()


async def get_order(db: AsyncSession, order_id: int):
    q = await db.execute(
        select(models.Order)
        .options(selectinload(models.Order.items).selectinload(models.OrderItem.menu_item))
        .where(models.Order.id == order_id)
    )
    return q.scalars().first()


async def update_order_status(db: AsyncSession, order_id: int, status: str, payment_method: Optional[str] = None, actor_id: Optional[int] = None):
    order = await db.get(models.Order, order_id)
    if not order:
        return None
    order.status = status
    if payment_method:
        order.payment_method = payment_method
    if status == models.OrderStatus.paid.value:
        order.paid_at = datetime.datetime.utcnow()
        order.closed_at = datetime.datetime.utcnow()
    await db.commit()
    # Re-fetch with items eagerly loaded for response serialization
    order = await get_order(db, order.id)
    await add_audit_log(db, actor_id, f"order_{status}", "order", order.id, f"Заказ №{order.id} переведён в статус {status}")

    # broadcast to connected websocket clients (in-process)
    try:
        await realtime.broadcast(json.dumps({"order_id": order.id, "status": order.status, "total": order.total}, ensure_ascii=False))
    except Exception:
        pass

    return order


# ------------------- Tables -------------------

async def list_tables(db: AsyncSession):
    q = await db.execute(select(models.Table).order_by(models.Table.number))
    return q.scalars().all()


async def create_table(db: AsyncSession, table: schemas.TableCreate):
    data = table.dict()
    if not data.get("number"):
        data["number"] = await _next_table_number(db)
    db_table = models.Table(**data)
    db.add(db_table)
    await db.commit()
    await db.refresh(db_table)
    return db_table


async def _next_table_number(db: AsyncSession):
    res = await db.execute(select(models.Table.number))
    used = {n for n in res.scalars().all() if n and n.isdigit()}
    n = 1
    while str(n) in used:
        n += 1
    return str(n)


async def update_table(db: AsyncSession, table_id: int, patch: schemas.TableUpdate):
    table = await db.get(models.Table, table_id)
    if not table:
        return None
    data = patch.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(table, k, v)
    await db.commit()
    await db.refresh(table)
    return table


async def delete_table(db: AsyncSession, table_id: int):
    table = await db.get(models.Table, table_id)
    if not table:
        return False
    # Unlink historical orders so the FK constraint doesn't block deletion.
    for o in (await db.execute(select(models.Order).where(models.Order.table_id == table_id))).scalars().all():
        o.table_id = None
    await db.delete(table)
    await db.commit()
    return True


# ------------------- Table bookings (reservations) -------------------

async def _booking_overlap(db: AsyncSession, table_ids: list[int], starts_at, ends_at, exclude_id: Optional[int] = None):
    q = select(models.TableBooking).where(
        or_(
            models.TableBooking.table_id.in_(table_ids),
            models.TableBooking.linked_table_id.in_(table_ids),
        ),
        models.TableBooking.status == "confirmed",
        models.TableBooking.starts_at < ends_at,
        models.TableBooking.ends_at > starts_at,
    )
    if exclude_id is not None:
        q = q.where(models.TableBooking.id != exclude_id)
    res = await db.execute(q)
    return res.scalars().first()


def _table_capacity(db: AsyncSession, table: models.Table) -> int:
    return table.seats if table.seats else 4


async def _validate_booking(db: AsyncSession, table: models.Table, linked: Optional[models.Table], guests: int, starts, ends, exclude_id: Optional[int] = None):
    table_ids = [table.id]
    capacity = _table_capacity(db, table)
    if linked:
        table_ids.append(linked.id)
        capacity += _table_capacity(db, linked)
    if guests > capacity:
        raise HTTPException(
            status_code=422,
            detail=f"Слишком много гостей для выбранных столиков — можно разместить не больше {capacity}",
        )
    if await _booking_overlap(db, table_ids, starts, ends, exclude_id=exclude_id):
        raise HTTPException(status_code=409, detail="Столик уже забронирован на это время")


async def list_bookings(db: AsyncSession, upcoming_only: bool = False):
    q = select(models.TableBooking)
    if upcoming_only:
        q = q.where(models.TableBooking.starts_at >= datetime.datetime.utcnow())
    q = q.order_by(models.TableBooking.starts_at.asc())
    res = await db.execute(q)
    return res.scalars().all()


async def create_table_booking(db: AsyncSession, payload: schemas.TableBookingCreate):
    table = await db.get(models.Table, payload.table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Столик не найден")
    linked = None
    if payload.linked_table_id:
        if payload.linked_table_id == payload.table_id:
            raise HTTPException(status_code=422, detail="Доп. столик не должен совпадать с основным")
        linked = await db.get(models.Table, payload.linked_table_id)
        if not linked:
            raise HTTPException(status_code=404, detail="Доп. столик не найден")
    starts = payload.starts_at.replace(tzinfo=None)
    ends = (payload.ends_at or (starts + datetime.timedelta(hours=2))).replace(tzinfo=None)
    if ends <= starts:
        raise HTTPException(status_code=422, detail="Конец брони должен быть позже начала")
    await _validate_booking(db, table, linked, payload.guests, starts, ends)
    booking = models.TableBooking(
        table_id=payload.table_id,
        linked_table_id=payload.linked_table_id,
        customer_name=payload.customer_name,
        phone=payload.phone,
        guests=payload.guests,
        starts_at=starts,
        ends_at=ends,
        note=payload.note,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def update_table_booking(db: AsyncSession, booking_id: int, patch: schemas.TableBookingUpdate):
    booking = await db.get(models.TableBooking, booking_id)
    if not booking:
        return None
    data = patch.dict(exclude_unset=True)
    table_id = data.get("table_id", booking.table_id)
    linked_id = data.get("linked_table_id", booking.linked_table_id)
    table = await db.get(models.Table, table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Столик не найден")
    linked = None
    if linked_id:
        if linked_id == table_id:
            raise HTTPException(status_code=422, detail="Доп. столик не должен совпадать с основным")
        linked = await db.get(models.Table, linked_id)
        if not linked:
            raise HTTPException(status_code=404, detail="Доп. столик не найден")
    guests = data.get("guests", booking.guests)
    starts = (data.get("starts_at") or booking.starts_at).replace(tzinfo=None)
    ends = (data.get("ends_at") or booking.ends_at or (starts + datetime.timedelta(hours=2))).replace(tzinfo=None)
    if ends <= starts:
        raise HTTPException(status_code=422, detail="Конец брони должен быть позже начала")
    await _validate_booking(db, table, linked, guests, starts, ends, exclude_id=booking.id)
    for k, v in data.items():
        if v is not None:
            setattr(booking, k, v)
    booking.table_id = data.get("table_id", booking.table_id)
    booking.linked_table_id = data.get("linked_table_id", booking.linked_table_id)
    booking.starts_at = starts
    booking.ends_at = ends
    await db.commit()
    await db.refresh(booking)
    return booking


async def delete_table_booking(db: AsyncSession, booking_id: int):
    booking = await db.get(models.TableBooking, booking_id)
    if not booking:
        return False
    await db.delete(booking)
    await db.commit()
    return True


# ------------------- Shifts -------------------

async def active_shift_for_user(db: AsyncSession, user_id: int):
    q = await db.execute(
        select(models.Shift).where(
            models.Shift.user_id == user_id,
            models.Shift.status == models.ShiftStatus.open.value,
        )
    )
    return q.scalars().first()


async def open_shift(db: AsyncSession, user_id: int, payload: schemas.ShiftOpen):
    existing = await active_shift_for_user(db, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="У пользователя уже есть открытая смена")
    shift = models.Shift(
        user_id=user_id,
        opening_balance=payload.opening_balance,
        notes=payload.notes,
    )
    db.add(shift)
    await db.commit()
    await db.refresh(shift)
    await add_audit_log(db, user_id, "shift_open", "shift", shift.id, "Открыта смена")
    return shift


async def close_shift(db: AsyncSession, user_id: int, payload: schemas.ShiftClose):
    shift = await active_shift_for_user(db, user_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Нет открытой смены")

    # compute revenue from orders in this shift (paid only)
    q = await db.execute(
        select(models.Order).where(
            models.Order.shift_id == shift.id,
            models.Order.status == models.OrderStatus.paid.value,
        )
    )
    paid_orders = q.scalars().all()
    total_revenue = sum((o.total or 0) for o in paid_orders)

    shift.ended_at = datetime.datetime.utcnow()
    shift.status = models.ShiftStatus.closed.value
    shift.closing_balance = payload.closing_balance
    shift.expected_cash = payload.expected_cash if payload.expected_cash is not None else (shift.opening_balance + total_revenue)
    if payload.notes:
        shift.notes = payload.notes
    await db.commit()
    await db.refresh(shift)
    await add_audit_log(db, user_id, "shift_close", "shift", shift.id, f"Закрыта смена, выручка {total_revenue}")
    shifts = await _shift_out(db, shift)
    return shifts


async def list_shifts(db: AsyncSession, user_id: Optional[int] = None):
    q = select(models.Shift).order_by(models.Shift.started_at.desc())
    if user_id:
        q = q.where(models.Shift.user_id == user_id)
    res = await db.execute(q)
    shifts = res.scalars().all()
    return [await _shift_out(db, s) for s in shifts]


async def _shift_out(db: AsyncSession, shift: models.Shift):
    q = await db.execute(
        select(models.Order).where(
            models.Order.shift_id == shift.id,
            models.Order.status == models.OrderStatus.paid.value,
        )
    )
    paid_orders = q.scalars().all()
    total_revenue = sum((o.total or 0) for o in paid_orders)
    # copy fields into a dict-like namespace for OrderOut-less output
    shift.orders_count = len(paid_orders)
    shift.total_revenue = round(total_revenue, 2)
    return shift


# ------------------- Audit log -------------------

async def add_audit_log(db: AsyncSession, user_id: Optional[int], action: str, entity: Optional[str] = None, entity_id: Optional[int] = None, detail: Optional[str] = None):
    log = models.AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, detail=detail)
    db.add(log)
    await db.commit()
    return log


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    q = await db.execute(select(models.User).where(models.User.email == email))
    return q.scalars().first()


async def create_user(db: AsyncSession, user: schemas.UserCreate):
    existing = await get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    hashed = get_password_hash(user.password)
    db_user = models.User(email=user.email, full_name=user.full_name, hashed_password=hashed, role=user.role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    await ensure_profile(db, db_user.id)
    return db_user


async def update_user(db: AsyncSession, user_id: int, patch: schemas.UserUpdate):
    user = await db.get(models.User, user_id)
    if not user:
        return None
    data = patch.dict(exclude_unset=True)
    if "email" in data and data["email"]:
        existing = await get_user_by_email(db, data["email"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=409, detail="Email already registered")
    for k, v in data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int):
    user = await db.get(models.User, user_id)
    if not user:
        return False

    # Keep order history: unlink orders from the removed user.
    for o in (await db.execute(select(models.Order).where(models.Order.user_id == user_id))).scalars().all():
        o.user_id = None
    for s in (await db.execute(select(models.Shift).where(models.Shift.user_id == user_id))).scalars().all():
        await db.delete(s)
    profile = (await db.execute(select(models.StaffProfile).where(models.StaffProfile.user_id == user_id))).scalars().first()
    if profile:
        await db.delete(profile)
    await db.delete(user)
    await db.commit()
    return True


async def list_users(db: AsyncSession):
    q = await db.execute(select(models.User))
    return q.scalars().all()


def _parse_json(text: Optional[str], default: dict | None = None) -> dict:
    default = default or {}
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


def _dump_json(data: dict) -> str:
    return json.dumps(data or {}, ensure_ascii=False)


async def ensure_profile(db: AsyncSession, user_id: int):
    q = await db.execute(select(models.StaffProfile).where(models.StaffProfile.user_id == user_id))
    profile = q.scalars().first()
    if profile:
        return profile
    profile = models.StaffProfile(user_id=user_id, socials="{}", dashboard_preferences="{}")
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_profile_by_user_id(db: AsyncSession, user_id: int):
    q = await db.execute(select(models.StaffProfile).where(models.StaffProfile.user_id == user_id))
    profile = q.scalars().first()
    if not profile:
        profile = await ensure_profile(db, user_id)
    return profile


async def update_profile(db: AsyncSession, user_id: int, payload: schemas.StaffProfileUpdate):
    profile = await get_profile_by_user_id(db, user_id)
    user = await db.get(models.User, user_id)
    if user and payload.full_name is not None:
        user.full_name = payload.full_name
    profile.phone = payload.phone
    profile.city = payload.city
    profile.position = payload.position
    profile.bio = payload.bio
    profile.avatar = payload.avatar
    profile.socials = _dump_json(payload.socials)
    profile.dashboard_preferences = _dump_json(payload.dashboard_preferences)
    await db.commit()
    await db.refresh(profile)
    return profile


async def merge_dashboard_preferences(db: AsyncSession, user_id: int, patch: dict):
    profile = await get_profile_by_user_id(db, user_id)
    current = _parse_json(profile.dashboard_preferences, {})
    current.update({k: v for k, v in patch.items() if v is not None})
    profile.dashboard_preferences = _dump_json(current)
    await db.commit()
    await db.refresh(profile)
    return profile


async def merge_social_links(db: AsyncSession, user_id: int, patch: dict):
    profile = await get_profile_by_user_id(db, user_id)
    current = _parse_json(profile.socials, {})
    current.update({k: v for k, v in patch.items() if v is not None})
    profile.socials = _dump_json(current)
    await db.commit()
    await db.refresh(profile)
    return profile


async def profile_to_dict(profile: models.StaffProfile):
    # Avoid lazy-loading relationship attribute in async session
    user = profile.user if 'user' in profile.__dict__ else None
    full_name = None
    if user:
        try:
            full_name = user.full_name
        except Exception:
            full_name = None
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": full_name,
        "phone": profile.phone,
        "city": profile.city,
        "position": profile.position,
        "bio": profile.bio,
        "avatar": profile.avatar,
        "socials": _parse_json(profile.socials, {}),
        "dashboard_preferences": _parse_json(profile.dashboard_preferences, {}),
    }


async def list_ingredients(db: AsyncSession):
    q = await db.execute(select(models.Ingredient))
    return q.scalars().all()


async def create_ingredient(db: AsyncSession, ing: schemas.IngredientCreate):
    db_ing = models.Ingredient(**ing.dict())
    db.add(db_ing)
    await db.commit()
    await db.refresh(db_ing)
    return db_ing


async def update_ingredient(db: AsyncSession, ing_id: int, patch: schemas.IngredientUpdate):
    ing = await db.get(models.Ingredient, ing_id)
    if not ing:
        return None
    data = patch.dict(exclude_unset=True)
    for k, v in data.items():
        if v is not None:
            setattr(ing, k, v)
    await db.commit()
    await db.refresh(ing)
    return ing


async def delete_ingredient(db: AsyncSession, ing_id: int):
    ing = await db.get(models.Ingredient, ing_id)
    if not ing:
        return False
    await db.delete(ing)
    await db.commit()
    return True


async def adjust_ingredient_quantity(db: AsyncSession, ing_id: int, delta: float):
    ing = await db.get(models.Ingredient, ing_id)
    if not ing:
        return None
    ing.quantity = float(ing.quantity) + float(delta)
    await db.commit()
    await db.refresh(ing)

    # publish low-stock notification
    try:
        if ing.quantity <= ing.threshold:
            await _publish_redis("inventory", json.dumps({"ingredient_id": ing.id, "low": True, "qty": ing.quantity}))
    except Exception:
        pass

    return ing


async def get_dashboard_stats(db: AsyncSession):
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)

    orders = (await db.execute(select(models.Order))).scalars().all()

    def _revenue(start, end=None):
        return sum(
            (o.total or 0) for o in orders
            if o.created_at and o.created_at >= start and (end is None or o.created_at < end)
        )

    revenue_today = _revenue(today_start)
    revenue_month = _revenue(month_start)
    orders_today = sum(
        1 for o in orders if o.created_at and o.created_at >= today_start
    )
    avg_check = round(revenue_today / orders_today, 2) if orders_today else 0.0
    if avg_check <= 0 and orders:
        avg_check = round(revenue_month / len(orders), 2)

    week_labels = []
    week_values = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_next = day + timedelta(days=1)
        week_labels.append(day.strftime("%a"))
        week_values.append(round(_revenue(day, day_next), 2))

    month_labels = []
    month_values = []
    month_days = (now.replace(day=28) + timedelta(days=4)).day
    bucket = 5
    start = month_start
    while start < now:
        end = start + timedelta(days=bucket)
        if end > now:
            end = now
        month_labels.append(f"{start.day}-{end.day}")
        month_values.append(round(_revenue(start, end), 2))
        start = end

    low_stock = (await db.execute(select(models.Ingredient))).scalars().all()
    low_stock = [
        {"name": i.name, "unit": i.unit, "quantity": i.quantity, "threshold": i.threshold}
        for i in low_stock if i.quantity <= i.threshold
    ]

    oi_rows = (await db.execute(
        select(
            models.OrderItem.price,
            models.OrderItem.qty,
            models.MenuItem.name,
            models.MenuItem.category,
            models.Order.created_at,
        )
        .join(models.MenuItem, models.OrderItem.menu_item_id == models.MenuItem.id)
        .join(models.Order, models.OrderItem.order_id == models.Order.id)
        .where(models.Order.created_at.isnot(None))
    )).all()

    qty_by_item = {}
    rev_by_cat = {}
    for price, qty, name, cat, created_at in oi_rows:
        qty = qty or 1
        qty_by_item[name] = qty_by_item.get(name, 0) + qty
        rev = (price or 0) * qty
        c = cat or "Прочее"
        rev_by_cat[c] = rev_by_cat.get(c, 0) + rev

    top_items = [{"name": k, "qty": v} for k, v in sorted(qty_by_item.items(), key=lambda x: x[1], reverse=True)[:5]]
    revenue_by_category = [
        {"label": k, "value": round(v, 2)}
        for k, v in sorted(rev_by_cat.items(), key=lambda x: x[1], reverse=True)
    ]

    hourly = {h: 0.0 for h in range(8, 24)}
    for o in orders:
        if o.created_at and today_start <= o.created_at < today_start + timedelta(days=1):
            h = o.created_at.hour
            if 8 <= h < 24:
                hourly[h] += o.total or 0
    revenue_by_hour = [
        {"label": f"{h}:00", "value": round(hourly[h], 2)} for h in range(8, 24)
    ]

    yesterday_start = today_start - timedelta(days=1)
    revenue_yesterday = _revenue(yesterday_start, today_start)

    week_start = today_start - timedelta(days=6)
    prev_week_start = week_start - timedelta(days=7)
    this_week = _revenue(week_start, today_start + timedelta(days=1))
    prev_week = _revenue(prev_week_start, week_start)
    week_delta_pct = round((this_week - prev_week) / prev_week * 100, 1) if prev_week else 0.0
    day_delta_pct = round((revenue_today - revenue_yesterday) / revenue_yesterday * 100, 1) if revenue_yesterday else 0.0

    all_orders = len(orders)
    revenue_all = sum((o.total or 0) for o in orders)

    return {
        "revenue_today": round(revenue_today, 2),
        "revenue_yesterday": round(revenue_yesterday, 2),
        "revenue_month": round(revenue_month, 2),
        "month_goal": 500000.0,
        "month_goal_pct": round(min(revenue_month / 500000.0 * 100, 100), 1) if revenue_month else 0.0,
        "orders_today": orders_today,
        "orders_total": all_orders,
        "avg_check": avg_check,
        "revenue_all": round(revenue_all, 2),
        "week_delta_pct": week_delta_pct,
        "day_delta_pct": day_delta_pct,
        "week_labels": week_labels,
        "week_values": week_values,
        "month_labels": month_labels,
        "month_values": month_values,
        "revenue_by_hour": revenue_by_hour,
        "revenue_by_category": revenue_by_category,
        "low_stock": low_stock,
        "top_items": top_items,
    }


# ------------------- Cashier dashboard (lightweight, day-focused) -------------------

async def get_cashier_stats(db: AsyncSession):
    now = datetime.datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    paid_orders = (await db.execute(
        select(models.Order).where(
            models.Order.status == models.OrderStatus.paid.value,
            models.Order.paid_at >= today_start,
        )
    )).scalars().all()

    revenue_today = round(sum((o.total or 0) for o in paid_orders), 2)
    orders_today = len(paid_orders)
    avg_check = round(revenue_today / orders_today, 2) if orders_today else 0.0

    payment_labels = {"cash": "Наличные", "card": "Карта", "other": "Другое"}
    grouped = {}
    for o in paid_orders:
        m = o.payment_method or "other"
        group = grouped.setdefault(m, {"method": m, "label": payment_labels.get(m, m), "value": 0.0, "count": 0})
        group["value"] = round(group["value"] + (o.total or 0), 2)
        group["count"] += 1
    payments = sorted(grouped.values(), key=lambda g: g["value"], reverse=True)

    active_q = await db.execute(
        select(models.Order).where(
            models.Order.status.in_([
                models.OrderStatus.new.value,
                models.OrderStatus.kitchen.value,
                models.OrderStatus.ready.value,
            ])
        )
    )
    orders_by_table: dict = {}
    for o in active_q.scalars().all():
        if o.table_id is None:
            continue
        orders_by_table.setdefault(o.table_id, []).append(o)

    open_tables = []
    if orders_by_table:
        tables = (await db.execute(
            select(models.Table).where(models.Table.id.in_(list(orders_by_table)))
        )).scalars().all()
        for t in tables:
            rows = orders_by_table[t.id]
            open_tables.append({
                "id": t.id,
                "number": t.number,
                "name": t.name,
                "total": round(sum((o.total or 0) for o in rows), 2),
                "orders": [
                    {"order_id": o.id, "status": o.status, "total": round(o.total or 0, 2)}
                    for o in sorted(rows, key=lambda x: x.created_at or datetime.datetime.min)
                ],
            })
        open_tables.sort(key=lambda t: t["number"])

    return {
        "revenue_today": revenue_today,
        "orders_today": orders_today,
        "avg_check": avg_check,
        "payments": payments,
        "open_tables": open_tables,
    }
