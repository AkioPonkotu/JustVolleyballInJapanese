# PCK解析・英文とフォントの特定結果

実施日: 2026-11-26。対象はSteam Build ID `26937150`。本調査の範囲はローカル展開と静的解析まで。ゲームの起動、翻訳の適用、ローダー導入は行っていない。

## 展開と復元

| 工程 | 結果 |
| --- | --- |
| gore v0.5.0によるPCK展開 | 13,778ファイルを書き出し、13,778ファイルを復号、スキップ0 |
| チェックサム | goreのMD5検証でエラー報告なし。GDREも展開エラーなしと報告 |
| GDRE Tools v2.7.4 | GDScript 293本を逆コンパイル、失敗0 |
| リソース変換 | 6,812件中6,811件成功。1件失敗 |
| フォント復元 | TTF 6個、OTF 1個、すべてcmapを解析可能 |

変換失敗は `game/stage/nationals/banner.blend`。参照画像 `game/stage/nationals/textures/CourtsideSeat_D.png` が見つからないため。英文とフォントの特定には支障がなかったが、復元プロジェクト全体の完全性や再エクスポート成功を意味しない。GDREには非原位置への変換171件、非可逆変換281件の報告もある。

実行EXEとPCKヘッダーは4.7.1、復元設定のfeaturesは4.7。一方、GDREの自動検出は4.5.0 / bytecode `4.5.0-stable (ebc36a7)` / Steam editionとなった。この食い違いは残っており、エディターやバイトコード再生成の版をGDREの推奨だけで確定しない。

展開先と成果物（ローカルのみ、Git管理対象外）:

- `work/raw/`: 元PCKから復号したファイル。
- `work/recovered/`: GDScript、テキストリソース、フォントなどの復元結果。
- `work/extract.log`: 展開結果。
- `work/recovered/gdre_export.log`: 復元結果と失敗詳細。
- `work/analysis/`: 文字列・参照先の索引。

元の `volleyball.exe` / `volleyball.pck` / `steam_api64.dll` は変更していない。復号鍵の値や復元したゲーム素材・ソースはGitに追加していない。

## 英文の保存場所

CSV / PO / MO / `.translation` はPCK内に見つからなかった。表示英文はスクリプト内の文字列、JSON、タイトル等のリソースに分かれている。メニューのシーンファイルだけを書き換える方法では、実行時にコードで生成されるUIを取りこぼす。

以下のパスは `work/recovered/` 以下。行番号は今回の復元結果のもの。

| 対象 | ファイルと位置 | 内容・確認例 |
| --- | --- | --- |
| メインメニュー | `game/ui/menu.gd:2088` | タブをコードで生成。`play`, `locker`, `shop`, `profile` など |
| メニュー説明・設定の補足 | `game/ui/menu_copy.gd:13` | `SUB` 辞書に画面説明と設定のツールチップ |
| 設定 | `game/ui/settings_panel.gd:261` | `audio`, `levels`, `master` など。753行にコントロールのリセット文言 |
| 遊び方本文 | `game/ui/how_to_text.json:1` | 10カテゴリ、49セクション。カテゴリ名・見出し・本文・表を収録 |
| 遊び方の読み込み | `game/ui/how_to_panel.gd:21` | `TEXT_PATH` が上記JSON。80行以降でFileAccess / JSON.parse_stringを使用 |
| チュートリアル | `game/drills/tutorial_director.gd:27` | 説明、コーチ文、操作プロンプトを配列・辞書で保持 |
| チュートリアル表示 | `game/ui/tutorial_overlay.gd:413` | `{jump}`, `{dive}` 等の入力表示用トークンを扱う |
| 試合HUD | `game/ui/hud.gd:1511` | 得点通知。1854行以降にセット・マッチポイント等の動的表示 |
| ポーズ | `game/ui/pause_menu.gd` | ポーズ中のメニュー文字列 |
| ロッカー・スタジオ | `game/character/locker.gd`, `game/character/studio/locker_studio.gd` | 編集UI、入力欄、ヒント |
| 実績 | `game/core/achievement_catalog.gd` | 実績名・説明文 |
| 称号 | `game/titles/items/*.tres` | リソースの `text` に称号文字列。UI辞書だけでは対象を網羅できない |

### 言語設定で見つかった点

`game/core/game_config.gd:73` の `_ready()` 内で `TranslationServer.set_locale("en")` が実行される。日本語Translationを追加する場合、登録だけでなく、この英語固定処理の扱いと実行順を解決する必要がある。

復元GDScriptでは `tr()` / `tr_n()` の呼び出しは検出されなかった。ただしLabel/Buttonの自動翻訳は別なので、辞書による翻訳が一切使えないという意味ではない。

`game/character/studio/studio_canvas.gd` の200・263・498行ではユーザー作成テキストの自動翻訳が無効化されている。ユーザー入力まで一括翻訳する変更は避ける。`title_chip.gd` や `replay_viewer.gd` には `draw_string()` による描画もあり、Labelの自動翻訳だけで全表示を扱えるとは判断できない。

### 文字列の索引

[解析スクリプト](../tools/analyze_localization.py) で、各文字列の元ファイル、行番号、周辺の式、候補とした理由をJSONに出力した。

