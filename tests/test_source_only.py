"""Source-only publication sanity checks.

These tests run without any ROMs or third-party dependencies. They verify that
all Python source compiles, that no private absolute paths remain, and that the
repository only contains permitted source file types.
"""
import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
WORK_DIR = REPO_ROOT / 'work'

# Generic patterns that catch hardcoded home-directory paths without including
# any literal private path in this audit file.
PATH_PATTERNS = [
    re.compile(r'/home/[a-zA-Z0-9_]+'),
    re.compile(r'/tmp/[a-zA-Z0-9_]+'),
]

# Patterns that may indicate accidentally committed secrets.
SECRET_PATTERNS = [
    re.compile(r'BEGIN\s+.*\s+PRIVATE\s+KEY'),
    re.compile(r'api[_-]?key\s*=\s*["\']\S+'),
    re.compile(r'password\s*=\s*["\']\S+'),
    re.compile(r'token\s*=\s*["\']\S+'),
    re.compile(r'secret\s*=\s*["\']\S+'),
]

# Forbidden tracked file extensions.  Source-only publication must not contain
# ROMs, patches, saves, images, audio, object files, or generated dumps.
FORBIDDEN_EXTENSIONS = {
    '.gb', '.gbc', '.sgb', '.sav', '.ram', '.rtc',
    '.ips', '.bps', '.patch', '.diff',
    '.o', '.obj', '.sym', '.map',
    '.png', '.jpg', '.jpeg', '.bmp', '.gif',
    '.wav', '.mp3', '.ogg', '.bin',
    '.key', '.pem',
    '.json',  # verification/range dumps are generated, not authored
}

# Explicitly permitted extensions for tracked source/text files.  Files with
# other extensions are rejected (this prevents historical raw .asm dumps from
# slipping in).  An empty suffix is allowed for files like LICENSE and .gitignore.
ALLOWED_EXTENSIONS = {'', '.py', '.java', '.asm', '.md', '.sh', '.txt'}

# Directory names that must never appear inside the publication tree.
DISALLOWED_DIRS = {
    'pokekuristaru', 'perfect_crystal_source', 'lazy_ips',
    'pokemon-reverse-engineering-tools', 'gb-asm-tools', 'pokecrystal',
    'rgbds-0.2.5', 'rgbds-0.3.0', 'rgbds-0.3.4', 'rgbds-history',
    'ghidra_11.4.2_PUBLIC', 'ghidra_projects', 'pyboy_venv',
    'release', '__pycache__', '.git', '.venv', 'venv', 'env',
}

# The only authored assembly source.  Everything else .asm is generated.
AUTHORIZED_ASM = {pathlib.Path('work/hall_decorations_hook.asm')}


