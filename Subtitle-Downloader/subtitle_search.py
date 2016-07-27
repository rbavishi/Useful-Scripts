#!/usr/bin/env python

import sys
from select import select

# Output Channel definitions
INPUT_CHANNEL = sys.stdin
OUTPUT_CHANNEL = sys.stderr

# Screen cursor related escapes
MOVE_UP = '\033[F'

# Keys
RETURN = '\r'
NEWLINE = '\n'
BACKSPACE = '\x7f'

# Colors
DEFAULT = '\033[0m'

FORE_BLACK = '\033[30m'
FORE_RED = '\033[31m'
FORE_GREEN = '\033[32m'
FORE_YELLOW = '\033[33m'
FORE_BLUE = '\033[34m'
FORE_MAGENTA = '\033[35m'
FORE_CYAN = '\033[36m'
FORE_WHITE = '\033[37m'

BACK_BLACK = '\033[40m'
BACK_RED = '\033[41m'
BACK_GREEN = '\033[42m'
BACK_YELLOW = '\033[43m'
BACK_BLUE = '\033[44m'
BACK_MAGENTA = '\033[45m'
BACK_CYAN = '\033[46m'
BACK_WHITE = '\033[47m'

# Formatting
BOLD = '\033[1m'

# Decoration
PROMPT = ' %s%s>> %s'%(FORE_RED, BOLD, DEFAULT)

def moveUp(numLines):
    for count in xrange(numLines):
        OUTPUT_CHANNEL.write(MOVE_UP)

def formatText(text, fore="", back="", style=""):
    return "%s%s%s"%(fore, back, style) + text + "%s"%DEFAULT

def subtitleSearch():
    argv = sys.argv[1:]

    # set raw input mode if relevant
    # it is necessary to make stdin not wait for enter
    try:
        import tty, termios

        prev_flags = termios.tcgetattr(INPUT_CHANNEL.fileno())
        tty.setraw(INPUT_CHANNEL.fileno())
    except ImportError:
        prev_flags = None

    inpBuf = ''
    OUTPUT_CHANNEL.write(PROMPT + '\r')

    while True: # main loop, reading input until ENTER
        rl, wl, xl = select([INPUT_CHANNEL], [], [])
        if rl: # some input
            inpChar = INPUT_CHANNEL.read(1)
            if inpChar in (RETURN, NEWLINE):
                break

            if inpChar == BACKSPACE:
                clearString = " " * (len(PROMPT) + len(inpBuf))
                OUTPUT_CHANNEL.write(clearString + "\r")

                inpBuf = inpBuf[:-1]

            else:
                inpBuf += inpChar

            OUTPUT_CHANNEL.write(PROMPT + formatText(inpBuf, fore=FORE_YELLOW, style=BOLD) + '\n\r')
            OUTPUT_CHANNEL.write(inpBuf + '\n\r')
            moveUp(2)
            OUTPUT_CHANNEL.write('\r')

        else:
            break

    # restore non-raw input
    if prev_flags is not None:
        termios.tcsetattr(INPUT_CHANNEL.fileno(), termios.TCSADRAIN, prev_flags)
    # and print newline
    OUTPUT_CHANNEL.write('\n')
