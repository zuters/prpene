#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Jānis Zuters

from __future__ import unicode_literals, division

import sys
import argparse

from io import open
argparse.open = open

from prpe_ne import collect_ne_pairs

def create_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="extract potential pairs of named entities from parallel corpora")
    parser.add_argument(
        '--input1', '-i', type=argparse.FileType('r'), default=sys.stdin,
        metavar='PATH',
        help="Input file #1")
    parser.add_argument(
        '--input2', '-k', type=argparse.FileType('r'),
        metavar='PATH',
        help="Input file #2")
    parser.add_argument(
        '--output1', '-o', type=argparse.FileType('w'), default=sys.stdout,
        metavar='PATH',
        help="Output file #1")
    parser.add_argument(
        '--output2', '-p', type=argparse.FileType('w'),
        metavar='PATH',
        help="Output file #2")
    return parser

if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

    collect_ne_pairs(args.input1.name,args.input2.name,args.output1.name,args.output2.name)
