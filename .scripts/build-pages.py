import json
import jinja2
import shutil
import argparse
import configparser


from tools import utils
from pathlib import Path


class Script:
    _args: argparse.Namespace

    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument('--repo',
                            type=str,
                            required=True)

        parser.add_argument('--pages_dir',
                            type=Path,
                            default=Path('.scripts', 'pages'))

        parser.add_argument('--build_dir',
                            type=Path,
                            default=Path('_pages'))

        self._args = parser.parse_args()

    def run(self):
        assert self._args.pages_dir.exists() and self._args.pages_dir.is_dir()

        self._args.build_dir.mkdir(exist_ok=True)

        data = {}
        releases = utils.get_releases()

        # Get packages data
        for file in Path('subprojects').iterdir():
            if file.is_file() and file.suffix == '.wrap':
                config = configparser.ConfigParser(interpolation=None)
                config.read(file)

                if file.stem not in releases:
                    continue

                data[file.stem] = {}
                data[file.stem]['versions'] = [str(version) for version in releases[file.stem]]

                provision = utils.get_provision(config)
                if provision is not None:
                    for provision_type, provision_names in provision.items():
                        provision_names.sort()
                        data[file.stem][provision_type] = provision_names

        # Build page
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self._args.pages_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

        template = env.get_template('index.html')
        rendered = template.render(repo=self._args.repo, data=data, get_download_url=utils.get_download_url)

        # Save index.html
        with open(Path(self._args.build_dir, 'index.html'), 'w') as f:
            f.write(rendered)

        # Save releases.json
        with open(Path(self._args.build_dir, 'releases.json'), 'w') as f:
            json.dump(data, f)


if __name__ == '__main__':
    Script().run()
