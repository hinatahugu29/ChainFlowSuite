use pyo3::prelude::*;
use std::cmp::Ordering;

#[pyclass]
#[derive(Clone)]
pub struct FileMetadata {
    #[pyo3(get, set)]
    pub name: String,
    #[pyo3(get, set)]
    pub is_dir: bool,
    #[pyo3(get, set)]
    pub size: i64,
    #[pyo3(get, set)]
    pub modified: i64,
}

#[pymethods]
impl FileMetadata {
    #[new]
    fn new(name: String, is_dir: bool, size: i64, modified: i64) -> Self {
        FileMetadata { name, is_dir, size, modified }
    }
}

/// フォルダ優先＋列比較の共通ロジック。常に「a < b（昇順）」の基準でOrderingを返す。
fn compare_ordering(a: &FileMetadata, b: &FileMetadata, sort_col: i32) -> Ordering {
    // 1. フォルダ優先ルール: これはソート方向に関わらず「フォルダ < ファイル」とする。
    if a.is_dir && !b.is_dir {
        return Ordering::Less;
    }
    if !a.is_dir && b.is_dir {
        return Ordering::Greater;
    }

    // 2. カラムごとの比較
    match sort_col {
        0 => { // Name (Case-insensitive)
            a.name.to_lowercase().cmp(&b.name.to_lowercase())
        }
        1 => a.size.cmp(&b.size), // Size
        2 => { // Type (Extension)
            let ext_a = std::path::Path::new(&a.name)
                .extension()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_lowercase();
            let ext_b = std::path::Path::new(&b.name)
                .extension()
                .and_then(|s| s.to_str())
                .unwrap_or("")
                .to_lowercase();
            ext_a.cmp(&ext_b)
        }
        3 => a.modified.cmp(&b.modified), // Date
        _ => Ordering::Equal,
    }
}

/// インテリジェントな比較ロジック (v23.1 Fix: 二重反転の解消)
/// QSortFilterProxyModelは内部で比較結果を反転させるため、
/// ここでは常に「a < b（昇順）」の基準で返す必要がある。
#[pyfunction]
fn compare_items(
    a: &FileMetadata,
    b: &FileMetadata,
    sort_col: i32,
) -> bool {
    compare_ordering(a, b, sort_col) == Ordering::Less
}

/// v23.5: 一括ソートによる高速化。
/// フォルダを開いた際に一度だけ呼び出し、全アイテムを昇順ソートした後の
/// インデックス列を返す。Python側はこれを元に path -> rank の辞書を作り、
/// lessThan() 内での逐次比較（Python/Rust境界越え）をO(1)の辞書引きに置き換える。
/// v23.6: キー事前計算方式。比較のたびに to_lowercase / 拡張子抽出で String を
/// 生成していた（O(n log n)回のアロケーション）のを、アイテムごとに1回だけ
/// キーを構築してからソートする（O(n)回）。順序は compare_ordering と同一。
#[pyfunction]
fn compute_rank_order(items: Vec<FileMetadata>, sort_col: i32) -> Vec<usize> {
    let mut indices: Vec<usize> = (0..items.len()).collect();
    // フォルダ優先: !is_dir を第1キーにする（false=フォルダ が先頭に来る）
    match sort_col {
        0 => {
            let keys: Vec<(bool, String)> = items
                .iter()
                .map(|it| (!it.is_dir, it.name.to_lowercase()))
                .collect();
            indices.sort_by(|&a, &b| keys[a].cmp(&keys[b]));
        }
        1 => {
            let keys: Vec<(bool, i64)> =
                items.iter().map(|it| (!it.is_dir, it.size)).collect();
            indices.sort_by(|&a, &b| keys[a].cmp(&keys[b]));
        }
        2 => {
            let keys: Vec<(bool, String)> = items
                .iter()
                .map(|it| {
                    let ext = std::path::Path::new(&it.name)
                        .extension()
                        .and_then(|s| s.to_str())
                        .unwrap_or("")
                        .to_lowercase();
                    (!it.is_dir, ext)
                })
                .collect();
            indices.sort_by(|&a, &b| keys[a].cmp(&keys[b]));
        }
        3 => {
            let keys: Vec<(bool, i64)> =
                items.iter().map(|it| (!it.is_dir, it.modified)).collect();
            indices.sort_by(|&a, &b| keys[a].cmp(&keys[b]));
        }
        _ => {
            indices.sort_by(|&a, &b| compare_ordering(&items[a], &items[b], sort_col));
        }
    }
    indices
}

#[pymodule]
fn chainflow_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FileMetadata>()?;
    m.add_function(wrap_pyfunction!(compare_items, m)?)?;
    m.add_function(wrap_pyfunction!(compute_rank_order, m)?)?;
    Ok(())
}
