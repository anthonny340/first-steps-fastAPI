from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, Union, Literal
from math import ceil
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, select, func, UniqueConstraint, Table, Column
from sqlalchemy.orm import Session, Mapped, mapped_column, relationship, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from theme import dark_css
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from core.db import Base, engine, get_db

load_dotenv()

# Esto unicamnete es para nuestro entorno de desarrollo, solo va a crear las
# tablas en caso de que no exista
Base.metadata.create_all(bind=engine)  # dev

# Para produccion, no se ocupa esto, se ocupa migraciones


DARK_DOCS = True

app = FastAPI(docs_url=None if DARK_DOCS else "/docs")


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    get_swagger_response = get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title="Docs"
    )

    html = bytes(get_swagger_response.body).decode("utf-8")

    html = html.replace("</head>", f"{dark_css}</head>")

    return HTMLResponse(html)


@app.get('/')
def home():
    return {'message': 'Bienvenidos a Mini Blog por Anthonny'}


@app.get('/posts', response_model=PaginatedPost, summary="Lista todos los posts",
         description="Devuelve una lista completa de posts disponibles. Se puede filtar por contenido del titulo."
         )
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
    results = select(PostORM)

    # En caso de que tengamos un parametro deprecated y no queremos afectar al funcionamiento de terceros que
    # lo usen lo queramos mantener hasta en un proximo realease eliminarlo por completo
    query = query or text

    # Filtrado
    if query:
        results = results.where(PostORM.title.ilike(f'%{query}%'))

    # Obteniendo variables para hacer calculos
    total = db.scalar(select(func.count()).select_from(
        results.subquery())) or 0
    total_pages = ceil(total/per_page) if total > 0 else 0

    current_page = 1 if total_pages == 0 else min(page, total_pages)
    if total_pages == 0:
        current_page = 1
    else:
        current_page = min(page, total_pages)

    # Ordenamiento
    if order_by == 'id':
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results = results.order_by(
        order_col.asc() if direction == 'asc' else order_col.desc())

    # Paginacion(Slicing) - Items
    if total_pages == 0:
        items: list[PostPublic] = []
    else:
        start = (current_page - 1) * per_page
        query_sql = results.limit(per_page).offset(
            start)

        items = [
            PostPublic.model_validate(post, from_attributes=True)
            for post in db.execute(query_sql).scalars().all()
        ]

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
        items=items)


@app.get('/post/by-tags', response_model=list[PostPublic])
def filter_by_tags(tags: list[str] = Query(..., min_length=1, description='Una o mas etiquetas.', example='?tags=python&tags=fastapi',),
                   db: Session = Depends(get_db),):

    normalized_tag: list[str] = [tag.strip().lower()
                                 for tag in tags if tag.strip()]

    if not normalized_tag:
        return []

    post_list = (
        select(PostORM)
        .options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author),
        )
        .where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag)))
        .order_by(PostORM.id.asc())
    )

    posts = db.execute(post_list).scalars().all()

    return [PostPublic.model_validate(post) for post in posts]


@app.get('/posts/{post_id}', response_model=Union[PostPublic, PostSummary],
         response_description='Post encontrado',
         summary="Busca un post por ID",
         description="Devuelve el post encontrado. Se puede especificar si se quiere visualizar el contenido."
         )
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
    # post = db.get(PostORM, post_id) #Opcion 1

    # Opcion 2 mas flexible a la hora de realizar busquedas
    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()

    if (not post):
        raise HTTPException(status_code=404, detail='Post no encontrado')

    if incluide_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@app.post('/posts', response_model=PostPublic, response_description='Post creado (OK)', status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    '''
    Crear un post.

    :param PostCreate post: Datos enviados para crear el post.
    :return: Diccionario con el post actualizado.
    :rtype: dict[str, Any]
    '''

    if (post.author):
        author_obj = db.execute(select(AuthorORM).where(
            AuthorORM.email == post.author.email)).scalar_one_or_none()

        if not author_obj:
            author_obj = AuthorORM(
                name=post.author.name, email=post.author.email)
            db.add(author_obj)
            db.flush()  # Sirve para asignar el id antes de hacer el commit. Solo para asegurarnos de que tenga un id

    list_tag_obj: list[TagORM] = []
    for tag in post.tags:
        # En el Where poner TagORM.name == tag.name no es lo mismo que poner TagORM.name.ilike(tag.name)
        # El == compara exactamente el string considerando mayusculas y minusculas (Python == python) esta condicion seria false
        # Mientas que ilike compara ignorando mayúsculas/minúsculas. En el mundo real para manejo de tags esto es mas util
        tag_obj = db.execute(select(TagORM).where(
            TagORM.name.ilike(tag.name))).scalar_one_or_none()

        if not tag_obj:
            tag_obj = TagORM(name=tag.name)
            db.add(tag_obj)
            db.flush()

        list_tag_obj.append(tag_obj)

    new_post = PostORM(
        title=post.title, content=post.content, author=author_obj, tags=list_tag_obj)

    try:
        db.add(new_post)
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


@app.put('/posts/{post_id}', response_model=PostPublic, response_description='Post actualizado (OK)', response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    '''
    Actualiza un post existente.

    :param int post_id: ID del post a actualizar.
    :param PostUpdate data: Datos enviados para actualizar el post.
    :return: Diccionario con el post actualizado.
    :rtype: dict[str, Any]

    .. note::
        Si se usa ``exclude_unset=True``, solo se actualizarán los campos
        enviados por el usuario.
    '''

    # Paso 1: Obtener el post enviado por el usuario
    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    # Paso 2: Filtrar los campos a actualizar evitando que se modifiquen campos que le usuario no ha enviado
    updates = data.model_dump(exclude_unset=True)

    # Paso 3: Actualizar el post con la nueva informacion
    for key, value in updates.items():
        setattr(post, key, value)

    # Paso 4: Mandar a guardar el post actualizado a la base de datos
    try:
        db.add(post)
        db.commit()
        db.refresh(post)

        return PostPublic.model_validate(post, from_attributes=True)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El titulo ya existe, debe cambiar el titulo")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al guardar el post")


# Este codigo quiere decir que salio bien pero no vamos a regresar nada de contenido
@app.delete('/posts/{post_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    '''
    Elimina un post existente.

    :param int post_id: (Path) ID del post.
    :rtype: None

    .. warning::
        Lanzara un status_code ``404``, si no se encuetra el post.
    '''

    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail='Post no encontrado')

    db.delete(post)
    db.commit()
