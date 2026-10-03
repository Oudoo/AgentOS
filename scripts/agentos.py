#!/usr/bin/env python3
"""Git-backed coordination. Standard library only; no deployment or model calls."""
import argparse
import contextlib
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


class Error(Exception):
    pass


def run(*args, cwd=None, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and p.returncode:
        raise Error(p.stderr.strip() or p.stdout.strip() or 'Command failed')
    return p


def git(root, *args, check=True):
    return run('git', '-C', str(root), *args, check=check)


def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value) or len(value) > 80:
        raise Error('IDs/session/resource names must be lowercase words joined by hyphens (max 80).')
    return value


def safe_text(value):
    if len(value) > 6000 or '\x00' in value:
        raise Error('Record text is too long or contains NUL.')
    if re.search(r'-----BEGIN .*PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{20,}|\bsk-[A-Za-z0-9_-]{20,}', value):
        raise Error('Possible credential detected. Store a secret reference instead.')
    return value


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def read_json(path):
    if path.is_symlink():
        raise Error('Ledger/config files must not be symlinks.')
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise Error('Cannot read {}: {}'.format(path, e))


def remote_url(value):
    if not value or value.startswith('-'):
        raise Error('Missing or invalid coordination repository.')
    if '://' in value:
        parsed = urlsplit(value)
        if parsed.scheme not in ('https', 'ssh') or parsed.password or parsed.query or parsed.fragment:
            raise Error('Use a clean HTTPS/SSH URL without credentials or query parameters.')
        if parsed.username and not (parsed.scheme == 'ssh' and parsed.username == 'git'):
            raise Error('Do not embed credentials in a repository URL.')
    elif '@' in value and not value.startswith('git@'):
        raise Error('Use SSH git@host:path or a credential-free URL.')
    return value


class Project:
    def __init__(self, path):
        self.root = Path(git(path, 'rev-parse', '--show-toplevel').stdout.strip())
        self.config = read_json(self.root / '.agent/config.json')
        if self.config.get('schema_version') != 1:
            raise Error('Unsupported config schema.')
        self.owner = self.config.get('owner', '')
        if not self.owner or self.owner == 'CHANGE_ME':
            raise Error('Set the real human owner in .agent/config.json.')
        self.project = slug(self.config['project'])
        self.branch = slug(self.config['state_branch'])
        if self.branch in ('main', 'master'):
            raise Error('State branch must be separate from the code default branch.')
        self.actors = self.config['actors']
        if 'human' not in self.actors or not all(re.fullmatch('[a-z]+', a) for a in self.actors):
            raise Error('Invalid actors; human must be registered.')
        url = self.config.get('coordination_repository')
        self.remote = remote_url(url or git(self.root, 'remote', 'get-url', 'origin').stdout.strip())
        self.name = git(self.root, 'config', 'user.name').stdout.strip()
        self.email = git(self.root, 'config', 'user.email').stdout.strip()
        if not self.name or not self.email:
            raise Error('Configure Git user.name and user.email before ledger writes.')

    def actor(self, actor):
        if actor not in self.actors:
            raise Error('Actor is not registered in this project.')
        return actor

    def code(self):
        branch = git(self.root, 'branch', '--show-current').stdout.strip()
        commit = git(self.root, 'rev-parse', 'HEAD').stdout.strip()
        return {'project': self.project, 'branch': branch, 'commit': commit,
                'dirty': bool(git(self.root, 'status', '--porcelain').stdout)}

    def pushed(self):
        code = self.code()
        if code['dirty'] or not code['branch']:
            raise Error('Handoff/review requires a clean, named code branch. Commit explicit files first.')
        ref = 'refs/heads/' + code['branch']
        remote = git(self.root, 'ls-remote', '--exit-code', 'origin', ref).stdout.split()
        if not remote or remote[0] != code['commit']:
            raise Error('Push the current code commit to its named origin branch before handoff/review.')
        return code


