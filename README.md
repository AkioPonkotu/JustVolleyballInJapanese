# Just Volleyball 日本語化MOD・実装方法の調査

調査日: 2026-11-26（日本時間）

**現時点では日本語表示の動作実証は未完了。** ローカル版の構造と、実装に必要な工程を確認した。Godotの翻訳機能を使う案はあるが、暗号化PCKと外部起動機能の無効化が先に解決すべき点。ゲーム本体のEXE/PCK/DLLは変更していない。

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

ハッシュとヘッダー情報は [evidence/installed-build.json](evidence/installed-build.json) に記録。各ファイルの暗号化フラグは一覧の復号前なので未確認。「一覧が暗号化されている」ことと「全ファイルが暗号化されている」ことは区別する。

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

ツールは今回インストール・実行していない。次回のローカル検証コマンド例（各ツールを準備した後）:

```powershell
# リポジトリのルートで実行。workはGit管理対象外。
gore info 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.pck'
gore extract 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.pck' --scan 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.exe' -o '.\work\raw'
# GDRE Toolsを準備し、展開結果が正常だった場合に実施。
gore recover '.\work\raw' -o '.\work\recovered'
```

これらは上流のCLI資料に基づく予定手順。本作ではまだ未実行。鍵やゲームから復元した素材・コードをリポジトリに追加しない。GDREが本作のバイトコード版を処理できるか、カスタムSteam機能の復元に制約がないかも確認する。復元プロジェクト全体の再エクスポートは、元のSteam機能等を維持できると確認するまで採用しない。

復元後に検索するもの:

```powershell
rg --files .\work\recovered | rg '\.(csv|po|translation|gd|tscn|tres|ttf|otf)$'
rg -n 'TranslationServer|tr\(|auto_translate|draw_string|draw_multiline_string|load_resource_pack|text\s*=' .\work\recovered
```

調べる対象はメニュー、設定、チュートリアル、操作説明、試合HUD、エラー文。`.translation` が既にあるか、英語がシーン・スクリプトに直接書かれているかで実装が変わる。現段階では具体的な翻訳ファイル名や収録文字列数は確定できていない。

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

日本語の字形を収録したフォント（例: Noto Sans JP）をMODに同梱し、ライセンスも同梱する。テーマの既定フォントまたは既存フォントのfallbackに設定し、個別のフォント指定も調べる。既存フォントの日本語対応は未確認。文字サイズ、改行、ボタン幅、リッチテキスト、スコア表示を実画面で検証する。

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

1. 暗号化PCKをローカルで展開できるか確認する。
2. メニューの文字列、フォント、翻訳関連設定の実パスを特定する。
3. オフラインでローダーの起動、または再構築PCKの起動を確認する。
4. ボタン1つを日本語化して描画・フォントを検証する。
5. メニュー→設定→チュートリアル→HUDの順に対象を増やす。

本調査で完了したのはファイル構造、暗号化ヘッダー、起動制約、関連ツール・配布案と規約の確認。復号・翻訳抽出・ローダー導入・日本語表示・オンライン動作の検証は実施していない。
