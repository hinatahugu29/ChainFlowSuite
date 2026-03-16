# ChainFlow PDF Studio 📄🔬

**ChainFlow PDF Studio** は、PDFを単に閲覧するだけでなく、内部構造やレイアウトを深く解剖するための専門的な解析ツールです。

### ✨ 主な機能 / Key Features
- **Synchronized 3-Pane Layout**:
    - **Left**: サムネイル・アウトライン・検証用レイヤー。
    - **Center**: 高解像度レンダリングエンジンによるメインプレビュー。
    - **Right**: メタデータ詳細、ページ属性、および注釈管理プロパティ。
- **Used Pages Analysis**: 文書内で実際に使用されているリソースやフォントの使用状況を、サムネイル上にオーバーレイ表示。
- **Metadata Inspector**: タイトル、作成者、暗号化設定、そしてPDF/Aなどの規格適合性を瞬時に確認。
- **Native Rendering**: 高速かつ忠実なベクトルレンダリングにより、複雑な図面や文字組も正確に再現。

### 🛠️ 技術情報 / Technical Info
- **Core Engine**: PyMuPDF + Qt (via PySide6)
- **UI Logic**: 各ペインが状態を相互に同期する、リアクティブなUI設計。
- **Theme**: 長時間の解析作業でも目が疲れにくい、プロ仕様のダーク配色。

### ⌨️ 操作方法 / Shortcuts
- `Ctrl + O`: PDFを開く
- `Ctrl + L`: サイドバーの表示切り替え
- `Home / End`: 文頭 / 文末へ
- `Ctrl + F`: 文書内検索
