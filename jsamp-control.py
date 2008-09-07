#!/usr/bin/env python

from __future__ import with_statement
from contextlib import closing
from optparse import OptionParser
from os import environ
from os.path import dirname
from socket import socket
from subprocess import PIPE, Popen
from sys import argv, stderr

class jsamp_exception(Exception): pass

def main(argv):
  try:
    p = OptionParser()
    p.add_option('-o', '--out', default = 'jsamp.out',
                 help = 'The JSamp output file where raw samples are to be dumped.')
    p.add_option('-P', '--pid',
                 help = 'The pid of the JVM to attach to.')
    p.add_option('-i', '--interval', default = 10,
                 help = 'Time in milliseconds between samples.')
    p.add_option('-p', '--port', default = 2857,
                 help = 'The port that JSamp listens on.')
    p.add_option('-j', '--jar',
                 help = 'The path to the JSamp jar file (if ommitted, use JSAMPJAR env var).')
    p.add_option('-t', '--toolsjar',
                 help = 'The path to the tools.jar file (if ommitted, guess based on java.home).')
    opts, args = p.parse_args()

    cmd = args[0]

    if cmd == 'attach':
      if opts.jar is None:
        try: opts.jar = environ['JSAMPJAR']
        except KeyError: raise jsamp_exception('jar path must be specified')
      if opts.pid is None:
        p = Popen(['pgrep','java'], stdout = PIPE)
        try: opts.pid = p.communicate()[0].split()[0]
        except: raise jsamp_exception('could not find a JVM to attach to')
      if opts.toolsjar is None:
        javapath = Popen(['which','javac'], stdout = PIPE).communicate()[0].strip()
        javapath = Popen(['readlink','-f',javapath], stdout = PIPE).communicate()[0].strip()
        opts.toolsjar = dirname(dirname(javapath)) + '/lib/tools.jar'
      cmd = ['java','-cp',opts.jar+':'+opts.toolsjar,'ca.evanjones.JSampAttach',
             opts.pid,opts.interval,opts.port,opts.out]
      print ' '.join(map(str, cmd))
      Popen(map(str, cmd)).wait()

    elif cmd == 'detach':
      with closing(socket()) as s:
        s.connect(('localhost',int(opts.port)))

    else:
      raise jsamp_exception('unknown command: ' + cmd)

  except Exception, ex:
    print >> stderr, ex
    return 1

if __name__ == '__main__':
  exit(main(argv))

# vim:et:sw=2:ts=2
