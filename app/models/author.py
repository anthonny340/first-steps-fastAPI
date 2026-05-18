from app.core.db import Base
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .post import PostORM

class AuthorORM(Base):
    __tablename__ = "authors"

    # Esta es la forma mas completa de crear restricciones porque se pueden crear:
    # |_ múltiples columnas  |_ nombre custom  |_ constraints avanzados

    # __table_args__ = (UniqueConstraint("name", name="unique_author_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # unique tambien sirve para hacer restricciones simples sobre una unica columna
    email: Mapped[str] = mapped_column(String, unique=True, index=True)

    posts: Mapped[list["PostORM"]] = relationship(back_populates='author',)
