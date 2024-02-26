from datetime import datetime
from typing import List
import os
from pathlib import Path
from dataclasses import dataclass
import json
import logging

ARTICLE_PATH = (Path(__file__).parent.absolute() / "static" / "articles").as_posix()


@dataclass
class Article:
    id: str
    title: str
    body: str
    overview: str = None
    author: str = "Ratso Remulini"
    url: str = None
    img_path: str = None
    generator: str = None
    timestamp: str = None

    def from_json(json: dict, id=None):
        if "id" not in json and id is not None:
            return Article(**json, id=id)
        return Article(**json)


def get_articles() -> List[Article]:
    articles = []
    article_dir = _daily_article_dir()
    for article_filename in os.listdir(article_dir):
        if not article_filename.endswith(".json"):
            continue
        filename = article_filename[: article_filename.rfind(".")]
        with open(os.path.join(article_dir, article_filename)) as f:
            logging.debug(f"Loading file {filename}")
            article = json.loads(f.read())
            article = format_article(Article.from_json(article, id=filename))
        articles.append(article)

    return articles


def format_article(article: Article) -> Article:
    body = article.body.split("\n")
    new_body = []
    for line in body:
        is_subtitle = "\n" not in line and "." not in line and 5 < len(line) < 65
        if is_subtitle:
            line = "<h3>" + line + "</h3>"
        new_body.append(line)
    article.body = "<br>".join(new_body)
    article.body = article.body.replace("</h3><br>", "</h3>")
    article.body = article.body.replace("**", "")
    # article.body = article.body.repla
    return article


def _daily_article_dir(time_format="%m%d%Y"):
    date = datetime.now().strftime(time_format)
    todays_articles_path = os.path.join(ARTICLE_PATH, date)

    # find the most recent day
    if not os.path.exists(todays_articles_path):
        article_dirs = []
        for filename in os.listdir(ARTICLE_PATH):
            full_path = os.path.join(ARTICLE_PATH, filename)
            if os.path.isdir(full_path):
                article_dirs.append(full_path)

        if len(article_dirs) == 0:
            logging.critical(f"ERROR: No articles exist in {ARTICLE_PATH}")
            raise Exception("No articles exist")

        closest_time = 1_000_000
        recent_dir = article_dirs[0]
        for dir_path in article_dirs:
            dir_name = os.path.basename(dir_path)
            try:
                dir_time = datetime.strptime(dir_name, time_format)
                print(dir_time)
                dir_time_diff = (datetime.now() - dir_time).days
                if dir_time_diff < closest_time:
                    closest_time = dir_time_diff
                    recent_dir = dir_path
            except ValueError as e:
                logging.error("Could not parse dir: " + str(e))
        print(recent_dir, closest_time)
        todays_articles_path = recent_dir

    return todays_articles_path


if __name__ == "__main__":
    for a in get_articles():
        print(a.title)
