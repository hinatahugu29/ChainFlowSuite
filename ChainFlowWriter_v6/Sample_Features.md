---
margin_top: 25
margin_right: 25
margin_bottom: 25
margin_left: 25
font_family: Sans-serif (Gothic)
base_size: 10
line_height: 1.6
heading_underline: true
table_style: Clean (No borders/bg)
page_size: A4
orientation: Portrait
document_id: "CFW-2026-001"
author_name: "担当者 A"
---

::: center
::: large
**ChainFlowWriter v6**
機能ショーケース・マニュアル
:::
:::

ChainFlowWriterは、標準的なMarkdown記法に加え、報告書やマニュアル作成に便利な**専用の拡張機能**をいくつか備えています。このファイルは、それらの機能を一覧できるサンプルです。

## 1. 基本的なテキスト装飾
レポート作成において、文字の強調や打ち消しは不可欠です。

* **太字（Bold）** : `**テキスト**` と書くと **強調** されます。
* *斜体（Italic）* : `*テキスト*` と書きます。
* ~~打ち消し線~~ : `~~テキスト~~` と書くと取り消し線が引かれます。
* インラインコード : 文章中に `コード片段` を埋め込めます。

## 2. 箇条書きとチェックリスト

情報を整理する際は、リスト記法が活用できます。

### 箇条書き
- 項目A
- 項目B
  - 項目B-1 (インデント付き)
  - 項目B-2

### 番号付きリスト
1. 手順1
2. 手順2
3. 手順3

### チェックリスト (Tasklists)
- [x] 完了したタスク
- [ ] 未完了のタスク
- [ ] 選択状態の保存もサポートしています

## 3. 引用とブロック
他の資料からの引用や、補足説明エリアとして使えます。

> これは引用ブロックです。
> 複数行にまたがる文章をグループ化し、左側にラインを引いて強調します。
> 背景色はつかず、シンプルな装飾となっています。


## 4. 表（テーブル）の表現と配置
複雑なデータも、パイプ（`|`）を使って簡単に表組み可能です。
「Table Style」プロパティを **Clean** に設定すると、以下のような美しい成績表のような見た目になります。

| 成分名 | CAS番号 | 含有量 | 備考 |
| :--- | :---: | :---: | ---: |
| エタノール | 64-17-5 | 50% | 第一種有機溶剤 |
| 水 | 7732-18-5 | 40% | |
| 香料 | - | < 10% | 企業秘密 |

※ ヘッダーの区切り文字 (`:---` など) を使うことで、列ごとに **「左揃え」「中央揃え」「右揃え」** を自由に制御できます。


## 5. 配置のコントロール（専用拡張）
ツールバーのボタンから挿入できる独自の配置タグを使えば、文字や画像のレイアウトを自在に操れます。

::: right
これは **「右寄せ (Right Text)」** ブロックの中のテキストです。
署名などをページ右下に配置したい時に適しています。
:::

::: center
これは **「中央揃え (Center Text)」** ブロックの中のテキストです。
:::


## 6. 大きな文字・小さな文字（専用拡張）
見出し（#）とは別に、単なる文字サイズの大小を表現したい場合に重宝します。

::: large
**「Large Text」ボタン**で挿入されるブロックです。
タイトルページや、特に強調したい注意書きなどに最適です。
:::

::: small
**「Small Text」ボタン**で挿入されるブロックです。
ページ下部の脚注や、特記事項の補足など、目立たせたくない長文に向いています。
:::


## 7. 画像のサイズ指定機能
画像をドラッグ＆ドロップすると生成されるHTMLタグの `style` 属性を直接編集することで、画像のサイズをパーセントやピクセルで自由に指定できます。もちろんA4サイズからはみ出すことはありません。

::: center
<img src="file:///C:/Users/T03000/Desktop/2.jpg" alt="サンプル画像" style="width: 60%;">

*↑中央揃え（::: center）と幅60%（style="width: 60%;"）の組み合わせ例*
:::


