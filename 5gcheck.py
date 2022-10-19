#!/usr/bin/env python3
import atexit
import datetime
import os.path
import sys
import time
from signal import signal, SIGINT

import requests as requests


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
        max_value_length = max([len(str(x)) for x in stats.values()])
        for key in sorted(stats.keys()):
            print(f"{indent}{key:.<{max_key_length}s}..{stats[key]:.>{max_value_length},d}", file=file)


def main():
    if len(sys.argv) < 2:
        print("Please add the authentication cookie.", file=sys.stderr)
        print(f"Usage:  {os.path.basename(sys.argv[0])} <authorization cookie>", file=sys.stderr)
        exit(1)
    exiter = Exiter()
    signal(SIGINT, exiter.on_signal)
    atexit.register(exiter.on_exit)
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
            exiter.record_data_point(resp)
            print("  ".join([
                f"{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                f"rsrp = {resp['rsrp']}",
                f"modemtype = {resp['modemtype']}",
                f"signal = {resp['signal']}"
            ]))
            sys.stdout.flush()
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    except TimeoutError:
        print("Request timed out, exiting...", file=sys.stderr)


if __name__ == '__main__':
    main()
