#!/usr/bin/env python3
"""Wait for the campus to load, then start a solo, untimed exploration session."""

import argparse
from pathlib import Path
import re
import socket
import time

try:
    from .cs2_console import run
except ImportError:
    from cs2_console import run


MAP = 'trento_povo_campus'
SETTINGS = (
    'sv_cheats 1',
    'r_always_render_all_windows true',
    'bot_quota 0', 'bot_kick',
    'mp_autoteambalance 0', 'mp_limitteams 0',
    'mp_team_intro_time 0', 'mp_freezetime 0',
    'mp_ignore_round_win_conditions 1', 'mp_timelimit 0',
    'mp_respawn_on_death_t 1', 'mp_respawn_on_death_ct 1',
    'mp_warmup_offline_enabled 1', 'mp_warmup_online_enabled 1',
    'mp_warmuptime_all_players_connected 0',
    'mp_warmup_pausetimer 1', 'mp_warmuptime 60',
    'jointeam 2', 'mp_warmup_start',
)


def campus_loaded(status):
    return (re.search(r'@ Current\s*:\s*game\b', status) is not None
            and f': {MAP} | main lump | mapload]' in status)


def explore(*, port=27400, timeout=90, fly=False, log=None):
    deadline = time.monotonic() + timeout
    transcript = []
    print('Waiting for the Povo campus to finish loading...', flush=True)
    while time.monotonic() < deadline:
        try:
            status = run(['status'], port=port, seconds=.3)
        except (OSError, socket.timeout):
            time.sleep(.5)
            continue
        if campus_loaded(status):
            break
        time.sleep(.5)
    else:
        raise RuntimeError('Campus did not become ready; check that CS2 loaded trento_povo_campus.')
    transcript.append(status)
    transcript.append(run(SETTINGS, port=port, seconds=2))
    # Joining and warmup create the player asynchronously. Apply player-local
    # settings after spawning; a second bot kick catches any pending bot joins.
    transcript.append(run(['bot_quota 0', 'bot_kick', 'mp_warmup_start', 'god 1',
                           'noclip 1' if fly else 'noclip 0',
                           'slot3', 'setang 0 -90 0',
                           'mp_warmup_pausetimer', 'status', 'getpos_exact'],
                          port=port, seconds=1))
    text = '\n'.join(transcript)
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(text, encoding='utf-8')
    if not re.search(r'players\s*:\s*1 humans, 0 bots\b', transcript[-1]):
        raise RuntimeError('Could not verify a solo session. See the exploration log.')
    print('Solo exploration ready: no bots, paused warmup, automatic respawn.', flush=True)
    print('Walk normally; open the developer console and enter noclip to toggle flying.', flush=True)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=27400)
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--fly', action='store_true')
    parser.add_argument('--log', type=Path)
    args = parser.parse_args()
    try:
        explore(port=args.port, timeout=args.timeout, fly=args.fly, log=args.log)
    except (OSError, RuntimeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
