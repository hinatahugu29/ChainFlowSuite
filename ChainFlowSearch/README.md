# ChainFlow Search

[Japanese] | [English]

## 🌟 Overview / 概要

**ChainFlow Search** is a lightning-fast, asynchronous file search engine built with PySide6. It is designed to find files instantly across large directories and network drives without freezing the UI.

**ChainFlow Search** は、PySide6 で構築された爆速の非同期ファイル検索エンジンです。UI をフリーズさせることなく、大容量のディレクトリやネットワークドライブから目的のファイルを瞬時に見つけ出すために設計されています。

---

## ✨ Key Features / 特徴

*   **Asynchronous Scan**: Real-time results update as it scans. Uses `os.scandir` for maximum performance.
*   **Smart Refinement**: Instantly filter existing results with additional keywords (AND search) without re-scanning.
*   **Filer Integration**: Copy found files directly to clipboard to paste into ChainFlow Filer or Explorer.
*   **Visual Feedback**: Real-time progress bar and scan count.
*   **非同期スキャン**: スキャン中もリアルタイムに結果を更新。`os.scandir` による最高速度の検索。
*   **スマート絞り込み**: 再スキャンなしで、既存の結果をキーワード（AND条件）で瞬時にフィルタリング。
*   **ファイラー連携**: 見つかったファイルをクリップボードにコピーし、そのままファイラーやエクスプローラーへ。
*   **視覚的フィードバック**: リアルタイムのプログレスバーと処理件数表示。

---

## 🚀 How to Run / 実行方法

```bash
python main.py
```
*(Requires PySide6)*

---

Developed by **hinatahugu29**.
Project log managed by **Antigravity AI**.
