"""
Main entry point of gibberify
"""

import json
import re
import pyphen
import random
import sys
import os
import argparse

# local imports
from gibberify.utils import __version__
from gibberify.config import real_langs, gib_langs


def gibberify(translator, text):
    """
    translate a text from real language into a specified gibberish language
    """
    # split words maintaining non-word characters in the right positions
    words = re.split(r'(\W+)(\w+)', text)

    # generate translation based on syllables
    trans_list = []
    hyph = pyphen.Pyphen(lang='it')
    for w in words:
        if re.match(r'\w+', w):
            syl = hyph.inserted(w).split('-')
            # translate syllables only if they are found, otherwise return a random one
            trans_syl = [translator.get(s.lower(), random.choice(list(translator.keys())))
                         for s in syl]
            # save word translation
            trans_w = ''.join(trans_syl)
            # let's preserve capitalisation, at least a bit
            if w[0].isupper():
                if w.isupper():
                    trans_w = trans_w.upper()
                else:
                    trans_w = trans_w.capitalize()
        else:
            # if w is not a word, just leave it as is
            trans_w = w

        trans_list.append(trans_w)

    # join everything
    trans = ''.join(trans_list)

    # remove multiple spaces due to input or unmapped syllables
    trans = re.sub(' +', ' ', trans)

    # TODO: strip ugly whitespaces and capitalise first letter in a smart way

    return trans


def interactive(dicts):
    """
    interactive mode. Deal with user input and call functions accordingly
    """
    # Make it a sort of menu for easier usage
    level = 0
    while True:
        try:
            if level == 0:
                # welcome and usage
                print(f'Welcome to Gibberify version {__version__}! '
                      f'Follow the prompts to translate a text.\n'
                      f'To go back to the previous menu, press Ctrl+C.\n')
                level += 1
                continue

            if level == 1:
                lang_in = lang_out = ''

                # language selection
                while not lang_in:
                    lang_in = input(f'What language do you want to translate from? '
                                    f'Options are: {", ".join(real_langs)}.\n')
                    # check if requested input language exists
                    if lang_in not in real_langs:
                        print(f'ERROR: you first need to generate a syllable pool for "{lang_in}"!')
                        lang_in = ''
                    else:
                        print(f'You chose "{lang_in}".')
                while not lang_out:
                    lang_out = input(f'What language do you want to translate into? '
                                     f'Options are: {", ".join(gib_langs)}.\n')
                    # check if requested output language exists
                    if lang_out not in gib_langs:
                        print(f'ERROR: you first need to generate a dictionary for "{lang_out}"!')
                        lang_out = ''
                    else:
                        print(f'You chose "{lang_out}".')
                level += 1
                continue

            if level == 2:
                translator = dicts[lang_in][lang_out]
                text = input('What do you want to translate?\n')
                print(f'... or as someone might say:\n'
                      f'{gibberify(translator, text)}')
                continue

        except KeyboardInterrupt:
            level -= 1
            # exit the program if user tries to go back to level 0
            if level < 1:
                print('\nGood bye!\n')
                return
            print('\nGoing back...\n')
            continue


def parse_message(somestring):
    """
    Handle message input nicely
    Passing '-' as the message will read from stdin
    Passing a valid file will read from the file
    Passing a string will use it as the message.
    If your string happens to accidentally be a valid file,
    tough shit i guess..
    """
    somestring = str(somestring)
    if somestring == '-':
        try:
            return sys.stdin.read()
        except KeyboardInterrupt:
            print()
            exit()
    elif os.path.exists(somestring):
        with open(somestring, 'r') as f:
            return f.read()
    else:
        return somestring


def main():
    # Parse arguments (also gives you help automatically with -h)
    parser = argparse.ArgumentParser(prog='gibberify')
    parser.add_argument('--from-lang', '-fl', dest='lang_in', type=str, default='en',
                        choices=real_langs, help='language to translate from')
    parser.add_argument('--to-lang', '-l', dest='lang_out', type=str, default='orc',
                        choices=gib_langs.keys(), help='language to translate into')
    parser.add_argument('--message', '-m', type=parse_message, nargs='*',
                        help='text to translate. If a filename is given, the '
                             'contents of the file will be translated to stdout. '
                             'If `-` is given, input text is take from stdin')
    args = parser.parse_args()

    # if no arguments were given, run interactive mode
    inter = False
    if len(sys.argv) == 1:
        inter = True

    # Set some convenient variable names
    if not inter:
        lang_in = args.lang_in
        lang_out = args.lang_out
        text = ' '.join(args.message)

    # fix path to files depending if we are running as script or as executable
    if hasattr(sys, "_MEIPASS"):
        data = os.path.join(sys._MEIPASS, 'data')
    else:
        data = os.path.join(os.path.dirname(__file__), 'data')

    # load translation dictionaries
    with open(os.path.join(data, 'dicts.json')) as f:
        dicts = json.load(f)

    if inter:
        interactive(dicts)
    else:
        translator = dicts[lang_in][lang_out]
        print(gibberify(translator, text))


if __name__ == '__main__':
    main()
