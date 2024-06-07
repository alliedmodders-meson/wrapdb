import io
import shutil
import hashlib
import argparse
import tempfile
import requests
import configparser

from tools import utils
from pathlib import Path
from packaging import version as pkgversion


class Script:
    _args: argparse.Namespace

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--repo',
                            type=str,
                            required=True)

        parser.add_argument('--token',
                            type=str,
                            required=True)

        self._args = parser.parse_args()

    def run(self):
        releases = utils.get_releases()

        for file in Path('subprojects').iterdir():
            if file.is_file() and file.suffix == '.wrap':
                config = configparser.ConfigParser(interpolation=None)
                config.read(file)
                header = config[config.sections()[0]]
                version = pkgversion.Version(header['wrapdb_version'])

                if utils.is_updated_package(file.stem, version, releases):
                    self._build_release(file, version, config, header)

    def _build_release(self,
                       file: Path,
                       version: pkgversion.Version,
                       config: configparser.ConfigParser,
                       header: configparser.SectionProxy):
        tag = f'{file.stem}_{str(version)}'

        print(f'Building {tag}... ', end='')

        upload_url = self._get_upload_url(tag, self._get_release_body(config))

        # Fallback
        response = requests.get(header['source_url'], stream=True)
        response.raise_for_status()

        self._upload(upload_url, header['source_filename'], response.content, 'application/zip')

        header['source_fallback_url'] = self._get_download_url(tag, header['source_filename'])

        # Patch
        if 'patch_directory' in header:
            base_dir = header.get('directory', file.stem)
            patch_dir = Path(file.parent, 'packagefiles', header['patch_directory'])

            with tempfile.TemporaryDirectory() as temp_dir:
                shutil.copytree(patch_dir, Path(temp_dir, base_dir))

                archive = Path(shutil.make_archive(f'{tag}_patch', 'zip', temp_dir, base_dir))
                archive_data = archive.read_bytes()

                self._upload(upload_url, archive.name, archive_data, 'application/zip')

                del header['patch_directory']

                sig = hashlib.sha256()
                sig.update(archive_data)

                header['patch_url'] = self._get_download_url(tag, archive.name)
                header['patch_hash'] = sig.hexdigest()
                header['patch_filename'] = archive.name

        # Config
        buffer = io.StringIO()
        config.write(buffer)
        buffer.seek(0)
        buffer = buffer.read().rstrip('\n') + '\n'

        self._upload(upload_url, file.name, buffer.encode(), 'text/plain')

        print('completed!')

    def _get_upload_url(self, tag: str, body: str) -> str:
        response = requests.post(
            url=f'https://api.github.com/repos/{self._args.repo}/releases',
            headers={
                'Authorization': f'token {self._args.token}'
            },
            json={
                'name': tag,
                'tag_name': tag,
                'body': body
            }
        )

        response.raise_for_status()

        return response.json()['upload_url'].replace(u'{?name,label}', '')

    def _upload(self, upload_url: str, filename: str, data: bytes, mimetype):
        response = requests.post(
            url=upload_url,
            headers={
                'Authorization': f'token {self._args.token}',
                'Content-Type': mimetype
            },
            params={
                'name': filename
            },
            data=data
        )

        response.raise_for_status()

    def _get_release_body(self, config: configparser.ConfigParser) -> str:
        provision = utils.get_provision(config)
        if provision is None:
            return ''

        body = ''
        mapping = {
            'dependency_names': 'Dependency names',
            'program_names': 'Program names'
        }

        for k, v in mapping.items():
            if k in provision:
                provision[k].sort()
                body += f'{v}: {', '.join([f'`{item}`' for item in provision[k]])}\n'

        return body

    def _get_download_url(self, tag: str, filename: str):
        return utils.get_download_url(self._args.repo, tag, filename)


if __name__ == '__main__':
    Script().run()
