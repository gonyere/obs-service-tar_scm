#!/usr/bin/env python
from __future__ import print_function
import glob
import os
import tempfile


class ScmInvocationLogs:
    """
    Provides log files which tracks invocations of SCM binaries.  The
    tracking is done via a wrapper around SCM to enable behaviour
    verification testing on tar_scm's repository caching code.  This
    is cleaner than writing tests which look inside the cache, because
    then they become coupled to the cache's implementation, and
    require knowledge of where the cache lives etc.

    One instance should be constructed per unit test.  If the test
    invokes the SCM binary multiple times, invoke next() in between
    each, so that a separate log file is used for each invocation -
    this allows more accurate fine-grained assertions on the
    invocation log.
    """

    @classmethod
    def setup_bin_wrapper(cls, scm, tests_dir):
        wrapper_dir = tempfile.mkdtemp(dir="/tmp")

        wrapper_src = os.path.join(tests_dir, 'scm-wrapper')
        wrapper_dst = wrapper_dir + '/' + scm

        if not os.path.exists(wrapper_dst):
            os.symlink(wrapper_src, wrapper_dst)

        path = os.getenv('PATH')
        prepend = wrapper_dir + ':'

        if not path.startswith(prepend):
            new_path = prepend + path
            os.environ['PATH'] = new_path

    def __init__(self, scm, test_dir):
        self.scm              = scm
        self.test_dir         = test_dir
        self.counter          = 0
        self.current_log_path = None

        self.unlink_existing_logs()

    def get_log_file_template(self):
        return '%s-invocation-%%s.log' % self.scm

    def get_log_path_template(self):
        return os.path.join(self.test_dir, self.get_log_file_template())

    def unlink_existing_logs(self):
        pat = self.get_log_path_template() % '*'
        for log in glob.glob(pat):
            os.unlink(log)

    def get_log_file(self, identifier):
        if identifier:
            identifier = '-' + identifier
        return self.get_log_file_template() % \
            ('%02d%s' % (self.counter, identifier))

    def get_log_path(self, identifier):
        return os.path.join(self.test_dir, self.get_log_file(identifier))

    def nextlog(self, identifier=''):
        self.counter += 1
        self.current_log_path = self.get_log_path(identifier)
        if os.path.exists(self.current_log_path):
            raise RuntimeError("%s already existed?!" % self.current_log_path)
        os.putenv('SCM_INVOCATION_LOG', self.current_log_path)
        os.environ['SCM_INVOCATION_LOG'] = self.current_log_path

    def annotate(self, msg):
        print(msg)
        with open(self.current_log_path, 'a', encoding="UTF-8") as log:
            log.write('# ' + msg + "\n")

    def read(self):
        if not os.path.exists(self.current_log_path):
            return '<no %s log>' % self.scm
        with open(self.current_log_path, 'r', encoding="UTF-8") as log:
            loglines = log.readlines()
        return loglines
