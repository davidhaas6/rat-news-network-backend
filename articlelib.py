from datetime import datetime
from typing import List
import os
from pathlib import Path
from dataclasses import dataclass
import json
import logging

ARTICLE_PATH = (Path(__file__).parent.absolute() / "static" / "articles" ).as_posix()

@dataclass
class Article:
    id: str
    title: str
    body: str
    overview: str = None
    author: str = 'Ratso Remulini'
    url: str = None
    img_path: str = None

    def from_json(json: dict, id=None):
        if 'id' not in json and id is not None:
            return Article(**json, id=id)
        return Article(**json)


def get_articles() -> List[str]:
    articles = []
    article_dir = _daily_article_dir()
    for article_filename in os.listdir(article_dir):
        if not article_filename.endswith('.json'):
            continue
        filename = article_filename[:article_filename.rfind('.')]
        with open(os.path.join(article_dir, article_filename)) as f:
            logging.debug(f'Loading file {filename}')
            article = json.loads(f.read())
        articles.append(Article.from_json(article, id=filename))
    return articles


def _daily_article_dir():
    date = datetime.now().strftime("%m%d%Y")
    todays_articles_path = os.path.join(ARTICLE_PATH, date)
    return todays_articles_path

    

if __name__ == '__main__':
    for a in get_articles():
        print(a.title)

    

