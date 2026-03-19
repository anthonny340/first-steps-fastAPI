from fastapi import FastAPI

app = FastAPI(title='Mini Blog')

BLOG_POST = [
    {'id': 1, 'title': 'Hola desde fastAPI', 'content': 'Mi primer post con fastAPI'},
    {'id': 2, 'title': 'Segundo post desde fastAPI', 'content': 'explorando fastAPI'},
    {'id': 3, 'title': 'Tercer post desde fastAPI', 'content': 'explorando fastAPI'},
]

@app.get('/')
def home():
    return {'message': 'Bienvenidos a Mini Blog por Anthonny'}

@app.get('/posts')
def list_post():
    return {'data': BLOG_POST}