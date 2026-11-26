# Just Volleyball 日本語化パッチ

調査日: 2026-11-26（日本時間）

**編集可能な翻訳2436項目と、適用・解除できるオフライン用パッチの初版を作成済み。** メニュー・設定・遊び方の日本語表示を検証用コピーで確認した。元のインストール先には未適用。

## パッチと翻訳の編集

- 作成済みパッケージ: `dist/just-volleyball-ja.zip`（ローカル生成物、Git管理対象外）
- 対応: Windows / Steam Build ID **26937150**。別ビルドへの適用は拒否する。
- 翻訳の正本: [translations/ja](translations/ja)。用途別JSON・固定ID・原文・訳文・レビュー状態・メモで管理する。
- [翻訳の編集・参照更新・再生成](docs/translation-editing.md)
- [パッチの導入・解除](docs/patch-user-guide.md)
- 配布ZIPの `JustVolleyballJA.exe` から適用・解除できます。利用者のPython・uv導入と実行時の通信は不要です。
- `main` へのpushごとに [GitHub Actions](https://github.com/AkioPonkotu/JustVolleyballInJapanese/actions/workflows/build-exe.yml) でWindows x64のexeをビルドします。成功した実行の **Artifacts** から `JustVolleyballJA-windows-x64-（コミットSHA）` をダウンロードできます（保存期間30日、GitHubへのログインが必要）。手動実行も可能です。
- Actionsのartifactにある `JustVolleyballJA.exe` **単体で適用・解除できます**。翻訳・フォント・差分データ・ライセンスはexeに埋め込んであり、外部の `manifest.json` や `payload/` は不要です。ライセンスはアプリの「ライセンス」から確認できます。
- [検証結果](evidence/patch-validation.json)
- [メニューの右端見切れ対策と幅の再測定](docs/menu-layout-fix.md)

遊び方の203表示フィールドと称号547件を含む。2436項目の内訳は、通常UIの共有メッセージ1686件、独立した文脈の称号547件、遊び方203件。訳文はすべて初稿で、人によるレビュー前。名前・記号等の原表記を維持した項目も含む。

再抽出では人の訳・レビュー状態・メモを上書きしない。出典行番号を別ファイルに分離し、翻訳ファイルの不要な差分を抑える。差し込み文字・操作アイコン・タグの欠落、JSONキーの重複、原文やIDの変更はビルド前に検出する。

```powershell
uv run --python 3.12 python tools/catalog.py validate
uv run --python 3.12 --with-requirements requirements-build.txt python tools/build_patch.py
```

元PCKを再エクスポートせず、変更リソースを暗号化して末尾に追加する。配布ZIPには変更分のバイナリ差分、自作コード、翻訳辞書と日本語フォントを含める。元PCK全体、ゲームEXE、復号鍵は含めない。適用・解除はバックアップとハッシュ照合を行う。

日本語フォントはNoto Sans JP由来の静的600/800ウェイトを既存7フォントのfallbackへ追加する。原版の欧文フォントや番号用フォントを保つ。表示文言の初版であり、全画面・全組み合わせの検証を意味しない。クレジットの長文、オンライン規約・サーバー側文言、一部の動的な文章や固有名詞には英語が残る。

以下は実装前に行った構造調査。具体的な原文・フォントの場所は [PCK解析結果](docs/pck-analysis.md) を参照。

## ローカルで確認した事実

対象: `F:\SteamLibrary\steamapps\common\just volleyball`

| 項目 | 結果 |
| --- | --- |
| Steam App ID / Build ID | 5037200 / 26937150（インストール済みmanifest） |
| 実行ファイルのバージョン | `4.7.1.stable.custom_build.a13da4feb`（`volleyball.exe --version`） |
| ゲームエンジン | Godot 4.7.1のカスタムビルド |
| 配置ファイル | `volleyball.exe`, `volleyball.pck`, `steam_api64.dll` |
| PCKサイズ | 171,181,436 bytes |
| PCK形式 | v4、ヘッダー上のエンジン版4.7.1 |
| PCK flags | 3 = 暗号化ディレクトリ + 相対file base |
| 格納エントリー数 | 13,778（暗号化テーブル直前の公開カウント） |
| ディレクトリ位置 | 169,725,040 bytes |
| 平文翻訳ファイル | インストール先の外部ファイルとしては存在しない |

ハッシュとヘッダー情報は [evidence/installed-build.json](evidence/installed-build.json) に記録。追加調査で13,778ファイルすべての復号に成功した。結果の集計は [evidence/localization-inventory.json](evidence/localization-inventory.json) に保存。

再確認用の読み取り専用スクリプト:

```powershell
Set-Location 'F:\Github\JustVolleyballInJapanese'
.\tools\Inspect-Game.ps1
```

ヘッダーの解釈はGodot公式の [file_access_pack.h](https://github.com/godotengine/godot/blob/master/core/io/file_access_pack.h) と [file_access_pack.cpp](https://github.com/godotengine/godot/blob/master/core/io/file_access_pack.cpp) を参照。

## 簡単な導入方法が使えない理由

- 実機の `--help` に `--script` / `--main-pack` がない。
- 存在しないスクリプトを指定して `--headless --script ... --quit` を実行したが、スクリプトの読み込みエラーにはならず通常起動側のgateログが出た。外部スクリプトが動作した証拠はない。
- `--headless --main-pack __probe_missing__.pck --quit` は次のエラーで終了した。

```text
--main-pack was specified on the command line, but this Godot binary
was compiled without support for path overrides. Aborting.
```

このため、起動オプションで翻訳用の別PCKやローダースクリプトを渡す手順は、この配布ビルドでは利用できない。根拠となるGodotの条件付き機能は [コマンドライン公式資料](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html) にも記載されている。

Godotは追加PCKを読み込むAPIを持つが、ゲームまたはローダー側から呼び出す必要がある。日本語化PCKを横に置くだけで自動適用されるとは判断できない。[公式PCK資料](https://docs.godotengine.org/en/stable/tutorials/export/exporting_pcks.html)

## 実装の候補

| 方法 | このゲームでの判断 |
| --- | --- |
| 公式に翻訳データやMOD読み込み口を提供してもらう | オンライン向けには最優先。現時点で提供の有無は確認できていない |
| GDPatchで翻訳・フォント・必要なコードを実行時に追加 | 配布方式として有力な検証候補。ただし本作の暗号化v4 / カスタム4.7.1での互換性は未検証 |
| PCKを解析し、購入者の環境で変更済みPCKを生成 | オフライン試作の候補。復号、再構築、起動時の整合性確認を順に実証する必要がある |
| `--script`を使うMod Loaderの自己導入 | このビルドの起動機能では使えない |
| `--main-pack`で差し替え | 実機で拒否された |
| Unity向け翻訳MOD | 本作はGodotなので適用対象外 |

### 1. ローカル解析で文字列の保存場所を特定する

[gore](https://github.com/figurophobia/gore) はWindows実行ファイル内の鍵探索と暗号化PCK v4の展開を実装しており、作者は別のGodot 4.7.1作品での検証を報告している。本作での成功を保証するものではない。必要なら [GDRE Tools](https://github.com/GDRETools/gdsdecomp) を後段に使い、シーン・リソース・GDScriptを復元する。

追加調査ではgore v0.5.0 / GDRE Tools v2.7.4を実行し、この工程まで完了した。以下は上流CLIによる手順例。実際のツール配置と実行結果は [PCK解析結果](docs/pck-analysis.md) を参照:

```powershell
# リポジトリのルートで実行。workはGit管理対象外。
gore info 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.pck'
gore extract 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.pck' --scan 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.exe' -o '.\work\raw'
# GDRE Toolsを準備し、展開結果が正常だった場合に実施。
gore recover '.\work\raw' -o '.\work\recovered'
```

鍵やゲームから復元した素材・コードはリポジトリに追加しない。GDREは293本すべてのスクリプトを逆コンパイルしたが、3Dリソース1件の変換失敗とエンジン版の検出差異がある。復元プロジェクト全体の再エクスポートは、元のSteam機能等を維持できると確認するまで採用しない。

復元後に検索するもの:

```powershell
rg --files .\work\recovered | rg '\.(csv|po|translation|gd|tscn|tres|ttf|otf)$'
rg -n 'TranslationServer|tr\(|auto_translate|draw_string|draw_multiline_string|load_resource_pack|text\s*=' .\work\recovered
```

英文は主にGDScriptへ直接記載され、遊び方は `game/ui/how_to_text.json` に収録されていた。CSV / PO / MO / `.translation` は見つからなかった。候補索引は作成済みだが、全翻訳対象の確定には手作業の分類が必要。

### 2. 最小の日本語表示を試作する

まずメニューボタン1つと日本語フォントで成立を確認する。GodotのButton/Labelには自動翻訳があるので、既存英語をキーにした日本語Translationを登録する案がある。英語キーは大文字小文字・改行・空白も一致させる。[公式国際化資料](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)

翻訳登録処理の概念例（ゲームに読み込ませる入口は別途必要）:

```gdscript
var translation := Translation.new()
translation.locale = "ja"
# 以下の英語は仮の例。解析で判明した実際の表示文に置き換える。
translation.add_message("Settings", "設定")
TranslationServer.add_translation(translation)
TranslationServer.set_locale("ja")
```

自動翻訳無効のコントロール、文字列連結、独自描画には個別の変更が必要になる。プレイヤー名・ロビー名・チャットなどのユーザー入力は翻訳対象から外す。`%s`、`%d`、`{name}`、BBCodeや入力アイコンは保持する。

日本語の字形を収録したフォント（例: Noto Sans JP）をMODに同梱し、ライセンスも同梱する。主要UIはNunitoの個別指定があり、既定テーマだけの変更では不足する。同梱7フォントすべてにひらがな・カタカナがないことを確認済み。文字サイズ、改行、ボタン幅、リッチテキスト、スコア表示は今後の実画面検証が必要。

### 3. ローダー互換性と配布方式を決める

[GDPatch導入資料](https://gdpatch.dev/using/install/) と [MOD作成資料](https://gdpatch.dev/modding/getting-started/) に基づく候補構成:

```text
GDPatch/mods/just_volleyball_ja/
  gdpatch_mod.toml
  patcher.lua     # 必要な場合にスクリプトを変更
  data.pck        # 自作の翻訳・日本語フォント・起動処理
```

`data.pck` 内の `res://gdpatch/mods/just_volleyball_ja/mod.gd` 等から翻訳を登録する設計が考えられる。元スクリプトの変更はGDPatchのpatcher APIを使用する。これは上流の方式説明であり、本作でロードが成立したという意味ではない。GDPatch自体はalpha版。まずオフライン環境で起動と暗号化パックの対応を確認する。

GDPatchが使えない場合は、変更済みPCKをローカルで生成する方法を検討する。元PCKを直接編集せず作業用コピーで検証し、対応するBuild IDとSHA-256をチェックしてから適用する。元のEXEが再構築PCKを受け入れるか、起動gateに整合性検査があるかは未確認。

公開するものは自作の翻訳データ、変更処理、再配布できるフォントとライセンス、導入・解除手順に限定する設計とする。ゲームの全PCKや復元コードを同梱する方式は避ける。ゲーム更新時はハッシュを照合して、文字列・パス・スクリプト変更箇所を再確認する。

## オンライン利用の制約

[公式オンライン規約](https://store.steampowered.com/eula/5037200_eula_0) の第3項はオンラインプレイ中のゲーム改変を禁止している。日本語化が例外であるという記載は確認できない。従って、この調査から提案できるのはオフライン試作まで。オンライン向けに配布・利用するには開発者へ日本語化の扱いを確認する必要がある。問い合わせは今回送信していない。

## 次に検証する順序

1. 完了: 暗号化PCKのローカル展開。
2. 完了: メニューの文字列、フォント、翻訳関連設定の実パスの特定。
3. 完了: 元EXEで読み込める変更PCKを生成し、隔離したコピーで起動確認。
4. 完了: 日本語描画・フォント・差し込み文字を検証。
5. 完了: メニュー・設定・チュートリアル・遊び方・HUD・ロッカー・実績・称号・リプレイ等の翻訳初稿を作成。

元のインストール先への適用とオンライン動作の検証は実施していない。オンライン中の改変禁止という公式規約は変わらず、このパッチはオフライン用。
