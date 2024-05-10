#!/usr/bin/python3
import sys
import argparse
import _iad

parser = argparse.ArgumentParser(
    description='Calculate inter-arrival distances')
# parser.add_argument('--addr', action=argparse.BooleanOptionalAction)
parser.add_argument('--width', type=int, default=0)
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                    default=sys.stdin)
args = parser.parse_args()
args.addr = False


def wprint(w, n):
    if w == 0:
        print(n)
    else:
        if n == -1:
            print('9' * w)
        else:
            print('%0*d' % (w, n))


d = dict()
t = 0
for line in args.infile:
    a = int(line)
    if a in d:
        if args.addr:
            print(a, t - d[a])
        else:
            wprint(args.width, t-d[a])
    else:
        if args.addr:
            print(a, -1)
        else:
            wprint(args.width, -1)
    d[a] = t
    t += 1
