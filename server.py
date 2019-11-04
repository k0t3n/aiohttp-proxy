import re
from itertools import cycle
from urllib.parse import urljoin

import html2text
from aiohttp import ClientSession, web

LIFEHACKER_URL = 'https://lifehacker.ru'
EMOJI = ['😃', '😂', '😎', '😡', '😍', '😐']
WORD_LENGTH = 6


def validate_words(words, word_length):
    """
    Validates words of required length
    :param word_length: required word length
    :param words: list of words
    :return: list of validated words of required length
    """
    validated_words = []
    for word in words:
        word_regexp = re.findall(r'\b\w+\b', word)  # extract only the word
        if any(word_regexp):
            word = word_regexp[0]
            if len(word) == word_length:
                validated_words.append(word_regexp[0])
    return validated_words


async def proxy_with_emoji(request):
    target_url = urljoin(LIFEHACKER_URL, request.match_info['path'])

    async with ClientSession() as session:
        async with session.get(target_url) as resp:
            html = await resp.text()

        words = validate_words(html2text.html2text(html).split(' '), WORD_LENGTH)
        changed_words = set()
        for index, (word, emoji) in enumerate(zip(words, cycle(EMOJI))):
            if word not in changed_words:  # the page may contain duplicate words
                html = re.sub(rf'\b{word}\b', f'{word}{emoji}', html)  # find a word and add emoji
                changed_words.add(word)

        return web.Response(body=html, content_type='text/html')


app = web.Application()
app.add_routes([web.get(r'/{path}', proxy_with_emoji)])

web.run_app(app)
