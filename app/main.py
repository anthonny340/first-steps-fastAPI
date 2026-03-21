from fastapi import FastAPI, Query, Body, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union

app = FastAPI(title='Mini Blog')

BLOG_POST = [
    {'id': 1, 'title': 'Hola desde fastAPI',
        'content': 'Mi primer post con fastAPI'},
    {'id': 2, 'title': 'Segundo post desde fastAPI',
        'content': 'explorando fastAPI'},
    {'id': 3, 'title': 'Tercer post desde fastAPI', 'content': 'explorando fastAPI'},
]


class PostBase(BaseModel):
    title: str
    content: str


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
    title: str
    content: Optional[str] = None


class PostPublic(PostBase):
    # Clases para dar formato a la salida de nuestros metodos HTTP
    id: int


class PostSummary(BaseModel):
    id: int
    title: str


@app.get('/')
def home():
    return {'message': 'Bienvenidos a Mini Blog por Anthonny'}


@app.get('/posts', response_model=List[PostPublic])
def list_post(query: str | None = Query(default=None, description='Texto para buscar por titulo')):
    '''
    Obtener los posts.

    :param str | None query: (Query) Texto para buscar posts por titulo.
    :return: Diccionario de posts coincidentes.
    :rtype: (dict[str, Any] | dict[str, list[dict[str, Any]]])
    '''
    if query:
        results = [post for post in BLOG_POST if query.lower()
                   in post['title'].lower()]
        # Se pude simplificar la logica con un list comprehension
        # for post in BLOG_POST:
        #     if query.lower() in post['title'].lower():
        #         results.append(post)
        return results

    return BLOG_POST


@app.get('/posts/{post_id}', response_model=Union[PostPublic, PostSummary], response_description='Post encontrado')
def get_post(post_id: int, incluide_content: bool = Query(default=True, description='Incluir o no el contenido')):
    '''
    Obtener los posts por ID o por coincidencia de contenido.

    :param int post_id: (Path) ID del post.
    :param bool incluide_content: (Query) Incluir el contentenido del post.
    :return: Diccionario de posts coincidentes.
    :rtype: (dict[str, dict[str, Any]] | dict[str, str])
    '''
    for post in BLOG_POST:
        if post_id == post['id']:
            if incluide_content:
                return post
            return {'id': post['id'], 'title': post['title']}

    raise HTTPException(status_code=404, detail='Post no encontrado')


@app.post('/posts')
def create_post(post: PostCreate):
    '''
    Crear un post.

    :param PostCreate post: Datos enviados para crear el post.
    :return: Diccionario con el post actualizado.
    :rtype: dict[str, Any]
    '''
    new_id = (BLOG_POST[-1]['id'] + 1) if BLOG_POST else 1
    new_post = {'id': new_id,
                'title': post.title, 'content': post.content}

    BLOG_POST.append(new_post)
    return {'message': 'Post creado', 'data': new_post}


@app.put('/posts/{post_id}')
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

            return {'message': 'Post actualizado', 'data': post}

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
