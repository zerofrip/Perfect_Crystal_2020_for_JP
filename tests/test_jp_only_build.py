"""JP-only build contract tests.

These tests run without any ROM.  They verify that the default JP-only
builder refuses bad inputs before writing outputs (including under python -O,
which strips asserts), that its entry sources never reference the historical
English dependencies, and that the authored hall hook keeps its assembled
byte layout.
"""
import ast
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORK_DIR = REPO_ROOT / 'work'
sys.path.insert(0, str(WORK_DIR))

# Tokens that must never appear in the JP-only default build path: each one
# would imply an implicit read of a historical English reference, a public
# disassembly tree, an extracted asset, or a previous build artifact.
FORBIDDEN_IN_JP_ONLY = (
    'Pokemon - Crystal Version (UE)',
    'perfect_crystal_ue_patched.gbc',
    'perfect_crystal_source',
    'pokekuristaru',
    'hall_decorations_hook.gb',
    'rc1_reference', 'rc2_reference', 'rc3_reference', 'rc4_reference',
    'apply_restored_sprites',
    'Pokemon Perfect Crystal 2020 Japanese RC5',
)

# SHA-256 of the assembled RGBDS hook this emitter must reproduce
# (hall_decorations_hook.asm assembled by work/build_hall_hook.sh).
AUTHORED_HOOK_SHA256 = 'c4aead83766e9099d605dc2af273f1342f13f7045065c08b0abadbb3d7f58f43'


class TestHallHook(unittest.TestCase):

    def test_hook_reproduces_the_assembled_rgbds_bytes(self):
        """Byte regression against the hook assembled from the authored ASM."""
        from rc5_defs.hall_hook import hall_hook_code, HOOK_SIZE
        from hashlib import sha256
        code = hall_hook_code()
        self.assertEqual(len(code), HOOK_SIZE)
        self.assertEqual(sha256(code).hexdigest(), AUTHORED_HOOK_SHA256)
        self.assertEqual(code[:4], bytes.fromhex('7aa72036'))   # ld a,d; and a; jr nz
        self.assertEqual(code[-3:], bytes.fromhex('c3412e'))    # jp $2e41 (.normal)

    def test_rc4_correction_lands_on_the_hook_skip_pair(self):
        """RC4 NOPs exactly the cp $b7 / jr z pair inside the authored hook."""
        from apply_rc4_corrections import (
            apply_hall_hook_correction, HALL_HOOK_START, HALL_HOOK_SIZE,
        )
        from rc5_defs.hall_hook import hall_hook_code
        hook = hall_hook_code()
        skip_offset = 20
        self.assertEqual(hook[skip_offset:skip_offset + 4], bytes.fromhex('feb72817'))
        candidate = bytearray(HALL_HOOK_START + HALL_HOOK_SIZE + 16)
        candidate[HALL_HOOK_START:HALL_HOOK_START + HALL_HOOK_SIZE] = hook
        apply_hall_hook_correction(candidate)
        patched = candidate[HALL_HOOK_START:HALL_HOOK_START + HALL_HOOK_SIZE]
        self.assertEqual(patched[:skip_offset], hook[:skip_offset])
        self.assertEqual(patched[skip_offset:skip_offset + 4], bytes(4))
        self.assertEqual(patched[skip_offset + 4:], hook[skip_offset + 4:])


