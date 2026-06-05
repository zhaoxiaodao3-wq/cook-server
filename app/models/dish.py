from sqlalchemy import ForeignKey, Integer, Numeric, SmallInteger, String, Text, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Dish(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dishes"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    cover: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    cuisine: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    cooking_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tips: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrition: Mapped[str | None] = mapped_column(Text, nullable=True)
    suitable_for: Mapped[str | None] = mapped_column(String(128), nullable=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="published")
    avg_rating: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False, default=0.0)

    author = relationship("User", back_populates="dishes")
    category = relationship("Category", back_populates="dishes")
    ingredients = relationship("Ingredient", back_populates="dish", cascade="all, delete-orphan")
    steps = relationship("Step", back_populates="dish", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="dish", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="dish", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="dish", cascade="all, delete-orphan")

    @property
    def rating_count(self) -> int:
        if "ratings" in inspect(self).unloaded:
            return 0
        return len(self.ratings) if self.ratings else 0
