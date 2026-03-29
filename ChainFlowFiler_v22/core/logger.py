"""
core/logger.py
v14.1 Refactoring: 一元化されたロギングシステム

print文を置き換え、一貫したエラーハンドリングとデバッグ出力を提供する。
"""
import logging
import os
import sys
from datetime import datetime
from functools import wraps
from typing import Callable, Any


# ============================================================
# ロガー設定
# ============================================================

def setup_logger(name: str = "ChainFlowFiler", level: int = logging.DEBUG) -> logging.Logger:
    """アプリケーション用ロガーをセットアップ
    
    Args:
        name: ロガー名
        level: ログレベル
        
    Returns:
        設定されたLogger
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        # 既に設定済み
        return logger
    
    logger.setLevel(level)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # フォーマット
    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(name)s.%(funcName)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


# グローバルロガーインスタンス
_logger = None


def get_logger() -> logging.Logger:
    """グローバルロガーを取得"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


# ============================================================
# ログ関数（print置き換え用）
# ============================================================

def log_debug(message: str, *args) -> None:
    """デバッグメッセージ"""
    get_logger().debug(message, *args)


def log_info(message: str, *args) -> None:
    """情報メッセージ"""
    get_logger().info(message, *args)


def log_warning(message: str, *args) -> None:
    """警告メッセージ"""
    get_logger().warning(message, *args)


def log_error(message: str, *args, exc_info: bool = False) -> None:
    """エラーメッセージ"""
    get_logger().error(message, *args, exc_info=exc_info)


# ============================================================
# エラーハンドリングデコレーター
# ============================================================

def safe_execute(default_return: Any = None, log_errors: bool = True):
    """例外を安全にキャッチするデコレーター
    
    Args:
        default_return: 例外発生時の戻り値
        log_errors: エラーをログに記録するか
        
    Example:
        @safe_execute(default_return=False)
        def risky_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    log_error(f"Exception in {func.__name__}: {e}", exc_info=True)
                return default_return
        return wrapper
    return decorator


def handle_file_operation(func: Callable) -> Callable:
    """ファイル操作用の特化したエラーハンドラー
    
    OSError, PermissionError, FileNotFoundError などを適切に処理
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            log_warning(f"File not found: {e}")
            return None
        except PermissionError as e:
            log_error(f"Permission denied: {e}")
            return None
        except OSError as e:
            log_error(f"OS error: {e}")
            return None
        except Exception as e:
            log_error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return None
    return wrapper


# ============================================================
# ユーザー通知用ヘルパー
# ============================================================

class UserNotification:
    """ユーザーへのフィードバック通知を管理"""
    
    @staticmethod
    def show_error(parent, title: str, message: str) -> None:
        """エラーダイアログを表示"""
        from PySide6.QtWidgets import QMessageBox
        log_error(f"User Error Dialog: {title} - {message}")
        QMessageBox.critical(parent, title, message)
    
    @staticmethod
    def show_warning(parent, title: str, message: str) -> None:
        """警告ダイアログを表示"""
        from PySide6.QtWidgets import QMessageBox
        log_warning(f"User Warning Dialog: {title} - {message}")
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def show_info(parent, title: str, message: str) -> None:
        """情報ダイアログを表示"""
        from PySide6.QtWidgets import QMessageBox
        log_info(f"User Info Dialog: {title} - {message}")
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        """確認ダイアログを表示"""
        from PySide6.QtWidgets import QMessageBox
        log_debug(f"User Confirm Dialog: {title} - {message}")
        result = QMessageBox.question(parent, title, message)
        return result == QMessageBox.Yes


# 便利なエイリアス
notify = UserNotification