class Ledger:
    def __init__(self, project, path):
        self.project, self.root = project, Path(path)
        if any((self.root / name).is_symlink() for name in ('tasks', 'handoffs', 'locks')):
            raise Error('Ledger directories must not be symlinks.')

    def task(self, ident):
        path = self.root / 'tasks' / (slug(ident) + '.json')
        t = read_json(path)
        if t.get('owner') != self.project.owner:
            raise Error('Task is not assigned to the configured human owner.')
        return t

    def holder(self, task, actor, session):
        self.project.actor(actor)
        slug(session)
        claim = task.get('claim') or {}
        if claim.get('actor') != actor or claim.get('session') != session:
            raise Error('Task is not held by this actor/session.')

    def locks(self):
        return [read_json(p) for p in sorted((self.root / 'locks').glob('*.json'))]

    def event(self, task, action, actor, session=None):
        task['updated_at'] = now()
        task.setdefault('events', []).append({'at': task['updated_at'], 'action': action,
            'actor': actor, 'session': session, 'git_identity': self.project.email,
            'code': self.project.code()})

    def save(self, task):
        write_json(self.root / 'tasks' / (task['id'] + '.json'), task)
        path = self.root / 'handoffs' / (task['id'] + '.md')
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ['# ' + task['id'], 'Owner: ' + task['owner'], 'Status: ' + task['status'],
                 'Goal: ' + task['title'], 'Scope: ' + ', '.join(task['scope']),
                 'Claim: ' + json.dumps(task.get('claim')), 'Next actor: ' + str(task.get('next_actor')),
                 'Updated: ' + task['updated_at'], '', '## Current state', task.get('state', ''),
                 '', '## Blocker', task.get('blocker', ''), '', '## Next step', task.get('next', ''),
                 '', '## Evidence'] + ['- ' + e for e in task.get('evidence', [])]
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def publish(self, message):
        git(self.root, 'add', '--', 'tasks', 'handoffs', 'locks')
        git(self.root, '-c', 'user.name=' + self.project.name, '-c', 'user.email=' + self.project.email,
            'commit', '-m', message)
        p = git(self.root, 'push', 'origin', 'HEAD:refs/heads/' + self.project.branch, check=False)
        if p.returncode:
            raise Error('Ledger push rejected or failed. No success recorded. Read current status before retrying.\n' + p.stderr.strip())


@contextlib.contextmanager
def checkout(project):
    with tempfile.TemporaryDirectory(prefix='agentos-') as folder:
        root = Path(folder) / 'ledger'
        run('git', 'clone', '--quiet', '--single-branch', '--branch', project.branch,
            '--no-tags', '--', project.remote, str(root))
        for name in ('tasks', 'handoffs', 'locks'):
            path = root / name
            if path.is_symlink():
                raise Error('Ledger directories must not be symlinks.')
            path.mkdir(exist_ok=True)
        yield Ledger(project, root)


def init_state(project):
    exists = git(project.root, 'ls-remote', '--heads', project.remote, 'refs/heads/' + project.branch)
    if exists.stdout.strip():
        raise Error('State branch already exists. No changes made.')
    with tempfile.TemporaryDirectory(prefix='agentos-init-') as folder:
        root = Path(folder)
        git(root, 'init', '--quiet')
        git(root, 'checkout', '--quiet', '--orphan', project.branch)
        (root / 'README.md').write_text('# AgentOS live ledger\nPrivate task/handoff/environment lock records. No secrets.\n'
            'Edit through scripts/agentos.py; never force-push. Actor labels are not authentication.\n')
        for name in ('tasks', 'handoffs', 'locks'):
            (root / name).mkdir()
            (root / name / '.gitkeep').touch()
        git(root, 'add', '--', 'README.md', 'tasks', 'handoffs', 'locks')
        git(root, '-c', 'user.name=' + project.name, '-c', 'user.email=' + project.email,
            'commit', '--quiet', '-m', 'chore: initialize shared operations ledger')
        git(root, 'remote', 'add', 'origin', project.remote)
        git(root, 'push', 'origin', 'HEAD:refs/heads/' + project.branch)
    print('Created ' + project.branch + '. No app/server changes.')


INSTALL_FILES = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agent/AGENTS.md', '.agent/HANDOFF.md',
    '.agent/config.json', '.agent/registry.example.json', '.agent/rules/sync.md',
    'scripts/agentos.py', 'docs/agentos-coordination.md', 'docs/agentos-migration.md')


