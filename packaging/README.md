# 単体EXE用の配布データ

`patch-data/` は `tools/build_patch.py` が出力する、Steam Build ID 26937150用の配布可能な差分データです。GitHub Actionsはゲーム本体なしでこれを検証し、ライセンスとともにEXEへ埋め込みます。

mainへのpush、またはmainを指定したActionsの手動実行で、検証に成功した `JustVolleyballJA.exe` をGitHub ReleasesのAssetsへ自動公開します。タグは `build-<実行番号>-<再実行番号>` とし、同じ実行を再実行した場合も既存の配布物を上書きせず、新しいReleaseを作成します。Release本文には利用ガイドを掲載します。Actionsのartifactにも引き続き30日間保存します。

翻訳・MOD・差分生成処理の変更後は、対応する元ゲームを使って完全ビルドし、このディレクトリの更新もコミットしてください。`inputs.json` と生成元が一致しない場合、Actionsのビルドは失敗します。

元のゲームEXE、全PCK、復号鍵、復元ソースは収録しません。フォントの出典・ライセンスは `FONT-NOTICE.txt` と `OFL.txt` を参照してください。
