"""Find the installed game using Steam's local library metadata."""
from pathlib import Path
import re


APP_ID = '5037200'


def steam_directory():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
            return Path(winreg.QueryValueEx(key, 'SteamPath')[0])
    except (ImportError, OSError, TypeError, ValueError):
        return None


def _values(text, key):
    # VDF quoted strings escape backslashes and quotes. Preserve other characters.
    pattern = r'"' + re.escape(key) + r'"\s+"((?:\\.|[^"\\])*)"'
    return [re.sub(r'\\([\\"])', r'\1', value)
            for value in re.findall(pattern, text)]


def _read(path):
    try:
        return path.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError, ValueError):
        return ''


def find_game_directory(steam_root=None):
    """Return a verified installation folder, or None when detection fails."""
    root = Path(steam_root) if steam_root is not None else steam_directory()
    if root is None:
        return None
    libraries = [root]
    for value in _values(_read(root / 'steamapps/libraryfolders.vdf'), 'path'):
        library = Path(value)
        if library.is_absolute() and library not in libraries:
            libraries.append(library)
    for library in libraries:
        metadata = _read(library / f'steamapps/appmanifest_{APP_ID}.acf')
        if _values(metadata, 'appid') != [APP_ID]:
            continue
        folders = _values(metadata, 'installdir')
        if len(folders) != 1:
            continue
        folder = Path(folders[0])
        if not folders[0] or folder.is_absolute() or folder.drive or '..' in folder.parts:
            continue
        game = library / 'steamapps/common' / folder
        try:
            if all((game / name).is_file() for name in ('volleyball.exe', 'volleyball.pck')):
                return game
        except (OSError, ValueError):
            continue
    return None
