# generate news articles
from typing import Tuple, Union
import logging
import os
from openai import OpenAI
import yaml
import json

VERBOSE = False
journalist1_system = {
    "role": "system",
    "content": "Your name is Whisker Walters. You are a famous journalist and the chief news editor for Rat News Network. Your job is to come up with the next juicy story."   # noqa: E501
}

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

logging.basicConfig(
    filename='logs/generator.log',
    format="%(asctime)s:%(levelname)s:%(message)s",
    encoding='utf-8',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)


def new_articles(num: int):
    ideas = article_ideas(num)
    ideas = json.loads(ideas)
    ideas = ideas[list(ideas.keys())[0]]
    idea = ideas[0]
    title, overview, body = article_body(json.dumps(idea))
    article_image(json.dumps(idea))
    return title, overview, body


def _cli_main():
    """Command line interface main function"""
    global VERBOSE
    VERBOSE = True
    import sys
    action = str(sys.argv[1])
    if 'idea' in action:
        print("\n***INITIAL IDEAS:")
        ideas = article_ideas(5)
        print("\n\n\n***IDEA SELECTION:")
        
        ideas = json.loads(ideas)
        ideas = ideas[list(ideas.keys())[0]]
        for idea in ideas:
            try:
                logging.info(idea['title'])
                image_url = article_image(json.dumps(idea))
                # article_outline = 

            except KeyError as e:
                logging.error("Error: %s. Could not parse JSON from: \n%s",str(e), idea)
            
            # create image
            
            # create ou

        # select_idea(ideas)
    elif 'full' in action:
        new_articles(1)
    
    elif 'image' in action:
        url = article_image("""{
      "title": "The Secret to Squeaky Clean Whiskers: Rat Beauticians Revealed",
      "description": "Ever wondered how rats maintain their impeccable whiskers? Look no further! We take you inside the exclusive world of rat beauticians who specialize in whisker grooming. From beard oils to mustache wax, we reveal the secrets and techniques these professionals employ to keep our whiskered companions looking sharp. Get ready for the ultimate rat pampering experience!",
      "category": "Lifestyle"
    }""")
        print(url)
        logging.info(url)


def get_text(chat_completion) -> str:
    text = chat_completion.choices[0].message.content
    if VERBOSE:
        print(text)
        # logger.info()
        logger.debug('\n%s', text)
    # TODO: error handle
    return text


def get_ad_prompt(article: str) -> str:
    pass


def article_image(article_idea: str) -> str:
    with open('prompts/images.yaml') as f:
        prompts = yaml.safe_load(f)

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompts['main_image'].replace('[IDEA]',article_idea),
        size="1024x1024",
        quality="standard",
        n=1,
    )
    for img in response.data:
        logging.info("\n%s", img.revised_prompt)
        logging.info("%s", img.url)
        
    image_url = response.data[0].url
    return image_url


def article_ideas(n, system_msg=journalist1_system) -> str:
    """Generate n 1-sentence article ideas

    Args:
        n (int): The number of ideas to create. 

    Returns:
        str: a string containing a set of article ideas
    """
    with open('prompts/ideas.yaml','rb') as f:
        prompts = yaml.safe_load(f)
    
    convo_1_ideas = [
        system_msg,
        {
            "role": "user",
            "content": prompts['idea_generator'].replace('[NUM IDEAS]', str(n))
        }
    ]
    chat_completion = client.chat.completions.create(
        messages=convo_1_ideas,
        # model="gpt-4-1106-preview",
        model="gpt-3.5-turbo",
        temperature=1
    )
    ideas = get_text(chat_completion)

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

    discrete_ideas = get_text(chat_completion2)
    if '{' not in discrete_ideas or '}' not in discrete_ideas:
        logger.warning(f'''JSON formatting of generation may be incorrect. brackets are 
                       missing.\n generation length: {len(discrete_ideas)}
                       generation:{discrete_ideas}''')
        return discrete_ideas
    idea_json = discrete_ideas[discrete_ideas.find('{'):discrete_ideas.rfind('}')+1]
    return idea_json


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
    best_article = get_text(chat_completion)

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
    idea_json = get_text(chat_completion)
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
            journalist1_system,
            {
                "role": "user",
                "content": prompts['outline'].replace('[IDEA]',idea.strip()),
            }
        ],
        # model="gpt-3.5-turbo",
        model="gpt-4-1106-preview",
    )
    return get_text(chat_completion)


prompt_body_usr = """Please write an excellent news article on the following topic. The article should be [PARA] paragraphs long and at an [LEVEL]th grade reading-level.

---
# Article Overview:
[IDEA]
# Article Outline
[OUTLINE]
---

Please write a high quality, realistic, and compelling [PARA]-paragraph news article:"""


def article_body(idea: str, n_paragraphs=5, reading_level=8) -> Union[Tuple[str], None]:
    """Generate the actual text for an article

    Args:
        topic (str): The article's topic sentence
        title (str): The title of the article
        outline (str): An outline of the article
        n_paragraphs (int): The length of the article
        reading_level (int): The complexity of the article's structure and vocabulary

    Returns:
        str: the article's text
    """
    outline = article_outline(idea)

    user_prompt = prompt_body_usr.replace('[PARA]', str(n_paragraphs)) \
        .replace('[LEVEL]', str(reading_level)) \
        .replace('[IDEA]', idea) \
        .replace('[OUTLINE]', outline)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """You are an expert AI rat-journalist who writes compelling stories for Rat News Network. Rat News Network is an organization run by rats in a fictional rat world. You specialize in writing articles from topic statements and outlines. You will be given the topic and outline of the article.\n\n## Article requirements:\n - NEVER mention or imply that the rat world is fictional.\n - Always act as if the author lives within this rat world.\n - Start the article with an interesting and compelling first sentence and hook.\n - Each paragraph should be 1-2 sentences, with a focus on readability.\n - You must include relevant quotes from fictional interviews.\n\n---\n## Output format:\n - You output three sections in the following order: the title, a two-sentence summary of the article, and the article itself.\n - You must delimit those three sentences with the <hr> tag\n\n---\nRemember, your job is to write an engaging and professional-quality news story. The article you create will be on par with articles from the New York Times or Al Jazeera.""" # noqa: E501 
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        # model="gpt-3.5-turbo",
        model="gpt-4-1106-preview",
    )

    article_sections = get_text(chat_completion).split('<hr>')
    num_sections = len(article_sections)

    logger.debug(get_text(chat_completion))

    if num_sections != 3:
        logger.warning(f"Article prompt returned {num_sections} sections instead of 3")

    if num_sections == 3:
        title, overview, body = article_sections[:3]
        return title, overview, body
    elif num_sections >= 3:
        title, overview = article_sections[:2]
        return title, overview, '\n. . .\n'.join(article_sections[2:])
    elif num_sections == 2:
        title_overview, body = article_sections
        if '\n' in title_overview:
            title, overview = title_overview.strip().split('\n')[:2]
            return title, overview, body
        return title_overview, '', body
    elif num_sections == 1:
        if '\n' in article_sections[0]:
            lines = article_sections[0].strip().split('\n')
            title = lines[0]
            body = '\n'.join(lines[1:])
            return title,'',body
        return '', '', article_sections[0]
    
    return None


if __name__ == '__main__':
    _cli_main()