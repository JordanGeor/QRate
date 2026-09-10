from sqlalchemy import func
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Restaurant, MenuCategory, MenuItem, Review, ContactRequest
from ..auth import (
    verify_password,
    hash_password,
    set_login_cookie,
    clear_login_cookie,
    get_current_user,
    get_csrf_token,
    set_csrf_cookie,
    verify_csrf_token,
)

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def ensure_superadmin(user: User):
    if user.role != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin only")


def ensure_owner_or_superadmin(user: User, restaurant: Restaurant):
    if user.role == "superadmin":
        return

    if restaurant.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")


def clean_slug(slug: str):
    return (
        slug.strip()
        .lower()
        .replace(" ", "-")
        .replace("&", "and")
        .replace("_", "-")
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    csrf_token = get_csrf_token(request)

    response = templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "error": None,
            "csrf_token": csrf_token,
        },
    )

    set_csrf_cookie(response, csrf_token)

    return response


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    verify_csrf_token(request, csrf_token)

    user = db.query(User).filter(
        User.username == username.lower().strip()
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Λάθος στοιχεία.",
                "csrf_token": csrf_token,
            },
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Ο λογαριασμός δεν έχει ενεργοποιηθεί ακόμα.",
                "csrf_token": csrf_token,
            },
        )

    resp = RedirectResponse(url="/admin", status_code=303)
    set_login_cookie(resp, user.id)

    return resp


@router.post("/logout")
def logout(
    request: Request,
    csrf_token: str = Form(...),
):
    verify_csrf_token(request, csrf_token)

    resp = RedirectResponse(url="/admin/login", status_code=303)
    clear_login_cookie(resp)
    return resp


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(db, request)
    csrf_token = get_csrf_token(request)

    if user.role == "superadmin":
        restaurants = (
            db.query(Restaurant)
            .order_by(Restaurant.created_at.desc())
            .all()
        )

        rows = (
            db.query(ContactRequest.restaurant_id, func.count(ContactRequest.id))
            .filter(ContactRequest.is_read == False)
            .group_by(ContactRequest.restaurant_id)
            .all()
        )

        pending_users = (
            db.query(User)
            .filter(User.role == "owner")
            .filter(User.is_active == False)
            .order_by(User.created_at.desc())
            .all()
        )

    else:
        restaurants = (
            db.query(Restaurant)
            .filter(Restaurant.owner_id == user.id)
            .order_by(Restaurant.created_at.desc())
            .all()
        )

        rows = (
            db.query(ContactRequest.restaurant_id, func.count(ContactRequest.id))
            .join(Restaurant, Restaurant.id == ContactRequest.restaurant_id)
            .filter(Restaurant.owner_id == user.id)
            .filter(ContactRequest.is_read == False)
            .group_by(ContactRequest.restaurant_id)
            .all()
        )

        pending_users = []

    counts_by_restaurant = {rid: cnt for rid, cnt in rows}

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "user": user,
            "restaurants": restaurants,
            "counts_by_restaurant": counts_by_restaurant,
            "pending_users": pending_users,
            "csrf_token": csrf_token,
        },
    )


@router.get("/users/create", response_class=HTMLResponse)
def create_user_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(db, request)
    ensure_superadmin(user)

    csrf_token = get_csrf_token(request)

    response = templates.TemplateResponse(
        request=request,
        name="admin_user_create.html",
        context={
            "error": None,
            "csrf_token": csrf_token,
        },
    )

    set_csrf_cookie(response, csrf_token)

    return response


@router.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    slug: str = Form(...),
    name_el: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)
    ensure_superadmin(admin)

    username = username.lower().strip()
    slug = clean_slug(slug)
    name_el = name_el.strip()

    if not slug:
        return templates.TemplateResponse(
            request=request,
            name="admin_user_create.html",
            context={
                "error": "Το slug είναι υποχρεωτικό.",
                "csrf_token": csrf_token,

            },
        )

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            request=request,
            name="admin_user_create.html",
            context={
                "error": "Υπάρχει ήδη χρήστης με αυτό το email.",
                "csrf_token": csrf_token,
            },
        )

    if db.query(Restaurant).filter(Restaurant.slug == slug).first():
     return templates.TemplateResponse(
        request=request,
        name="admin_user_create.html",
        context={
            "error": "Υπάρχει ήδη κατάστημα με αυτό το slug.",
            "csrf_token": csrf_token,
        },
    )

    owner = User(
        username=username,
        password_hash=hash_password(password),
        role="owner",
        is_active=True,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    restaurant = Restaurant(
        owner_id=owner.id,
        slug=slug,
        name_el=name_el,
    )

    db.add(restaurant)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@router.post("/restaurants/{rid}/delete")
def delete_restaurant(
    request: Request,
    rid: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)
    ensure_superadmin(user)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    db.delete(r)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)


