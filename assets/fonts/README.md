# 日本語フォント

`NotoSansJP.ttf` はNoto Sans JP Variableの未改変配布ファイル。

- 上流: https://github.com/notofonts/noto-cjk
- 取得元: `Sans/Variable/TTF/Subset/NotoSansJP-VF.ttf`
- SHA-256: `f4b373b226668ee33a6e54b02823dcd2d1209f17159f777421ae8c2275160369`
- ライセンス: 同梱の `OFL.txt`（SIL Open Font License 1.1）

配布パッチでは、この可変フォントから生成した静的600/800ウェイトの `JVVolleyballJP-SemiBold.ttf` / `JVVolleyballJP-ExtraBold.ttf` を使用する。改変版のフォント名は `JV Volleyball Japanese` に変更し、OFL 1.1と元の著作権表記を保持する。既存の欧文フォントを保持し、日本語のfallbackとして利用する。

再生成: `uv run --python 3.12 --with-requirements requirements-build.txt python tools/prepare_fonts.py`

フォント内の著作権表記：© 2014-2021 Adobe (http://www.adobe.com/), with Reserved Font Name 'Source'.
