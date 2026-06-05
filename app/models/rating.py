from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class Rating(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ratings"
    __table_args__ = (UniqueConstraint("dish_id", "user_id"),)

    dish_id: Mapped[str] = mapped_column(ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    stars: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    dish = relationship("Dish", back_populates="ratings")
    user = relationship("User", back_populates="ratings")
