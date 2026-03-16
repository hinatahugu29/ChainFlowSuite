import json
import os
import io

file_path = r"E:\CODE\Antigravity\Py_FILE\agent-work-log.json"
try:
    with io.open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = []

new_entry = {
  "timestamp": "2026-03-02T15:18:00+09:00",
  "user_request_summary": "PDFエクスポート非同期化の修正案（QThread化）の承認",
  "ai_interpretation": "提案した修正計画に基づき、メインスレッドをブロックしていたPDF発行処理をQThreadを利用したバックグラウンド処理へと移行することで、フリーズ問題を解決する。",
  "status": "completed",
  "duration_minutes": 5,
  "files_changed": [
    "app/ui/right_pane.py"
  ],
  "executed_actions": [
    "RightPane クラス外部に QThread を継承した ExportWorker クラスを定義",
    "PDF保存処理を ExportWorker 内へ移動し、pyqtSignal を用いて進捗(progress)と完了(finished)をメインスレッドへ通知",
    "RightPane.process_all_jobs の同期処理を削除し、ExportWorker の start() を呼び出す非同期設計へリファクタリング"
  ],
  "uploaded_images": [],
  "notes": "この変更により、数十ページ以上の重いPDF発行操作を行ってもUIがフリーズせず、ログもリアルタイムに更新されるようになった。",
  "artifacts": [
    "walkthrough.md"
  ]
}

data.append(new_entry)

with io.open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Log successfully updated")
