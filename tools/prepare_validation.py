"""Prepare isolated runtime checks; never change the installed game or its saves."""
import argparse
from pathlib import Path
import shutil

from catalog import ROOT
from pck import Pack


SMOKE = '''extends Node
func _ready():
    load("res://jvja/bootstrap.gd").install()
    var original = load("res://game/fonts/Nunito/Nunito-SemiBold.ttf")
    var guide = JSON.parse_string(FileAccess.get_file_as_string("res://game/ui/how_to_text.json"))
    var checks = {
        "locale": TranslationServer.get_locale() == "ja",
        "translation": TranslationServer.translate("settings") == "設定",
        "formatting": TranslationServer.translate("set %d") % 2 == "第2セット",
        "default context": TranslationServer.translate("pro") == "公式球",
        "title context": TranslationServer.translate("pro", &"titles") == "プロ",
        "Japanese glyph": original.fallbacks.size() > 0 and original.fallbacks.back().has_char(0x8a2d),
        "Japanese weight": original.fallbacks.back().get_font_weight() == 600,
        "guide JSON": guide.categories[0].name == "操作設定",
    }
    for label in checks:
        if not checks[label]:
            push_error("[JVJA TEST] FAILED: " + label)
            get_tree().quit(1)
            return
    print("[JVJA TEST] PASS: ", checks.size(), " explicit runtime checks (release assertions not used)")
    get_tree().quit()
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, default=Path('F:/SteamLibrary/steamapps/common/just volleyball'))
    parser.add_argument('--patched-pck', type=Path, default=ROOT / 'work/build/volleyball-ja.pck')
    args = parser.parse_args()
    exe = (args.game_dir / 'volleyball.exe').read_bytes()
    data = args.patched_pck.read_bytes()
    for mode in ['smoke', 'visual']:
        target = ROOT / 'work/validation' / mode
        target.mkdir(parents=True, exist_ok=True)
        pack = Pack(data, exe[81005808:81005840])
        del pack.entries['project.binary']
        if mode == 'smoke':
            settings = '[application]\nconfig/name="JVJA Smoke Test"\nrun/main_scene="res://jvja/test.tscn"\n'
            changes = {'jvja/test.gd': SMOKE.encode('utf-8'),
                       'jvja/test.tscn': b'[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://jvja/test.gd" id="1"]\n[node name="Test" type="Node"]\nscript = ExtResource("1")\n'}
        else:
            settings = (ROOT / 'work/recovered/project.godot').read_text(encoding='utf-8')
            settings = settings.replace('config/name="volleyball"', 'config/name="JVJA Validation"')
            settings = settings.replace('run/main_scene=', 'config/use_custom_user_dir=true\nconfig/custom_user_dir="JVJA_Validation"\nrun/main_scene=', 1)
            changes = {}
        changes['project.godot'] = settings.encode('utf-8')
        pack.write_patched(target / 'volleyball.pck', changes)
        shutil.copyfile(args.game_dir / 'volleyball.exe', target / 'volleyball.exe')
        shutil.copyfile(args.game_dir / 'steam_api64.dll', target / 'steam_api64.dll')
        print(target)


if __name__ == '__main__':
    main()
