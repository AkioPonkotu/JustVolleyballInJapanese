"""Create renamed static OFL fonts so fallback weight is independent of variable-font handling."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'assets/fonts'
    for weight, style in [(600, 'SemiBold'), (800, 'ExtraBold')]:
        font = TTFont(folder / 'NotoSansJP.ttf', recalcTimestamp=False)
        instantiateVariableFont(font, {'wght': weight}, inplace=True)
        family = 'JV Volleyball Japanese'
        names = {1: family, 2: style, 3: 'JVVolleyballJapanese-' + style,
                 4: family + ' ' + style, 6: 'JVVolleyballJapanese-' + style,
                 16: family, 17: style}
        for record in font['name'].names:
            if record.nameID in names:
                record.string = names[record.nameID].encode(record.getEncoding())
        font.save(folder / f'JVVolleyballJP-{style}.ttf')
        print(f'Created static Japanese font weight {weight}: {style}')


if __name__ == '__main__':
    main()
