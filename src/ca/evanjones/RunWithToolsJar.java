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

import java.io.IOException;
import java.lang.reflect.Method;
import java.net.URL;
import java.net.URLClassLoader;

/** Hack to add tools.jar in the JDK to the classpath.

NOTE: It is critical that this class not reference any other JSamp classes,
since those classes require tools.jar to be part of the classpath. */
public class RunWithToolsJar {
    private static final String MAIN_CLASS = "ca.evanjones.JSampAttach";
    public static void main(String[] args) throws Exception {
        String javaHome = System.getProperty("java.home");
        String toolsJarURL = "file:" + javaHome + "/../lib/tools.jar";

        // Make addURL public
        Method method = URLClassLoader.class.getDeclaredMethod("addURL", URL.class);
        method.setAccessible(true);
        URLClassLoader sysloader = (URLClassLoader) ClassLoader.getSystemClassLoader();
        method.invoke(sysloader, (Object) new URL(toolsJarURL));

        // Now that we have loaded the required classes, load and run the main program
        Class<?> realMain = sysloader.loadClass(MAIN_CLASS);
        Method m = realMain.getMethod("main", String[].class);
        m.invoke(null, (Object) args);
    }
}
