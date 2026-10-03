"""Integration tests against local bare Git repos; no accounts or server access."""
import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/agentos.py'
spec = importlib.util.spec_from_file_location('agentos', SCRIPT)
oslib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oslib)


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.remote, self.repo = self.base / 'remote.git', self.base / 'repo'
        oslib.run('git', 'init', '--bare', '--quiet', str(self.remote))
        self.repo.mkdir()
        oslib.git(self.repo, 'init', '--quiet')
        oslib.git(self.repo, 'config', 'user.name', 'Test Owner')
        oslib.git(self.repo, 'config', 'user.email', 'owner@example.test')
        oslib.git(self.repo, 'checkout', '--quiet', '-b', 'feat/test')
        oslib.write_json(self.repo / '.agent/config.json', {
            'schema_version': 1, 'owner': 'Test Owner', 'project': 'test-app',
            'coordination_repository': str(self.remote), 'state_branch': 'agentos-state',
            'actors': ['human', 'codex', 'claude', 'gemini']})
        for path in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agent/AGENTS.md', '.agent/HANDOFF.md'):
            (self.repo / path).write_text('Test instructions\n')
        oslib.git(self.repo, 'add', '--', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agent')
        oslib.git(self.repo, 'commit', '--quiet', '-m', 'test fixture')
        oslib.git(self.repo, 'remote', 'add', 'origin', str(self.remote))
        oslib.git(self.repo, 'push', '--quiet', 'origin', 'HEAD:refs/heads/feat/test')
        self.project = oslib.Project(self.repo)
        with contextlib.redirect_stdout(io.StringIO()):
            oslib.init_state(self.project)

    def command(self, text):
        import shlex
        args = oslib.parser().parse_args(shlex.split(text))
        with contextlib.redirect_stdout(io.StringIO()):
            oslib.execute(self.project, args)

    def create(self, task='one'):
        self.command('create {} --title Example --scope docs'.format(task))

    def claim(self, task='one', actor='codex', session='first'):
        self.command('claim {} --actor {} --session {}'.format(task, actor, session))

    def test_duplicate_claim_rejected_even_same_actor_different_session(self):
        self.create()
        self.claim()
        with self.assertRaises(oslib.Error):
            self.claim(session='second')

    def test_wrong_session_cannot_checkpoint_or_unlock(self):
        self.create()
        self.claim()
        self.command('lock production --task one --actor codex --session first')
        for cmd in ('checkpoint one --state x --next y', 'unlock production --task one'):
            with self.assertRaises(oslib.Error):
                self.command(cmd + ' --actor codex --session second')

    def test_environment_lock_blocks_another_task(self):
        self.create()
        self.claim()
        self.create('two')
        self.claim('two', 'claude', 'second')
        self.command('lock production --task one --actor codex --session first')
        with self.assertRaises(oslib.Error):
            self.command('lock production --task two --actor claude --session second')
        with self.assertRaises(oslib.Error):
            self.command('handoff one --actor codex --session first --to claude --state x --next y')
        self.command('unlock production --task one --actor codex --session first')
        self.command('lock production --task two --actor claude --session second')

    def test_handoff_recipient_and_review_flow(self):
        self.create()
        self.claim()
        self.command('handoff one --actor codex --session first --to claude --state Ready --next Review')
        with self.assertRaises(oslib.Error):
            self.claim(actor='gemini', session='wrong')
        self.claim(actor='claude', session='second')
        self.command('review one --actor claude --session second --state Tested --next Merge')
        with self.assertRaises(oslib.Error):
            self.command('close one --actor claude --evidence PR')
        self.command('close one --actor human --evidence PR')
        with oslib.checkout(self.project) as ledger:
            self.assertEqual(ledger.task('one')['status'], 'done')

    def test_checkpoint_never_stages_code_and_handoff_requires_clean_pushed_code(self):
        self.create()
        self.claim()
        before = self.project.code()['commit']
        (self.repo / 'uncommitted.txt').write_text('Remain local')
        self.command('checkpoint one --actor codex --session first --state Dirty --next Commit')
        self.assertEqual(self.project.code()['commit'], before)
        self.assertEqual(oslib.git(self.repo, 'diff', '--cached', '--name-only').stdout, '')
        with self.assertRaises(oslib.Error):
            self.command('handoff one --actor codex --session first --to claude --state x --next y')
        oslib.git(self.repo, 'add', '--', 'uncommitted.txt')
        oslib.git(self.repo, 'commit', '--quiet', '-m', 'unpublished code')
        with self.assertRaises(oslib.Error):
            self.command('handoff one --actor codex --session first --to claude --state x --next y')

    def test_stale_writer_rejected_by_git(self):
        self.create()
        with oslib.checkout(self.project) as a, oslib.checkout(self.project) as b:
            for ledger, actor in ((a, 'codex'), (b, 'claude')):
                task = ledger.task('one')
                task.update(status='in_progress', claim={'actor': actor, 'session': actor})
                ledger.event(task, 'claim', actor, actor)
                ledger.save(task)
            a.publish('ops: first writer')
            with self.assertRaisesRegex(oslib.Error, 'push rejected'):
                b.publish('ops: competing writer')
        with oslib.checkout(self.project) as ledger:
            self.assertEqual(ledger.task('one')['claim']['actor'], 'codex')

    def test_other_owner_task_rejected(self):
        self.create()
        with oslib.checkout(self.project) as ledger:
            t = ledger.task('one')
            t['owner'] = 'Someone Else'
            ledger.save(t)
            ledger.publish('ops: reassign fixture')
        with self.assertRaisesRegex(oslib.Error, 'not assigned'):
            self.claim()

    def test_text_is_data_and_common_credentials_rejected(self):
        self.create()
        self.claim()
        marker = self.base / 'must-not-exist'
        text = '$(touch {}) `touch {}`'.format(marker, marker)
        args = argparse.Namespace(command='checkpoint', id='one', actor='codex', session='first',
            state=text, next='Review', blocker='none', evidence=[])
        with contextlib.redirect_stdout(io.StringIO()):
            oslib.execute(self.project, args)
        self.assertFalse(marker.exists())
        with self.assertRaises(oslib.Error):
            oslib.safe_text('-----BEGIN OPENSSH PRIVATE KEY-----')
        with self.assertRaises(oslib.Error):
            oslib.remote_url('https://user:password@github.com/owner/repo')
        with self.assertRaises(oslib.Error):
            oslib.slug('../escape')

    def test_init_refuses_existing_ledger(self):
        with self.assertRaisesRegex(oslib.Error, 'already exists'):
            oslib.init_state(self.project)

    def test_install_conflict_makes_no_partial_writes(self):
        with self.assertRaisesRegex(oslib.Error, 'before writing'):
            oslib.install(self.repo, apply=True)
        self.assertFalse((self.repo / 'scripts/agentos.py').exists())
        self.assertEqual((self.repo / 'AGENTS.md').read_text(), 'Test instructions\n')

    def test_install_dry_run_and_symlink_refusal(self):
        target = self.base / 'fresh'
        target.mkdir()
        oslib.git(target, 'init', '--quiet')
        with contextlib.redirect_stdout(io.StringIO()):
            oslib.install(target)
        self.assertFalse((target / 'AGENTS.md').exists())
        (target / '.agent').symlink_to(self.repo / '.agent', target_is_directory=True)
        with self.assertRaisesRegex(oslib.Error, 'symlink'):
            oslib.install(target, apply=True)


if __name__ == '__main__':
    unittest.main()
