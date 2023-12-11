import argparse
import base64
from babel.dates import format_datetime
from bs4 import BeautifulSoup
import configparser
import datetime
import hashlib
import hmac
import json
import requests
import secrets
import sys
from urllib.parse import urlparse
from urllib.request import urlopen

config_filename = 'vbn.cfg'
ticket_filename = 'tickets.json'

# API Secret
secret = b'dohCeewoghAX1Wah2Us8'

# User Agent
user_agent = "VBN Android Mobile-Shop/6.3.4 (78)/2019.12/vbn-live (unknown generic_x86_64 - 'Android SDK built for x86_64'; Android; 9, SDK: 28)"

def gen_device_id():
    return secrets.token_hex(20)

def get_signature(msg, key):
    return hmac.new(key, bytearray(msg, encoding='utf8'), hashlib.sha512).hexdigest()

def request(url_string, content, add_headers={}):
    content_string = json.dumps(content, separators=(',', ':'))
    content_signature = get_signature(content_string, secret)

    url = urlparse(url_string)
    current_time = datetime.datetime.utcnow()
    datetime_str = format_datetime(current_time, format='EEE, dd MMM yyyy HH:mm:ss', locale='en')+' GMT'

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


if __name__ == '__main__':

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='downloads mobile tickets from VBN',
    )

    subparsers = parser.add_subparsers(dest='action')

    login_subparser = subparsers.add_parser('login', help='login to VBN')
    login_subparser.add_argument('email')
    login_subparser.add_argument('password')

    export_subparser = subparsers.add_parser('export', help='export tickets to image')

    sync_subparser = subparsers.add_parser('sync', help='synchronize tickets')

    config = configparser.ConfigParser()
    config.read(config_filename)

    args = parser.parse_args()

    if args.action == 'login':
        # read config
        if not config.has_section('client'):
            config.add_section('client')
        device_id = config.get('client', 'device_id', fallback=gen_device_id())

        # login
        res = login_request(args.email, args.password)
        if res.status_code != requests.codes.ok:
            # error handling
            res_data = res.json()
            print(f"Error: {res_data['message']}", file=sys.stderr)
            exit(1)

        # extract auth token
        print("Login successful!", file=sys.stderr)
        res_data = res.json()
        auth_header = res_data['authorization_types'][0]['header']
        auth_token = f"{auth_header['type']} {auth_header['value']}"

        # write to config
        config.set('client', 'auth_token', auth_token)
        config.set('client', 'device_id', device_id)
        with open(config_filename, 'w') as config_file:
            config.write(config_file)

    elif args.action == 'sync':
        if not config.has_section('client') or \
           not config.has_option('client', 'auth_token') or \
           not config.has_option('client', 'device_id'):
            print("No client configuration found, try login first.", file=sys.stderr)
            exit(1)

        auth_token = config.get('client', 'auth_token')
        device_id = config.get('client', 'device_id')

        # sync
        res = sync_request(auth_token)
        res_data = res.json()
        tickets = res_data['tickets']

        content = {
            'details': True,
            'parameters': True,
            'provide_aztec_content': True,
            'tickets': tickets
        }
        res = ticket_request(auth_token, content)
        content = res.content.decode('utf-8')

        print("Sync successful!", file=sys.stderr)

        # write to file
        with open(ticket_filename, 'w') as ticket_file:
            ticket_file.write(content)

    elif args.action == 'export':
        try:
            ticket_file = open(ticket_filename, 'r')
        except:
            print("No tickets found, try synchronizing first.", file=sys.stderr)
            exit(1)

        tickets = json.load(ticket_file)

        for ticket in tickets['tickets']:
            ticket_content = tickets['tickets'][ticket]

            meta = json.loads(ticket_content['meta'])
            validity_begin = meta['validity_begin']

            template = json.loads(ticket_content['template'])
            html_page = template['content']['pages'][0]
            soup = BeautifulSoup(html_page, 'html.parser')
            barcode_url = soup.find('img', attrs={'class':'barcode'})['src']
            barcode_png = urlopen(barcode_url).read()

            barcode_filename = f'{validity_begin[:7]}_{ticket[4:]}.png'
            with open(barcode_filename, 'wb') as barcode_file:
                barcode_file.write(barcode_png)

            print(f"Ticket export to {barcode_filename} successful!", file=sys.stderr)

    else:
        parser.print_help()
