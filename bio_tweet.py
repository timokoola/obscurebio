from twython import Twython
import sys
import os
import argparse  # requires 2.7
import json
import codecs
import pprint
import textwrap
import time
import random


LETTER_SCORE = {'a': 23, 'c': 43, 'b': 94, 'e': 17, 'd': 57, 'g': 79, 'f': 108, 'i': 26, 'h': 65, 'k': 178, 'j': 1000, 'm': 65, 'l':
                35, 'o': 27, 'n': 29, 'q': 1000, 'p': 61, 's': 34, 'r': 25, 'u': 54, 't': 28, 'w': 152, 'v': 194, 'y': 110, 'x': 675, 'z': 719}


class TwythonHelper:

    def __init__(self, keyfile):
        f = open(keyfile)
        lines = f.readlines()
        f.close()
        consumerkey = lines[0].split("#")[0]
        consumersecret = lines[1].split("#")[0]
        accesstoken = lines[2].split("#")[0]
        accesssec = lines[3].split("#")[0]

        self.api = Twython(consumerkey, consumersecret, accesstoken, accesssec)


def handle_command_line():
    parser = argparse.ArgumentParser(
        description="Tweets random bios from around the Twitter.")
    parser.add_argument("-w", "--word",
                        help="initial word", default=None)
    parser.add_argument("-f", "--wordfile",
                        help="File contains words we are using next.", default="words.txt")
    parser.add_argument("-u", "--used_words_file", default="used_words.txt")
    parser.add_argument("-k", "--keyfile",
                        help="Twitter account consumer and accesstokens")
    parser.add_argument("-t", "--testkey",
                        help="for debug tweets", default=None)
    args = parser.parse_args()
    return args


def obscure_score(text, search_word):
    if len(text) == 0:
        return 0
    scalers = len(filter(lambda x: x.isupper() or x in ",.#", text))
    no_http_please = 1000 if text.find("http://") != -1 else 1
    no_at = 1000 if text.find("@") != -1 else 1
    scanthis = text.lower()
    search_in = 50 if search_word.lower() in scanthis else 1
    result = (search_in * sum(map(lambda x: LETTER_SCORE.get(x, 10), scanthis)) ) / \
        (max(1, scalers * no_http_please * no_at))
    return result


def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, "Shouldn't get here"


def get_new_word(wf, uwf, first=None):
    f = open(wf)
    words = set(" ".join(f.readlines()).split())
    if first:
        words.add(first)
    f.close()
    f2 = open(uwf)
    used_words = set(" ".join(f2.readlines()).split())
    f2.close()

    print words, used_words
    usable = list(words.difference(used_words))

    return (random.choice(usable), used_words)


def add_to_used(word, uwf):
    w = word.lower()
    f2 = open(uwf, "a")
    f2.write(w + "\n")
    f2.close()


def add_to_candidates(best, wf):
    b = [b.lower() for b in best.split() if len(b) > 4]
    f = open(wf, "a")
    f.write(u" ".join(b) + "\n")
    f.close()


if __name__ == "__main__":
    args = handle_command_line()
    api = (TwythonHelper(args.keyfile)).api
    if args.testkey:
        testapi = (TwythonHelper(args.testkey)).api
    else:
        testapi = None
    (search_item, sitems) = get_new_word(args.wordfile,
                                         args.used_words_file, args.word)

    tweeted = False

    rounds = 0

    while not tweeted:
        if rounds > 10:
            if testapi:
                testapi.update_status(status=search_item)
            sys.exit()
        items = api.search_users(q=search_item, page=4)
        if len(items) == 0:
            search_item, tmp = get_new_word(
                args.wordfile, args.used_words_file)
            continue
        l = [i["description"] for i in items]
        lm = map(lambda x: (x, obscure_score(x, search_item)), l)
        best = sorted(lm, key=lambda x: -x[1])[0][0]

        try:
            api.update_status(status=best)
            tweeted = True

        except:
            search_item, tmp = get_new_word(
                args.wordfile, args.used_words_file)
            tweeted = False
        finally:
            if testapi:
                testapi.update_status(status=search_item)

        add_to_used(search_item, args.used_words_file)
        add_to_candidates(best, args.wordfile)
        rounds = rounds + 1
