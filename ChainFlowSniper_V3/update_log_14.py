import json
import os

log_file = "g:/CODE/Antigravity/web-parts/agent-work-log.json"
new_entry = {
  "timestamp": "2026-03-26T00:40:00+09:00",
  "user_request_summary": "案2：バッチ・ハンティング（一括コピペ・モード）の実装指示とUI省略のアイデア。",
  "task_summary": "フェーズ7（バッチ・ハンティング）の設計。Cキーを押している間に情報を蓄積し、離した瞬間に一括コピーするシーケンスの実現。",
  "ai_interpretation": "つまり、ユーザー様は『Cキーを押している間だけ複数の情報を仕留め続け、キーを離した瞬間にそれらを一纏めにして収穫する』という、流れるようなバッチ抽出体験を構築したいということですね。ボタン操作などの余計なUIを省き、キーボードとマウスの連携による直感的な『まとめ作業』の自動化を実現したいと理解しました。",
  "status": "in_progress",
  "duration_minutes": 5,
  "files_changed": [
    "task.md",
    "implementation_plan.md"
  ],
  "executed_actions": [
    "フェーズ7（バッチ・ハンティング）のタスク追加",
    "Cキーの押下・離上をトリガーとした蓄積・一括コピーロジックの設計"
  ],
  "uploaded_images": [],
  "notes": "次はExecutionモードへ移行し、sniper.jsのイベントハンドラを拡張する。",
  "artifacts": [
    "task.md",
    "implementation_plan.md"
  ]
}

if os.path.exists(log_file):
    with open(log_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = []
else:
    data = []

data.append(new_entry)

with open(log_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
