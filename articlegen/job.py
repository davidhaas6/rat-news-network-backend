
from datetime import datetime
from multiprocessing import Pool
from typing import List
import os
from pathlib import Path
import gen
import traceback
import sys
import uuid


ARTICLE_PATH = (Path(__file__).parent.absolute() / ".." / "static" / "articles" ).as_posix()

print(ARTICLE_PATH)

def main():
    if len(sys.argv) > 1:
        write_articles(int(sys.argv[1]))


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
    
    print(f"{articles=}")
    print(f'{num_new=}')
    print(f'cpu count: {os.cpu_count()}')

    # figure out # of new articles to write
   

    if num_new > 0:
        with Pool(min(num_new,os.cpu_count())) as pool:
            new_files = [uuid.uuid4().hex for _ in range(n - num_new, n)]
            print(f'{new_files=}')
            pool.map(_write_article, new_files)    


def _write_article(filename, delim='---'):
    # gen.VERBOSE = True
    try:
        result = gen.new_article()
        if result is None:
            return False
        
        title, overview, body = result
        with open(os.path.join(_daily_article_dir(), f'{filename}.txt'), 'w') as f:
            f.write(title.strip() + delim)
            f.write(overview.strip() + delim)
            f.write(body.strip())
    except Exception as e:
        traceback.print_tb(sys.exception().__traceback__)
        print(e)

    return True


def get_article_paths():
    article_dir = _daily_article_dir()
    paths = []
    for path in os.listdir(article_dir):
        if path.endswith('txt'):
            paths.append(os.path.join(_daily_article_dir(),path))
    return paths


def _daily_article_dir():
    date = datetime.now().strftime("%m%d%Y")
    todays_articles_path = os.path.join(ARTICLE_PATH, date)
    return todays_articles_path


if __name__ == '__main__':
    main()

