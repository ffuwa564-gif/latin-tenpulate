# Latin 1000 — 意味テンプレート学習

ラテン語の基本語彙 **1,000語**を、品詞と意味分野に基づく **23種類の意味テンプレート**へ分類したPDF教材。

## 完成PDF

- [完全版PDF（1,000語）](output/latin_1000_semantic_templates.pdf)
- [PDF検証結果（manifest.json）](output/manifest.json)

## 収録範囲

- DCCの基本語彙997語（英語の語義を維持）
- 追加補助語3語：gemma（宝石）、vitrum（ガラス）、puellula（少女）
- 23種類の意味テンプレート（章ごとに日本語の説明を掲載）
- 各行に順位、ラテン語の見出し語、英語語義を掲載

**重要**: テンプレートは学習用の便宜的分類であり、語の意味を完全に予測できる法則ではありません。英語語義は元データに基づくもので、1,000語すべての日本語訳を追加した版ではありません。同じ単純化された語形でも同音異義語などがあるため、類似語の差は辞書や実例で確かめてください。

## 再生成と検証

必要な環境：Python 3、reportlab、pymupdf、DejaVu Sansフォント。

    pip install reportlab pymupdf
    python scripts/build_pdf.py

スクリプトはdata/latin_1000.csvから以下を生成します。

- output/latin_1000_semantic_templates.pdf
- output/manifest.json

**ビルドが成功する条件**：CSVが厳密に1,000行あり、通し番号1〜1,000に欠番や重複がなく、PDFからも1,000件の番号を再抽出できること。

GitHub Actionsでも自動的に生成・検証して、PDFとマニフェストをリポジトリへコミットします。

## 出典

- [Dickinson College Commentaries: Latin Core Vocabulary](https://dcc.dickinson.edu/latin-core-list1)
- [元CSVの公開ミラー](https://github.com/sjhuskey/latin-vocabulary/blob/main/dcc-latin-core-list.csv)

## フォルダ

- data/latin_1000.csv — 1,000語の完全な語彙データ
- scripts/build_pdf.py — 分類、PDF生成、検証
- output/ — 完成PDFと件数検証結果
- .github/workflows/build-pdf.yml — 自動生成
