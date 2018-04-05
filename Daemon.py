#!/usr/bin/env python
# filename: Daemon.py
#

import os
import sys
import time
import atexit
import signal


class Daemon(object):
    def __init__(self, pidfile, *, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        # Need for debugging information to change: stdin='/dev/stdin',
        # stdout='/dev/stdout', stderr='/dev/stderr', running it as super user root
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        # Check the pid file exists to detect whether there is a process
        if os.path.exists(self.pidfile):
            raise RuntimeError('Daemon already running')

        # First fork (detaches from parent)
        try:
            if os.fork() > 0:
                raise SystemExit(0)  # Parent exit
        except OSError as e:
            raise RuntimeError('fork #1 failed.')

        os.chdir('/')
        os.umask(0)
        os.setsid()
        # Second fork (relinquish session leadership)
        try:
            if os.fork() > 0:
                raise SystemExit(0)
        except OSError as e:
            raise RuntimeError('fork #2 failed.')

        # Flush I/O buffers
        sys.stdout.flush()
        sys.stderr.flush()

        # Replace file descriptors for stdin, stdout, and stderr
        with open(self.stdin, 'rb', 0) as f:
            os.dup2(f.fileno(), sys.stdin.fileno())
        with open(self.stdout, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
        with open(self.stderr, 'ab', 0) as f:
            os.dup2(f.fileno(), sys.stderr.fileno())

        # Write the PID file
        with open(self.pidfile, 'w') as f:
            print(os.getpid(), file=f)

        # Arrange to have the PID file removed on exit/signal
        atexit.register(lambda: os.remove(self.pidfile))

        # Signal handler for termination (required)
        def sigterm_handler(signo, frame):
            raise SystemExit(1)

        signal.signal(signal.SIGTERM, sigterm_handler)

    def _run(self):
        sys.stdout.write('Daemon started with pid {}\n'.format(os.getpid()))
        while True:
            sys.stdout.write('Daemon Alive! {}\n'.format(time.ctime()))
            time.sleep(12)

    def start(self):
        try:
            print('Starting Daemon with pid {}'.format(os.getpid()))
            self.daemonize()
        except RuntimeError as e:
            print(e, file=sys.stderr)
            raise SystemExit(1)
        self._run()

    def stop(self):
        if os.path.exists(PIDFILE):
            print('Stopping Daemon with pid {}'.format(os.getpid()))
            with open(PIDFILE) as f:
                os.kill(int(f.read()), signal.SIGTERM)
        else:
            print('Daemon not running', file=sys.stderr)
            raise SystemExit(1)

    def restart(self):
        self.stop()
        time.sleep(2)
        self.start()


if __name__ == '__main__':
    PIDFILE = '/tmp/daemon.pid'
    daemon = Daemon(PIDFILE, stdout='/tmp/daemon.log', stderr='/tmp/daemon.log')

    if len(sys.argv) != 2:
        print('Usage: {} [start|stop|restart]'.format(sys.argv[0]), file=sys.stderr)
        raise SystemExit(1)

    if sys.argv[1] == 'start':
        daemon.start()

    elif sys.argv[1] == 'stop':
        daemon.stop()
    elif sys.argv[1] == 'restart':
        daemon.restart()
    else:
        print('Unknown command {!r}'.format(sys.argv[1]), file=sys.stderr)
        raise SystemExit(1)
