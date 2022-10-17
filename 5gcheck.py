#!/usr/bin/env python3
import datetime
import os.path
import sys
import time

import requests as requests


def main():
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


if __name__ == '__main__':
    main()
