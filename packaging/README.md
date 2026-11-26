# 単体EXE用の配布データ

`patch-data/` は `tools/build_patch.py` が出力する、Steam Build ID 26937150用の配布可能な差分データです。GitHub Actionsはゲーム本体なしでこれを検証し、ライセンスとともにEXEへ埋め込みます。

翻訳・MOD・差分生成処理の変更後は、対応する元ゲームを使って完全ビルドし、このディレクトリの更新もコミットしてください。`inputs.json` と生成元が一致しない場合、Actionsのビルドは失敗します。

元のゲームEXE、全PCK、復号鍵、復元ソースは収録しません。フォントの出典・ライセンスは `FONT-NOTICE.txt` と `OFL.txt` を参照してください。
