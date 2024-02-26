# generate news articles
from datetime import datetime
from multiprocessing import Pool
from typing import Tuple, Union, List
import logging
import os
from openai import OpenAI
import yaml
import json
import uuid
import sys
import random

VERBOSE = False
journalist1_system = {
    "role": "system",
    "content": "Your name is Whisker Walters. You are a famous journalist and the chief news editor for Rat News Network. Your job is to come up with the next juicy story."   # noqa: E501
}

with open('prompts/system.yaml') as f:
    systems = yaml.safe_load(f)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

logging.basicConfig(
    # filename='logs/generator.log',
    format="%(asctime)s:%(levelname)s:%(message)s",
    # encoding='utf-8',
    level=logging.INFO,
    # prevent logs from other files from showing
)
logger = logging.getLogger(__name__)




def _cli_main():
    """Command line interface main function
    """
    global VERBOSE
    VERBOSE = True
    action = str(sys.argv[1])
    if 'idea' in action:
        print("\n***INITIAL IDEAS:")
        ideas = article_ideas(1)
        # print(ideas)
        outline = article_outline(ideas[0])
        # print()
        print(article_image(ideas[0], outline))
    elif 'full' in action:
        logger.info(new_articles(3))
    elif 'image' in action:
        url = article_image("""{
      "title": "The Secret to Squeaky Clean Whiskers: Rat Beauticians Revealed",
      "description": "Ever wondered how rats maintain their impeccable whiskers? Look no further! We take you inside the exclusive world of rat beauticians who specialize in whisker grooming. From beard oils to mustache wax, we reveal the secrets and techniques these professionals employ to keep our whiskered companions looking sharp. Get ready for the ultimate rat pampering experience!",
      "category": "Lifestyle"
    }""","""""")
        print(url)
        logger.info(url)
    elif 'topic' in action:
        article_from_idea(sys.argv[2])



def new_articles(num: int) -> List[dict]:
    """Generates a list of new articles

    Args:
        num (int): number of new articles to generate

    Returns:
        List[dict]: the article objects
    """
    if num <= 0:
        return []
    ideas_str = article_ideas(num)
    ideas = json.loads(ideas_str)
    ideas = ideas[list(ideas.keys())[0]]
    with Pool(min(num, os.cpu_count())) as pool:
        articles = pool.map(article_from_idea, map(json.dumps,ideas))   

    return articles


def article_from_idea(idea: str) -> dict:
    """Create an article from an idea

    Args:
        idea (str): A description of the article

    Returns:
        dict: an article object. returns empty dict on error.
              keys:
                url -> image url
                title -> article title
                overview -> article overview
                body -> article body
                timestamp -> article timestamp 
    """
    try:
        outline = article_outline(idea.strip())
        text, version = article_body(idea, outline)
        article = json.loads(text)
        article['generator'] = version
        article['url'] = article_image(idea,outline)
        article['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f'*Article created*\nTitle: {article["title"]}\nImage: {article["url"]}\nOverview:{article["overview"]}')
    except Exception as e:
        logger.error(e)
    return article



def get_ad_prompt(article: str) -> str:
    pass


def article_image(article_idea: str, outline: str) -> str:
    with open('prompts/images.yaml') as f:
        prompts = yaml.safe_load(f)

    convo_1_ideas = [
        {
            "role": "user",
            "content": prompts['brainstorming'].replace('{{idea}}', str(article_idea)).replace('{{outline}}', str(outline))
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=convo_1_ideas,
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    ideas = _get_text(chat_completion)

    convo_2_discretize = convo_1_ideas + [
        {
            "role": "assistant",
            "content": ideas
        },
        {
            "role": "user",
            "content": prompts['select']
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=convo_2_discretize,
        model="gpt-3.5-turbo",
        temperature=0
    )
    img_idea_json = _extract_jsonstr(_get_text(chat_completion))

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompts['create'].replace('{{image_idea}}', img_idea_json),
        quality="standard",
        n=1,
    )
    for img in response.data:
        logger.info("\n%s", img.revised_prompt)
        logger.info("%s", img.url)
        
    image_url = response.data[0].url
    return image_url


def article_ideas(n, system_prompt='whisker') -> str:
    """Generate n 1-sentence article ideas

    Args:
        n (int): The number of ideas to create. 

    Returns:
        str: a string containing a set of article ideas
    """
    with open('prompts/ideas.yaml','rb') as f:
        prompts = yaml.safe_load(f)
    
    convo_1_ideas = [
        {
            "role": "system",
            "content": systems[system_prompt],
        },
        {
            "role": "user",
            "content": prompts['idea_generator'].replace('{{n}}', str(n))
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=convo_1_ideas,
        model="gpt-4",
        # model="gpt-3.5-turbo",
        temperature=1
    )
    ideas = _get_text(chat_completion)

    convo_2_discretize = convo_1_ideas + [
        {
            "role": "assistant",
            "content": ideas
        },
        {
            "role": "user",
            "content": prompts['json_formatter']
        }
    ]
    chat_completion2 = client.chat.completions.create(
        messages=convo_2_discretize,
        model="gpt-3.5-turbo",
        temperature=0
    )

    discrete_ideas = _get_text(chat_completion2)
    return _extract_jsonstr(discrete_ideas)


def select_idea(ideas: str) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "As an expert AI news editor for Rat News Network, please analyze each of these article ideas and select the idea that will make the best article."  # noqa: E501
            },
            {
                "role": "user",
                "content": f"# Article Ideas:\n\n{ideas}",
            }
        ],
        model="gpt-3.5-turbo",
    )
    best_article = _get_text(chat_completion)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "As an expert AI news editor for Rat News Network, please analyze each of these article ideas and select the idea that will make the best article."  # noqa: E501
            },
            {
                "role": "user",
                "content": f"# Article Ideas:\n\n{ideas}",
            },
            {
                "role": "assistant",
                "content": best_article,
            },
            {
                "role": "user",
                "content": "Thank you! Now, please **copy** the article's title, description, and a summary of your editorial analysis into a *valid* JSON formatted string.",  # noqa: E501
            },
        ],
        model="gpt-3.5-turbo"
    )
    idea_json = _get_text(chat_completion)
    idea_json = idea_json[idea_json.find('{'):idea_json.rfind('}')+1]
    return idea_json


