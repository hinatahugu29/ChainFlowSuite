# ChainFlow Sniper V3 [Research Shell] 🔍🎯

**ChainFlow Sniper** は、Web 情報の「構造」と「見た目」を瞬時に射抜く、プロフェッショナル向けリサーチ・ステーションです。
複雑な Web ページから必要なデータだけを正確に抜き出し、価値ある資産へと変換するためのツールとして再定義されました。

---

## 🚀 究極の抽出アーキテクチャ / 4-Quadrant Extraction

### 🎯 4象限・スナイプモード (A/Z/S/D)
必要なデータの種類に合わせて、最適なモードで情報を射抜きます。
- **【A】Text Sniper (Direct Text)**: 青枠。マウスホバーした単一要素のテキストを正確に狙撃。
- **【Z】Structure Sniper (Markdown)**: 紫枠。表(Table)やリスト(UL/OL)を、Markdown 形式の構造化データとして一括抽出。
- **【S】Style Restorer (CSS/Layout)**: CSS Grid や Filter までをポータブルに再構築。Web の表現力をドキュメントへ持ち込みます。
- **【D】Pure DOM Sniper (AI Optimized)**: 装飾を排除した「純粋な構造」のみを抽出。AI 連携や Writer テーマへの統合に最適化。

### 🏹 深層貫通探索 (Deep Penetration)
iFrame / Shadow DOM、あるいは透明なオーバーレイに隠されたデータであっても、透過して射抜くことが可能です。業務システム等の複雑な DOM 構造に屈しません。

### 🔍 抽出範囲のインテリジェント調整
ホールドキー（A/Z/S/D）を押しながらマウスホイールを回転させることで、抽出対象の範囲を「親要素へ広げる」「子要素へ狭める」ことが可能です。

---

## 🎨 プロフェッショナルなリサーチ機能 / Advanced Features

- **Massive Storage (Extractions Pane)**: 抽出したデータは右ペインに蓄積。クリックで全文コピー、ダブルクリックで展開/省略が可能です。
- **Detach View**: 抽出リストを最前面の独立ウィンドウとして切り離し可能。Excel や他のアプリケーションへの転記作業に最適です。
- **Smart Scoring**: クリックした箇所の ID パターンや属性から、ラベルではなく「実データ」を優先的に判別して抽出するアルゴリズムを搭載。
- **Secure Profiles**: 永続的なログイン状態を維持。社内システム等での煩雑な再ログインを不要にします。

---

## ⌨️ 操作方法 / Sniper Operations
- **`A` / `Z` / `S` / `D` (Hold) + Click**: 各モードでの抽出を実行。
- **Hold Key + Mouse Wheel**: 抽出範囲（バウンディングボックス）の拡大縮小。
- **`Ctrl + P` (Slash Menu)**: Suite アプリの呼び出し。
- **`Detach` Button**: 抽出リストを独立ウィンドウ化。

---

## 🛠️ 技術スタック / Tech Stack
- **Framework**: PySide6 (Qt for Python 6)
- **Engine**: QtWebEngine (Chromium)
- **Language**: Python 3.12+
- **Persistence**: 独自セッション・プロファイル管理

---

## 📄 ライセンス / License
© 2026 hinatahugu29. All rights reserved.
**Snipe the Truth, Structure the Flow.** — 情報を射抜き、資産へと変える。
