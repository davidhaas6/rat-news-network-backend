
# scrape the HTML data from the website in main.py
from datetime import datetime
import glob
import logging
from typing import List
import requests
from bs4 import BeautifulSoup
import os
import shutil
import articlelib
import re
from pathlib import Path

LOCAL_URL = "http://127.0.0.1:8000/"

# set up independent logging stream
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("generate_static.log"),
        logging.StreamHandler()
    ],
)

def main():
    dst_folder = Path("mirrors") / f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # create file structure
    if not os.path.exists("mirrors"):
        os.makedirs("mirrors")
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)
        os.makedirs(dst_folder / "articles")
        os.makedirs(dst_folder / "static")
    
    # pull site data
    download_index(os.path.join(dst_folder, "index.html"))
    download_articles(os.path.join(dst_folder, "articles"))

    # move static files
    shutil.copy("static/styles.css", os.path.join(dst_folder, "static/styles.css"))


# Get root page
def download_index(save_path: Path, replace_url="/"):
    r = requests.get(LOCAL_URL)
    soup = BeautifulSoup(r.content, "html.parser")
    with open(save_path, "w") as f:
        html = soup.prettify()
        html = re.sub(r'static\/articles\/(.+)\/(\w+)\.png', r'articles/\2.png', html)
        if replace_url is not None:
            html = html.replace(LOCAL_URL, replace_url)
        f.write(html)


def download_articles(save_path, replace_url="/") -> List[str]:
    site_paths = []
    daily_articles = articlelib.get_articles()
    for article in daily_articles:
        site_path = f"{LOCAL_URL}articles/{article.id}"
        site_paths.append(site_path)
        r = requests.get(site_path)
        soup = BeautifulSoup(r.content, "html.parser") 
        article_dst_path = os.path.join(save_path, f'{article.id}.html')
        with open(article_dst_path, "w") as f:
            # replace image path
            html = soup.prettify()
            html = re.sub(r'static\/articles\/.*?\.png', f'articles/{article.id}.png', html)
            if replace_url is not None:
                html = html.replace(LOCAL_URL, replace_url)
            f.write(html)
            logging.debug("Saving article %s to %s", article.id, article_dst_path)
        
        # copy image
        img_src = os.path.join('static/', article.img_path)
        img_dst = os.path.join(save_path, f'{article.id}.png')
        logging.debug("Copying %s to %s", img_src, img_dst)
        shutil.copy(img_src, img_dst)

        

    return site_paths


if __name__ == "__main__":
    main()
