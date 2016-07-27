#!/usr/bin/env python

import sys
from select import select

def main():
    argv = sys.argv[1:]
    prompt = '> '
    max_chars = 150

    # set raw input mode if relevant
    # it is necessary to make stdin not wait for enter
    try:
        import tty, termios

        prev_flags = termios.tcgetattr(sys.stdin.fileno())
        tty.setraw(sys.stdin.fileno())
    except ImportError:
        prev_flags = None

    buf = ''

    while True: # main loop
        rl, wl, xl = select([sys.stdin], [], [])
        if rl: # some input
            c = sys.stdin.read(1)
            # you will probably want to add some special key support
            # for example stop on enter:
            if c == '\n' or c == '\r':
                break


            # auto-output is disabled as well, so you need to print it

            if c == '\x7f':
                sys.stderr.write((len(prompt + buf) * " ") + "\r")
                buf = buf[:-1]
            else:
                buf += c

            sys.stderr.write(prompt + buf + '\n')
            sys.stderr.write('\r')
            sys.stderr.write(buf + '\n')
            sys.stderr.write(c + '\n')
            sys.stderr.write('\r')
            sys.stderr.write('\033[F')
            sys.stderr.write('\033[F')
            sys.stderr.write('\033[F')
            sys.stderr.write('\r')

            # stop if N characters
            if len(buf) >= max_chars:
                break
        else:
            # timeout
            break

    # restore non-raw input
    if prev_flags is not None:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, prev_flags)
    # and print newline
    sys.stderr.write('\n')

    # now buf contains your input
    # ...
