#!/usr/bin/env python3
import base64
import os
import sys

import requests

from requests import HTTPError
# noinspection PyPackageRequirements
from Crypto.Cipher import PKCS1_v1_5
# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA


def sign_in(output_file=sys.stderr):
    auth_header = None
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
                auth_header = cookie_bits[0]
                print(auth_header, file=output_file)
            except HTTPError as error:
                print(f"Error using secret ({error}), trying command line arg...", file=sys.stderr)
    return auth_header


if __name__ == '__main__':
    sign_in(output_file=sys.stdout)
