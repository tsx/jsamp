#!/usr/bin/env python

"""
Post-processor that produces human-friendly aggregate results from the raw
samples collected by the JSamp runtime.
"""

import re, sys, optparse, collections

frame_pat = re.compile(r"^(?P<meth>[^(]+)\((?P<loc>.+)\)$")

def pars(f):
    """
    >>> list(pars(StringIO('a\nb\nc\n\nd\ne\nf\n')))
    [['a\n','b\n','c\n'],['d\n','e\n','f\n']]
    """
    par = []
    for line in f:
        if line == '\n':
            yield par
            par = []
        else:
            par.append(line)
    if par != []:
        yield par

def sliding_windows(xs, winsize):
    """
    >>> list(sliding_windows([1,2,3,4,5], 3))
    [[1,2,3],[2,3,4],[3,4,5]]
    """
    for i in range(len(xs) - (winsize - 1)):
        yield xs[i], xs[i+1], xs[i+2]

def parse_stacks(f, merge_overloads):
    for par in pars(f):
        yield [ ( (line.rstrip('\n'), None)
                  if not merge_overloads else
                  frame_pat.match(line).groups() )
                for line in par ]

def filter_stacks(stacks, filters, match_any = False):
    """
    match_any means that we will filter out stacks not just by the top-most
    frame but any of its frames.
    """
    for stack in stacks:
        if match_any:
            for meth, loc in stack:
                if any(meth.startswith(filter) for filter in filters): break
            else:
                yield stack
        else:
            meth, loc = stack[0]
            if not any(meth.startswith(filter) for filter in filters):
                yield stack

class methinfo(object):
    def __init__(self):
        # Number of self samples (appeared at the top of the stack).
        self.nself = 0
        # Number of cumulative samples (appeared anywhere in the stack).
        self.ncum  = 0
        # Immediate parent method -> count.
        self.parents = collections.defaultdict(lambda: 0)
        # Immediate child method -> count.
        self.children = collections.defaultdict(lambda: 0)

def cgline(meth, count, total):
    "Produce an oprofile-formatted callgraph line of output for a single frame."
    return '%d  %.4f  -  %s' % (count, 100. * count / total, meth)

def main(argv):
    p = optparse.OptionParser()
    p.add_option('-x', '--exclude', action = 'append',
                 help = '''filter out stacks where the top frame begins with the
                 given string''')
    p.add_option('-m', '--merge-overloads', action = 'store_true',
                 help = '''treat all overloads with the same function name as
                 the same function (aggregate their samples)''')
    p.add_option('-g', '--call-graph', action = 'store_true',
                 help = '''output an oprofile-formatted callgraph instead of
                 the flat aggregation summary''')
    p.add_option('-f', '--filter-any', action = 'store_true',
                 help = '''filter out stacks where the frames specified via
                 --exclude appear anywhere in the stack''')
    opts, args = p.parse_args()
    if opts.exclude is None: opts.exclude = []

    stacks = list(filter_stacks(parse_stacks(sys.stdin, opts.merge_overloads),
                                opts.exclude, opts.filter_any))
    # method name -> methinfo
    meth2info = collections.defaultdict(methinfo)

    for stack in stacks:
        meths, locs = map(list, zip(*stack))

        for child, meth, parent in sliding_windows([None] + meths + [None], 3):
            if parent is not None: meth2info[meth].parents[parent] += 1
            if child is not None:  meth2info[meth].children[child] += 1
        meth2info[meths[0]].nself += 1

        # Avoid counting recursive methods more than once per stack.
        for meth in set(meths):
            meth2info[meth].ncum += 1

    # Sanity check.
    for meth, info in meth2info.iteritems():
        assert info.nself <= len(stacks)
        assert info.ncum  <= len(stacks)

    if not opts.call_graph:
        for attr, desc in [('nself', 'Self counts'), ('ncum', 'Total counts')]:
            print desc + ':'
            with_counts = ( ( getattr(info, attr), meth, info )
                            for meth, info in meth2info.iteritems() )
            for count, meth, info in sorted( with_counts, reverse = True ):
                if count == 0: break
                print "%s\t%d\t%.1f%%" % (meth, count, 100. * count / len(stacks))
            print
    else:
        print 'samples  %        image name               symbol name'
        print 80 * '-'
        for meth, info in meth2info.iteritems():
            sumparents = sum(info.parents.itervalues())
            for parent, count in info.parents.iteritems():
                print '  ' + cgline(parent, count, sumparents)
            print cgline(meth, info.nself, len(stacks))
            sumchildren = sum(info.children.itervalues())
            for child, count in info.children.iteritems():
                print '  ' + cgline(child, count, sumchildren)
            print 80 * '-'

if __name__ == '__main__':
    sys.exit(main(sys.argv))

# vim:et:sw=4:ts=4
