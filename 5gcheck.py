#!/usr/bin/env python3
import atexit
import base64
import datetime
import os.path
import sys
import time
from signal import signal, SIGINT

import requests as requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from requests import HTTPError

public_key = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCyQHO0OklO8jRISTLvooaFWlwe
cQXlI8G0ssKSWl7Eeh3EUC4lzrwqCKpFSmMFbooXoTZRu4u99Ix9nSrkD51rO4v+
yIDO30GBMTVowmlTB0rk8/rtnMIeCUlVlt5EwAYafquQDy95kS8lQPrHLxT1VOVD
fFLX43W6JJ8BcXCzeQIDAQAB
-----END PUBLIC KEY-----
"""
started = datetime.datetime.now()


class Exiter:
    def __init__(self):
        self.counts = {}
        self.stats = {}
        self.max_modem_type_len = 0
        self.at_exit_run = False

    def record_data_point(self, data_point):
        modem_type = data_point['modemtype'].strip()
        self.max_modem_type_len = max(self.max_modem_type_len, len(modem_type))
        self.counts[modem_type] = self.counts[modem_type] + 1 if modem_type in self.counts else 1
        self.record_stats(modem_type, data_point)

    def record_stats(self, modem_type, data_point):
        rsrp = data_point['rsrp']
        sig = data_point['signal']
        if modem_type not in self.stats:
            self.stats[modem_type] = {
                'rsrp': {},
                'signal': {}
            }
        if rsrp not in self.stats[modem_type]['rsrp']:
            self.stats[modem_type]['rsrp'][rsrp] = 0
        self.stats[modem_type]['rsrp'][rsrp] += 1
        if sig not in self.stats[modem_type]['signal']:
            self.stats[modem_type]['signal'][sig] = 0
        self.stats[modem_type]['signal'][sig] += 1

    @staticmethod
    def on_signal(signal_received, frame):
        try:
            frame.f_locals['exiter'].on_exit()
        except KeyError:
            pass
        exit(0)

    def on_exit(self):
        global started
        duration = datetime.datetime.now() - started
        print(f"Ran for {duration}", file=sys.stderr)
        sys.stdout.flush()
        if not self.at_exit_run:
            self.at_exit_run = True
            file = sys.stderr
            print("\nSummary:", file=file)
            self.print_stats(self.counts, file=file, indent="  ")
            print("Statistics:", file=file)
            print("  rsrp:", file=file)
            for modem_type in self.stats:
                print(f"    {modem_type}:", file=file)
                self.print_stats(self.stats[modem_type]['rsrp'], file=file, indent="      ")
            print("  signal:", file=file)
            for modem_type in self.stats:
                print(f"    {modem_type}:", file=file)
                self.print_stats(self.stats[modem_type]['signal'], file=file, indent="      ")

    @staticmethod
    def print_stats(stats: dict(), file, indent=""):
        max_key_length = max([len(x) for x in stats.keys()])
        max_value_length = max([len(f"{x:,d}") for x in stats.values()])
        for key in sorted(stats.keys()):
            print(f"{indent}{key:.<{max_key_length}s}...{stats[key]:.>{max_value_length},d}", file=file)


def seconds_from(num_seconds, started_at):
    delta = datetime.datetime.now() - started_at
    return num_seconds - (delta.seconds - delta.microseconds / 1_000_000)


def main():
    auth_header = None
    secret_path = os.path.expanduser('~')
    secret_path += "/.5g-secret"
    if os.path.isfile(secret_path):
        with open(secret_path, 'r') as f:
            secret = f.readline().strip('\n')
            key_pair = RSA.importKey(public_key)
            encryptor = PKCS1_v1_5.new(key_pair)
            username = base64.b64encode(encryptor.encrypt(bytes("admin", 'utf-8')))
            password = base64.b64encode(encryptor.encrypt(bytes(secret, 'utf-8')))
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Enconding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
            }
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
                print(auth_header, file=sys.stderr)
            except HTTPError as error:
                print(f"Error using secret, trying command line arg...", file=sys.stderr)
    if not auth_header:
        if len(sys.argv) < 2:
            print("Please add the authentication cookie, or set up `~/.5g-secret`.", file=sys.stderr)
            print(f"Usage:  {os.path.basename(sys.argv[0])} <authorization cookie>", file=sys.stderr)
            exit(1)
        else:
            auth_header = sys.argv[1]
    exiter = Exiter()
    signal(SIGINT, exiter.on_signal)
    atexit.register(exiter.on_exit)
    headers = {
        'Accept': 'application/json',
        'Cookie': auth_header
    }
    try:
        while True:
            started_at = datetime.datetime.now()
            resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/network/getStatus", headers=headers)
            resp.raise_for_status()
            new_cookie = resp.headers['Set-Cookie']
            cookie_bits = new_cookie.split(';')
            auth_header = cookie_bits[0]
            headers = {
                'Accept': 'application/json',
                'Cookie': auth_header
            }
            resp = resp.json()
            exiter.record_data_point(resp)
            print("  ".join([
                f"{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                f"rsrp = {resp['rsrp']}",
                f"modemtype = {resp['modemtype']}",
                f"signal = {resp['signal']}"
            ]))
            sys.stdout.flush()
            time.sleep(max(seconds_from(2.0, started_at), 0))
    except KeyboardInterrupt:
        pass
    except TimeoutError:
        print("Request timed out, exiting...", file=sys.stderr)


if __name__ == '__main__':
    main()
