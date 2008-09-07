#!/usr/bin/env python

"""
Post-processor that produces human-friendly aggregate results from the raw
samples collected by the JSamp runtime.
"""

from optparse import OptionParser
from sys import argv, stdin, exit
from re import compile

frame_pat = compile(r"^([^(]+)\(([^)]+)\)$")

def parse_stacks(f):
    stack = []
    for line in f:
        if line == "\n":
            if len(stack) > 0: yield stack
            stack = []
        else:
            match = frame_pat.match(line)
            method = match.group(1)
            location = match.group(2)
            stack.append((method, location))
    if len(stack) > 0:
        yield stack

def filter_stacks(stacks, filters):
    for stack in stacks:
        for method, location in stack:
            if any(method.startswith(filter) for filter in filters): break
        else:
            yield stack

def main(argv):
    p = OptionParser()
    p.add_option('-x', '--exclude', action = 'append',
                 help = 'filter out stacks whose traces include the given string')
    opts, args = p.parse_args()

    # Maps method name -> [selfcount , self+children]
    total_methods = {}
    if opts.exclude is None: opts.exclude = []
    stacks = list(filter_stacks(parse_stacks(stdin), opts.exclude))
    nstacks = len(stacks)

    for stack in stacks:
        # Used to avoid counting recursive methods more than once per stack
        stack_methods = {}
        for method, location in stack:
            stack_methods[method] = False
        stack_methods[stack[0][0]] = True

        for method, is_top in stack_methods.iteritems():
            if method not in total_methods:
                total_methods[method] = [0, 0]

            if is_top:
                total_methods[method][0] += 1
            total_methods[method][1] += 1

    self = []
    total = []
    for method, (self_count, total_count) in total_methods.iteritems():
        assert self_count <= nstacks
        assert total_count <= nstacks
        self.append((self_count, method))
        total.append((total_count, method))

    self.sort(reverse=True)
    total.sort(reverse=True)


    print "Self counts:"
    for count, method in self:
        if count == 0: break
        print "%s\t%d\t%.1f%%" % (method, count, float(count)/nstacks*100)

    print
    print "Total counts:"
    for count, method in total:
        if count == 0: break
        print "%s\t%d\t%.1f%%" % (method, count, float(count)/nstacks*100)

if __name__ == '__main__':
    exit(main(argv))

# vim:et:sw=4:ts=4
