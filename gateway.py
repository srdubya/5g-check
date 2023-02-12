import base64
import logging
import os
import re
import sys
import time

import requests
from requests import HTTPError
# noinspection PyPackageRequirements
from Crypto.Cipher import PKCS1_v1_5
# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA


def _make_logger():
    logging.basicConfig(
        filename=os.path.expanduser('~/.5g-history.txt'),
        level=logging.INFO,
        format='%(asctime)s  %(message)s',
        datefmt="%Y/%m/%Y %I:%M:%S %p"
    )
    return logging.getLogger(os.path.basename(sys.argv[0]))


class Gateway:
    logger = _make_logger()
    _next_speedtest_hour = 5
    csrf_token = None

    @classmethod
    def advance_speedtest_hour(cls):
        cls._next_speedtest_hour += 12
        cls._next_speedtest_hour %= 24

    @classmethod
    def get_speedtest_hour(cls):
        return cls._next_speedtest_hour

    @classmethod
    def get_status(cls, auth_token):
        headers = cls._make_header(auth_token)
        resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/network/getStatus", headers=headers)
        resp.raise_for_status()
        new_cookie = resp.headers['Set-Cookie']
        cookie_bits = new_cookie.split(';')
        auth_token = cookie_bits[0]
        resp = resp.json()
        return auth_token, resp

    @classmethod
    def reboot(cls, auth_token):
        cls.logger.info("Initiating reboot...")
        headers = cls._make_header(auth_token)
        resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/reboot", headers=headers)
        resp.raise_for_status()
        cls.logger.info("...waiting")
        time.sleep(60 * 3)
        cls.logger.info("...reconnecting")
        try:
            return Gateway.sign_in()
        finally:
            cls.logger.info("...reboot complete")
            cls.csrf_token = None

    @classmethod
    def run_speed_test(cls, auth_token):
        cls.logger.info("Starting speed test...")
        if not cls.csrf_token:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Cookie': auth_token,
                'Host': '192.168.0.1',
                'Referer': 'http://192.168.0.1/cgi-bin/luci',
                'Upgrade-Insecure-Requests': '1',
            }
            resp = requests.get("http://192.168.0.1/cgi-bin/luci/", headers=headers)
            content = resp.content.decode(resp.encoding)
            match = re.search(r'.*<meta name="csrf-token" content="([0-9a-f]+)"/>.*', content)
            if match:
                cls.csrf_token = match.group(1)
        headers = cls._make_header(auth_token)
        headers['X-CSRF-TOKEN'] = cls.csrf_token
        resp = requests.post("http://192.168.0.1/cgi-bin/luci/verizon/speedtest", headers=headers, data="run=run", allow_redirects=True)
        resp.raise_for_status()
        new_cookie = resp.headers['Set-Cookie']
        cls.csrf_token = resp.headers['X-CSRF-TOKEN']
        cookie_bits = new_cookie.split(';')
        auth_token = cookie_bits[0]
        resp = resp.json()
        cls.logger.info(f"...response:  download: {resp['download']} Mb/s  upload: {resp['upload']} Mb/s")
        cls.logger.info(f"               latency: {resp['ping']}  jitter: {resp['jitter']}")
        return auth_token, {
            'download': resp['download'],
            'upload': resp['upload'],
            'latency': resp['ping'],
            'jitter': resp['jitter']
        }

    @classmethod
    def format_speed_data(cls, speed_data):
        return "\n".join([
            f"download..{float(speed_data['download']):.>8,.2f} MB/s",
            f"upload....{float(speed_data['upload']):.>8,.2f} MB/s",
            f"latency...{float(speed_data['latency']):.>8,.2f} ms",
            f"jitter....{float(speed_data['jitter']):.>8,.2f} ms",
            ])

    @classmethod
    def _make_header(cls, auth_token):
        headers = {
            'Accept': 'application/json, text/javascript, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-us, en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': auth_token,
            'Host': '192.168.0.1',
            'Origin': 'http://192.168.0.1',
            'Referer': 'http://192.168.0.1/cgi-bin/luci/',
            'sec-gpc': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        return headers

    @classmethod
    def sign_in(cls, output_file=sys.stderr):
        auth_token = None
        secret_path = os.path.expanduser('~')
        secret_path += "/.5g-secret"
        if os.path.isfile(secret_path):
            with open(secret_path, 'r') as f:
                secret = f.readline().strip('\n')
                headers = {
                    "Accept": ",".join([
                        "text/html",
                        "application/xhtml+xml",
                        "application/xml;q=0.9",
                        "image/avif",
                        "image/webp",
                        "image/apng",
                        "*/*;q=0.8",
                        "application/signed-exchange;v=b3;q=0.9"
                    ]),
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/sentPublicKey")
                resp.raise_for_status()
                public_key = resp.json()
                key_pair = RSA.importKey(public_key)
                encryptor = PKCS1_v1_5.new(key_pair)
                username = base64.b64encode(encryptor.encrypt(bytes("admin", 'utf-8')))
                password = base64.b64encode(encryptor.encrypt(bytes(secret, 'utf-8')))
                data = {
                    'luci_username': username,
                    'luci_password': password
                }
                try:
                    resp = requests.post("http://192.168.0.1/cgi-bin/luci/", data, headers=headers)
                    resp.raise_for_status()
                    new_cookie = resp.headers['Set-Cookie']
                    cookie_bits = new_cookie.split(';')
                    auth_token = cookie_bits[0]
                    print(auth_token, file=output_file)
                except HTTPError as error:
                    print(f"Error using secret ({error}), trying command line arg...", file=sys.stderr)
        return auth_token
