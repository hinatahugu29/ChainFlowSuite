import json
import datetime
import os
import sys

# Force UTF-8 for stdout/stderr just in case
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

log_file = 'agent-work-log.json'
entry = {
    'timestamp': datetime.datetime.now().isoformat(),
    'user_request_summary': 'v19の現状確認と、パフォーマンス問題（タブ切り替え時のラグ）の解決',
    'task_summary': 'QFileSystemModelのシングルトン化によるパフォーマンス最適化',
    'ai_interpretation': '各ペインで個別にファイルシステム監視モデルを生成していたのがボトルネックと特定。グローバルな共有モデルを導入してスレッド数とメモリ消費を抑制した。',
    'status': 'completed',
    'duration_minutes': 15,
    'files_changed': ['core/global_model.py', 'widgets/file_pane/file_pane.py', 'widgets/navigation_pane.py'],
    'executed_actions': ['ファイルシステムモデルのシングルトン実装', 'FilePaneのモデル差し替え', 'NavigationPaneのモデル差し替え', 'リフレッシュロジックの最適化'],
}

try:
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            current = json.load(f)
    else:
        current = []
except Exception as e:
    current = []

current.append(entry)

with open(log_file, 'w', encoding='utf-8') as f:
    json.dump(current, f, indent=2, ensure_ascii=False)
