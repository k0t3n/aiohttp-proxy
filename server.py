import re
from itertools import cycle
from urllib.parse import urljoin

import html2text
from aiohttp import ClientSession, web

LIFEHACKER_URL = 'https://lifehacker.ru'
BASE_URL = 'http://0.0.0.0:8080'
EMOJI = ['😃', '😂', '😎', '😡', '😍', '😐']
WORD_LENGTH = 6


def change_links(string, old_link, new_link):
    """
    Changes all matched links from string to new link
    :param string
    :param new_link
    :param old_link
    :return: string with new links
    """
    return re.sub(rf'\b{old_link}\b', new_link, string)


def clear_string_from_links(string):
    """
    Clear string from urls
    :param string: string
    :return: string without urls
    """
    return re.sub(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)', '', string)


def validate_words(words, word_length):
    """
    Validates words of required length
    :param word_length: required word length
    :param words: list of words
    :return: list of validated words of required length
    """
    validated_words = []
    for raw_word in words:
        words_regexp = re.findall(r'\b\w+\b', clear_string_from_links(raw_word))  # extract only the word
        for word in words_regexp:
            if len(word) == word_length:
                # print(word)
                validated_words.append(word)
    return validated_words


async def proxy_with_emoji(request):
    target_url = urljoin(LIFEHACKER_URL, request.match_info['path'])

    async with ClientSession() as session:
        async with session.get(target_url) as resp:
            content_type = resp.content_type
            # return other content without modifying
            if content_type != 'text/html':
                return web.Response(body=await resp.read(), content_type=content_type)
            html = await resp.text()

        words = validate_words(html2text.html2text(html).replace('\n', '').split(' '), WORD_LENGTH)
        html = change_links(html, LIFEHACKER_URL, BASE_URL)
        changed_words = set()
        for index, (word, emoji) in enumerate(zip(words, cycle(EMOJI))):
            if word not in changed_words:  # the page may contain duplicate words
                html = re.sub(rf'\b{word}\b', f'{word}{emoji}', html)  # find a word and add emoji
                changed_words.add(word)

        return web.Response(body=html, content_type='text/html')


app = web.Application()
app.add_routes([web.get('/{path:.*}', proxy_with_emoji)])

web.run_app(app)
