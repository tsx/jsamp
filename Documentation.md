# Introduction #

JSamp is a pure Java sampling profiler. It has some important limitations, but it does work.


# Benefits #

  * Minimal impact on running programs since it uses sampling
  * Can attach to any running JVM
  * Can control it from within Java, to sample specific items of interest.
  * Portable since it is written in Java


# Limitations #

  * Cannot distinguish a "sleeping" thread from a running thread. Hence, threads that are blocked on monitors (`synchronized` blocks) or I/O will appear frequently in the samples, even though they are not consuming any CPU. Fixing this would require [using native code](http://jeremymanson.blogspot.com/2007/05/profiling-with-jvmtijvmpi-sigprof-and.html).


# Quick Reference Guide #

## Recording Samples ##

To start recording samples, attach JSamp to a running JVM:

```
java -jar jsamp.jar <jvm pid> <inter-sample period (ms)> <stop port> <output file>
```


To stop recording, connect to the port argument supplied above using a command like `nc`, `telnet`, `curl`, or a web browser.

```
nc localhost <port>
```


## Interpreting Results ##

To interpret the results of a profiling run, use the included `jsame-postproc.py` script:

```
./jsamp-postproc.py < <input file>
```

The section labelled `Self counts` sorts methods by the number of times they appear at the top of the stack trace. The section labelled `Total counts` sorts methods by the number of times that they appear **anywhere** in the stack trace.

## Example Output ##

```
Self counts:
java.lang.Object.wait   5419    76.9%
java.net.PlainSocketImpl.socketAccept   1083    15.4%
sun.awt.X11.XToolkit.waitForEvents      540     7.7%
sun.awt.X11.XlibWrapper.XEventsQueued   1       0.0%
sun.awt.X11.XToolkit.wakeup_poll        1       0.0%
java.io.UnixFileSystem.list     1       0.0%

Total counts:
java.lang.Object.wait   5419    76.9%
java.lang.Thread.run    2710    38.5%
java.util.TimerThread.run       1084    15.4%
java.util.TimerThread.mainLoop  1084    15.4%
java.lang.ref.ReferenceQueue.remove     1084    15.4%
java.net.ServerSocket.implAccept        1083    15.4%
java.net.ServerSocket.accept    1083    15.4%
java.net.PlainSocketImpl.socketAccept   1083    15.4%
java.net.PlainSocketImpl.accept 1083    15.4%
sun.java2d.Disposer.run 542     7.7%
sun.awt.X11.XToolkit.run        542     7.7%
```