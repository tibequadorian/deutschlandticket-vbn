import hmac
import hashlib
import requests
from urllib.parse import urlparse
import locale
from time import gmtime, strftime
from bs4 import BeautifulSoup
import urllib.request
import base64
import json

# Import login credentials
from login import username, password

# Set date format
locale.setlocale(locale.LC_TIME, 'en_US')
dateformat = '%a, %d %b %Y %H:%M:%S GMT'

# API Secret
secret = b'dohCeewoghAX1Wah2Us8'

# User Agent
user_agent = "VBN Android Mobile-Shop/6.3.4 (78)/2019.12/vbn-live (unknown generic_x86_64 - 'Android SDK built for x86_64'; Android; 9, SDK: 28)"
device_id = '1dd817743297a7584d5a15dacdec2e81147105a1'


def get_signature(msg, key):
    return hmac.new(key, bytearray(msg, encoding='utf8'), hashlib.sha512).hexdigest()


def request(url_string, content, add_headers={}):
    content_string = json.dumps(content, separators=(',', ':'))
    content_signature = get_signature(content_string, secret)

    url = urlparse(url_string)
    datetime_str = strftime(dateformat, gmtime())

    headers = {
        'Accept-Language': 'en',
        'Accept-Charset': 'utf-8',
        'User-Agent': user_agent,
        'Content-Type': 'application/json; charset=utf-8',
        'Device-Identifier': device_id,
        'X-Eos-Date': datetime_str,
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    } | add_headers

    message = f"{content_signature}|{url.hostname}|{url.port}|{url.path}|{headers.get('X-Eos-Date', '')}|{headers.get('Content-Type', '')}|{headers.get('Authorization', '')}|{headers.get('X-TickEOS-Anonymous', '')}|{headers.get('X-EOS-SSO', '')}|{headers.get('User-Agent', '')}"
    headers['X-Api-Signature'] = get_signature(message, secret)

    return requests.post(url_string, headers=headers, data=content_string)


def login_request(username, password):
    return request("https://shop.vbn.de:443/index.php/mobileService/login", {'credentials':{'password':password,'username':username}})


def sync_request(auth):
    return request("https://shop.vbn.de:443/index.php/mobileService/sync", {'anonymous_tickets':[]}, add_headers={'Authorization': auth})


def ticket_request(auth, content):
    return request("https://shop.vbn.de:443/index.php/mobileService/ticket", content, add_headers={'Authorization': auth})


# login
res = login_request(username, password).json()
auth = res['authorization_types'][0]['header']
auth = f"{auth['type']} {auth['value']}"

# sync
res = sync_request(auth).json()
ticket = res['tickets'][0]

# ticket
content = {
    'details': True,
    'parameters': True,
    'provide_aztec_content': True,
    'tickets': [ ticket ]
}
res = ticket_request(auth, content).json()

template = res['tickets'][ticket]['template']
template = json.loads(template)

html_page = template['content']['pages'][0]
soup = BeautifulSoup(html_page, 'html.parser')

barcode = soup.find('img', attrs={'class':'barcode'})['src']
res = urllib.request.urlopen(barcode)

with open('barcode.png', 'wb') as f:
    f.write(res.file.read())
