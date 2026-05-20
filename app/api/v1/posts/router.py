from math import ceil
from typing import Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from .repository import PostRepository
from .schemas import PaginatedPost, PostCreate, PostUpdate, PostSummary, PostPublic
from app.models import PostORM, AuthorORM, TagORM

from app.core.db import get_db

from app.api.v1.posts import repository

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("", response_model= PaginatedPost, summary="Lista todos los posts",
         description="Devuelve una lista completa de posts disponibles. Se puede filtar por contenido del titulo.")
def list_post(
    # Esto nos ayuda a en un entorno de produccion queremos implementar otros parametros
    # seguimos manteniendo la misma funcionalidad sin embargo avisamos al cliente que pronto
    # modificaremos y eliminaremos ese parametro para que otro (mejorado) tome su lugar
    text: Optional[str] = Query(
        default=None,
        deprecated=True,  # Con esto avisamos que este campo esta por ser removido
        description='Parametro obsoleto, usa "query o search" en su lugar'
    ),
    query: Optional[str] = Query(
        default=None,
        alias='search',
        min_length=3,
        max_length=50,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚÜü-]+$",
        description='Texto para buscar por titulo'
    ),
    per_page: int = Query(
        10, ge=1, le=50, description='Numero de resultados (1-50)'
    ),
    page: int = Query(
        1, ge=1,
        description='Numero de pagina (Mayor o igual a 1)'
    ),
    order_by: Literal['id', 'title'] = Query(
        'id', description='Campo de orden'
    ),
    direction: Literal['asc', 'desc'] = Query(
        'asc', description='Direccion de orden'
    ),
    db: Session = Depends(get_db)

):
    '''
    Obtener los posts.

    :param str | None query: (Query) Texto para buscar posts por titulo.
    :return: Diccionario de posts coincidentes.
    :rtype: (dict[str, Any] | dict[str, list[dict[str, Any]]])
    '''
    repository = PostRepository(db)

    # En caso de que tengamos un parametro deprecated y no queremos afectar al funcionamiento de terceros que
    # lo usen lo queramos mantener hasta en un proximo realease eliminarlo por completo
    query = query or text

    total, posts = repository.search(query, per_page, page, order_by, direction)

    posts = [PostPublic.model_validate(post, from_attributes=True) for post in posts]

    total_pages = ceil(total/per_page) if total > 0 else 0
    current_page = 1 if total_pages == 0 else min(page, total_pages)

    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPost(
        page=current_page,
        per_page=per_page,
        total=total,
        total_page=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=posts)

# ListPostByTags
@router.get("/by-tags", response_model=list[PostPublic])
def filter_by_tags(tags: list[str] = Query(..., min_length=1, description='Una o mas etiquetas.', example='?tags=python&tags=fastapi',),
                   db: Session = Depends(get_db),):

    normalized_tag: list[str] = [tag.strip().lower()
                                 for tag in tags if tag.strip()]

    if not normalized_tag:
        return []

    repository = PostRepository(db)
    posts = repository.by_tags(normalized_tag)

    if not posts:
        raise HTTPException(status_code=404, detail='Post no encontrado')


    return [PostPublic.model_validate(post) for post in posts]


@router.get("/{post_id}", response_model=Union[PostPublic, PostSummary],response_description='Post encontrado',
         summary="Busca un post por ID",
         description="Devuelve el post encontrado. Se puede especificar si se quiere visualizar el contenido.")
def get_post(post_id: int = Path(
    ..., ge=1, title='ID del post',
    description='Identificador entero del post. Debe ser mayor a uno',
    example=1
), incluide_content: bool = Query(default=True, description='Incluir o no el contenido'), db: Session = Depends(get_db)):
    '''
    Obtener los posts por ID.

    :param int post_id: (Path) ID del post.
    :param bool incluide_content: (Query) Incluir el contentenido del post.
    :return: Diccionario de posts coincidentes.
    :rtype: (dict[str, dict[str, Any]] | dict[str, str])
    '''
    
    repository = PostRepository(db)
    post = repository.get(post_id)

    if (not post):
        raise HTTPException(status_code=404, detail='Post no encontrado')

    if incluide_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)




@router.post("", response_model=PostPublic, response_description='Post creado (OK)', status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    '''
    Crear un post.

    :param PostCreate post: Datos enviados para crear el post.
    :return: Diccionario con el post actualizado.
    :rtype: dict[str, Any]
    '''

    repository = PostRepository(db)

    try:
        new_post = repository.create_post(post.title, post.content, [tag.model_dump() for tag in post.tags], post.author.model_dump() if post.author else None)
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail='Ese titulo ya existe, pruebe otro')

    except SQLAlchemyError as e:
        print('SALTO UN ERROR TIPO SQLAlchemyError')
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail='Error al crear el post')


@router.put("/{post_id}", response_model=PostPublic, response_description='Post actualizado (OK)',
            response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    '''
    Actualiza un post existente.

    :param int post_id: ID del post a actualizar.
    :param PostUpdate data: Datos enviados para actualizar el post.
    :return: Diccionario con el post actualizado.
    :rtype: dict[str, Any]
    '''

    repository = PostRepository(db)

    # Paso 1: Obtener el post enviado por el usuario
    post = repository.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    # Paso 2: Filtrar los campos a actualizar evitando que se modifiquen campos que le usuario no ha enviado
    updates = data.model_dump(exclude_unset=True)

    try:
        # Paso 3: Actualizar el post con la nueva informacion
        updated_post = repository.update_post(post, updates)
        # Paso 4: Mandar a guardar el post actualizado a la base de datos
        db.commit()
        db.refresh(updated_post)

        return PostPublic.model_validate(post, from_attributes=True)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El titulo ya existe, debe cambiar el titulo")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar el post")


# Este codigo quiere decir que salio bien pero no vamos a regresar nada de contenido
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    '''
    Elimina un post existente.

    :param int post_id: (Path) ID del post.
    :rtype: None

    .. warning::
        Lanzara un status_code ``404``, si no se encuetra el post.
    '''

    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:
        raise HTTPException(status_code=404, detail='Post no encontrado')

    try:
        repository.delete_post(post)
        db.commit()
    except SQLAlchemyError:
        HTTPException(status_code=500, detail="Error al eliminar el post")
