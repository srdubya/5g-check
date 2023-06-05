#!/usr/bin/env python3
import atexit
import datetime
import os.path
import sys
import time
from signal import signal, SIGINT
from typing import Dict

from requests import HTTPError

from gateway import Gateway

started = datetime.datetime.now()


class Exiter:
    logger = Gateway.logger

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
        self.logger.info("  ".join([
            # f"{datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
            f"reboots = {self.reboots}",
            f"rsrp = {data_point['rsrp']}",
            f"signal = {data_point['signal']}",
            f"modemtype = {modem_type}",
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


def seconds_from(num_seconds, started_at):
    delta = datetime.datetime.now() - started_at
    return num_seconds - (delta.seconds - delta.microseconds / 1_000_000)


def within_reboot_window():
    start_hour = 1
    end_hour = 5
    now = datetime.datetime.now()
    return start_hour <= now.hour <= end_hour


def main():
    exiter = Exiter()
    signal(SIGINT, exiter.on_signal)
    atexit.register(exiter.on_exit)

    while True:
        try:
            auth_header = Gateway.sign_in()
            if not auth_header:
                if len(sys.argv) < 2:
                    print("Please add the authentication cookie, or set up `~/.5g-secret`.", file=sys.stderr)
                    print(f"Usage:  {os.path.basename(sys.argv[0])} <authorization cookie>", file=sys.stderr)
                    exit(1)
                else:
                    auth_header = sys.argv[1]
            count_4g = 0
            auth_header = run_speed_test(auth_header)
            while True:
                started_at = datetime.datetime.now()
                auth_header, resp = Gateway.get_status(auth_header)
                modem_type = exiter.record_data_point(resp)
                if modem_type != '5G' and modem_type != 'N/A' and within_reboot_window():
                    count_4g += 1
                    if count_4g > 5:
                        print("")
                        auth_header = run_speed_test(auth_header)
                        auth_header = Gateway.reboot(auth_header)
                        exiter.record_reboot()
                    else:
                        wait_a_while(started_at)
                else:
                    count_4g = 0
                    try:
                        if modem_type == '5G' and started_at.hour == Gateway.get_speedtest_hour():
                            Gateway.advance_speedtest_hour()
                            auth_header = run_speed_test(auth_header)
                        else:
                            wait_a_while(started_at)
                    except HTTPError as error:
                        print(f"\nFailed to run speed test:  {error.response.reason}")

        except KeyboardInterrupt:
            break
        except TimeoutError:
            print("\nRequest timed out, sleeping for a minute before retrying...", file=sys.stderr)
            time.sleep(60)
        except HTTPError as error:
            print(f"\nHTTPError({error.response.reason}), sleeping for a minute before retrying...", file=sys.stderr)
            time.sleep(60)
        except KeyError:
            print(f"\nGot a wonky return from the 5G Gateway, sleeping for a minute before retrying...", file=sys.stderr)
            time.sleep(60)


def run_speed_test(auth_header):
    auth_header, speed_data = Gateway.run_speed_test(auth_header)
    print()
    print(Gateway.format_speed_data(speed_data))
    print()
    return auth_header


def wait_a_while(started_at):
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


if __name__ == '__main__':
    main()
