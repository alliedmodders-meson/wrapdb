import unittest
import argparse
import subprocess
import configparser

from tools import utils
from pathlib import Path
from packaging import version as pkgversion


class Script(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = argparse.ArgumentParser()

        parser.add_argument('--diff_ref',
                            type=str,
                            default='origin/main')

        parser.add_argument('--build_dir',
                            type=Path,
                            default=Path('builddir'))

        cls._args = parser.parse_args()

    def test_packages(self):
        releases = utils.get_releases()

        for file in Path('subprojects').iterdir():
            if file.is_file() and file.suffix == '.wrap':
                with self.subTest('check package', path=file.as_posix()):
                    config = configparser.ConfigParser(interpolation=None)
                    config.read(file)

                    sections = config.sections()
                    self.assertGreater(len(sections), 0, 'empty config')

                    header = config[config.sections()[0]]

                    self.assertIn('wrapdb_version', header)
                    version = pkgversion.Version(header['wrapdb_version'])
                    self.assertEqual(str(version), header['wrapdb_version'])

                    if (
                        self._has_diff(file) or (
                            'patch_directory' in header
                            and
                            self._has_diff(Path(file.parent, 'packagefiles', header['patch_directory']))
                        )
                    ):
                        self.assertTrue(
                            utils.is_updated_package(file.stem, version, releases),
                            'package has been updated, but its version has not changed or is lower than the latest'
                        )

                        self._check_update(file, config, header)

    def _check_update(self, file: Path, config: configparser.ConfigParser, header: configparser.SectionProxy):
        with self.subTest('check naming'):
            self.assertRegex(file.stem, r'^[a-z0-9-]+$')

            provision = utils.get_provision(config)
            if provision is not None:
                for provision_type, provision_names in provision.items():
                    for provision_name in provision_names:
                        with self.subTest('check provision naming', provision_type=provision_type):
                            self.assertRegex(provision_name, fr'^{file.stem}$|^{file.stem}-[a-z0-9-]+$')

        with self.subTest('check config'):
            self.assertEqual(header.name, 'wrap-file')

            # required keys
            self.assertIn('source_url', header)
            self.assertIn('source_hash', header)
            self.assertIn('source_filename', header)

            # prohibited keys
            self.assertNotIn('patch_url', header)
            self.assertNotIn('patch_hash', header)
            self.assertNotIn('patch_filename', header)
            self.assertNotIn('patch_fallback_url', header)
            self.assertNotIn('source_fallback_url', header)

            meson_test = subprocess.run(
                [
                    'meson',
                    'setup',
                    self._args.build_dir,
                    '--wipe',
                    '--backend=none',
                    f'-Dproject={file.stem}'
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            if meson_test.returncode:
                log_file = Path(self._args.build_dir, 'meson-logs', 'meson-log.txt')

                self.assertTrue(log_file.exists() and log_file.is_file(),
                                f'Meson test failed, but "{log_file.as_posix()}" file does not exists')

                self.fail('Meson test failed.\n'
                          + '-' * 10 + '[' + log_file.as_posix() + ']' + '-' * 10 + '\n'
                          + log_file.read_text())

    def _has_diff(self, path: Path) -> bool:
        return len(subprocess.check_output(['git', 'diff', self._args.diff_ref, '--', path.as_posix()])) > 0


if __name__ == '__main__':
    unittest.main(verbosity=2)
