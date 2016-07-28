#!/usr/bin/env python

import sys
import os
import urllib2
import operator
import tty, termios
from fuzzywuzzy import process
from bs4 import BeautifulSoup
from select import select

# Output Channel definitions
INPUT_CHANNEL = sys.stdin
OUTPUT_CHANNEL = sys.stderr

# Important flags
PREV_FLAGS = ''

# Screen cursor related escapes
MOVE_UP = '\033[F'
ERASE_LINE = '\x1b[2K'

# Keys
RETURN = '\r'
NEWLINE = '\n'
BACKSPACE = '\x7f'
TAB = '\t'

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
BLINK = '\033[5m'

# Decoration
TITLE_PROMPT = '%s%sEnter title >> %s'%(FORE_CYAN, BOLD, DEFAULT)
SELECT_PROMPT = '%s%s>> %s'%(FORE_RED, BOLD, DEFAULT)
BLINKING_CURSOR = '%s%s_%s'%(BLINK, BACK_WHITE, DEFAULT)

def moveUp(numLines):
    for count in xrange(numLines):
        OUTPUT_CHANNEL.write(MOVE_UP)

def formatText(text, fore="", back="", style=""):
    return "%s%s%s"%(fore, back, style) + text + "%s"%DEFAULT

def titleQuery(query):
    query = query.replace(' ','%20').replace('\n', '%20').replace('\t', '%20')

    url = 'http://subscene.com/subtitles/release?q=%s'%(query)
    req = urllib2.Request(url, headers={'User-Agent':'Mozilla'})
    resp = urllib2.urlopen(req)
    respSoup = BeautifulSoup(resp.read(), "html.parser")
    result = resp.geturl()

    if not 'release' in result: # We got to pick from the titles
        titles_html = respSoup('div',{'class':'search-result'})[0].find_all('ul')
        titles = reduce(operator.add, [map(lambda x : x.text, [items for items in curList.find_all('a')]) for curList in titles_html])
        links = reduce(operator.add, [map(lambda x : x['href'], [items for items in curList.find_all('a')]) for curList in titles_html])
        titles = map(lambda x : x.replace("\t", "").replace("\n", "").replace("\r", ""), titles)

        title_link_dict = dict(zip(titles, links))
        print formatText("\r%d suitable titles found. Please select one"%(len(titles)), fore=FORE_CYAN, style=BOLD)

        selTitle = selectWithSuggestions(titles, SELECT_PROMPT)
        selLink = title_link_dict[selTitle]
        print formatText("\rRequested Title : %s\n\rFetching subtitle list"%(selTitle), fore=FORE_GREEN, style=BOLD)

        # Now fetch the subtitle list
        url = 'http://subscene.com' + selLink
        req = urllib2.Request(url, headers={'User-Agent':'Mozilla'})
        respSoup = BeautifulSoup(urllib2.urlopen(req), "html.parser")
        byFilm = respSoup('div',{'class':'subtitles byFilm'})[0]
        subtitles = byFilm.find_all('td',{'class':'a1'})

    else:
        contentTag = respSoup('div',{'class':'content'})[0]
        subtitles = contentTag.find_all('td',{'class':'a1'})

    relevantSubs = []
    for subtitle in subtitles:
        details = subtitle.find_all('span')
        language = details[0].text.replace('\r', '').replace('\n', '').replace('\t', '')
        name = details[1].text.replace('\r', '').replace('\n', '').replace('\t', '')
        link = subtitle.find_all('a')[0]['href']
        relevantSubs += [[language, name, link]]

    relevantSubs = filter(lambda x : "English" in x[0], relevantSubs)
    if len(relevantSubs) == 0:
        print formatText("\r No subtitles found. Sorry!", fore=FORE_RED, style=BOLD)
        sys.exit(1)

    print formatText("\r%d English subtitles found. Please select one"%(len(relevantSubs)), fore=FORE_CYAN, style=BOLD)
    return relevantSubs


def enterTitle(prompt):
    inpBuf = ''
    PROMPT = prompt
    OUTPUT_CHANNEL.write('\r' + PROMPT + BLINKING_CURSOR + '\r')

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

            elif inpChar == '\003':
                OUTPUT_CHANNEL.write('\n')
                raise KeyboardInterrupt

            elif inpChar != TAB:
                inpBuf += inpChar


            OUTPUT_CHANNEL.write(PROMPT + formatText(inpBuf, fore=FORE_YELLOW, style=BOLD) + BLINKING_CURSOR + '\n\r')
            moveUp(1)
            OUTPUT_CHANNEL.write('\r')

        else:
            break

    return inpBuf

def displaySelectSuggestions(candidates, numEntries, curSelection=0):
    limit = min(len(candidates), numEntries)
    for count in xrange(limit):
        OUTPUT_CHANNEL.write('\r' + ERASE_LINE)
        if count == curSelection:
            OUTPUT_CHANNEL.write(formatText('\r%s\n'%(candidates[count]), fore=FORE_BLACK, back=BACK_WHITE, style=BOLD))
        else:
            OUTPUT_CHANNEL.write('\r%s\n'%(candidates[count]))

    moveUp(limit + 2) # To account for the prompt and border
    OUTPUT_CHANNEL.write('\r')


