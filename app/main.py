from fastapi import FastAPI, Query

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
