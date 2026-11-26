"""Freeze the patch tool and assemble an offline Windows release ZIP."""
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP_NAME = 'JustVolleyballJA'


def package_release(output):
    if os.name != 'nt':
        raise RuntimeError('Build the Windows release on Windows')
    build = ROOT / 'work/pyinstaller'
    build.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
        '--console', '--noupx', '--name', APP_NAME,
        '--distpath', str(build / 'dist'), '--workpath', str(build / 'build'),
        '--specpath', str(build), str(ROOT / 'tools/patch_app.py'),
    ], check=True, cwd=ROOT)
    shutil.copyfile(build / 'dist' / f'{APP_NAME}.exe', output / f'{APP_NAME}.exe')
    shutil.copyfile(ROOT / 'docs/patch-user-guide.md', output / 'README.md')
    licenses = output / 'licenses'
    licenses.mkdir(exist_ok=True)
    # Include licenses from the exact distributions used by this build, including
    # native libraries' bundled notices (e.g. OpenSSL in cryptography's license).
    license_files = []
    for name in ('bsdiff4', 'cryptography', 'cffi', 'pycparser', 'pyinstaller', 'pyinstaller-hooks-contrib'):
        distribution = importlib.metadata.distribution(name)
        found = []
        for file in distribution.files or []:
            if Path(str(file)).name.lower().startswith(('license', 'copying', 'notice')) and distribution.locate_file(file).is_file():
                target = licenses / name / Path(str(file))
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(distribution.locate_file(file), target)
                found.append(target.relative_to(output).as_posix())
        if not found:
            raise RuntimeError(f'No license found for {name}')
        license_files.extend(found)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    shutil.copyfile(python_license, licenses / 'Python-LICENSE.txt')
    license_files.append('licenses/Python-LICENSE.txt')
    # Tcl/Tk supply the GUI and carry their own license notices.
    import tkinter
    tcl = tkinter.Tcl()
    tcl_library = Path(tcl.eval('info library'))
    for name in ('tcl8.6', 'tk8.6'):
        source = tcl_library.parent / name / 'license.terms'
        if not source.exists() and name == 'tcl8.6':
            version = tcl.eval('info patchlevel')
            source = ROOT / 'packaging/licenses' / f'tcl{version}-license.terms'
        shutil.copyfile(source, licenses / f'{name}-license.terms')
        license_files.append(f'licenses/{name}-license.terms')
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    include = [f'{APP_NAME}.exe', 'manifest.json', 'OFL.txt', 'FONT-NOTICE.txt', 'README.md']
    include += license_files + [item['payload'] for item in manifest['files']]
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(set(include)):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, (output / name).read_bytes())
    print(f'Built offline EXE release: {archive}')


if __name__ == '__main__':
    package_release(ROOT / 'dist/just-volleyball-ja')
