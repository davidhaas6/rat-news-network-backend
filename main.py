from typing import Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import articlelib
from random import choice, sample

app = FastAPI()

app.mount(
    (Path(__file__).parent.parent.absolute() / "static").as_posix(), 
    StaticFiles(directory="static"), 
    name="static"
)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    preview_articles = sample(articlelib.get_articles(), k=5)
    print(list(map(lambda k: k.title, preview_articles)))
    return templates.TemplateResponse(
        request=request, 
        name="frontpage.html",
        context={
            "articles": preview_articles

        }
    )


@app.get("/articles/{article_id}", response_class=HTMLResponse)
def read_item(request: Request, article_id: str):
    articles = articlelib.get_articles()
    if article_id == 'random':
        matches = [choice(articles)]
    else:
        matches = [article for article in articles if article.id == article_id]
    print('matches')
    if len(matches) > 0:
        article = matches[0]
        return templates.TemplateResponse(
            request=request, 
            name="article2.html",
            context={
                "title": article.title,
                "overview": article.overview,
                "body": article.body.replace('\n','<br >')
            }
        )
    return templates.TemplateResponse(
            request=request, 
            name="article.html",
            context={
                "title": "Article not found",
                "overview": "",
                "body": ""
            }
        )