#!/usr/bin/env python3
import re
from org import Org
import argparse

def main():
    parser = argparse.ArgumentParser()
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-t', '--token', required=True)
    parent_parser.add_argument('-p', '--project', required=True)
    parent_parser.add_argument('-o', '--org', required=True)
    parent_parser.add_argument('-c', '--column', nargs='+')
    parent_parser.add_argument('-f', '--file', default="")
    subparsers = parser.add_subparsers(dest="subparser")
    update_org_parser = subparsers.add_parser('toorg', parents=[parent_parser])
    update_org_parser.set_defaults(func=toorg)
    update_gh_parser = subparsers.add_parser('togithub', parents=[parent_parser])
    update_gh_parser.set_defaults(func=togithub)
    args = parser.parse_args()
    if args.__contains__("func"):
        args.func(args)
    else:
        parser.print_help()

def toorg(args):
    org = Org(args.file, args.org, args.project)
    #org.UpdateFromGH(columns=args.column, token=args.token)
    print(org)

def togithub(args):
    pass

if __name__ == "__main__":
    main()