def install(target, apply=False, preserve=False):
    source = Path(__file__).resolve().parents[1]
    target = Path(target).expanduser().absolute()
    if target.is_symlink() or not target.is_dir():
        raise Error('Install target must be an existing, non-symlink directory.')
    # Confirm that we are enrolling a repository root, not a nested/unrelated folder.
    root = Path(git(target, 'rev-parse', '--show-toplevel').stdout.strip())
    if root.resolve() != target.resolve():
        raise Error('Install at the target Git repository root.')
    plan, conflicts, preserved = [], [], []
    for name in INSTALL_FILES:
        origin = name.replace('docs/agentos-coordination.md', 'docs/coordination.md').replace(
            'docs/agentos-migration.md', 'docs/migration.md')
        src, dst = source / origin, target / name
        for parent in [dst] + list(dst.parents):
            if parent == target.parent:
                break
            if parent.is_symlink():
                raise Error('Refusing symlink target path: ' + name)
        if preserve and name in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md') and dst.exists():
            preserved.append(name)
            continue
        data = src.read_bytes()
        if name == '.agent/HANDOFF.md':
            data = b'# AgentOS orientation\nRead AGENTS.md, .agent/AGENTS.md, and .agent/config.json.\nRun scripts/agentos.py status; live handoffs are on agentos-state.\n'
        if dst.exists():
            if not dst.is_file() or dst.read_bytes() != data:
                conflicts.append(name)
        else:
            plan.append((dst, data))
    if conflicts:
        raise Error('Install stopped before writing; conflicts: ' + ', '.join(conflicts))
    if apply:
        # Track our new files so an I/O failure leaves existing files untouched.
        created = []
        try:
            for dst, data in plan:
                dst.parent.mkdir(parents=True, exist_ok=True)
                with dst.open('xb') as out:
                    created.append(dst)
                    out.write(data)
        except OSError:
            for dst in created:
                dst.unlink(missing_ok=True)
            raise
    print(('Installed ' if apply else 'Dry run: would add ') + str(len(plan)) + ' files. No commits/uploads.')
    if preserved:
        print('Preserved ' + ', '.join(preserved) + '; manually add shared agreement imports/references.')
    print('Set target .agent/config.json owner/project/coordination_repository; review diff before committing.')


