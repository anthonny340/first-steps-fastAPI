from app.core.db import Base
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .post import PostORM, post_tags

class TagORM(Base):
    __tablename__ = "tags"
    # __table_args__ = (UniqueConstraint("name", name="unique_tag_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    posts: Mapped[list["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags"
    )