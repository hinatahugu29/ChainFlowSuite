use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};
use std::fs;
use std::path::Path;
use std::cmp::Ordering;
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone)]
struct FileEntry {
    name: String,
    path: String,
    is_dir: bool,
    size: u64,
    mtime: i64,
}

/// ソート条件：0: Name, 1: Ext, 2: Size, 3: Date
#[derive(Copy, Clone)]
enum SortType {
    Name = 0,
    Ext = 1,
    Size = 2,
    Date = 3,
}

#[pyfunction]
fn list_directory_native(
    py: Python<'_>,
    root: String,
    sort_type_val: i32,
    ascending: bool,
    show_hidden: bool,
) -> PyResult<PyObject> {
    let root_path = Path::new(&root);
    let sort_type = match sort_type_val {
        0 => SortType::Name,
        1 => SortType::Ext,
        2 => SortType::Size,
        3 => SortType::Date,
        _ => SortType::Name,
    };

    // --- 爆速ディレクトリ走査 ---
    // PythonのGILを解放して、他のペインの描画なども止めないようにする
    let entries_raw = py.allow_threads(move || {
        let mut entries = Vec::new();
        if let Ok(read_dir) = fs::read_dir(root_path) {
            for entry in read_dir {
                if let Ok(entry) = entry {
                    let file_name = entry.file_name();
                    let name_str = file_name.to_string_lossy();
                    
                    if !show_hidden && name_str.starts_with('.') {
                        continue;
                    }

                    if let Ok(meta) = entry.metadata() {
                        entries.push(FileEntry {
                            name: name_str.to_string(),
                            path: entry.path().to_string_lossy().to_string(),
                            is_dir: meta.is_dir(),
                            size: meta.len(),
                            mtime: meta.modified().map_or(0, |st| {
                                st.duration_since(std::time::UNIX_EPOCH)
                                    .unwrap_or_default()
                                    .as_secs() as i64
                            }),
                        });
                    }
                }
            }
        }
        
        // --- Rust内部での超高速ソート ---
        entries.sort_by(|a, b| {
            // ディレクトリを優先
            if a.is_dir && !b.is_dir { return Ordering::Less; }
            if !a.is_dir && b.is_dir { return Ordering::Greater; }

            let mut ord = match sort_type {
                SortType::Name => {
                    let a_norm = a.name.nfkc().collect::<String>().to_lowercase();
                    let b_norm = b.name.nfkc().collect::<String>().to_lowercase();
                    a_norm.cmp(&b_norm)
                },
                SortType::Ext => {
                    let a_ext = Path::new(&a.name).extension().map_or("", |s| s.to_str().unwrap_or("")).to_lowercase();
                    let b_ext = Path::new(&b.name).extension().map_or("", |s| s.to_str().unwrap_or("")).to_lowercase();
                    a_ext.cmp(&b_ext).then_with(|| a.name.to_lowercase().cmp(&b.name.to_lowercase()))
                },
                SortType::Size => a.size.cmp(&b.size),
                SortType::Date => a.mtime.cmp(&b.mtime),
            };

            if !ascending {
                ord = ord.reverse();
            }
            ord
        });
        entries
    });

    // --- 一括バッチ変換 (国境越えを1回に凝縮) ---
    let py_list = PyList::empty_bound(py);
    for e in entries_raw {
        let tuple = PyTuple::new_bound(py, &[
            e.name.to_object(py),
            e.path.to_object(py),
            e.is_dir.to_object(py),
            e.size.to_object(py),
            e.mtime.to_object(py),
        ]);
        py_list.append(tuple)?;
    }

    Ok(py_list.to_object(py))
}

#[pymodule]
fn chainflow_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(list_directory_native, m)?)?;
    Ok(())
}
