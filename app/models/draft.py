from sqlalchemy import ForeignKey, Integer, JSON, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Draft(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "drafts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(8), nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingredients: Mapped[list | None] = mapped_column(JSON, nullable=True)
    steps_data: Mapped[list | None] = mapped_column("steps", JSON, nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cuisine: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    crowd: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tips: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="drafts")
