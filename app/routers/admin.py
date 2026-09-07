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
    return templates.TemplateResponse(
        request=request,
        name="admin_login.html",
        context={
            "error": None,
        },
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.username == username.lower().strip()
    ).first()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Λάθος στοιχεία.",
            },
        )
    if not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Ο λογαριασμός δεν έχει ενεργοποιηθεί ακόμα.",
            },
        )

    resp = RedirectResponse(url="/admin", status_code=303)
    set_login_cookie(resp, user.id)

    return resp


@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/admin/login", status_code=303)
    clear_login_cookie(resp)
    return resp


@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

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
        },
    )


@router.post("/restaurants/create")
def create_restaurant(
    request: Request,
    slug: str = Form(...),
    name_el: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    ensure_superadmin(user)

    slug = clean_slug(slug)

    if not slug:
        raise HTTPException(status_code=400, detail="Slug invalid.")

    if " " in slug:
        raise HTTPException(status_code=400, detail="Slug invalid (no spaces).")

    if db.query(Restaurant).filter(Restaurant.slug == slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists.")

    r = Restaurant(
        owner_id=None,
        slug=slug,
        name_el=name_el.strip(),
    )

    db.add(r)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)


@router.get("/users/create", response_class=HTMLResponse)
def create_user_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(db, request)
    ensure_superadmin(user)

    return templates.TemplateResponse(
        request=request,
        name="admin_user_create.html",
        context={
            "error": None,
        },
    )


@router.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    slug: str = Form(...),
    name_el: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = get_current_user(db, request)
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
            },
        )

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse(
            request=request,
            name="admin_user_create.html",
            context={
                "error": "Υπάρχει ήδη χρήστης με αυτό το email.",
            },
        )

    if db.query(Restaurant).filter(Restaurant.slug == slug).first():
     return templates.TemplateResponse(
        request=request,
        name="admin_user_create.html",
        context={
            "error": "Υπάρχει ήδη κατάστημα με αυτό το slug.",
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
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)
    ensure_superadmin(user)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    db.delete(r)
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)

@router.post("/users/{uid}/approve")
def approve_user(
    request: Request,
    uid: int,
    db: Session = Depends(get_db),
):
    admin = get_current_user(db, request)
    ensure_superadmin(admin)

    user = db.query(User).filter(User.id == uid).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()

    return RedirectResponse(url="/admin", status_code=303)


@router.get("/restaurants/{rid}", response_class=HTMLResponse)
def edit_restaurant(request: Request, rid: int, db: Session = Depends(get_db)):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    ensure_owner_or_superadmin(user, r)

    return templates.TemplateResponse(
        request=request,
        name="admin_restaurant_edit.html",
        context={
            "r": r,
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
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)

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
        },
    )


@router.post("/restaurants/{rid}/categories/create")
def create_category(
    request: Request,
    rid: int,
    name_el: str = Form(...),
    name_en: str = Form(""),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
):
    user = get_current_user(db, request)

    r = db.query(Restaurant).filter(Restaurant.id == rid).first()

    if not r:
        raise HTTPException(status_code=404)

    ensure_owner_or_superadmin(user, r)

    c = MenuCategory(
        restaurant_id=r.id,
        name_el=name_el.strip(),
        name_en=name_en.strip() or None,
        sort_order=sort_order,
    )

    db.add(c)
    db.commit()

    return RedirectResponse(url=f"/admin/restaurants/{rid}/menu", status_code=303)


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
        sort_order: int = Form(0),
        db: Session = Depends(get_db),
    ):
        user = get_current_user(db, request)

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

    it = MenuItem(
        restaurant_id=r.id,
        category_id=category_id,
        name_el=name_el.strip(),
        name_en=name_en.strip() or None,
        description_el=description_el.strip() or None,
        description_en=description_en.strip() or None,
        price=float(price),
        sort_order=sort_order,
    )

    db.add(it)
    db.commit()

    return RedirectResponse(url=f"/admin/restaurants/{rid}/menu", status_code=303)


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
