#!/usr/bin/env python3
import datetime
import os.path
import sys
import time

import requests as requests
# import rsa
# import urllib
# from rsa import PublicKey

public_key = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDGKAHl+/ayHj031E/l/08ScLFb
p9/jcLqAQJjbq6IDXiLeo23gXmlf3OwMpQlmQQLuOOBEizCHXKOgXn7HIfmonV5P
qaCV72ot6N4ZO4FnYtdbun91rAYb1wq6s2Uyu6JuBomeMViapw4TPKv37GqLoAeF
HNHwtHyPIJ14pT8HywIDAQAB
-----END PUBLIC KEY-----
'''


def main():
    # pub_key = PublicKey.load_pkcs1_openssl_pem(bytes(public_key, 'utf-8'))
    # username = rsa.encrypt(bytes('admin', 'utf8'), pub_key)
    # password = rsa.encrypt('Won4der2.'.encode('utf8'), pub_key)
    # resp = requests.post("http://192.168.0.1/cgi-bin/luci", data=urllib.parse.urlencode({
    #     'luci_username': username,
    #     'luci_password': password
    # }), headers={
    #     'Content-Type': 'application/x-www-form-urlencoded'
    # })
    if len(sys.argv) < 2:
        print("Please add the authentication cookie.")
        print(f"Usage:  {os.path.basename(sys.argv[0])} <authorization cookie>")
        exit(1)
    headers = {
        'Accept': 'application/json',
        'Cookie': sys.argv[1]
    }
    try:
        while True:
            resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/network/getStatus", headers=headers)
            new_cookie = resp.headers['Set-Cookie']
            cookie_bits = new_cookie.split(';')
            headers = {
                'Accept': 'application/json',
                'Cookie': cookie_bits[0]
            }
            resp = resp.json()
            print(f"{datetime.datetime.now()}  rsrp = {resp['rsrp']}  modemtype = {resp['modemtype']}  signal = {resp['signal']}")
            sys.stdout.flush()
            time.sleep(5)
    except KeyboardInterrupt:
        sys.stdout.flush()
    except TimeoutError:
        print("Request timed out, exiting...", file=sys.stderr)
        sys.stdout.flush()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
