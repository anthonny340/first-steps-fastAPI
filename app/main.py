import os
from datetime import datetime
from fastapi import FastAPI, Query, Body, HTTPException, Path, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, Union, Literal
from math import ceil
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from theme import dark_css
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./blog.db')
print(f'Conectado a: {DATABASE_URL}')

engine_kwargs = {}
if DATABASE_URL.startswith('sqlite'):
    engine_kwargs['connect_args'] = {'check_same_thread': False}

# echo muestra el SQL ejecutado, util para ver las consultas que se estan haciendo
# future en True lo que dice es que queremos ocuparar la sintaxis moderna de SQLAlchemy 2
engine = create_engine(DATABASE_URL, echo=True, future=True, **engine_kwargs)

# autoflush lo que hace es no enviar cambios automaticos hasta hacer el commit
# autocommit en False lo que hace es que tenga control explicito sobre el commit
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, class_=Session)


class Base(DeclarativeBase):
    pass


class PostORM(Base):
    __tablename__ = 'post'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    create_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now())


# Esto unicamnete es para nuestro entorno de desarrollo, solo va a crear las
# tablas en caso de que no exista
Base.metadata.create_all(bind=engine)  # dev

# Para produccion, no se ocupa esto, se ocupa migraciones


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DARK_DOCS = True

app = FastAPI(docs_url=None if DARK_DOCS else "/docs")

BLOG_POST = [
    {'id': 1, 'title': 'Hola desde FastAPI',
        'content': 'Mi primer post con FastAPI', 'tags': [{'name': 'python'}, {'name': 'java'}]},
    {'id': 2, 'title': 'Segundo post desde FastAPI',
        'content': 'Explorando FastAPI'},
    {'id': 3, 'title': 'Tercer post desde FastAPI', 'content': 'Explorando FastAPI'},
    {'id': 4, 'title': 'Creando mi primera API',
        'content': 'FastAPI hace todo más sencillo'},
    {'id': 5, 'title': 'Probando rutas dinámicas',
        'content': 'Aprendiendo a manejar parámetros'},
    {'id': 6, 'title': 'Usando Pydantic',
        'content': 'Validación de datos con modelos', 'tags': [{'name': 'python'}, {'name': 'java'}]},
    {'id': 7, 'title': 'Métodos GET y POST',
        'content': 'Primeros pasos con métodos HTTP', 'tags': [{'name': 'python'}, {'name': 'java'}]},
    {'id': 8, 'title': 'Conectando FastAPI con una base de datos',
        'content': 'Probando SQLite'},
    {'id': 9, 'title': 'Middleware en FastAPI',
        'content': 'Interceptando requests'},
    {'id': 10, 'title': 'Aprendiendo sobre CORS',
        'content': 'Configurando acceso entre dominios'},
    {'id': 11, 'title': 'Documentación automática',
        'content': 'Swagger UI es increíble'},
    {'id': 12, 'title': 'Probando Redoc',
        'content': 'Otra forma de documentar APIs'},
    {'id': 13, 'title': 'Creando modelos más complejos',
        'content': 'Pydantic es muy flexible'},
    {'id': 14, 'title': 'Usando Query Parameters',
        'content': 'Filtrando datos desde la URL'},
    {'id': 15, 'title': 'Path Parameters avanzados',
        'content': 'Validación y conversión automática'},
    {'id': 16, 'title': 'Aprendiendo sobre Response Models',
        'content': 'Controlando la salida de datos'},
    {'id': 17, 'title': 'Manejo de errores', 'content': 'Usando HTTPException'},
    {'id': 18, 'title': 'Custom Exception Handlers',
        'content': 'Respuestas personalizadas'},
    {'id': 19, 'title': 'Background Tasks', 'content': 'Procesos en segundo plano'},
    {'id': 20, 'title': 'Subiendo archivos',
        'content': 'Manejo de File y UploadFile'},
    {'id': 21, 'title': 'Descargando archivos',
        'content': 'StreamingResponse en acción'},
    {'id': 22, 'title': 'Autenticación básica',
        'content': 'Primeros pasos con seguridad'},
    {'id': 23, 'title': 'OAuth2 con Password Flow',
        'content': 'Implementando login'},
    {'id': 24, 'title': 'JWT en FastAPI', 'content': 'Tokens para autenticación'},
    {'id': 25, 'title': 'Dependencias en FastAPI', 'content': 'Reutilizando lógica'},
    {'id': 26, 'title': 'Dependencias con clases',
        'content': 'Organizando mejor el código'},
    {'id': 27, 'title': 'Routers en FastAPI', 'content': 'Modularizando la API'},
    {'id': 28, 'title': 'Versionando la API',
        'content': 'Buenas prácticas para crecer'},
    {'id': 29, 'title': 'Probando WebSockets',
        'content': 'Comunicación en tiempo real'},
    {'id': 30, 'title': 'FastAPI y asyncio',
        'content': 'Ventajas del código asíncrono'},
    {'id': 31, 'title': 'Integrando SQLAlchemy',
        'content': 'ORM para bases de datos'},
    {'id': 32, 'title': 'Migraciones con Alembic',
        'content': 'Controlando cambios en el esquema'},
    {'id': 33, 'title': 'CRUD completo', 'content': 'Creando operaciones básicas'},
    {'id': 34, 'title': 'Paginación de resultados',
        'content': 'Mejorando la experiencia del usuario'},
    {'id': 35, 'title': 'Filtros avanzados', 'content': 'Consultas más potentes'},
    {'id': 36, 'title': 'Testing con pytest', 'content': 'Probando endpoints'},
    {'id': 37, 'title': 'TestClient de FastAPI', 'content': 'Simulando peticiones'},
    {'id': 38, 'title': 'Deploy en Uvicorn', 'content': 'Servidor ASGI ligero'},
    {'id': 39, 'title': 'Deploy en Gunicorn', 'content': 'Producción con workers'},
    {'id': 40, 'title': 'Deploy en Docker', 'content': 'Contenerizando la API'},
    {'id': 41, 'title': 'FastAPI en la nube', 'content': 'Probando con Render'},
    {'id': 42, 'title': 'FastAPI y Nginx',
        'content': 'Configurando un reverse proxy'},
    {'id': 43, 'title': 'Optimización de rendimiento',
        'content': 'Mejorando tiempos de respuesta'},
    {'id': 44, 'title': 'Cache con Redis', 'content': 'Acelerando consultas'},
    {'id': 45, 'title': 'Rate limiting', 'content': 'Controlando el tráfico'},
    {'id': 46, 'title': 'Logging avanzado', 'content': 'Monitoreando la API'},
    {'id': 47, 'title': 'Buenas prácticas con FastAPI',
        'content': 'Código limpio y mantenible'},
    {'id': 48, 'title': 'Estructura profesional de proyecto',
        'content': 'Organizando carpetas y módulos'},
    {'id': 49, 'title': 'FastAPI + Frontend',
        'content': 'Conectando con React o Vue'},
    {'id': 50, 'title': 'Conclusiones del viaje con FastAPI',
        'content': 'Un framework rápido y elegante'},
]


