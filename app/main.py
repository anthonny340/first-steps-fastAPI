from fastapi import FastAPI, Query, Body

app = FastAPI(title='Mini Blog')

BLOG_POST = [
    {'id': 1, 'title': 'Hola desde fastAPI',
        'content': 'Mi primer post con fastAPI'},
    {'id': 2, 'title': 'Segundo post desde fastAPI',
        'content': 'explorando fastAPI'},
    {'id': 3, 'title': 'Tercer post desde fastAPI', 'content': 'explorando fastAPI'},
]


@app.get('/')
def home():
    return {'message': 'Bienvenidos a Mini Blog por Anthonny'}


@app.get('/posts')
def list_post(query: str | None = Query(default=None, description='Texto para buscar por titulo')):
    if query:
        results = [post for post in BLOG_POST if query.lower()
                   in post['title'].lower()]
        # Se pude simplificar la logica con un list comprehension
        # for post in BLOG_POST:
        #     if query.lower() in post['title'].lower():
        #         results.append(post)
        return {'data': results, 'query': query}

    return {'data': BLOG_POST}


@app.get('/posts/{post_id}')
def get_post(post_id: int, incluide_content: bool = Query(default=True, description='Incluir o no el contenido')):
    for post in BLOG_POST:
        if post_id == post['id']:
            if incluide_content:
                return {'data': post}
            else:
                return {'data': {'id': post['id'], 'title': post['title']}}

    return {'error': 'Post no encontrado'}


@app.post('/posts')
def create_post(post: dict = Body(...)):
    if 'title' not in post or 'content' not in post:
        return {'error': 'Title y Content son requeridos'}

    if not str(post['title']).strip():
        return {'error': 'Title no puede estar vacio'}

    new_id = (BLOG_POST[-1]['id'] + 1) if BLOG_POST else 1
    new_post = {'id': new_id,
                'title': post['title'], 'content': post['content']}

    BLOG_POST.append(new_post)
    return {'message': 'Post creado', 'data': new_post}


@app.put('/posts/{post_id}')
def update_post(post_id: int, data: dict = Body(...)):
    for post in BLOG_POST:
        if post_id == post['id']:
            if 'title' in data:
                post['title'] = data['title']

            if 'content' in data:
                post['content'] = data['content']

            return {'message': 'Post actualizado', 'data': post}

    return {'error': 'No se encontro el post'}
