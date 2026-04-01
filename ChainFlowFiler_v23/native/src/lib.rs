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

/// インテリジェントな比較ロジック (v23.1 Fix: 二重反転の解消)
/// QSortFilterProxyModelは内部で比較結果を反転させるため、
/// ここでは常に「a < b（昇順）」の基準で返す必要がある。
#[pyfunction]
fn compare_items(
    a: &FileMetadata,
    b: &FileMetadata,
    sort_col: i32,
) -> bool {
    // 1. フォルダ優先ルール: これはソート方向に関わらず「フォルダ < ファイル」とする。
    // aがディレクトリでbがファイルなら、常にaの方が「小さい（＝先に来る）」と判定する。
    if a.is_dir && !b.is_dir {
        return true;
    }
    if !a.is_dir && b.is_dir {
        return false;
    }

    // 2. カラムごとの比較
    let order = match sort_col {
        0 => { // Name (Case-insensitive)
            a.name.to_lowercase().cmp(&b.name.to_lowercase())
        }
        1 => a.size.cmp(&b.size), // Size
        3 => a.modified.cmp(&b.modified), // Date
        _ => Ordering::Equal,
    };

    // 常に「a が b より小さいか」を返す
    order == Ordering::Less
}

#[pymodule]
fn chainflow_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<FileMetadata>()?;
    m.add_function(wrap_pyfunction!(compare_items, m)?)?;
    Ok(())
}
