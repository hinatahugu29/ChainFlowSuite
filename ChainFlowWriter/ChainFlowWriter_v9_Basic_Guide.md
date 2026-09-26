# ChainFlow Writer v8 Basic ガイドブック ✍️
## 「心地よい Markdown」から「極致の DTP」まで

---

<div style="display: flex; gap: 20px; align-items: stretch;">
<div style="flex: 1; min-width: 0;">
<m-d>

## 1. 概要 (Overview)
**ChainFlow Writer** は、標準的な Markdown 執筆の心地よさをベースに、必要に応じて高度なレイアウト制御（DTP 志向）までをシームレスに拡張できる次世代エディタです。

「シンプルに書き始め、美しく仕上げる」
メモ書きから、技術資料、そして印影まで必要な正式な事務報告書まで、この一冊（一つのアプリ）で完結します。
</m-d>
</div>

<div style="flex: 1; min-width: 0;">
<m-d>

## 3. v8 の主要な進化点：Split View
ChainFlow Writer v8 では、エディタ画面を上下に分割し、同一ドキュメントの異なる箇所を同時に表示・編集できる **Split View機能** を搭載しました。
- **「見ながら書く」**: 上下で別々の箇所を参照・編集。
- **完全同期**: どちらに入力しても即座にプレビューへ反映。
</m-d>
</div>
</div>

---

## 2. 執筆の 3 Step レベル

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

### 【Step 1】 ベースは Markdown
特別な知識は不要です。標準的な GitHub Flavored Markdown (GFM) で即座に執筆を開始できます。
- **A4 プレビュー**: 編集画面に「印刷境界線」を表示。
- **1:1 PDF Fidelity**: プレビューがそのまま PDF に。
- **パス自動解決**: Windows の絶対パス（`C:\...`）を貼るだけで画像が表示されます。
</m-d>
</div>

<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

### 【Step 2】 ＆ 【Step 3】
**【Step 2】 必要に応じた数式**
- **📐 KaTeX**: 物理・数学などの高度な数式を美しくレンダリング。

**【Step 3】 究極のレイアウト**
- **魔法のタグ `<m-d>`**: HTML の中に Markdown を直接書ける。
- **Stamp Syntax**: ページの絶対座標にロゴや印影を配置。
</m-d>
</div>
</div>

---

## 4. 機能実践ガイド (Showcase Gallery)

ChainFlow Writerは、便利な**専用の拡張機能**をいくつか備えています。
ここでは **「3 Step レベル」** に合わせた具体的な使用例を紹介します。

### 【Step 1 実践】 基本的なテキスト装飾と構造化

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 1. シンプルな装飾
文字の強調や打ち消しは不可欠です。
* **太字 (Bold)** : `**テキスト**`
* *斜体 (Italic)* : `*テキスト*`
* ~~打ち消し線~~ : `~~テキスト~~`
* インラインコード: `コード片段`
</m-d>
</div>

<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 2. 箇条書きとチェックリスト
- 項目A / 項目B
  - 項目B-1 (インデント付き)
1. 手順1 / 2. 手順2

- [x] 完了したタスク
- [ ] 選択状態の保存もサポート
</m-d>
</div>
</div>

<br>

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 3. 引用と補足ブロック
> これは引用ブロックです。
> 複数行にまたがる文章をグループ化し強調します。

::: info
**【情報】** 背景色と罫線で際立たせる「アドモニション」も可能。
:::

::: warning
**【注意】** 危険な操作や禁止事項をアピールします。
:::
</m-d>
</div>

<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 4. 美しいテーブル (Clean)
パイプ (`|`) で表現。「Table Style」を Clean にすると実績表のように。

| 成分名 | 含有量 | 備考 |
| :--- | :---: | ---: |
| エタノール | 50% | 溶剤 |
| 香料 | < 10% | 秘密 |

#### 5. 画像サイズと配置
::: center
<img src="file:///C:/Users/T03000/Desktop/2.jpg" alt="サンプル画像" style="width: 60%;">
:::
</m-d>
</div>
</div>

---

### 【Step 2 実践 & Step 3 実践】 高度な表現とレイアウト

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 6. 数式表現 (KaTeX)
美しい数式のレンダリング。インライン式 `$E=mc^2$` も可能です。
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

#### 7. 配置・文字サイズ制御
::: right
これは **「右寄せ (Right Text)」** ブロックです。署名などに適当。
:::

::: large
**「Large Text」**タイトルページや注意書きに。
:::
</m-d>
</div>

<div style="flex: 1; min-width: 0; background: #fafafa; padding: 15px; border: 1px solid #eaeaea; border-radius: 6px;">
<m-d>

