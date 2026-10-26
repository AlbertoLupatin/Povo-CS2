#!/usr/bin/env python3
"""Send local playtest commands to CS2 launched with -netconport 27400."""

import argparse
from pathlib import Path
import socket
import time


def run(commands, *, port=27400, seconds=2):
    chunks = []
    with socket.create_connection(('127.0.0.1', port), timeout=5) as connection:
        connection.settimeout(0.2)
        for command in commands:
            connection.sendall((command + '\n').encode('utf-8'))
        until = time.monotonic() + min(60, max(0.2, seconds))
        while time.monotonic() < until:
            try:
                data = connection.recv(65536)
            except socket.timeout:
                continue
            if not data:
                break
            chunks.append(data)
    return b''.join(chunks).decode('utf-8', errors='replace')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commands', nargs='+')
    parser.add_argument('--port', type=int, default=27400)
    parser.add_argument('--seconds', type=float, default=2)
    parser.add_argument('--log', type=Path)
    args = parser.parse_args()
    output = run(args.commands, port=args.port, seconds=args.seconds)
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        with args.log.open('a', encoding='utf-8') as stream:
            stream.write('\n> ' + '\n> '.join(args.commands) + '\n' + output)
    print(output, end='')


if __name__ == '__main__':
    main()