@router.get("/restaurants/{rid}", response_class=HTMLResponse)
def edit_restaurant(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    ensure_owner_or_superadmin(user, r)
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="admin_restaurant_edit.html",
        context={
            "r": r,
            "csrf_token": csrf_token,
        },
    )


@router.post("/restaurants/{rid}/save")
def save_restaurant(
    request: Request,
    rid: int,
    name_el: str = Form(...),
    name_en: str = Form(""),
    address_el: str = Form(""),
    address_en: str = Form(""),
    phone: str = Form(""),
    logo_url: str = Form(""),
    google_review_url: str = Form(""),
    manager_contact_url: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    ensure_owner_or_superadmin(user, r)

    r.name_el = name_el.strip()
    r.name_en = name_en.strip() or None
    r.address_el = address_el.strip() or None
    r.address_en = address_en.strip() or None
    r.phone = phone.strip() or None
    r.logo_url = logo_url.strip() or None
    r.google_review_url = google_review_url.strip() or None
    r.manager_contact_url = manager_contact_url.strip() or None

    db.commit()

    return RedirectResponse(url=f"/admin/restaurants/{rid}", status_code=303)


@router.get("/restaurants/{rid}/menu", response_class=HTMLResponse)
def admin_menu(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)
    csrf_token = get_csrf_token(request)

    categories = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == r.id)
        .order_by(MenuCategory.sort_order.asc())
        .all()
    )

    items = (
        db.query(MenuItem)
        .filter(MenuItem.restaurant_id == r.id)
        .order_by(MenuItem.category_id.asc(), MenuItem.sort_order.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_menu.html",
        context={
            "r": r,
            "categories": categories,
            "items": items,
            "csrf_token": csrf_token,
        },
    )


@router.post("/restaurants/{rid}/categories/create")
def create_category(
    request: Request,
    rid: int,
    name_el: str = Form(...),
    name_en: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    last_category = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == r.id)
        .order_by(MenuCategory.sort_order.desc())
        .first()
    )

    next_sort_order = (
        last_category.sort_order + 1
        if last_category
        else 0
    )

    c = MenuCategory(
        restaurant_id=r.id,
        name_el=name_el.strip(),
        name_en=name_en.strip() or None,
        sort_order=next_sort_order,
    )

    db.add(c)
    db.commit()

    return RedirectResponse(url=f"/admin/restaurants/{rid}/menu", status_code=303)

@router.post("/restaurants/{rid}/categories/{category_id}/move")
def move_category(
    request: Request,
    rid: int,
    category_id: int,
    direction: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    category = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.id == category_id,
            MenuCategory.restaurant_id == r.id,
        )
        .first()
    )

    if not category:
        raise HTTPException(status_code=404)

    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Invalid direction")

    categories = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == r.id)
        .order_by(
            MenuCategory.sort_order.asc(),
            MenuCategory.id.asc(),
        )
        .all()
    )

    current_index = next(
        (i for i, c in enumerate(categories) if c.id == category.id),
        None,
    )

    if current_index is None:
        raise HTTPException(status_code=404)

    target_index = (
        current_index - 1
        if direction == "up"
        else current_index + 1
    )

    if 0 <= target_index < len(categories):
        categories[current_index], categories[target_index] = (
            categories[target_index],
            categories[current_index],
        )

        for index, c in enumerate(categories):
            c.sort_order = index

        db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/categories/{category_id}/delete")
def delete_category(
    request: Request,
    rid: int,
    category_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    category = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.id == category_id,
            MenuCategory.restaurant_id == r.id,
        )
        .first()
    )

    if not category:
        raise HTTPException(status_code=404)

    items_count = (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == r.id,
            MenuItem.category_id == category.id,
        )
        .count()
    )

    if items_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a category that contains items",
        )

    db.delete(category)
    db.commit()

    remaining_categories = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == r.id)
        .order_by(
            MenuCategory.sort_order.asc(),
            MenuCategory.id.asc(),
        )
        .all()
    )

    for index, c in enumerate(remaining_categories):
        c.sort_order = index

    db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/categories/{category_id}/edit")