| ローカル成果物 | 内容 |
| --- | --- |
| `work/analysis/all-english-literals.json` | 英字を含む文字列リテラル45,249出現。内部キー・パスも含む |
| `work/analysis/text-candidates.json` | 表示プロパティや補助関数、語句から抽出した3,759出現・重複除去3,182文字列 |
| `work/analysis/how-to-display-strings.json` | 遊び方JSONの表示フィールド203出現。JSON Pointerで元の位置を保持 |
| `work/analysis/resource-map.json` | `.remap` / `.import` とPCK内の実体パスの対応 |
| `work/analysis/font-references.json` | フォントへの直接参照12か所 |
| `work/analysis/localization-markers.json` | 言語固定、自動翻訳無効、独自描画等の検索結果 |

候補数は確定した翻訳総数ではない。チャットのフィルター辞書、ログ、内部キー、素材名、開発用UIも含み、短い動的表示や複数行の補助関数呼び出しには取りこぼしがあり得る。全文索引とソースで手作業の分類・文脈確認を行うための資料として使う。遊び方203件は `name` / `title` / `body` / `table` の空でない文字列で、IDや画像パスを除外した値。

なお、同梱の `game/net/mod.gd` は制裁・BAN等の処理で、名前だけからMODローダーと解釈できない。全293本の復元GDScriptに `load_resource_pack` の呼び出しは見つからなかった。その他の実装形態の読み込み口の有無までは断定しない。

## フォントの特定

| フォント | 元のリソースパス | 静的に確認した用途 |
| --- | --- | --- |
| Nunito Black | `game/fonts/Nunito/Nunito-Black.ttf` | UiStyleの見出し、タブ、HUD、タイトル等 |
| Nunito ExtraBold | `game/fonts/Nunito/Nunito-ExtraBold.ttf` | ボタン、強調表示、HUD等 |
| Nunito SemiBold | `game/fonts/Nunito/Nunito-SemiBold.ttf` | プロジェクト既定テーマ、本文、入力欄等 |
| Nunito SemiBold Italic | `game/fonts/Nunito/Nunito-SemiBoldItalic.ttf` | スタジオの斜体文字 |
| Nunito Bold | `game/fonts/Nunito/Nunito-Bold.ttf` | 同梱を確認。直接パス参照は今回の索引にない |
| Varsity Team Bold | `game/fonts/VarsityTeam-Bold.otf` | キャラクターモデルの番号、スタジオ |
| Public Pixel | `game/fonts/PublicPixel/PublicPixel.ttf` | pixelタイトル効果、スタジオ |

`project.godot` の `gui/theme/custom` は `res://game/ui/game_theme.tres`。このThemeはNunito SemiBoldを既定フォントにしている。

ただし、`game/ui/style/ui_style.gd:35`～の `FONT_BLACK` / `FONT_XBOLD` / `FONT_SEMI` と `font(path)` が各コントロールに個別のフォントを割り当てる。例えば172行でボタン、226行以降でLabel、672行以降でタブを設定している。**既定テーマのフォントだけを変更しても、個別指定が残る。**

PCK内の実体は `.godot/imported/*.fontdata`。例えばNunito SemiBoldは以下に対応する。

```text
res://game/fonts/Nunito/Nunito-SemiBold.ttf
 -> res://.godot/imported/Nunito-SemiBold.ttf-967b3762826f2d4e3d6c6109f4f6048f.fontdata
```

シーンやThemeもエクスポート時にバイナリへ変換されている。例えば `game_theme.tres.remap` は `.godot/exported/133200997/export-d462c3f25201b7e066ea06080b71da42-game_theme.res` を指す。将来の差し替えではソース名と実際にロードされるインポート先を区別する。

### 日本語の字形

fontTools 4.69.1で7個のフォントのUnicode cmapを解析した。

- 全7個でひらがな・カタカナの収録数は0。
- Nunito各書体とVarsity TeamではCJK統合漢字の収録数も0。
- Public PixelのCJK統合漢字は `U+5143`（元）と `U+5186`（円）の2字のみ。
- 全7個でサンプル `日本語設定あいうアイウ` の字形は未収録。

これは同梱フォント単体の結果。OS側のフォントfallbackによって一部表示できる可能性とは区別し、画面上で必ず文字化けするとは断定しない。環境に左右されず日本語を表示するには、日本語フォントを明示的にfallback追加または差し替えする設計が必要になる。今回、実画面の日本語表示確認はしていない。

## 再実行

ツールは公式GitHub Releasesから取得し、APIが返すSHA-256 digestと一致することを確認した。版とダイジェストは [toolchain.json](../evidence/toolchain.json) に保存。

```powershell
Set-Location 'F:\Github\JustVolleyballInJapanese'
# 新規の出力先に対して実行する。既存成果物を上書きする必要はない。
.\.local\gore\gore.exe extract 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.pck' --scan 'F:\SteamLibrary\steamapps\common\just volleyball\volleyball.exe' -o work/raw
# GDREはWindowsのGUIサブシステムEXEなので、PowerShellからは終了を待つ。
$gdreArgs = @('--headless', '--recover=F:\Github\JustVolleyballInJapanese\work\raw', '--output=F:\Github\JustVolleyballInJapanese\work\recovered')
Start-Process -FilePath '.\.local\gdre\gdre_tools.exe' -ArgumentList $gdreArgs -WindowStyle Hidden -Wait
uv run --with fonttools==4.69.1 python tools/analyze_localization.py
```

確定できたのは、PCK全体の復号、全GDScriptのテキスト化、主要英文の保存場所、フォントと字形範囲。日本語への置換や表示方式の試作は次の工程であり、今回は実施していない。
