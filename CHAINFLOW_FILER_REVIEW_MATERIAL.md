# ChainFlow Filer v23.4 - System Overview & Review Material

このドキュメントは、**ChainFlow Filer v23.4 [Native Compiled & Transparent Extension Edition]** のアーキテクチャ、設計思想、技術スタック、および進捗状況をまとめたものです。
外部のAIアシスタントにこのアプリケーションのコンテキストを共有し、コードレビューやアーキテクチャ設計のアドバイスを受けるための「プロンプト入力用素材」として作成されています。

---

## 1. アプリケーションの概要 (Executive Summary)

ChainFlow Filer は、Python と Rust を融合させたプロフェッショナル向けの高度なファイルマネージャーです。
単なる「フォルダ閲覧ソフト」ではなく、大量の素材を複数のツール群へ高速かつ正確に「流し込む（Flow）」ための**「ワークフローのハブ（作業用コックピット）」**として設計されています。

### コアコンセプト・独自性
- **Native Speed (v23.1+)**: ディレクトリ走査やソート処理を Rust (PyO3) で実装したネイティブコアへ委譲。
- **Transparent Extension (v23.4)**: OS依存のショートカット（.lnk）の解決を完全に掌握。フォルダショートカットを透過的に実体化し、ディレクトリの物理構造からユーザーの思考を解き放ちます。
- **Flow UI Evolution (v23.3+)**: 「E」キーによる詳細/名称のみ表示の瞬時切り替え（Layout Toggle）を実装。
- **Suite-wide Launcher**: `tools.json` の成熟により、`ChainFlowPad` などの外部ツールを現在のコンテキストを維持したまま `Ctrl+P` (Slash Menu) から呼び出す「ツールチェーンの完成」。
- **Stability Guard**: `shiboken6` を利用した C++ オブジェクトの生存確認により、高速操作時のクラッシュを徹底排除。

---

## 2. 技術スタック (Tech Stack)

- **言語**: Python 3.11+ / Rust (PyO3)
- **GUI フレームワーク**: PySide6 (Qt for Python 6)
- **ネイティブエンジン**: `chainflow_core` (Maturin によりビルドされた Rust モジュール)
- **ビルドツール**: **Nuitka** (PythonエコシステムをCソースレベルへトランスパイルし、圧倒的な起動速度と静的解析への耐性を付与)
- **配布形式**: **Standalone Binary 配布**。かつての Internal フォルダ依存から脱却し、Nuitkaコンパイルによるクリーンで自己完結的なバイナリによる配布を実現。
- **非同期処理**: `QThread` (Rust エンジンとの非同期通信)
- **安定性レイヤー**: `shiboken6` (C++/Python オブジェクト生存チェック)

---

## 3. 主要なモジュール構造 (Module Architecture)

### 階層構造
1. **`main.py`**: エントリーポイント。v23.4 では Nuitka によるコンパイルパスと開発パスをシームレスに調停。
2. **`widgets/main_window.py`**: 画面全体の統括、グローバルショートカット、`ChainFlowPad` などのツール起動ロジック。
3. **`widgets/file_pane/file_pane.py`**: フォルダ表示の最小単位。
4. **`models/proxy_model.py`**: `QFileSystemModel` と連動し、Rustソートエンジンおよびショートカット透過バッジ機能を提供するUIエンジンの心臓部。
5. **`core/actions.py`**: ファイル操作ロジック（コピー、リネーム、ツール起動等）。

---

## 4. 進捗状況と解決済みの課題 (Milestones & Fixes)

### 1. [v23.4] UX 最適化：透過的フォルダショートカットの統合
- **状況**: **完了**。
- **内容**: OSレベルのシンボリック解決（`setResolveSymlinks(False)`）をバイパスし、プロキシ内で.lnkを実体として認識。UI上は専用バッジを付けつつフォルダとして扱わせることで、ファイル構造のエイリアス化を実現。

### 2. [v23.4] 配布標準：Nuitkaコンパイルによる「真のネイティブ配布」
- **状況**: **完了**。
- **内容**: PythonスクリプトやDLL群をInternalフォルダに生置きしていた方式を放棄。NuitkaによってCコンパイルされ、より堅牢でアンチウイルスソフトから誤検知されにくいクリーンなバイナリディストリビューションを確立。

### 3. [v23.3] 思考の道具：ChainFlowPad の統合
- **状況**: **完了**。
- **内容**: 不揮発性のタブ型スクラッチパッドをスイートに追加。`storage.py` による状態保持と、Filer からの `Ctrl+P` 経由でのダイレクトアクセスを確立。

---

## 5. 今後の技術的焦点 (Future Targets)

1. **Rust-Python 間のメモリ安全性・ゼロコピー転送**: 大量のファイルメタデータをPythonからRustへ渡す際のシリアライズオーバーヘッドの完全撤廃。
2. **スイート全体のNuitkaコンパイル標準化**: 他のサブツール群も全て独立バイナリ化し、`Internal` の残余依存ネットワークを完全解体。
3. **描画エンジンの更なる高速化**: 数千ファイル表示時のペイントイベント最適化。

---

## 6. 外面的特徴とユーザー体験 (Visual & Interaction)

### 「Flow UI」のレイアウト構成
- **Fractal Lane Overlay**: 従来の2窓ではなく、情報を右へ右へと流し込むことで「思考の軌跡」を視覚化します。
- **E-Key Layout Toggle**: 密集した多ペイン環境において、必要な時だけ詳細情報を表示し、通常時はファイル名のみで情報密度を最大化する「呼吸する UI」。

---

## 7. AIへのリクエストプロンプト例 (How to use this doc)

> **【プロンプト例】**
> 「上記は、Python + Rust で構築され、Nuitkaによってコンパイル配布される高性能ファイラ（ChainFlow Filer v23.4）の最新設計資料です。
> 1. v23.4 で導入した『.lnkショートカットの透過的実体化』において、モデル（QFileSystemModel）とプロキシの間に潜む潜在的なバグ（キャッシュ周り）をレビューしてください。
> 2. Nuitkaコンパイル環境下での、サブツール呼び出しプロセス (`subprocess.Popen`) におけるリソース管理のベストプラクティスを提案してください。」

---
*Updated for v23.4 Native Compiled & Transparent Extension Edition with Suite-Style focus.*
