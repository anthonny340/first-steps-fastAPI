



from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30,
                      description='Nombre de la etiqueta')

    model_config = ConfigDict(from_attributes=True)


class Author(BaseModel):
    name: str = Field(..., min_length=10, max_length=100,
                      description='Nombre del autor')
    email: EmailStr = Field(..., description='Correo electronico del autor')
    # Esto permite validar tambien objetos y no solo diccionarios
    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: str
    # Field(default_factory=list) ayuda a crear siempre una lista de forma independiente
    tags: Optional[list[Tag]] = Field(default_factory=list)  # []
    author: Optional[Author] = None
    model_config = ConfigDict(from_attributes=True)


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
        
        title_lower = value.lower()

        for word in forbidden_words:
            if word in title_lower:
                raise ValueError(
                    f'El titulo no puede contener la palabra "{value}". (NOT ALLOWED)')
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
