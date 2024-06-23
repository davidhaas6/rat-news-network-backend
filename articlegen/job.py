
from datetime import datetime
from multiprocessing import Pool
from typing import List
import os
from pathlib import Path
import gen
import traceback
import sys
import uuid
import json
import requests
import logging
import time

# logging.


ARTICLE_PATH = (Path(__file__).parent.parent / "static" / "articles" ).as_posix()


def main():
    if len(sys.argv) > 1:
        start=time.time()
        n = int(sys.argv[1])
        write_articles(n)
        logging.info(f'Generated {n} articles in {round(time.time()-start,2)} seconds')


def write_articles(n: int) -> List[str]:
    """Generates and writes n articles to disk

    Args:
        n (int): The number of articles to generate
    """
    article_dir = _daily_article_dir()
    if not os.path.isdir(article_dir):
        os.makedirs(article_dir)

    articles = get_article_paths()
    num_new = n - len(articles)
    
    print(f"existing {articles=}")
    print(f'{num_new=}')

    try:
        article_jsons = gen.new_articles(num_new)
        for article in article_jsons:
            article_id = article['article_id']  # new articles have article_id
            article['id'] = article_id  # backwards compatibility
            if 'img_path' in article:
                local_imgpath = os.path.join(_daily_article_dir(), f'{article_id}.png')
                try:
                    if  _download_file(article['img_path'], local_imgpath):
                        article['url'] = article['img_path']
                        article['img_path'] = 'articles/' \
                            + _daily_article_dir().split('/')[-1]  \
                            + '/' + f'{article_id}.png'
                        
                except Exception as e:
                    logging.error('Error downloading images' + str(e))
            
            fpath = os.path.join(_daily_article_dir(), f'{article_id}.json')
            with open(fpath, 'w') as f:
                json.dump(article, f)


    except Exception as e:
        traceback.print_tb(sys.exception().__traceback__)
        print(e)


def get_article_paths():
    article_dir = _daily_article_dir()
    paths = []
    for path in os.listdir(article_dir):
        if path.endswith('json'):
            paths.append(os.path.join(_daily_article_dir(),path))
    return paths


def _download_file(url: str, file_path:str) -> str:
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path,'wb') as f:
            f.write(response.content)
        logging.info(f'Downloaded file to {file_path}')
        return True
    else:
        logging.error(f'Image couldn\'t be retrieved. {url=}')
    return False


def _daily_article_dir():
    date = datetime.now().strftime("%m%d%Y")
    todays_articles_path = os.path.join(ARTICLE_PATH, date)
    return todays_articles_path


if __name__ == '__main__':
    main()