class TestJPOnlyInputs(unittest.TestCase):

    def _run_source_main(self, source_name, workspace_root):
        """Run a driver's __main__ with PC_WORKSPACE pointed at a fixture."""
        original_argv = sys.argv
        original_workspace = os.environ.get('PC_WORKSPACE')
        os.environ['PC_WORKSPACE'] = str(workspace_root)
        sys.argv = [source_name]
        popped = []
        try:
            for module in ('pc_env', 'rc5_layers', 'port_cerulean_cave',
                           'port_cerulean_cave_ranges'):
                if module in sys.modules:
                    sys.modules.pop(module, None)
                    popped.append(module)
            runpy.run_path(str(WORK_DIR / source_name), run_name='__main__')
        finally:
            sys.argv = original_argv
            if original_workspace is None:
                os.environ.pop('PC_WORKSPACE', None)
            else:
                os.environ['PC_WORKSPACE'] = original_workspace

    def test_builder_refuses_truncated_rom_without_writing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'Pocket Monsters - Crystal Version (Japan).gbc').write_bytes(b'\x00' * 1024 * 1024)
            with self.assertRaises(SystemExit):
                self._run_source_main('build_rc5_from_jp.py', root)
            self.assertFalse((root / 'work' / 'development_only_jp_partial.gbc').exists())
            self.assertFalse((root / 'work' / 'development_only_jp_partial.ips').exists())

    def test_builder_refuses_wrong_rom_without_writing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'Pocket Monsters - Crystal Version (Japan).gbc').write_bytes(
                bytes(range(256)) * (2 * 1024 * 1024 // 256))
            with self.assertRaises(SystemExit):
                self._run_source_main('build_rc5_from_jp.py', root)
            self.assertFalse((root / 'work' / 'development_only_jp_partial.gbc').exists())
            self.assertFalse((root / 'work' / 'development_only_jp_partial.ips').exists())

    def test_builder_refuses_same_size_mutation_even_with_python_o(self):
        """python -O strips asserts: the hash gate must still reject and write nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            rom = root / 'Pocket Monsters - Crystal Version (Japan).gbc'
            rom.write_bytes(bytes((7,)) * (2 * 1024 * 1024))  # right size, wrong ROM
            env = dict(os.environ, PC_WORKSPACE=str(root))
            result = subprocess.run(
                [sys.executable, '-O', str(WORK_DIR / 'build_rc5_from_jp.py')],
                capture_output=True, text=True, env=env, timeout=300)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertFalse((root / 'work' / 'development_only_jp_partial.gbc').exists())
            self.assertFalse((root / 'work' / 'development_only_jp_partial.ips').exists())

    def test_packager_refuses_unverified_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / 'work').mkdir()
            (root / 'Pocket Monsters - Crystal Version (Japan).gbc').write_bytes(
                bytes(range(256)) * (2 * 1024 * 1024 // 256))
            (root / 'work' / 'development_only_jp_partial.gbc').write_bytes(bytes(2048))
            (root / 'work' / 'development_only_jp_partial.ips').write_bytes(b'PATCH')
            with self.assertRaises(SystemExit):
                self._run_source_main('package_rc5_from_jp.py', root)
            self.assertFalse((root / 'work' / 'release').exists())


class TestJPOnlySources(unittest.TestCase):

    JP_ONLY_ENTRY_SOURCES = (
        'build_rc5_from_jp.py',
        'package_rc5_from_jp.py',
        'rc5_layers.py',
        'apply_rc4_corrections.py',
    )

    def test_entry_sources_are_free_of_historical_reads(self):
        for name in self.JP_ONLY_ENTRY_SOURCES + tuple(
                f'rc5_defs/{n}' for n in
                ('__init__.py', 'charmap.py', 'maps.py', 'encounters.py',
                 'trainers.py', 'items.py', 'cave.py', 'hall_hook.py')):
            source = (WORK_DIR / name).read_text(encoding='utf-8')
            for token in FORBIDDEN_IN_JP_ONLY:
                self.assertNotIn(token, source, (name, token))

    def test_def_modules_stay_data_only(self):
        """rc5_defs modules must not read the filesystem or evaluate code."""
        for path in sorted((WORK_DIR / 'rc5_defs').glob('*.py')):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, ('open', 'eval', 'exec'),
                                     (path.name, node.func.id))


class TestAuthoredText(unittest.TestCase):

    def _encoded_literals(self, node):
        """String constants encode() receives, skipping transform calls such
        as line.replace('リ', 'り') whose arguments are never encoded."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                continue
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                yield child.value
            yield from self._encoded_literals(child)

    def test_charmap_covers_encoded_dialogue_literals(self):
        """Every kana string passed through encode()/dialogue() encodes."""
        from japanese_text import CHARMAP
        missing = []
        for path in sorted(WORK_DIR.glob('*.py')):
            if path.name in ('build_partial_jp_patch.py', 'package_jp_patch.py',
                             'apply_jp_patch.py'):
                continue  # historical audit-only drivers
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ('encode', 'dialogue', 'localized_text'):
                        for literal in self._encoded_literals(node):
                            for ch in literal:
                                if '\u3040' <= ch <= '\u30ff' and ch not in CHARMAP:
                                    missing.append((path.name, ch))
        self.assertEqual(missing, [])


if __name__ == '__main__':
    unittest.main()