#### 8. 電子印影・スタンプ機能
`::: stamp` ブロックを使用すると、絶対座標に画像を配置できます。標準で「乗算」ブレンドがかかるためリアルです。
::: center
::: stamp right:30mm; margin-top:-10mm; transform:rotate(-10deg); opacity:0.8;
<img src="seal.png" alt="承認印" style="width: 25mm;">
:::
*↑文字に重なる「認め印」*
:::

#### 9. 非表示ブロックと変数
::: no-print
PDF出力時に自動削除される **印刷非表示ブロック** も用意されています。
:::
`{{変数名}}` による定義値の置換も可能です。
</m-d>
</div>
</div>

---

## 5. 究極のキーボード・ワークフロー (ショートカット一覧)

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0;">
<m-d>

| カテゴリ | コマンド / 操作 | キー操作 |
| :--- | :--- | :--- |
| **ファイル** | 保存 / 名前付けて保存 | `Ctrl+S` / `Shift+Ctrl+S` |
| | PDF 出力 | `Ctrl+P` |
| **表示** | **集中モード (Focus)** | `F11` |
| | **上下エディタ間切替** | `Ctrl+Tab` |
</m-d>
</div>

<div style="flex: 1; min-width: 0;">
<m-d>

| カテゴリ | コマンド / 操作 | キー操作 |
| :--- | :--- | :--- |
| **構造/装飾** | 太字 / 斜体 | `Ctrl+B` / `Ctrl+I` |
| | 見出し / リスト | `Ctrl+1〜3` / `Shift+Ctrl+8/9` |
| | 強制改ページ | `Shift+Ctrl+Enter` |
| **拡張機能** | スニペットギャラリー | `Ctrl+Q` |
| | `<m-d>`タグ / スタンプ | `Shift+Ctrl+D/T` |
</m-d>
</div>
</div>

---

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0;">
<m-d>

## 6. プロパティとレイアウト設定
- **用紙/タイポグラフィ**: A4/B5 等のサイズやフォント微調整。
- **枠線設定**: テーブルの枠線有無をワンクリック切替。
- **ページ装飾**: ヘッダー・フッターやページ番号の自動挿入。
</m-d>
</div>

<div style="flex: 1; min-width: 0;">
<m-d>

## 7. インストール・環境設定
Python 3.12 以上が必要です。
```powershell
py -m pip install PySide6 markdown2 pygments python-frontmatter PyYAML
```
```powershell
py main.py
```
</m-d>
</div>
</div>

---

## 8. ディレクトリ構成とポータビリティ
- `app/`: コアロジック (UI, Widget, Utils)
- `snippets_data/`: 登録済みスニペットと設定データ。
  - すべての設定がこのフォルダに集約されているため、フォルダごと持ち運ぶだけでどこでも同じ環境が再現されます。

---
---

## 9. 付録：テクニカル検証と統合テスト (Technical Verification)

# 🚀 ChainFlow Writer v8 統合テスト用ドキュメント
以降は、v8で実装された新機能（パス自動解決など）と既存のレンダリングが正常に動作するかを網羅的に確認するためのテスト用セクションです。必要に応じてプレビュー結果と突き合わせてください。

<div style="display: flex; gap: 20px;">
<div style="flex: 1; min-width: 0; background: #fdfdfd; padding: 15px; border: 1px dashed #ccc;">
<m-d>

### 1. スタンプ & パス自動解決テスト
v8の目玉機能である絶対パス正規化をテストします。
::: stamp width:15mm;
![](C:\Users\T03000\Desktop\rect1.png)
:::
> **[Check 1]** 右上に絶対パス指定画像が表示されていますか？

### 2. 魔法のタグ `<m-d>` テスト
<div style="background: #fdf6e3; padding: 20px; border-radius: 8px;">
<m-d>
- **太字** や *斜体*
- `code line`
</m-d>
</div>
</m-d>
</div>

<div style="flex: 1; min-width: 0; background: #fdfdfd; padding: 15px; border: 1px dashed #ccc;">
<m-d>

### 3. 数式 & コードブロック
$$
e^{i\pi} + 1 = 0
$$

```python
def v8_feature_test():
    path = r"C:\Users\T03000\Desktop\rect1.png"
    return path
```

### 4. テーブルレンダリングテスト
| 機能名 | 状況 | 備考 |
|:---|:---:|:---|
| Path解決 | ✅ | v8 新規 |
| Stamp | ✅ | CSS改善済み |
</m-d>
</div>
</div>

<div style="page-break-before: always;"></div>
※ここで改ページが行われれば正常です。

---
*ChainFlow Writer v8 - 執筆を、もっと美しく、もっと自由に。*