def edit_category(
    request: Request,
    rid: int,
    category_id: int,
    name_el: str = Form(...),
    name_en: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    category = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.id == category_id,
            MenuCategory.restaurant_id == r.id,
        )
        .first()
    )

    if not category:
        raise HTTPException(status_code=404)

    category.name_el = name_el.strip()
    category.name_en = name_en.strip()

    db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/items/create")
def create_item(
    request: Request,
    rid: int,
    category_id: int = Form(...),
    name_el: str = Form(...),
    name_en: str = Form(""),
    description_el: str = Form(""),
    description_en: str = Form(""),
    price: float = Form(0.0),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    category = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.id == category_id,
            MenuCategory.restaurant_id == r.id,
        )
        .first()
    )

    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")

    last_item = (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == r.id,
            MenuItem.category_id == category_id,
        )
        .order_by(MenuItem.sort_order.desc())
        .first()
    )

    next_sort_order = (
        last_item.sort_order + 1
        if last_item
        else 0
    )

    it = MenuItem(
        restaurant_id=r.id,
        category_id=category_id,
        name_el=name_el.strip(),
        name_en=name_en.strip() or None,
        description_el=description_el.strip() or None,
        description_en=description_en.strip() or None,
        price=float(price),
        sort_order=next_sort_order,
    )

    db.add(it)
    db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/items/{item_id}/move")
def move_item(
    request: Request,
    rid: int,
    item_id: int,
    direction: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == r.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404)

    if direction not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Invalid direction")

    items = (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == r.id,
            MenuItem.category_id == item.category_id,
        )
        .order_by(
            MenuItem.sort_order.asc(),
            MenuItem.id.asc(),
        )
        .all()
    )

    current_index = next(
        (i for i, it in enumerate(items) if it.id == item.id),
        None,
    )

    if current_index is None:
        raise HTTPException(status_code=404)

    target_index = (
        current_index - 1
        if direction == "up"
        else current_index + 1
    )

    if 0 <= target_index < len(items):
        items[current_index], items[target_index] = (
            items[target_index],
            items[current_index],
        )

        for index, it in enumerate(items):
            it.sort_order = index

        db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/items/{item_id}/delete")
def delete_item(
    request: Request,
    rid: int,
    item_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == r.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404)

    category_id = item.category_id

    db.delete(item)
    db.commit()

    remaining_items = (
        db.query(MenuItem)
        .filter(
            MenuItem.restaurant_id == r.id,
            MenuItem.category_id == category_id,
        )
        .order_by(
            MenuItem.sort_order.asc(),
            MenuItem.id.asc(),
        )
        .all()
    )

    for index, it in enumerate(remaining_items):
        it.sort_order = index

    db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )

