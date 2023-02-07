#!/usr/bin/env python3
import sys

from gateway import Gateway

if __name__ == '__main__':
    Gateway.sign_in(output_file=sys.stdout)
