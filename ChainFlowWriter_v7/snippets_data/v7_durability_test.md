---
project_name: "ChainFlowWriter v7 Durability Test"
author: "Antigravity Debugger"
code_bg: "#1e1e1e"
---

# 🛡️ v7 耐久・ストレステストドキュメント

このファイルは、ChainFlowWriter v7 の PDF レンダリングエンジン、自動改ページ、マージン一貫性、およびスタンプ配置の堅牢性を検証するためのものです。

## 1. 大容量テキストによる自動改ページ
以下のセクションは大量のテキストを含み、自然な自動改ページを誘発します。マージンが全ページで一定であることを確認してください。

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 

(同じ内容を複数回複製して長文化...)

::: stamp right:10mm; margin-top:-10mm;
![](rect1.png)
:::

---

## 2. 複雑な要素のページ境界テスト

### 意地悪な配置のテーブル
このテーブルはページの下端ギリギリから始まり、次のページへ跨ぎます。

| No | Status | Description | Note |
| :--- | :--- | :--- | :--- |
| 01 | OK | データ行 1 | 正常 |
| 02 | OK | データ行 2 | 正常 |
| 03 | OK | データ行 3 | 正常 |
| 04 | OK | データ行 4 | 正常 |
| 05 | OK | データ行 5 | 正常 |
| 06 | OK | **このあたりで改ページが発生するはずです** | 要確認 |
| 07 | OK | データ行 7 | 次ページ |
| 08 | OK | データ行 8 | 次ページ |

<div style="page-break-before: always;"></div>

## 3. 手動改ページ直後のスタンプテスト
2ページ目の冒頭にスタンプを配置し、マージン設定の影響を受けずに正しい位置（右端10mm）に出力されるか確認します。

::: stamp right:10mm; margin-top:-10mm;
![](rect1.png)
:::

### [CHECK] スタンプの垂直位置
この見出しのすぐ右側にスタンプが重なっていれば成功です（垂直補正を外した効果の確認）。

---

## 4. 極限のネスト構造
HTMLコンテナとMarkdownのネストをテストします。

<div style="border: 2px solid #333; padding: 10mm; background: #fafafa;">
<m-d>
### ネストされた領域
::: info
**INFO**: コンテナの中にコンテナを入れています。
:::
- リスト 1
    - リスト 2
        - リスト 3
</m-d>
</div>

---

## 5. 大量のスタンプ同時配置 (連打テスト)
同一ページ内に複数のスタンプを配置し、描画負荷や重なりの挙動を確認します。

::: stamp right:10mm; margin-top: 10mm; width: 15mm;
![](rect1.png)
:::

::: stamp right:30mm; margin-top: 10mm; width: 15mm; transform: rotate(-5deg);
![](rect1.png)
:::

::: stamp right:50mm; margin-top: 10mm; width: 15mm; opacity: 0.5;
![](rect1.png)
:::

---

## 6. 数式とコードの混在
$$
\int_{a}^{b} f(x)dx = F(b) - F(a)
$$

```python
# v7 Durability Check
for i in range(100):
    print(f"Checking line {i} rendering...")
```

---

## 7. 最終ページへの到達
このページが 3 ページ目以降になり、マージンが 1 ページ目と同様に保たれていることを確認してテストを終了します。
