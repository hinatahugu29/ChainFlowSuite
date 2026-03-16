# ChainFlow Designer 🎨

**ChainFlow Designer** は、思考を形にするための直感的な操作性と、プロフェッショナルな精度を両立させた軽量DTP・レイアウトエディタです。

### ✨ 主な機能 / Key Features
- **Smart Snapping**: オブジェクトの端点、中心、あるいは他のオブジェクトとの幾何学的な整合性を自動検知し、磁石のように吸着。
- **Excel-like Tables**: 表形式のオブジェクトにおいて、各行の高さや列の幅を個別にドラッグでリサイズ可能。構造変更もコンテキストメニューから自在に。
- **Unified Undo Stack**: すべての移動、リサイズ、属性変更（色、不透明度、影）を完全に元に戻すことが可能な、堅牢なアンドゥ・リドゥシステム。
- **Advanced Export**: 用途に合わせたDPI設定での画像出力や、グリッド込のPDF出力。
- **Layer & Swatches**: 階層管理が可能なレイヤーパネルと、色の一貫性を保つスウォッチパネルを搭載。

### 🛠️ 技術情報 / Technical Info
- **Framework**: PySide6 (Qt GraphicsView Framework)
- **Architecture**: `QUndoStack` によるコマンドパターンベースの手順管理.
- **Filing**: XMLベースの独自保存形式により、全てのDTP要素を正確に保持。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + G`: グループ化 / `Ctrl + Shift + G`: 解除
- `Ctrl + L`: ロック / `Ctrl + Shift + L`: 全て解除
- `Ctrl + C / V`: アイテムの複製
- `Ctrl + Z / Y`: 元に戻す / やり直し
- `F11`: フルスクリーン（ZENモード）
