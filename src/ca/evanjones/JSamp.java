/*
Copyright (c) 2008 Evan Jones, Yang Zhang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 */

package ca.evanjones;

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.net.Socket;
import java.net.ServerSocket;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/** A minimal pure Java sampling profiler. */
public class JSamp implements Runnable {
	public JSamp(int intersampleMillis, String outputPath) {
		this.intersampleMillis = intersampleMillis;
		this.outputPath = outputPath;
	}

	public void sample() {
		// Note: Thread.getAllStackTraces seems to be a bit faster than
		// ThreadMXBean.dumpAllThreads.
		// 187190 < 214187 ns / call
		// ThreadMXBean.getAllThreadIds() seems to be faster than
		// Thread.enumerate
		// 3662 < 7389 ns / call
		// Filtering Thread objects from Thread.enumerate() then using
		// Thread.getStackTrace() on
		// only the threads we care about is slower than getting all stack
		// traces, even if we only
		// call Thread.enumerate every 128th time. Same with using
		// ThreadMXBean.getAllThreadIds()
		// then getThreadInfo()
		samples.add(Thread.getAllStackTraces());
	}

	// figure out why the last two don't seem to be working as filters
	static final String[] SPECIAL_NAMES = { "Finalizer", "Reference Handler",
											"JSamp", "JSamp Server" };

	public void dumpSamples(PrintStream out, Thread sampleThread) {
		// The set of threads that will not be dumped
		HashSet<Thread> ignoreThreads = new HashSet<Thread>();

		// Ignore the thread that was sampling
		ignoreThreads.add(sampleThread);

		// Ignore the "special" threads
		for (Map.Entry<Thread, StackTraceElement[]> entry : Thread
				.getAllStackTraces().entrySet()) {
			Thread t = entry.getKey();
			for (String special : SPECIAL_NAMES) {
				if (t.getName().equals(special)) {
					ignoreThreads.add(t);
					break;
				}
			}

			if (entry.getValue().length == 0) {
				// Many JVM daemon threads have no stack
				ignoreThreads.add(t);
			}
		}

		for (Map<Thread, StackTraceElement[]> sample : samples) {
			for (Map.Entry<Thread, StackTraceElement[]> entry : sample
					.entrySet()) {
				if (ignoreThreads.contains(entry.getKey()))
					continue;

				assert entry.getValue().length > 0;
				for (StackTraceElement element : entry.getValue()) {
					out.println(element.toString());
				}
				out.println();
			}
		}
	}

	public void run() {
		if (System.getProperties().containsKey("nojsampler") && !System.getProperty("nojsampler").equals("${nojsampler}"))
			return;

		assert Thread.currentThread().getThreadGroup().getParent() == null;
		System.out.println("sampling every " + intersampleMillis);

		long start = System.currentTimeMillis();
		while (!doStop.get()) {
			sample();
			try {
				Thread.sleep(intersampleMillis);
			} catch (InterruptedException e) {
				throw new RuntimeException(e);
			}
		}
		long end = System.currentTimeMillis();

		System.out.println(samples.size() + " samples; real rate = " + ((end - start) / samples.size()));
		try {
			PrintStream out = new PrintStream(new File(outputPath));
			dumpSamples(out, Thread.currentThread());
			out.close();
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
	}

	public void stop() {
		this.doStop.set(true);
	}

	public static void agentmain(String agentargs) {
		final String[] args = agentargs.split(";");

		final int interval = Integer.parseInt(args[0]);
		final int port     = Integer.parseInt(args[1]);
		final String outputPath = args[2];

		final JSamp jsampler = new JSamp(interval, outputPath);

		// start jsampler in its own thread
		final Thread jsamplerThread = new Thread(jsampler, "JSamp");
		jsamplerThread.start();

		// kill jsampler as soon as we get a connection on the specified port
		// The other connection will "hang" until jsampler has quit. This keeps
		// the JSamp Server thread alive until after the dumping is done, which
		// also excludes it from the stack traces
		new Thread(jsampler, "JSamp Server") {
			public void run() {
				try {
					Socket socket = new ServerSocket(port).accept();
					jsampler.stop();
					jsamplerThread.join();
					socket.close();
				} catch (Exception ex) {
					throw new RuntimeException(ex);
				}
			}
		}.start();
	}

	int intersampleMillis;
	String outputPath;
	AtomicBoolean doStop = new AtomicBoolean(false);
	private final Deque<Map<Thread, StackTraceElement[]>> samples = new ArrayDeque<Map<Thread, StackTraceElement[]>>();
}
