import os
from ..models import Restaurant, MenuCategory, MenuItem, Review, ContactRequest
from ..utils.mail import send_email
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_lang(request: Request) -> str:
    lang = request.query_params.get("lang", "el").lower()
    return lang if lang in {"el", "en"} else "el"


def tr(lang: str, el: str, en: str) -> str:
    return en if (lang == "en" and en) else el


def get_restaurant(db: Session, slug: str) -> Restaurant:
    r = (
        db.query(Restaurant)
        .filter(Restaurant.slug == slug, Restaurant.is_active == True)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return r


@router.get("/r/{slug}", response_class=HTMLResponse)
def info_page(request: Request, slug: str, db: Session = Depends(get_db)):
    lang = get_lang(request)
    r = get_restaurant(db, slug)
    return templates.TemplateResponse(
        "public_info.html",
        {"request": request, "r": r, "lang": lang, "tr": tr},
    )


@router.get("/r/{slug}/menu", response_class=HTMLResponse)
def menu_page(request: Request, slug: str, db: Session = Depends(get_db)):
    lang = get_lang(request)
    r = get_restaurant(db, slug)

    categories = (
        db.query(MenuCategory)
        .filter(MenuCategory.restaurant_id == r.id)
        .order_by(MenuCategory.sort_order.asc())
        .all()
    )

    items_by_cat = {}
    for c in categories:
        items_by_cat[c.id] = (
            db.query(MenuItem)
            .filter(MenuItem.category_id == c.id, MenuItem.is_available == True)
            .order_by(MenuItem.sort_order.asc())
            .all()
        )

    return templates.TemplateResponse(
        "public_menu.html",
        {
            "request": request,
            "r": r,
            "lang": lang,
            "tr": tr,
            "categories": categories,
            "items_by_cat": items_by_cat,
        },
    )


@router.get("/r/{slug}/review", response_class=HTMLResponse)
def review_page(request: Request, slug: str, db: Session = Depends(get_db)):
    lang = get_lang(request)
    r = get_restaurant(db, slug)
    return templates.TemplateResponse(
        "public_review.html",
        {"request": request, "r": r, "lang": lang, "tr": tr},
    )


@router.post("/r/{slug}/review")
def submit_review(
    request: Request,
    slug: str,
    rating: int = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    lang = get_lang(request)
    r = get_restaurant(db, slug)

    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1..5")

    rev = Review(
        restaurant_id=r.id,
        rating=rating,
        notes=(notes or "").strip()[:2000],
    )

    db.add(rev)
    db.commit()
    db.refresh(rev)  # για να έχουμε rev.id

    return RedirectResponse(
        url=f"/r/{slug}/thanks?lang={lang}&rid={rev.id}",
        status_code=303,
    )


@router.get("/r/{slug}/thanks", response_class=HTMLResponse)
def thanks_page(request: Request, slug: str, db: Session = Depends(get_db)):
    lang = get_lang(request)
    r = get_restaurant(db, slug)

    google_review_url = (getattr(r, "google_review_url", None) or "").strip() or None

    rid = request.query_params.get("rid")
    review_text = ""
    rating = None
    is_negative = False

    if rid and rid.isdigit():
        rev = (
            db.query(Review)
            .filter(Review.id == int(rid), Review.restaurant_id == r.id)
            .first()
        )
        if rev:
            review_text = (rev.notes or "").strip()
            rating = rev.rating
            is_negative = (rating is not None and rating <= 3)  # ✅ 1-3 αστέρια

    contact_ok = request.query_params.get("contact") == "ok"
    
    return templates.TemplateResponse(
        "public_thanks.html",
        {
            "request": request,
            "r": r,
            "lang": lang,
            "tr": tr,
            "google_review_url": google_review_url,
            "review_text": review_text,
            "rating": rating,
            "is_negative": is_negative,
            "contact_ok": contact_ok,
        },
    )


@router.get("/r/{slug}/contact", response_class=HTMLResponse)
def contact_page(request: Request, slug: str, db: Session = Depends(get_db)):
    lang = get_lang(request)
    r = get_restaurant(db, slug)
    rid = request.query_params.get("rid", "")
    return templates.TemplateResponse(
        "public_contact.html",
        {"request": request, "r": r, "lang": lang, "tr": tr, "rid": rid},
    )


@router.post("/r/{slug}/contact")
def submit_contact(
    request: Request,
    slug: str,
    rid: str = Form(""),
    name: str = Form(""),
    email: str = Form(""),   # ✅ νέο
    phone: str = Form(""),
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    lang = get_lang(request)
    r = get_restaurant(db, slug)

    review_id = int(rid) if (rid and rid.isdigit()) else None

    # ✅ 1) Save στη DB
    cr = ContactRequest(
        restaurant_id=r.id,
        review_id=review_id,
        name=(name or "").strip()[:200] or None,
        email=(email or "").strip()[:200] or None,
        phone=(phone or "").strip()[:60] or None,
        message=(message or "").strip()[:5000] or None,
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)

    # ✅ 2) Email ειδοποίηση στον admin
    admin_email = os.getenv("ADMIN_EMAIL", "")
    subject = f"[Contact] {r.name_el} (req #{cr.id})"
    body = (
        f"Restaurant: {r.name_el} (slug: {r.slug}, id: {r.id})\n"
        f"ContactRequest ID: {cr.id}\n"
        f"Review ID: {cr.review_id}\n"
        f"Name: {cr.name}\n"
        f"Email: {cr.email}\n"
        f"Phone: {cr.phone}\n"
        f"Time: {cr.created_at}\n\n"
        f"Message:\n{cr.message}\n\n"
        f"Admin link: /admin/contacts/{cr.id}\n"
    )
    send_email(subject, body, admin_email)

    qrid = f"&rid={rid}" if (rid and rid.isdigit()) else ""
    return RedirectResponse(
        url=f"/r/{slug}/thanks?lang={lang}{qrid}&contact=ok",
        status_code=303,
    )

