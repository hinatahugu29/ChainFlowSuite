use std::path::Path;
use glob::Pattern;

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum CompressionMethod {
    Deflate,
    Zstd,
}

#[derive(Clone, Debug)]
pub struct ZipConfig {
    pub compress_level: u32, // 0..9
    pub compression_method: CompressionMethod,
    pub exclude_patterns: Vec<String>,
}

impl Default for ZipConfig {
    fn default() -> Self {
        Self {
            compress_level: 5, // 速度と圧縮率のバランス
            compression_method: CompressionMethod::Deflate,
            exclude_patterns: vec![
                "**/.git/**".to_string(),
                "**/__pycache__/**".to_string(),
                "**/*.tmp".to_string(),
                "**/*.blend1".to_string(),
                "**/.DS_Store".to_string(),
                "**/.idea/**".to_string(),
                "**/.vscode/**".to_string(),
                "**/node_modules/**".to_string(),
                "**/.venv/**".to_string(),
            ],
        }
    }
}

pub struct ExcludeChecker {
    patterns: Vec<Pattern>,
}

impl ExcludeChecker {
    pub fn is_excluded(&self, path: &Path) -> bool {
        let path_str = path.to_string_lossy().replace('\\', "/");
        for pattern in &self.patterns {
            if pattern.matches(&path_str) {
                return true;
            }
            // パス名単体でマッチさせるためのフォールバック (例: ファイル名のみにマッチするパターン用)
            if let Some(file_name) = path.file_name() {
                let name_str = file_name.to_string_lossy();
                if pattern.matches(&name_str) {
                    return true;
                }
            }
        }
        false
    }
}

impl ZipConfig {
    pub fn create_exclude_checker(&self) -> ExcludeChecker {
        let mut patterns = Vec::new();
        for pat in &self.exclude_patterns {
            if let Ok(p) = Pattern::new(pat) {
                patterns.push(p);
            } else {
                // アスタリスクなどが足りない場合にマッチしやすくするための簡易フォーマット
                let normalized = if !pat.contains('*') && !pat.contains('/') {
                    format!("**/{}/**", pat)
                } else {
                    pat.clone()
                };
                if let Ok(p) = Pattern::new(&normalized) {
                    patterns.push(p);
                }
            }
        }
        ExcludeChecker { patterns }
    }
}
