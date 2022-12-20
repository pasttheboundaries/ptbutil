import re

URL_PATTERN = r'(http|https)://\w+\.\w{1,10}(:\d{1,6})?(/\w+)*(\.\w+|\?(\w+=\w+&?)*)?$'


def validate_http_url(url):
    if not isinstance(url, str):
        raise TypeError('url must be type str')
    if not re.fullmatch(URL_PATTERN, url):
        raise ValueError(f'Invalid html url : {url}')
    return True