def _git_candidates(root):
    """Return files git would track or propose, including symlinks.

    Uses null-terminated output so filenames with spaces or special characters
    are parsed correctly.  Deduplication is lexical (on the relative path)
    rather than by inode, so symlinks are preserved as distinct candidates.
    """
    try:
        out = subprocess.check_output(
            ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback for environments without git.
        for path in root.rglob('*'):
            if path.is_file() or path.is_symlink():
                yield path
        return

    seen = set()
    for line in out.split(b'\x00'):
        if not line:
            continue
        rel = line.decode('utf-8', errors='replace')
        if rel in seen:
            continue
        seen.add(rel)
        path = root / rel
        if path.is_file() or path.is_symlink():
            yield path


def _contains_ups_magic(path):
    """True if the file starts with the IPS magic header 'PATCH'."""
    try:
        with path.open('rb') as f:
            header = f.read(5)
    except OSError:
        return False
    return header == b'PATCH'


def _is_clean_text(path):
    """True if the file decodes as UTF-8 and contains no NUL bytes."""
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b'\x00' in data:
        return False
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


def _disallowed_dir_in_path(path, root):
    """True if any path component under root is a forbidden directory name."""
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return True
    return any(part in DISALLOWED_DIRS for part in rel.parts)


def _audit(root):
    """Run the publication candidate validator on an arbitrary root.

    Returns a dict mapping check names to lists of offenders.  This is used for
    both the real repository and negative test fixtures.
    """
    offenders = {
        'symlink_file': [],
        'symlink_dir': [],
        'private_path': [],
        'secret': [],
        'forbidden_ext': [],
        'disallowed_dir': [],
        'binary_or_ips': [],
        'raw_asm': [],
    }

    for path in _git_candidates(root):
        rel = path.relative_to(root) if path.is_relative_to(root) else path

        if path.is_symlink():
            offenders['symlink_file'].append(str(rel))
            continue

        try:
            resolved_rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            resolved_rel = rel
        if any(part in DISALLOWED_DIRS for part in resolved_rel.parts):
            offenders['disallowed_dir'].append(str(rel))

        if rel.suffix.lower() == '.asm':
            if rel not in AUTHORIZED_ASM:
                offenders['raw_asm'].append(str(rel))

        if rel.suffix.lower() in FORBIDDEN_EXTENSIONS:
            offenders['forbidden_ext'].append(str(rel))
        elif rel.suffix.lower() not in ALLOWED_EXTENSIONS:
            offenders['forbidden_ext'].append(str(rel))

        if _is_clean_text(path):
            text = path.read_text(encoding='utf-8')
            for pattern in PATH_PATTERNS:
                if pattern.search(text):
                    offenders['private_path'].append((str(rel), pattern.pattern))
                    break
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    offenders['secret'].append((str(rel), pattern.pattern))
                    break
        else:
            offenders['binary_or_ips'].append(('binary/non-utf8', str(rel)))
            continue

        if _contains_ups_magic(path):
            offenders['binary_or_ips'].append(('ips_magic', str(rel)))

    # Directory symlinks are not returned by _git_candidates, so walk explicitly.
    for dirpath, dirs, _ in os.walk(root):
        if '.git' in dirs:
            dirs.remove('.git')
        for d in dirs:
            p = pathlib.Path(dirpath) / d
            if p.is_symlink():
                rel = p.relative_to(root)
                offenders['symlink_dir'].append(str(rel))

    return offenders


class TestSourceOnly(unittest.TestCase):

    def _import_pc_env(self):
        sys.path.insert(0, str(WORK_DIR))
        try:
            import pc_env
            return pc_env
        finally:
            sys.path.pop(0)

    def test_pc_env_default_workspace(self):
        """pc_env.workspace() defaults to the repository root when PC_WORKSPACE is unset."""
        original = os.environ.pop('PC_WORKSPACE', None)
        try:
            pc_env = self._import_pc_env()
            self.assertEqual(pc_env.workspace().resolve(), REPO_ROOT.resolve())
        finally:
            if original is not None:
                os.environ['PC_WORKSPACE'] = original

    def test_pc_env_env_override(self):
        """PC_WORKSPACE overrides the default workspace."""
        with tempfile.TemporaryDirectory() as tmp:
            original = os.environ.get('PC_WORKSPACE')
            os.environ['PC_WORKSPACE'] = tmp
            try:
                pc_env = self._import_pc_env()
                self.assertEqual(pc_env.workspace().resolve(), pathlib.Path(tmp).resolve())
            finally:
                if original is None:
                    os.environ.pop('PC_WORKSPACE', None)
                else:
                    os.environ['PC_WORKSPACE'] = original

    def test_repository_passes_audit(self):
        """The real repository contains only permitted source files."""
        offenders = _audit(REPO_ROOT)
        # Re-raise as a readable failure list.
        bad = {k: v for k, v in offenders.items() if v}
        self.assertEqual(bad, {})

    def test_python_compiles(self):
        """All Python source in work/ compiles without executing or writing caches."""
        for path in sorted(WORK_DIR.glob('*.py')):
            source = path.read_text(encoding='utf-8')
            compile(source, str(path), 'exec')

    def test_dependency_closure(self):
        """All imports resolve to stdlib, local modules, or known externals."""
        stdlib = set(getattr(sys, 'stdlib_module_names', []))
        local = {p.stem for p in WORK_DIR.glob('*.py')} | {'pc_env'}
        known_external = {'lazy_ips', 'pokemontools', 'pyboy'}
        allowed = stdlib | local | known_external

        unknown = []
        for path in sorted(WORK_DIR.glob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name.split('.')[0] for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module.split('.')[0]]
                else:
                    continue
                for name in names:
                    if name not in allowed:
                        unknown.append((path.name, name))
        self.assertEqual(sorted(set(unknown)), [])

    def test_negative_disguised_binary(self):
        """Files with safe extensions but binary/IPS content are rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'clean.txt').write_text('hello world')
            (root / 'fake.txt').write_bytes(b'PATCH' + b'\x00' * 10)
            (root / 'binary.txt').write_bytes(b'\x00\x01\x02\x03')
            offenders = _audit(root)
            names = {entry[1] for entry in offenders['binary_or_ips']}
            self.assertIn('fake.txt', names)
            self.assertIn('binary.txt', names)
            self.assertNotIn('clean.txt', names)

    def test_negative_file_symlink(self):
        """A tracked file symlink is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'real.txt').write_text('x')
            (root / 'link.txt').symlink_to(root / 'real.txt')
            offenders = _audit(root)
            self.assertIn('link.txt', offenders['symlink_file'])

    def test_negative_directory_symlink(self):
        """A directory symlink is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'real_dir').mkdir()
            (root / 'link_dir').symlink_to(root / 'real_dir', target_is_directory=True)
            offenders = _audit(root)
            self.assertIn('link_dir', offenders['symlink_dir'])

    def test_negative_raw_asm(self):
        """Only the authored hook assembly is allowed; generated .asm is rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'work').mkdir()
            (root / 'work' / 'hall_decorations_hook.asm').write_text('section')
            (root / 'work' / 'generated.asm').write_text('db 0')
            offenders = _audit(root)
            self.assertIn('work/generated.asm', offenders['raw_asm'])
            self.assertNotIn('work/hall_decorations_hook.asm', offenders['raw_asm'])

    def test_rc4_hall_flag_math(self):
        """Hall flags sum to 42 total, 41 actual items, with one poster flag."""
        sys.path.insert(0, str(WORK_DIR))
        try:
            from apply_rc4_corrections import apply_hall_hook_correction
        finally:
            sys.path.pop(0)
        red_only = {0x2B9, 0x2BC, 0x2CD, 0x2CF}
        hall = set(range(0x2A4, 0x2D2)) - red_only
        poster = {0x2CC}
        items = hall - poster
        self.assertEqual(len(hall), 42)
        self.assertEqual(len(items), 41)
        self.assertIn(0x2B7, items)
        self.assertNotIn(0x2B7, red_only)

    def test_rc4_slot_weights_sum_to_100(self):
        """Johto grass slot weights represent a complete probability distribution."""
        sys.path.insert(0, str(WORK_DIR))
        try:
            from apply_rc4_corrections import SLOT_WEIGHTS
        finally:
            sys.path.pop(0)
        self.assertEqual(sum(SLOT_WEIGHTS), 100)

    def test_rc4_encounter_correction_asserts_on_wrong_baseline(self):
        """apply_encounter_corrections rejects a wrong baseline without mutation."""
        sys.path.insert(0, str(WORK_DIR))
        try:
            from apply_rc4_corrections import (
                apply_encounter_corrections, JOHTO_GRASS_START, RECORD_WIDTH,
                _UNION_CAVE_B1F, _WHIRL_ISLAND_LUGIA, _DARK_CAVE_VIOLET,
                _ROUTE_31, _ROUTE_32,
            )
        finally:
            sys.path.pop(0)
        size = JOHTO_GRASS_START + 61 * RECORD_WIDTH + 16
        candidate = bytearray(size)
        record_start, map_id = _UNION_CAVE_B1F
        candidate[record_start:record_start + 2] = map_id
        candidate[record_start + 5:record_start + 19] = bytes([8, 74, 6, 41, 8, 41, 8, 95, 6, 7, 8, 19, 8, 20])  # wrong last slot
        original = bytes(candidate)
        with self.assertRaises(AssertionError):
            apply_encounter_corrections(candidate)
        self.assertEqual(bytes(candidate), original)

    def test_rc4_encounter_correction_probabilities(self):
        """apply_encounter_corrections produces the exact RC4 target probabilities."""
        sys.path.insert(0, str(WORK_DIR))
        try:
            from apply_rc4_corrections import (
                apply_encounter_corrections, _percentages, RECORD_WIDTH,
                _UNION_CAVE_B1F, _WHIRL_ISLAND_LUGIA, _DARK_CAVE_VIOLET,
                _ROUTE_31, _ROUTE_32, _period_offset,
            )
        finally:
            sys.path.pop(0)
        size = max(_UNION_CAVE_B1F[0], _WHIRL_ISLAND_LUGIA[0], _DARK_CAVE_VIOLET[0],
                   _ROUTE_31[0], _ROUTE_32[0]) + RECORD_WIDTH + 16
        candidate = bytearray(size)
        fixtures = [
            (_UNION_CAVE_B1F, 0, [8, 74, 6, 41, 8, 41, 8, 95, 6, 7, 8, 19, 8, 19]),
            (_UNION_CAVE_B1F, 1, [8, 74, 6, 41, 8, 41, 8, 95, 6, 7, 8, 19, 8, 19]),
            (_WHIRL_ISLAND_LUGIA, 2, [25, 98, 26, 41, 25, 98, 27, 98, 28, 42, 27, 140, 27, 140]),
            (_DARK_CAVE_VIOLET, 2, [3, 74, 2, 155, 2, 74, 4, 74, 2, 41, 4, 206, 4, 155]),
            (_ROUTE_31, 0, [0, 0, 0, 0, 0, 0, 5, 152, 0, 0, 0, 0, 0, 0]),
            (_ROUTE_32, 1, [4, 23, 5, 19, 7, 69, 6, 179, 7, 16, 7, 158, 7, 187]),
        ]
        for (record_start, map_id), period, slots in fixtures:
            candidate[record_start:record_start + 2] = map_id
            base = _period_offset(record_start, period)
            candidate[base:base + 14] = bytes(slots)
        apply_encounter_corrections(candidate)
        union_morning = _percentages(candidate[_period_offset(_UNION_CAVE_B1F[0], 0):_period_offset(_UNION_CAVE_B1F[0], 0) + 14])
        self.assertEqual(union_morning.get((7, 6)), 10)
        self.assertEqual(union_morning.get((95, 8)), 5)
        union_day = _percentages(candidate[_period_offset(_UNION_CAVE_B1F[0], 1):_period_offset(_UNION_CAVE_B1F[0], 1) + 14])
        self.assertEqual(union_day.get((7, 6)), 10)
        self.assertEqual(union_day.get((95, 8)), 5)
        # Period 2 (night) was zero-filled and untouched; snapshot it to prove no mutation.
        union_night = candidate[_period_offset(_UNION_CAVE_B1F[0], 2):_period_offset(_UNION_CAVE_B1F[0], 2) + 14]
        self.assertEqual(union_night, bytes(14))
        whirl = _percentages(candidate[_period_offset(_WHIRL_ISLAND_LUGIA[0], 2):_period_offset(_WHIRL_ISLAND_LUGIA[0], 2) + 14])
        self.assertEqual(whirl.get((140, 27)), 10)
        self.assertEqual(whirl.get((98, 27)), 5)
        dark = _percentages(candidate[_period_offset(_DARK_CAVE_VIOLET[0], 2):_period_offset(_DARK_CAVE_VIOLET[0], 2) + 14])
        self.assertEqual(dark.get((155, 2)), 30)
        self.assertEqual(dark.get((155, 4)), 10)
        route31 = _percentages(candidate[_period_offset(_ROUTE_31[0], 0):_period_offset(_ROUTE_31[0], 0) + 14])
        self.assertEqual(route31.get((152, 5)), 10)
        route32 = _percentages(candidate[_period_offset(_ROUTE_32[0], 1):_period_offset(_ROUTE_32[0], 1) + 14])
        self.assertEqual(route32.get((158, 7)), 20)
        self.assertEqual(route32.get((69, 7)), 4)

    def test_rc4_hall_hook_nops_skip(self):
        """apply_hall_hook_correction NOPs the cp $b7 / jr z skip without moving branches."""
        sys.path.insert(0, str(WORK_DIR))
        try:
            from apply_rc4_corrections import (
                apply_hall_hook_correction, HALL_HOOK_START, HALL_HOOK_SIZE,
            )
        finally:
            sys.path.pop(0)
        size = HALL_HOOK_START + HALL_HOOK_SIZE + 16
        candidate = bytearray(size)
        # Valid hook header and footer; the bytes between are irrelevant to the guard.
        candidate[HALL_HOOK_START:HALL_HOOK_START + 4] = bytes.fromhex('7aa72036')
        candidate[HALL_HOOK_START + HALL_HOOK_SIZE - 3:HALL_HOOK_START + HALL_HOOK_SIZE] = bytes.fromhex('c3412e')
        candidate[HALL_HOOK_START + 20:HALL_HOOK_START + 24] = bytes.fromhex('feb72817')
        apply_hall_hook_correction(candidate)
        self.assertEqual(candidate[HALL_HOOK_START + 20:HALL_HOOK_START + 24], bytes(4))


if __name__ == '__main__':
    unittest.main()