class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30,
                      description='Nombre de la etiqueta')


class Author(BaseModel):
    name: str = Field(..., min_length=10, max_length=100,
                      description='Nombre del autor')
    email: EmailStr = Field(..., description='Correo electronico del autor')


class PostBase(BaseModel):
    title: str
    content: str
    # Field(default_factory=list) ayuda a crear siempre una lista de forma independiente
    tags: Optional[list[Tag]] = Field(default_factory=list)  # []
    author: Optional[Author] = None


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description='Titulo del post (min 3 caracteres, max 100)',
        examples=['Mi primer post con FastAPI']
    )
    content: Optional[str] = Field(
        default='Contenido no disponible',
        min_length=10,
        description='Contenido del post (min 10 caracteres)',
        examples=['Este es un contenido valido porque tiene 10 caracteres o mas']
    )
    tags: list[Tag] = Field(default_factory=list)
    author: Optional[Author] = None

    @field_validator('title')
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        forbidden_words = ['spam', 'fake', 'test',
                           'dummy', 'banned', 'prohibited']
        if value.lower() in forbidden_words:
            raise ValueError(
                f'El titulo no puede contener la palabra "{value}" no es permitido (NOT ALLOWED)')
        return value


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None


class PostPublic(PostBase):
    # Clases para dar formato a la salida de nuestros metodos HTTP
    id: int

    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):
    id: int
    title: str
    tags: Optional[list[Tag]] = Field(default_factory=list)  # []
    author: Optional[Author] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_page: int
    has_prev: bool
    has_next: bool
    order_by: Literal['id', 'title']
    direction: Literal['asc', 'desc']
    search: Optional[str] = None
    items: list[PostPublic]


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Docs"
    ).body.decode("utf-8")

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
        items: list[PostORM] = []
    else:
        start = (current_page - 1) * per_page
        query_sql = results.limit(per_page).offset(
            start)
        items = db.execute(query_sql).scalars().all()

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
def filter_by_tags(tags: list[str] = Query(..., min_length=1, description='Una o mas etiquetas.', example='?tags=python&tags=fastapi')):

    tags_lower = [tag.lower() for tag in tags]

    return [post for post in BLOG_POST if any(tag['name'].lower() in tags_lower for tag in post.get('tags', []))]


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
    new_post = PostORM(title=post.title, content=post.content)
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except SQLAlchemyError:
        print('SALTO UN ERROR TIPO SQLAlchemyError')
        db.rollback()
        raise HTTPException(status_code=500, detail='Error al crear el post')


@app.put('/posts/{post_id}', response_model=PostPublic, response_description='Post actualizado (OK)', response_model_exclude_none=True)
def update_post(post_id: int, data: PostUpdate):
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
    for post in BLOG_POST:
        if post_id == post['id']:
            # Podemos converitir data que es tipo PostUpdate en un diccionario con la siguiente linea de codigo
            # playload = data.model_dump(exclude_unset=True)
            # exclude_unset=True sirve para excluir los parametros que no envia el usuario, evitando la asignacion de None a los parametros no enviados
            if data.title:
                post['title'] = data.title

            if data.content:
                post['content'] = data.content

            return post

    raise HTTPException(status_code=404, detail='Post no encontrado')


# Este codigo quiere decir que salio bien pero no vamos a regresar nada de contenido
@app.delete('/posts/{post_id}', status_code=204)
def delete_post(post_id: int):
    '''
    Elimina un post existente.

    :param int post_id: (Path) ID del post.
    :rtype: None

    .. warning::
        Lanzara un status_code ``404``, si no se encuetra el post.
    '''
    for index, post in enumerate(BLOG_POST):
        if post_id == post['id']:
            BLOG_POST.pop(index)
            return
    raise HTTPException(status_code=404, detail='Post no encontrado')
