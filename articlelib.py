from datetime import datetime
from typing import List
import os
from pathlib import Path
from dataclasses import dataclass

ARTICLE_PATH = (Path(__file__).parent.absolute() / "static" / "articles" ).as_posix()

@dataclass
class Article:
    id: str
    title: str
    body: str
    overview: str = None
    author: str = 'Ratso Remulini'
    image: str = None


def get_articles() -> List[str]:
    articles = []
    article_dir = _daily_article_dir()
    for article_filename in os.listdir(article_dir):
        filename = article_filename[:article_filename.rfind('.')]
        with open(os.path.join(article_dir, article_filename)) as f:
            article = f.read()
            title, overview, body = article.split('---')
            if len(overview) == 0:
                overview = None
        articles.append(Article(filename, title, body, overview))
    return articles


def _daily_article_dir():
    date = datetime.now().strftime("%m%d%Y")
    todays_articles_path = os.path.join(ARTICLE_PATH, date)
    return todays_articles_path

    

if __name__ == '__main__':
    for a in get_articles():
        print(a.title)

    