def article_outline(idea: str) -> str:
    """Create an outline for an article

    Args:
        idea (str): a textual description of an article idea

    Returns:
        str: A brief outline for the article
    """
    with open('prompts/article.yaml','rb') as f:
        prompts = yaml.safe_load(f)
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": systems['whisker'],
            },
            {
                "role": "user",
                "content": prompts['outline'].replace('{{idea}}',idea.strip()),
            }
        ],
        # model="gpt-3.5-turbo",
        model="gpt-4-1106-preview",
        temperature=0.2
    )
    return _get_text(chat_completion)


def article_body(idea: str, outline: str, num_words=500) -> str:
    """Generate the actual text for an article

    Args:
        topic (str): The article's topic sentence
        title (str): The title of the article
        outline (str): An outline of the article
        n_paragraphs (int): The length of the article
        reading_level (int): The complexity of the article's structure and vocabulary

    Returns:
        str: an article json string:
               title -> article title
               overview -> article overview
               body -> article body
        str: generator version
    """
    
    with open('prompts/article.yaml','rb') as f:
        prompts = yaml.safe_load(f)

    article_generator = random.choice([k for k in prompts.keys() if k.startswith('article_gen')])

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": systems['whisker'],
            },
            {
                "role": "user",
                "content": prompts[article_generator].replace('{{idea}}', idea) \
                                                    .replace('{{outline}}', outline) \
                                                    .replace('{{num_words}}', str(num_words)).strip()
            }
        ],
        # model="gpt-3.5-turbo",
        model="gpt-4-1106-preview",
    )
    raw_article = _get_text(chat_completion).strip()

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": systems['discretize']
            },
            {
                "role": "user",
                "content":prompts['articleToJson'].replace('{{article}}', raw_article).strip()
            }
        ],
        model="gpt-3.5-turbo",
        # model="gpt-4-1106-preview",
        temperature=0
    )

    article_text = _get_text(chat_completion)
    
    return _extract_jsonstr(article_text), article_generator


def _get_text(chat_completion) -> str:
    text = chat_completion.choices[0].message.content
    if VERBOSE:
        print(text)
        # logger.info()
        logger.debug('\n%s', text)
    # TODO: error handle
    return text


def _extract_jsonstr(text: str) -> str:
    if '{' not in text or '}' not in text:
        logger.warning(f'''JSON formatting of generation may be incorrect. brackets are 
                       missing.\n generation length: {len(text)}
                       generation:{text}''')
        return text
    return text[text.find('{'):text.rfind('}')+1]


if __name__ == '__main__':
    _cli_main()