## 8. 高度なHTMLスニペットの挿入
エディタ上部の **「HTML ▾」** メニューから、Markdownでは表現が難しい便利なHTML構造をワンクリックで挿入できます。

### 2段組みレイアウト (Flex Multi-Col)
左右で情報を比較したり、写真を並べたいときに非常に便利です。

<div style="display: flex; gap: 20px;">
  <div style="flex: 1; min-width: 0;">
    **【左カラム】** <br>
    ここは左側のコンテンツです。Flexboxを使ってレイアウトされているため、ウィンドウや用紙の幅に応じて自動で均等に割り付けられます。
  </div>
  <div style="flex: 1; min-width: 0;">
    **【右カラム】** <br>
    ここは右側のコンテンツです。例えば片方に画像、もう片方にその説明文を配置するといった高度なページ構成が可能になります。
  </div>
</div>
<div style="clear: both;"></div>

### 一部だけ文字色を変える (Red Span)
Markdownには文字色を変える記法がありませんが、HTMLを使えば <span style="color: #d32f2f; font-weight: bold;">このように赤文字</span> などを文中に混ぜることも簡単にできます。

### PDF出力時の強制改頁 (Page Break)
「ここからは絶対に次のページから始めたい」という箇所に `ページ区切り` を挿入します。


## 9. 構造化された補足情報（アドモニション）
単なる引用（>）とは別に、背景色と罫線で「情報」や「警告」を際立たせる専用ブロックです。これらもツールバーからワンクリックで挿入できます。

::: info
**【情報】** これは補足説明用のブロックです。背景に淡い青色を敷くことで、本文との差別化を図ります。重要な前提条件や参考リンクなどを書くのに適しています。
:::

::: warning
**【注意】** ここに入力した内容は、読み手に注意を促すための重要なメッセージとして処理されます。手順における危険な操作や、絶対に守ってほしい禁止事項を強調するために用意されています。
:::


## 10. 変数埋め込み機能（v2新機能）
文書冒頭のフロントマター（`---` で囲まれた部分）で定義した値を、本文中で `{{変数名}}` として参照できます。

- 文書番号: **{{document_id}}**
- 作成担当: **{{author_name}}**

※ 同じ値を複数の箇所で使いたい場合や、日付や名称を一括で変更したい場合に非常に強力です。


## 11. 電子印影・スタンプ機能（v2新機能）
`::: stamp` ブロックを使用すると、現在の文字位置を起点にしつつ、ページの任意の位置（絶対座標）に画像を配置できます。

::: center
::: stamp right:30mm; margin-top:-20mm; transform:rotate(-10deg); opacity:0.8;
<img src="file:///C:/Users/T03000/Desktop/seal.png" alt="承認印" style="width: 25mm;">
:::
*↑このように、文字の上に重なる「認め印」や「社外秘スタンプ」を表現できます。*
:::

※ 標準で「乗算(multiply)」ブレンドがかかるため、下の文字や罫線を透過させ、紙に押したようなリアルな質感を再現します。


## 12. マクロとチートシート
執筆効率を最大化するためのツール群です。

- **マクロメニュー**: 「今日の日付」を自由な形式（YYYY/MM/DD, 2026年3月13日, 13 March 2026 など）で一発挿入できます。
- **チートシート (`Ctrl+H`)**: よく使うHTML構造や定型文をギャラリー形式でプレビューしながら挿入できます。自分専用のスニペット登録も可能です。


## 13. 数式表現（LaTeX/MathJax）
技術文書や研究報告書に欠かせない数式を美しくレンダリングします。

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

また、文章の中に `$E = mc^2$` のように書くことで、インライン数式も表現可能です。


## 14. 図解とフローチャート（Mermaid.js）
テキストだけで複雑な図が描けます。

```mermaid
graph TD
    A[システムの起動] --> B{設定ファイルの確認}
    B -- 正常 --> C[メイン画面表示]
    B -- 異常 --> D[エラー表示]
    D --> E[終了]
    C --> F[ユーザー操作待機]
```


## 15. プログラミングコードの挿入
等幅フォントと背景色を用いて、ソースコードを綺麗に表示します。