@router.post("/restaurants/{rid}/items/{item_id}/edit")
def edit_item(
    request: Request,
    rid: int,
    item_id: int,
    category_id: int = Form(...),
    name_el: str = Form(...),
    name_en: str = Form(""),
    description_el: str = Form(""),
    description_en: str = Form(""),
    price: float = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    verify_csrf_token(request, csrf_token)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    item = (
        db.query(MenuItem)
        .filter(
            MenuItem.id == item_id,
            MenuItem.restaurant_id == r.id,
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404)

    old_category_id = item.category_id

    category = (
        db.query(MenuCategory)
        .filter(
            MenuCategory.id == category_id,
            MenuCategory.restaurant_id == r.id,
        )
        .first()
    )

    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")

    if category_id != old_category_id:
        last_item = (
            db.query(MenuItem)
            .filter(
                MenuItem.restaurant_id == r.id,
                MenuItem.category_id == category_id,
            )
            .order_by(MenuItem.sort_order.desc())
            .first()
        )

        item.sort_order = (
            last_item.sort_order + 1
            if last_item
            else 0
        )

    item.category_id = category_id
    item.name_el = name_el.strip()
    item.name_en = name_en.strip()
    item.description_el = description_el.strip()
    item.description_en = description_en.strip()
    item.price = price

    if category_id != old_category_id:
        old_items = (
            db.query(MenuItem)
            .filter(
                MenuItem.restaurant_id == r.id,
                MenuItem.category_id == old_category_id,
                MenuItem.id != item.id,
            )
            .order_by(
                MenuItem.sort_order.asc(),
                MenuItem.id.asc(),
            )
            .all()
        )

        for index, old_item in enumerate(old_items):
            old_item.sort_order = index

    db.commit()

    return RedirectResponse(
        url=f"/admin/restaurants/{rid}/menu",
        status_code=303,
    )


@router.get("/restaurants/{rid}/analytics", response_class=HTMLResponse)
def admin_analytics(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    total_reviews = (
        db.query(func.count(Review.id))
        .filter(Review.restaurant_id == r.id)
        .scalar()
    ) or 0

    average_rating = (
        db.query(func.avg(Review.rating))
        .filter(Review.restaurant_id == r.id)
        .scalar()
    )

    average_rating = round(float(average_rating), 1) if average_rating is not None else 0

    positive_reviews = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating >= 4,
        )
        .scalar()
    ) or 0

    negative_reviews = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating <= 3,
        )
        .scalar()
    ) or 0

    rating_rows = (
        db.query(Review.rating, func.count(Review.id))
        .filter(Review.restaurant_id == r.id)
        .group_by(Review.rating)
        .all()
    )

    rating_counts = {i: 0 for i in range(1, 6)}

    for rating, count in rating_rows:
        if rating in rating_counts:
            rating_counts[rating] = count

    positive_percentage = (
        round((positive_reviews / total_reviews) * 100)
        if total_reviews > 0
        else 0
    )

    recent_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == r.id)
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    tracked_positive_reviews = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating >= 4,
            Review.google_tracking_enabled == True,
        )
        .scalar()
    ) or 0

    google_clicks = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating >= 4,
            Review.google_tracking_enabled == True,
            Review.google_clicked_at.isnot(None),
        )
        .scalar()
    ) or 0

    google_intent_rate = (
        round((google_clicks / tracked_positive_reviews) * 100)
        if tracked_positive_reviews > 0
        else 0
    )

    tracked_negative_reviews = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating <= 3,
            Review.google_tracking_enabled == True,
        )
        .scalar()
    ) or 0

    negative_google_clicks = (
        db.query(func.count(Review.id))
        .filter(
            Review.restaurant_id == r.id,
            Review.rating <= 3,
            Review.google_tracking_enabled == True,
            Review.google_clicked_at.isnot(None),
        )
        .scalar()
    ) or 0

    negative_containment_rate = (
        round(
            (
                (tracked_negative_reviews - negative_google_clicks)
                / tracked_negative_reviews
            )
            * 100
        )
        if tracked_negative_reviews > 0
        else 0
    )
    
    return templates.TemplateResponse(
        request=request,
        name="admin_analytics.html",
        context={
            "r": r,
            "total_reviews": total_reviews,
            "average_rating": average_rating,
            "positive_reviews": positive_reviews,
            "negative_reviews": negative_reviews,
            "rating_counts": rating_counts,
            "positive_percentage": positive_percentage,
            "recent_reviews": recent_reviews,
            "tracked_positive_reviews": tracked_positive_reviews,
            "google_clicks": google_clicks,
            "google_intent_rate": google_intent_rate,
            "tracked_negative_reviews": tracked_negative_reviews,
            "negative_google_clicks": negative_google_clicks,
            "negative_containment_rate": negative_containment_rate,
        },
    )

@router.get("/restaurants/{rid}/reviews", response_class=HTMLResponse)
def admin_reviews(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == r.id)
        .order_by(Review.created_at.desc())
        .limit(200)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_reviews.html",
        context={
            "r": r,
            "reviews": reviews,
        },
    )


@router.get("/restaurants/{rid}/contacts", response_class=HTMLResponse)
def admin_contacts(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    (
        db.query(ContactRequest)
        .filter(ContactRequest.restaurant_id == r.id)
        .filter(ContactRequest.is_read == False)
        .update({ContactRequest.is_read: True}, synchronize_session=False)
    )

    db.commit()

    contacts = (
        db.query(ContactRequest)
        .filter(ContactRequest.restaurant_id == r.id)
        .order_by(ContactRequest.created_at.desc())
        .limit(200)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_contacts.html",
        context={
            "r": r,
            "contacts": contacts,
        },
    )


@router.get("/restaurants/{rid}/contacts/{cid}", response_class=HTMLResponse)
def admin_contact_detail(
    request: Request,
    rid: int,
    cid: int,
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    cr = (
        db.query(ContactRequest)
        .filter(ContactRequest.id == cid)
        .filter(ContactRequest.restaurant_id == r.id)
        .first()
    )

    if not cr:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        request=request,
        name="admin_contact_detail.html",
        context={
            "r": r,
            "cr": cr,
        },
    )
