---
project_name: "ChainFlowWriter v7 Simple Check"
author: "Antigravity"
---

# ✅ v7 簡易レイアウト確認用ファイル

このファイルは、新機能「フル・フィディリティ方式」が正しく動作しているかを、パッと見て判断するためのものです。

::: stamp right:5mm; margin-top:5mm; width:30mm;
![](rect1.png)
:::

## 1. ページ1 の確認ポイント
- **上端の余白**: この見出しの上が 25mm 程度空いていますか？
- **右端のスタンプ**: 上の角にある赤いスタンプが、**「紙の端（余白領域）」に食い込んでいても欠けていなければ成功**です。
- **左右の余白**: 左右も 25mm ずつ均等に空いていますか？

---

## 2. 数式と図形（基本）
数式や図が、ページの横幅に収まり、崩れていないか確認します。

**数式:**
$$ a^2 + b^2 = c^2 $$

**図表:**
```mermaid
graph LR
    A[入力] --> B[処理];
    B --> C[PDF出力];
```

<div style="page-break-before: always;"></div>

## 3. ページ2 の確認ポイント
手動改ページ（`---` または `div`）を入れた後のページです。

::: stamp right:5mm; margin-top:5mm;
![](rect1.png)
:::

### [CHECK] 1ページ目と同じ位置ですか？
- **開始位置**: この見出しの高さが、**「1ページ目の最初の見出し」と全く同じ高さ**から始まっていれば、全ページのマージン同期が成功しています。
- **スタンプ**: 同様に、右上のスタンプが欠けずに配置されていますか？

---

## 4. コンテナ内の表示
::: info
**INFOブロック**: この青い枠線が、左右の余白（25mm）の内側に正しく収まっているか確認してください。
:::

---

## 5. 最終チェック
一番下の余白も 25mm 確保されていれば、すべてのテストは合格です。

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 

**[テスト終了]**
