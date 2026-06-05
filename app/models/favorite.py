from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Favorite(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "dish_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="favorites")
    dish = relationship("Dish", back_populates="favorites")
