"""Measure real menu bars in an isolated pack; never change installed game files or saves."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess

from catalog import ROOT
from pck import Pack, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, default=Path('F:/SteamLibrary/steamapps/common/just volleyball'))
    parser.add_argument('--patched-pck', type=Path, required=True)
    parser.add_argument('--scale', type=float, default=1.4)
    parser.add_argument('--output', type=Path, default=ROOT / 'work/validation/menu-layout-result.json')
    args = parser.parse_args()
    folder = ROOT / 'work/validation/menu-layout-regression'
    folder.mkdir(parents=True, exist_ok=True)
    exe = (args.game_dir / 'volleyball.exe').read_bytes()
    data = args.patched_pck.read_bytes()
    pack = Pack(data, exe[81005808:81005840])
    del pack.entries['project.binary']
    settings = (ROOT / 'work/recovered/project.godot').read_text(encoding='utf-8')
    settings = re.sub(r'run/main_scene=.*', 'run/main_scene="res://jvja/layout_probe.tscn"\nconfig/use_custom_user_dir=true\nconfig/custom_user_dir="JVJA_Layout_Regression"', settings, count=1)
    settings = re.sub(r'window/stretch/scale=.*', f'window/stretch/scale={args.scale}', settings, count=1)
    scene = '''[gd_scene load_steps=3 format=3]
[ext_resource type="Script" path="res://jvja/layout_probe.gd" id="1"]
[ext_resource type="Script" path="res://game/camera/camera_rig.gd" id="2"]
[node name="Menu" type="Node3D"]
script = ExtResource("1")
[node name="MenuCam" type="Camera3D" parent="."]
[node name="CameraRig" type="Node3D" parent="."]
script = ExtResource("2")
[node name="Camera3D" type="Camera3D" parent="CameraRig"]
[node name="Ui" type="CanvasLayer" parent="."]
'''
    pack.write_patched(folder / 'volleyball.pck', {
        'project.godot': settings.encode(),
        'jvja/layout_probe.gd': (ROOT / 'tests/menu_layout_probe.gd').read_bytes(),
        'jvja/layout_probe.tscn': scene.encode(),
    })
    for name in ['volleyball.exe', 'steam_api64.dll']:
        shutil.copyfile(args.game_dir / name, folder / name)
    process = subprocess.run([str(folder / 'volleyball.exe'), '--headless', '--rendering-method', 'gl_compatibility', '--audio-driver', 'Dummy'], capture_output=True, cwd=folder, timeout=120)
    log = (process.stdout + process.stderr).decode('utf-8', errors='replace')
    (folder / 'runtime.log').write_text(log, encoding='utf-8')
    rows = [json.loads(line.removeprefix('LAYOUT_JSON ')) for line in log.splitlines() if line.startswith('LAYOUT_JSON ')]
    if not rows:
        raise RuntimeError('Probe did not produce a result; inspect ' + str(folder / 'runtime.log'))
    result = rows[-1] | {'source_pck_sha256': sha256(data), 'script_errors': log.count('SCRIPT ERROR'), 'runtime_errors': log.count('ERROR:'), 'exit_code': process.returncode}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'combinations={result["combinations"]}, fits={result["fits"]}, tooltips={result["tooltips_ok"]}, errors={result["runtime_errors"]}')
    for sample in result['samples']:
        print(f'{sample["case"]}: available={sample["available_width"]:.3f}, top={sample["top"]["minimum_width"]}, bottom={sample["bottom"]["minimum_width"]}')
    if process.returncode or result['runtime_errors'] or not result['fits'] or not result['tooltips_ok']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
