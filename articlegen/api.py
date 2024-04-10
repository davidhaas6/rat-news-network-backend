# API endpoint for article generation


from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import gen

app = FastAPI()


@app.get('/')
def index():
    return RedirectResponse('/docs')


@app.get("/create/", response_class=HTMLResponse)
def create_articles(n: int = 1, topic: str = 'rats'):
    if n < 1:
        return JSONResponse(
            status_code=404, 
            content={"message": f"must generate at least 1 article. you requested {n}"}
        )
    if n > 10:
        n = 10
    
    article_jsons = gen.new_articles(n)
    return JSONResponse({"articles": article_jsons})