```python
def hello_world():
    # ChainFlowWriterはコードブロックを自動で整形します
    print("Hello, ChainFlowWriter v2!")
```


## 16. 脚注（Footnotes）
文章の途中で詳細な注釈を入れたい場合、文末にまとめて表示する注釈機能が使えます[^1]。

[^1]: このように、設定項目の詳細や用語の定義などは脚注として分離することで、本筋の文章が非常に読みやすくなります。


## 17. 印刷制御（Advanced Print Control）
PDF出力（印刷）を見据えた、マニュアル作成者垂涎の機能です。

::: no-print
**【印刷非表示ブロック】**
この「no-print」ブロック内の内容は、**エディタ上では見えますが、PDF出力時には自動的に完全に削除されます。**
執筆者向けのメモエリアとして最適です。
:::


## 18. インタラクティブ・スニペット（クリックでコピー）
プレビュー画面上で「クリックするだけで定型文をクリップボードにコピー」できる工夫です。マニュアルや、チームで共有するテンプレート集の中に組み込むと、転記ミスをゼロにできます。

<div style="background: #f9f9f9; border-radius: 8px; padding: 15px; border: 1px solid #eee; margin: 10px 0;">
  <p style="margin-top: 0; font-weight: bold; color: #555; font-size: 0.9em;">👇 以下のボタンをクリックして試してみてください</p>
  
  <span id='copy-btn-1' style='display: inline-block; padding: 6px 14px; background: #ffffff; border: 1px solid #0078d4; border-radius: 6px; color: #0078d4; cursor: pointer; user-select: none; font-weight: bold; font-size: 0.95em; transition: all 0.2s;' 
        onmouseover='this.style.background="#f0f7ff"' 
        onmouseout='this.style.background="#ffffff"'
        onclick="const text = '---\ntitle: 週次報告書\ndate: {{today}}\nauthor: {{author_name}}\n---\n\n## 1. 今週の成果\n- \n'; navigator.clipboard.writeText(text).then(() => { const oldBody = this.innerHTML; this.innerHTML = '✅ コピーしました！'; this.style.color = '#28a745'; this.style.borderColor = '#28a745'; setTimeout(() => { this.innerHTML = oldBody; this.style.color = '#0078d4'; this.style.borderColor = '#0078d4'; }, 2000); })">
    📋 報告書ヘッダーをコピー
  </span>

  <span id='copy-btn-2' style='display: inline-block; margin-left: 10px; padding: 6px 14px; background: #ffffff; border: 1px solid #0078d4; border-radius: 6px; color: #0078d4; cursor: pointer; user-select: none; font-weight: bold; font-size: 0.95em; transition: all 0.2s;' 
        onmouseover='this.style.background="#f0f7ff"' 
        onmouseout='this.style.background="#ffffff"'
        onclick="const text = '::: info\n**【本日のお知らせ】**\n\n:::'; navigator.clipboard.writeText(text).then(() => { const oldBody = this.innerHTML; this.innerHTML = '✅ コピー完了'; this.style.color = '#28a745'; this.style.borderColor = '#28a745'; setTimeout(() => { this.innerHTML = oldBody; this.style.color = '#0078d4'; this.style.borderColor = '#0078d4'; }, 2000); })">
    📋 Infoブロックをコピー
  </span>
</div>

## 19. 最新の図解機能 (Mermaid v11 新機能: XY Chart)
Writer v6 では最新の Mermaid v11 を搭載。これまで難しかった XY グラフなどもテキストだけで記述可能です。

```mermaid
xychart-beta
    title "販売実績推移 (2025)"
    x-axis [jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec]
    y-axis "売上 (万円)" 0 --> 100
    bar [50, 60, 45, 82, 75, 58, 89, 94, 78, 42, 66, 95]
    line [50, 60, 45, 82, 75, 58, 89, 94, 78, 42, 66, 95]
```

---

*※ ChainFlowWriter v6 では、最新のライブラリ（Mermaid v11 / KaTeX v0.16）を搭載し、より表現の幅が広がりました。*