def execute(project, args):
    if args.command == 'init-state':
        return init_state(project)
    if args.command == 'doctor':
        missing = [p for p in ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '.agent/AGENTS.md',
                              '.agent/HANDOFF.md') if not (project.root / p).is_file()]
        if missing:
            raise Error('Missing entry points: ' + ', '.join(missing))
        exists = git(project.root, 'ls-remote', '--heads', project.remote, 'refs/heads/' + project.branch)
        print(json.dumps({'project': project.project, 'owner': project.owner, 'code': project.code(),
                          'ledger_ready': bool(exists.stdout.strip()), 'actors': project.actors}, indent=2))
        if not exists.stdout.strip():
            raise Error('Coordination ledger not initialized. Run init-state once on the private coordinator.')
        return
    with checkout(project) as ledger:
        if args.command == 'status':
            tasks = [read_json(p) for p in sorted((ledger.root / 'tasks').glob('*.json'))]
            print(json.dumps({'tasks': [{k: t.get(k) for k in ('id', 'owner', 'project', 'status', 'claim', 'next_actor')}
                                      for t in tasks], 'locks': ledger.locks()}, indent=2))
            return
        if args.command == 'show':
            t = ledger.task(args.id)
            print((ledger.root / 'handoffs' / (t['id'] + '.md')).read_text())
            return
        actor = project.actor(args.actor)
        ident = slug(args.task if args.command in ('lock', 'unlock') else args.id)
        if args.command == 'create':
            if (ledger.root / 'tasks' / (ident + '.json')).exists():
                raise Error('Task already exists.')
            t = {'schema_version': 1, 'id': ident, 'owner': project.owner, 'project': project.project,
                 'title': safe_text(args.title), 'scope': [safe_text(s) for s in args.scope],
                 'status': 'queued', 'claim': None, 'next_actor': None, 'evidence': []}
        else:
            t = ledger.task(ident)
        if args.command == 'claim':
            if t.get('claim') or t['status'] != 'queued':
                raise Error('Task is claimed, in review, or closed.')
            if t.get('next_actor') and t['next_actor'] != actor:
                raise Error('Handoff is addressed to another actor.')
            code = project.code()
            if code['branch'] in ('', 'main', 'master'):
                raise Error('Create an isolated feature branch before claiming code work.')
            if t['project'] != project.project:
                raise Error('Claim from the assigned project repository/config.')
            t.update(status='in_progress', next_actor=None,
                     claim={'actor': actor, 'session': slug(args.session), 'started_at': now(), 'code': code})
        if args.command in ('checkpoint', 'handoff', 'review', 'lock', 'unlock'):
            ledger.holder(t, actor, args.session)
        if args.command in ('checkpoint', 'handoff', 'review'):
            t.update(state=safe_text(args.state), next=safe_text(args.next), blocker=safe_text(args.blocker))
            t['evidence'] = t.get('evidence', []) + [safe_text(e) for e in args.evidence]
        if args.command in ('handoff', 'review'):
            project.pushed()
            if any(lock['task'] == ident for lock in ledger.locks()):
                raise Error('Release this task\'s environment locks before transfer/review.')
            recipient = project.actor(args.to) if args.command == 'handoff' else 'human'
            t.update(claim=None, next_actor=recipient,
                     status='queued' if args.command == 'handoff' else 'review')
        if args.command == 'close':
            if actor != 'human' or t['status'] != 'review':
                raise Error('Only the human review workflow closes reviewed tasks.')
            t.update(status='done', next_actor=None)
            t['evidence'].append(safe_text(args.evidence))
        if args.command in ('lock', 'unlock'):
            resource = slug(args.resource)
            path = ledger.root / 'locks' / (resource + '.json')
            if args.command == 'lock':
                if path.exists():
                    raise Error('Environment is already locked. No takeover/expiry.')
                write_json(path, {'resource': resource, 'task': ident, 'actor': actor,
                                 'session': args.session, 'acquired_at': now()})
            else:
                lock = read_json(path)
                if (lock['task'], lock['actor'], lock['session']) != (ident, actor, args.session):
                    raise Error('Environment lock belongs to another task/session.')
                path.unlink()
        ledger.event(t, args.command, actor, getattr(args, 'session', None))
        ledger.save(t)
        ledger.publish('ops: {} {} by {}'.format(args.command, ident, actor))
        print('Recorded {} {} on {}.'.format(args.command, ident, project.branch))


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', default='.', help='Local code repository root')
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('doctor', 'status', 'init-state'):
        sub.add_parser(command)
    c = sub.add_parser('install')
    c.add_argument('target')
    c.add_argument('--apply', action='store_true')
    c.add_argument('--preserve-entrypoints', action='store_true')
    sub.add_parser('show').add_argument('id')
    for command in ('create', 'claim', 'checkpoint', 'handoff', 'review', 'close', 'lock', 'unlock'):
        c = sub.add_parser(command)
        c.add_argument('resource' if command in ('lock', 'unlock') else 'id')
        c.add_argument('--actor', default='human' if command in ('create', 'close') else None,
                       required=command not in ('create', 'close'))
        if command in ('lock', 'unlock'):
            c.add_argument('--task', required=True)
        if command not in ('create', 'close'):
            c.add_argument('--session', required=True)
        if command == 'create':
            c.add_argument('--title', required=True)
            c.add_argument('--scope', action='append', required=True)
        if command in ('checkpoint', 'handoff', 'review'):
            c.add_argument('--state', required=True)
            c.add_argument('--next', required=True)
            c.add_argument('--blocker', default='none')
            c.add_argument('--evidence', action='append', default=[])
        if command == 'handoff':
            c.add_argument('--to', required=True)
        if command == 'close':
            c.add_argument('--evidence', required=True)
    return p


def main():
    args = parser().parse_args()
    try:
        if args.command == 'install':
            install(args.target, args.apply, args.preserve_entrypoints)
        else:
            execute(Project(args.repo), args)
    except (Error, OSError, KeyError, TypeError) as e:
        print('AgentOS: ' + str(e), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
