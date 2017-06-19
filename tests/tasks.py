from __future__ import print_function

import sys
import os
import inspect
import shutil
from mock import MagicMock

from tar_scm import TarSCM

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class TasksTestCases(unittest.TestCase):
    def setUp(self):
        self.basedir   = os.path.abspath(os.path.dirname(__file__))
        # os.getcwd()
        self.tests_dir = os.path.abspath(os.path.dirname(__file__))
        self.tmp_dir   = os.path.join(self.tests_dir, 'tmp')
        self.outdir    = os.path.join(self.tmp_dir,
                                      self.__class__.__name__, 'out')
        self.cur_dir   = None
        self._prepare_cli()

    def tearDown(self):
        if os.path.exists(self.outdir):
            shutil.rmtree(self.outdir)

    def _prepare_cli(self):
        self.cli = TarSCM.cli()
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        self.cli.parse_args(['--outdir', self.outdir, '--scm', 'git'])
        self.cli.snapcraft  = True

    def _cd_fixtures_dir(self):
        self.cur_dir = os.getcwd()
        cl_name = self.__class__.__name__
        fn_name = inspect.stack()[1][3]
        try:
            os.chdir(os.path.join(self.basedir, 'fixtures', cl_name, fn_name))
        except OSError:
            print("current working directory: %s" % os.getcwd())
            raise

    def _restore_cwd(self):
        try:
            os.chdir(self.basedir)
        except OSError:
            print("failed to restore : current working directory: %s" %
                  os.getcwd())
            raise

    def test_generate_tl_single_task(self):
        expected = {
            'scm': 'bzr', 'clone_prefix': '_obs_', 'snapcraft': True,
            'revision': None, 'url': 'lp:~mterry/libpipeline/printf',
            'filename': 'libpipeline', 'use_obs_scm': True,
            'outdir': self.cli.outdir, 'changesgenerate': False}
        self._cd_fixtures_dir()
        tasks = TarSCM.tasks()
        tasks.generate_list(self.cli)
        self._restore_cwd()
        for k in expected:
            self.assertEqual(tasks.task_list[0].__dict__[k], expected[k])
        self.assertEqual(len(tasks.task_list), 1)

    def test_generate_tl_st_appimage(self):
        '''Test generates task list with single task from appimage.yml'''
        self.cli.snapcraft = False
        self.cli.appimage = True
        expected = {
            'scm': 'git', 'appimage': True,
            'revision': None,
            'url': 'https://github.com/probonopd/QtQuickApp.git',
            'use_obs_scm': True,
            'outdir': self.cli.outdir,
            'changesgenerate': False
        }
        self._cd_fixtures_dir()
        tasks = TarSCM.tasks()
        tasks.generate_list(self.cli)
        self._restore_cwd()
        for k in expected:
            self.assertEqual(tasks.task_list[0].__dict__[k], expected[k])
        self.assertEqual(len(tasks.task_list), 1)

    def test_appimage_empty_build_git(self):
        self.cli.snapcraft = False
        self.cli.appimage = True
        self._cd_fixtures_dir()
        tasks = TarSCM.tasks()
        tasks.generate_list(self.cli)

    def test_generate_tl_multi_tasks(self):
        expected = {
            'libpipeline': {
                'changesgenerate': False,
                'clone_prefix': '_obs_',
                'filename': 'libpipeline',
                'outdir': self.cli.outdir,
                'revision': None,
                'scm': 'bzr',
                'snapcraft': True,
                'url': 'lp:~mterry/libpipeline/printf',
                'use_obs_scm': True
            },
            'kanku': {
                'changesgenerate': False,
                'clone_prefix': '_obs_',
                'filename': 'kanku',
                'outdir': self.cli.outdir,
                'revision': None,
                'scm': 'git',
                'snapcraft': True,
                'url': 'git@github.com:M0ses/kanku',
                'use_obs_scm': True
            }
        }
        self._cd_fixtures_dir()
        tasks = TarSCM.tasks()
        tasks.generate_list(self.cli)
        # test values in the objects instead of objects
        for got in tasks.task_list:
            got_f = got.__dict__['filename']
            for key in expected[got_f].keys():
                self.assertEqual(got.__dict__[key], expected[got_f][key])
        self._restore_cwd()

    def test_tasks_finalize(self):
        expected = '''\
apps:
  pipelinetest:
    command: ./bin/test
description: 'This is an example package of an autotools project built with snapcraft

  using a remote source.

  '
name: pipelinetest
parts:
  kanku:
    after:
    - libpipeline
    plugin: make
    source: kanku
  libpipeline:
    plugin: autotools
    source: libpipeline
summary: Libpipeline example
version: 1.0
'''  # noqa
        self._cd_fixtures_dir()
        tasks           = TarSCM.tasks()
        if not os.path.exists(self.cli.outdir):
            os.makedirs(self.cli.outdir)
        tasks.generate_list(self.cli)
        tasks.finalize(self.cli)
        self._restore_cwd()
        scf = open(os.path.join(self.cli.outdir,
                                '_service:snapcraft:snapcraft.yaml'), 'r')
        got = scf.read()
        scf.close()
        self.assertEqual(got, expected)

    def test_cleanup(self):
        tasks  = TarSCM.tasks()
        cln    = self.__class__.__name__
        cn_dir = os.path.join(self.tmp_dir, cln)
        if not os.path.exists(self.tmp_dir):
            os.mkdir(self.tmp_dir)
        if not os.path.exists(cn_dir):
            os.mkdir(cn_dir)
        os.mkdir(os.path.join(cn_dir, 'test1'))
        tasks.cleanup_dirs.append(os.path.join(cn_dir, 'test1'))
        tasks.cleanup_dirs.append(os.path.join(cn_dir, 'does not exits'))
        tasks.cleanup_dirs.append(cn_dir)
        tasks.cleanup()
        self.assertEqual(os.path.exists(cn_dir), False)

    def test_get_version(self):
        class FakeSCM():
            # pylint: disable=unused-argument,no-self-use,no-init,
            # pylint: disable=too-few-public-methods
            def detect_version(self, args):
                return '0.0.1'

        scm     = FakeSCM()
        tasks   = TarSCM.tasks()
        ver     = tasks.get_version(scm, self.cli)
        self.assertEqual(ver, '0.0.1')
        self.cli.versionprefix = "r"
        ver     = tasks.get_version(scm, self.cli)
        self.assertEqual(ver, 'r.0.0.1')

    def test_get_version_with_versionrw(self):
        '''Test for get_version with versionrewrite'''
        class FakeSCM():
            # pylint: disable=unused-argument,no-self-use,no-init,
            # pylint: disable=too-few-public-methods
            def detect_version(self, args):
                return 'v0.0.1'

        self.cli.versionrewrite_pattern = r'v(\d[\d\.]*)'
        self.cli.versionrewrite_replacement = '\\1-stable'
        scm     = FakeSCM()
        tasks   = TarSCM.tasks()
        ver     = tasks.get_version(scm, self.cli)
        self.assertEqual(ver, '0.0.1-stable')

    def test_process_list(self):
        tasks   = TarSCM.tasks()
        self.cli.snapcraft = False
        tasks.process_single_task = MagicMock(name='process_single_task')
        tasks.generate_list(self.cli)
        tasks.process_list()