# just volleyball 日本語化パッチ

対応: Steam Build ID 26937150、Windows版。非公式のオフライン用パッチです。
翻訳は初稿であり、人手によるレビュー前です。オンライン中のゲーム改変は公式規約で禁止されているため、オンラインでは使用しないでください。

通常UI1686メッセージ、称号547件、遊び方203表示フィールドの計2436項目を収録しています。メニュー、設定、チュートリアル、練習、HUD、ロッカー、ショップ、実績、称号、リプレイ等が対象です。記号や固有名詞の一部は原表記を維持しています。クレジットの長文、オンライン規約・サーバー側の文言、一部の動的な文章には英語が残ります。

## 適用

1. ゲームを終了します。
2. ZIPを任意のフォルダーへ展開します。
3. uvを用意します: https://docs.astral.sh/uv/getting-started/installation/
4. 展開先でPowerShellを開いて実行します。

```powershell
.\Install.ps1 -GameDirectory 'F:\SteamLibrary\steamapps\common\just volleyball'
```

Python 3.12と依存パッケージはuvが用意します。初回はインターネット接続が必要です。
EXE・PCKのハッシュが対応版と一致しない場合は適用を拒否します。別ビルドに強制適用する方法はありません。
元のPCKは `volleyball.pck.ja-backup` に保存されます。翻訳以外のゲーム素材を再エクスポートしません。

適用後も旧版のバックアップは残してください。翻訳を更新して適用し直す場合は、先に解除してから新しいパッチを適用します。

## 解除

ゲームを終了し、パッチの展開先で実行します。

```powershell
.\Restore.ps1 -GameDirectory 'F:\SteamLibrary\steamapps\common\just volleyball'
```

適用後にゲームが更新された場合は、古いバックアップへの復元を拒否します。その場合はSteamの「インストール済みファイル > ゲームファイルの整合性を確認」で現行版へ戻してください。バックアップは自動削除しません。

## 翻訳の修正

ソースリポジトリの `translations/ja/*.json` の `ja` を編集し、パッチを再生成してください。ZIP内の差分ファイルを直接編集しても反映できません。
編集方法と再生成手順はリポジトリの `docs/translation-editing.md` を参照してください。

同梱フォントはNoto Sans JPから固定ウェイトで生成し、JV Volleyball Japaneseへ改名したものです。SIL Open Font License 1.1で配布します。`OFL.txt` と `FONT-NOTICE.txt` を参照してください。
