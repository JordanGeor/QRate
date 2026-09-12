from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, default="owner", nullable=False)  # superadmin ή owner
    is_active = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    restaurants = relationship("Restaurant", back_populates="owner")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    slug = Column(String, unique=True, index=True, nullable=False)

    name_el = Column(String, nullable=False)
    name_en = Column(String, nullable=True)

    address_el = Column(String, nullable=True)
    address_en = Column(String, nullable=True)

    phone = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

    google_review_url = Column(String, nullable=True)

    manager_contact_url = Column(String, nullable=True)
    manager_contacts_json = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="restaurants")

    categories = relationship(
        "MenuCategory",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    items = relationship(
        "MenuItem",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    reviews = relationship(
        "Review",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    contact_requests = relationship(
        "ContactRequest",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"

    id = Column(Integer, primary_key=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    name = Column(String(100), nullable=False)

    token = Column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant")

class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    sort_order = Column(Integer, default=0)

    name_el = Column(String, nullable=False)
    name_en = Column(String, nullable=True)

    restaurant = relationship(
        "Restaurant",
        back_populates="categories",
    )

    items = relationship(
        "MenuItem",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("menu_categories.id"),
        nullable=False,
    )

    sort_order = Column(Integer, default=0)

    name_el = Column(String, nullable=False)
    name_en = Column(String, nullable=True)

    description_el = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)

    price = Column(Float, default=0.0)

    is_available = Column(Boolean, default=True, nullable=False)

    restaurant = relationship(
        "Restaurant",
        back_populates="items",
    )

    category = relationship(
        "MenuCategory",
        back_populates="items",
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
    )

    table_id = Column(
        Integer,
        ForeignKey("restaurant_tables.id"),
        nullable=True,
    )

    table = relationship("RestaurantTable")

    rating = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)

    google_clicked_at = Column(DateTime, nullable=True)
    google_tracking_enabled = Column(Boolean, default=True, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship(
        "Restaurant",
        back_populates="reviews",
    )

    contact_requests = relationship(
        "ContactRequest",
        back_populates="review",
        cascade="all, delete-orphan",
    )


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True)

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True,
    )

    review_id = Column(
        Integer,
        ForeignKey("reviews.id"),
        nullable=True,
        index=True,
    )

    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    message = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_handled = Column(Boolean, default=False, nullable=False, index=True)

    restaurant = relationship(
        "Restaurant",
        back_populates="contact_requests",
    )

    review = relationship(
        "Review",
        back_populates="contact_requests",
    )