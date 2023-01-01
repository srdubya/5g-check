#!/usr/bin/env python3
import atexit
import datetime
import logging
import math
import os.path
import sys
import time
from signal import signal, SIGINT
from typing import Dict

import requests as requests

from signin5g import sign_in

started = datetime.datetime.now()
logging.basicConfig(
    filename=os.path.expanduser('~/.5g-history.txt'),
    level=logging.INFO,
    format='%(asctime)s  %(message)s',
    datefmt="%Y/%m/%Y %I:%M:%S %p"
)
logger = logging.getLogger(os.path.basename(sys.argv[0]))


class Exiter:
    def __init__(self):
        self.reboots = 0
        self.counts = {}
        self.stats = {}
        self.max_modem_type_len = 0
        self.at_exit_run = False

    def record_data_point(self, data_point):
        modem_type = data_point['modemtype'].strip()
        colored_modem_type = modem_type
        if modem_type == '5G':
            colored_modem_type = f'\033[92m{modem_type}\033[39m'
        print("  ".join([
            f"\033[2K\r"
            f"{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
            f"reboots = {self.reboots}",
            f"rsrp = {data_point['rsrp']}",
            f"signal = {data_point['signal']}",
            f"modemtype = {colored_modem_type}",
        ]), end="")
        logger.info("  ".join([
            # f"{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
            f"reboots = {self.reboots}",
            f"rsrp = {data_point['rsrp']}",
            f"signal = {data_point['signal']}",
            f"modemtype = {colored_modem_type}",
        ]))
        sys.stdout.flush()
        self.max_modem_type_len = max(self.max_modem_type_len, len(modem_type))
        self.counts[modem_type] = self.counts[modem_type] + 1 if modem_type in self.counts else 1
        self.record_stats(modem_type, data_point)
        return modem_type

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
            print(f'KeyError for `exiter` while handling signal `{signal_received}`', file=sys.stderr)
        exit(0)

    def on_exit(self):
        global started
        duration = datetime.datetime.now() - started
        print(f"\nRan for {duration}", file=sys.stderr)
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
    def print_stats(stats: Dict[str, int], file, indent=""):
        max_key_length = max([len(x) for x in stats.keys()])
        max_value_length = max([len(f"{x:,d}") for x in stats.values()])
        for key in sorted(stats.keys()):
            print(f"{indent}{key:.<{max_key_length}s}...{stats[key]:.>{max_value_length},d}", file=file)

    def record_reboot(self):
        self.reboots += 1


def reboot(headers):
    logger.info("Initiating reboot...")
    resp = requests.get("http://192.168.0.1/cgi-bin/luci/verizon/reboot", headers=headers)
    resp.raise_for_status()
    logger.info("...waiting")
    time.sleep(60 * 3)
    logger.info("...reconnecting")
    try:
        return sign_in()
    finally:
        logger.info("...reboot complete")


def seconds_from(num_seconds, started_at):
    delta = datetime.datetime.now() - started_at
    return num_seconds - (delta.seconds - delta.microseconds / 1_000_000)


def within_reboot_window():
    start_hour = 1
    end_hour = 5
    now = datetime.datetime.now()
    return start_hour <= now.hour <= end_hour


def main():
    auth_header = sign_in()
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
            modem_type = exiter.record_data_point(resp)
            if modem_type != '5G' and within_reboot_window():
                print("")
                headers = {
                    'Accept': 'application/json',
                    'Cookie': reboot(headers)
                }
                exiter.record_reboot()
            else:
                while True:
                    time_left = round(max(seconds_from(10.0, started_at), 0))
                    time_left_str = f'  {time_left}  '
                    print(f"\033[0K{time_left_str}", end="")
                    sys.stdout.flush()
                    if time_left > 0:
                        time.sleep(1)
                        print(f"\033[{len(time_left_str)}D", end="")
                        continue
                    break
    except KeyboardInterrupt:
        pass
    except TimeoutError:
        print("Request timed out, exiting...", file=sys.stderr)


if __name__ == '__main__':
    main()
