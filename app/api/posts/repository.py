from math import ceil

from app.models import PostORM, AuthorORM, TagORM
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()
    
    def search(self, query: Optional[str], per_page: int, page: int, order_by: str, direction: str) -> tuple[int, list[PostORM]]:
        results = select(PostORM)

        # Filtrado
        if query:
            results = results.where(PostORM.title.ilike(f'%{query}%'))

        # Obteniendo variables para hacer calculos
        total = self.db.scalar(select(func.count()).select_from(
            results.subquery())) or 0
        
        if total == 0:
            return (0, [])
        total_pages = ceil(total/per_page)

        current_page = min(page, max(1, total_pages))

        # Ordenamiento
        order_col = PostORM.id if order_by == 'id' else func.lower(PostORM.title)
        results = results.order_by(
            order_col.asc() if direction == 'asc' else order_col.desc())

        # Paginacion(Slicing) - Items
        start = (current_page - 1) * per_page
        query_sql = results.limit(per_page).offset(
            start)

        items: list[PostORM] = list(self.db.execute(query_sql).scalars().all())
        
        return (total, items)
    
    def by_tags(self, tags: list[str]) -> list[PostORM]:
        post_list = (
        select(PostORM)
        .options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author),
        )
        .where(PostORM.tags.any(func.lower(TagORM.name).in_(tags)))
        .order_by(PostORM.id.asc())
        )

        posts: list[PostORM] = list(self.db.execute(post_list).scalars().all())
        return posts
    
    def ensure_author(self, name: str, email: str) -> AuthorORM:
        author_obj = self.db.execute(select(AuthorORM).where(
            AuthorORM.email == email)).scalar_one_or_none()

        if not author_obj:
            author_obj = AuthorORM(
                name=name, email=email)
            self.db.add(author_obj)
            self.db.flush()  # Sirve para asignar el id antes de hacer el commit. Solo para asegurarnos de que tenga un id

        return author_obj

    def ensure_tag(self, tag_name: str) -> TagORM:
        tag_obj = self.db.execute(select(TagORM).where(
            TagORM.name.ilike(tag_name))).scalar_one_or_none()

        if not tag_obj:
            tag_obj = TagORM(name=tag_name)
            self.db.add(tag_obj)
            self.db.flush()

        return tag_obj
    
    def create_post(self, title: str, content: str, tags: list[dict], author: dict[str, str]):
        
        author_obj = None
        if author:
            author_obj = self.ensure_author(author["name"], author["email"])

        post: PostORM = PostORM(title= title, content=content, author=author_obj)

        for tag in tags:
            tag_obj = self.ensure_tag(tag["name"])
            post.tags.append(tag_obj)

        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)
        return post
    
    
    # Esta opcion es la que vamos a estar ocupando normalmente
    def update_post(self, post: PostORM, updates: dict[str, str])-> PostORM:
        for key, value in updates.items():
            setattr(post, key, value)

        self.db.add(post)
        self.db.refresh(post)
        return post

    
    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)
