"""Compare controller-card layout using isolated original and installed packs."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from catalog import ROOT
from pck import Pack, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'evidence/config-layout-investigation.json')
    parser.add_argument('--patched-pck', type=Path, help='Measure a generated PCK instead of the installed one')
    args = parser.parse_args()
    game = Path('F:/SteamLibrary/steamapps/common/just volleyball')
    exe = (game / 'volleyball.exe').read_bytes()
    settings = (ROOT / 'work/recovered/project.godot').read_text(encoding='utf-8')
    scene = '''[gd_scene load_steps=3 format=3]
[ext_resource type="Script" path="res://jvja/config_probe.gd" id="1"]
[ext_resource type="Script" path="res://game/camera/camera_rig.gd" id="2"]
[node name="Menu" type="Node3D"]
script = ExtResource("1")
[node name="MenuCam" type="Camera3D" parent="."]
[node name="CameraRig" type="Node3D" parent="."]
script = ExtResource("2")
[node name="Camera3D" type="Camera3D" parent="CameraRig"]
[node name="Ui" type="CanvasLayer" parent="."]
'''
    results = {}
    for language, name in [('en', 'volleyball.pck.ja-backup'), ('ja', 'volleyball.pck')]:
        folder = ROOT / 'work/validation/config-layout' / language
        folder.mkdir(parents=True, exist_ok=True)
        config = re.sub(r'run/main_scene=.*', 'run/main_scene="res://jvja/config_probe.tscn"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir="JVJA_Config_Investigation_' + language + '"', settings, count=1)
        data = (args.patched_pck if language == 'ja' and args.patched_pck else game / name).read_bytes()
        pack = Pack(data, exe[81005808:81005840])
        del pack.entries['project.binary']
        pack.write_patched(folder / 'volleyball.pck', {
            'project.godot': config.encode(),
            'jvja/config_probe.gd': (ROOT / 'tools/config_layout_probe.gd').read_bytes(),
            'jvja/config_probe.tscn': scene.encode(),
        })
        for binary in ['volleyball.exe', 'steam_api64.dll']:
            shutil.copyfile(game / binary, folder / binary)
        process = subprocess.run([str(folder / 'volleyball.exe'), '--headless', '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy'], capture_output=True, cwd=folder, timeout=90)
        log = (process.stdout + process.stderr).decode('utf-8', errors='replace')
        (folder / 'runtime.log').write_text(log, encoding='utf-8')
        rows = [json.loads(line.removeprefix('CONFIG_LAYOUT_JSON ')) for line in log.splitlines() if line.startswith('CONFIG_LAYOUT_JSON ')]
        if not rows or process.returncode or 'ERROR:' in log:
            raise RuntimeError('Inspect ' + str(folder / 'runtime.log'))
        results[language] = rows[-1] | {'source_pck_sha256': sha256(data), 'exit_code': process.returncode, 'runtime_errors': log.count('ERROR:')}
    output = args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
