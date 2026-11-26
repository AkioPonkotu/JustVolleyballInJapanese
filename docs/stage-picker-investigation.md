# 会場選択UIの未翻訳原因

調査日: 2026-11-27。対象: Steam Build ID `26937150`、インストール済み日本語化PCK。ゲームファイルの変更や再適用は行っていない。

## 結論

会場選択画面が表示する大文字を含む会場名が、日本語翻訳辞書に登録されていない。既存の小文字の訳とはキーが異なるため、Labelの自動翻訳で一致せず英語が残る。画面全体の翻訳初期化失敗や画像への文字の埋め込みではない。

## 表示経路

以下のパスはローカルの `work/recovered/` 以下。

- `game/ui/menu.gd:1153`: `_open_stage_picker()` が `StagePicker` を開く。
- `game/stage/stage.gd:205`: `STAGES` 辞書が `Nationals Arena` 等の表示名を持つ。
- `game/stage/stage.gd:907`: `Stage.title(id)` が表示名をそのまま返す。
- `game/ui/lobby/stage_picker.gd`: `_tile()` が `name_lbl.text = Stage.title(id)` として各タイルのLabelを生成する。ツールチップも同じ表示名を使う。
- `game/ui/lobby/stage_banner.gd:330`: 上部プレビューも `_title.text = Stage.title(id)` を使う。
- 一方、`game/ui/menu.gd:935` の通常メニュー用会場表示は `.to_lower()` を使い、`tools/build_patch.py` がその表示に `tr(t)` を追加している。選択画面にはこの小文字化がない。

## インストール済みデータの確認

元PCKのバックアップとインストール済みPCKを読み取り、会場定義・選択UI・バナーの3スクリプトが元と同一であることを確認した。`jvja/messages.json` の既定コンテキストには1,686件あり、次の状態だった。現在の翻訳カタログにも大文字の7キーはすべて存在しない。

| 画面で使うキー | 完全一致の訳 | 小文字キーの訳 |
| --- | --- | --- |
| `Nationals Arena` | なし | 全国大会会場 |
| `School Gym` | なし | 学校の体育館 |
| `Grass Court` | なし | なし |
| `Beach` | なし | ビーチ |
| `Tutorial` | なし | チュートリアル |
| `Clouds` | なし | なし |
| `Outer Space` | なし | なし |

同じ画面の「完了」は `done.text = "done"` に対応する `done → 完了` が辞書にあるため翻訳できており、添付画像と整合する。機械可読の確認結果は [stage-picker-investigation.json](../evidence/stage-picker-investigation.json) に保存した。

## 取りこぼした背景

`tools/catalog.py` の `sync` は未翻訳候補を `game/ui/`・`game/drills/`・`game/character/` に限定する。表示名の定義がある `game/stage/stage.gd` は対象外。UI側には表示名のリテラルがなく `Stage.title(id)` しかないため、この候補一覧では会場名を拾えない。

また、`tools/analyze_localization.py` の表示候補抽出はヒューリスティックであり、全文索引には7件とも存在するが、候補索引にはそのうち4件しかない。候補抽出と辞書収録の両方で動的な表示元を追う必要がある。

## 修正方針

最小修正は、この画面で実際に使う大文字の7キーに訳を追加し、翻訳データを再ビルド・適用すること。Labelの自動翻訳が利用できるため、画像の加工は不要。別途、練習用会場等の表示名も含め `STAGES` の全表示名を候補検査の対象にすると再発を防ぎやすい。

今回の依頼は原因調査のため、翻訳カタログ・ビルド処理・配布物・インストール済みゲームは変更していない。ゲーム起動による表示の再検証は行わず、添付画像と復元コード・実際のPCK内辞書の照合に基づいて判定した。
