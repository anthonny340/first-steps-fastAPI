from app.core.db import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Text, TYPE_CHECKING

# Esto es para evitar importaciones circulares, porque AuthorORM y TagORM necesitan importar PostORM y viceversa,
# entonces se usa TYPE_CHECKING para que solo se importe en tiempo de chequeo de tipos y no en tiempo de ejecución. 
# Esto es necesario porque si se importan normalmente, se generaría un ciclo de importación que causaría errores.
if TYPE_CHECKING:
    from .author import AuthorORM
    from .tag import TagORM

post_tags = Table(
    "posts_tags",
    Base.metadata,

    Column(
        "post_id",
        ForeignKey("posts.id"),
        primary_key=True
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id"),
        primary_key=True,
    ),
)

class PostORM(Base):
    __tablename__ = 'posts'
    __table_args__ = (UniqueConstraint("title", name="unique_post_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now())

    author: Mapped[Optional["AuthorORM"]] = relationship(
        back_populates='posts',)
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("authors.id"), nullable=True)

    tags: Mapped[list["TagORM"]] = relationship(
        secondary=post_tags,
        back_populates="posts"
    )