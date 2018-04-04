#!/usr/bin/env python
# filename: DaemonPy.py
#

import sys, os, time, atexit
from signal import SIGTERM


class Daemon(object):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        # Need for debugging information to change: stdin='/dev/stdin',
        # stdout='/dev/stdout', stderr='/dev/stderr', running it as super user root
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def _daemonize(self):
        try:
            pid = os.fork()  # The fork for the first time, to generate the child from the parent process
            if pid > 0:
                sys.exit(0)  # Exit the main process
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")  # Modify the working directory
        os.setsid()  # Set the new session connection
        os.umask(0)  # To re-set file creation permissions

        try:
            pid = os.fork()  # The second fork, disable process to open a terminal
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        # Redirect file descriptor
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'ab+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Register exit function, according to the file pid judge whether there is a process
        atexit.register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write('%s\n' % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        # Check the pid file exists to detect whether there is a process
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running!\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Startup Monitoring
        self._daemonize()
        self._run()

    def stop(self):
        # Get pid from pid file
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:  # Restart and no error occurs
            message = 'pidfile %s does not exist. Daemon not running!\n'
            sys.stderr.write(message % self.pidfile)
            return

        # Kill process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

    def _run(self):
        """ run your fun"""
        while True:
            # This would run in daemon mode; output is not visible
            sys.stdout.write('{}:hello world\n'.format(time.ctime(), ))
            sys.stdout.flush()
            time.sleep(2)


if __name__ == '__main__':
    daemon = Daemon('/tmp/Daemon_proc.pid', stdout='/tmp/daemon_stdout.log')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print('unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print('usage: {} start|stop|restart'.format(sys.argv[0]))
        sys.exit(2)