def selectWithSuggestions(candidates, prompt, numEntries=5, returnValues=[]):
    inpBuf = ''
    PROMPT = prompt

    border = "=" * ((sum([len(candidate) for candidate in candidates])/len(candidates)) + 5)
    OUTPUT_CHANNEL.write('\r' + PROMPT + BLINKING_CURSOR + '\n\r')
    OUTPUT_CHANNEL.write(formatText(border, fore=FORE_MAGENTA) + '\n\r')

    displaySelectSuggestions(candidates, numEntries)
    curSelection = 0
    initialCandidatesCopy = candidates[:]

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
                if not inpBuf:
                    candidates = initialCandidatesCopy
                else:
                    candidates = map(lambda x : x[0], process.extract(inpBuf, candidates, limit=len(candidates)))

            elif inpChar == TAB:
                curSelection = (curSelection + 1) % numEntries

            elif inpChar == '>':
                if numEntries < len(candidates):
                    numEntries += 5

            elif inpChar == '<':
                newNumEntries = max(5, numEntries - 5)
                for count in xrange(newNumEntries + 1):
                    OUTPUT_CHANNEL.write("\n")
                for count in xrange(numEntries - newNumEntries):
                    OUTPUT_CHANNEL.write("\r" + ERASE_LINE + "\n")

                moveUp(numEntries + 1)
                numEntries = newNumEntries
                curSelection = curSelection % numEntries

            elif inpChar == '\003':
                limit = min(len(candidates), numEntries)
                for count in xrange(limit + 2):
                    OUTPUT_CHANNEL.write("\r" + ERASE_LINE + "\n")

                moveUp(limit + 2)

                raise KeyboardInterrupt

            else:
                inpBuf += inpChar
                if not inpBuf:
                    candidates = initialCandidatesCopy
                else:
                    candidates = map(lambda x : x[0], process.extract(inpBuf, candidates, limit=len(candidates)))

            OUTPUT_CHANNEL.write(PROMPT + formatText(inpBuf, fore=FORE_YELLOW, style=BOLD) + BLINKING_CURSOR + '\n\r')
            OUTPUT_CHANNEL.write(formatText(border, fore=FORE_MAGENTA) + '\n\r')
            displaySelectSuggestions(candidates, numEntries, curSelection)

        else:
            break


    limit = min(len(candidates), numEntries)
    for count in xrange(limit + 2):
        OUTPUT_CHANNEL.write("\r" + ERASE_LINE + "\n")

    moveUp(limit + 2)

    if returnValues:
        return candidates[curSelection], returnValues[curSelection]
    else:
        return candidates[curSelection]

def subtitleSearch(argv):
    # set raw input mode if relevant
    # it is necessary to make stdin not wait for enter
    global PREV_FLAGS

    try:
        PREV_FLAGS = termios.tcgetattr(INPUT_CHANNEL.fileno())
        tty.setraw(INPUT_CHANNEL.fileno())
    except ImportError:
        PREV_FLAGS = None


    # First take release title
    inpBuf = enterTitle(TITLE_PROMPT)
    print formatText("Requested Title : %s"%(inpBuf), fore=FORE_GREEN, style=BOLD)

    # Get the list of relevant english subs 
    relevantSubs = titleQuery(inpBuf)
    name_link_dict = dict(zip(map(lambda x : x[1], relevantSubs), map(lambda x : x[2], relevantSubs)))

    # Allow the user to pick what he wants
    selectedSub, subLink = selectWithSuggestions(map(lambda x : x[1], relevantSubs), SELECT_PROMPT, returnValues=map(lambda x : x[2], relevantSubs))
    print formatText("\rRequested Subtitle : %s"%(selectedSub), fore=FORE_MAGENTA, style=BOLD)
    subLink = "http://subscene.com" + subLink

    # Get the actual download link now
    url = subLink
    req = urllib2.Request(url, headers={'User-Agent':'Mozilla'})
    respSoup = BeautifulSoup(urllib2.urlopen(req), "html.parser")
    linkElem = respSoup('div',{'class':'download'})[0]
    linkElem = linkElem.find_all('a')[0]
    link = linkElem['href']
    link = "http://subscene.com" + link

    # Cleanup is necessary now to prevent weird output
    cleanUp()

    # Download!
    print "\r\n"
    os.system("wget -O /tmp/subscene_temporary %s"%(link))
    os.system("unar -no-directory /tmp/subscene_temporary")

    # and print newline
    OUTPUT_CHANNEL.write('\n')

def cleanUp():
    # restore non-raw input
    if PREV_FLAGS is not None:
        termios.tcsetattr(INPUT_CHANNEL.fileno(), termios.TCSADRAIN, PREV_FLAGS)

    os.system('setterm -cursor on')

def main():
    try:
        os.system('setterm -cursor off')
        subtitleSearch(sys.argv[1:])
        os.system('setterm -cursor on')

    except KeyboardInterrupt:
        cleanUp()
        print formatText("\rCancelling", fore=FORE_RED, back=BACK_BLACK, style=BOLD)
        sys.exit(2)

    except: 
        cleanUp()
        print formatText("\rFAILED!", fore=FORE_RED, back=BACK_BLACK, style=BOLD)
        sys.exit(1)
