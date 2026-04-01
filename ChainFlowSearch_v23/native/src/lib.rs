use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};
use ignore::WalkBuilder;
use regex::Regex;
use std::sync::mpsc;
use std::thread;
use unicode_normalization::UnicodeNormalization;

#[derive(Debug, Clone)]
struct SearchResult {
    name: String,
    path: String,
    size: u64,
    mtime: i64,
}

struct QueryGroup {
    positives: Vec<String>,
    negatives: Vec<String>,
    regexes: Vec<Regex>,
}

struct Matcher {
    groups: Vec<QueryGroup>,
}

impl Matcher {
    fn new(query: &str) -> Self {
        let normalized_query = query.nfkc().collect::<String>().to_lowercase();
        let or_groups: Vec<&str> = normalized_query.split('|').collect();
        let mut groups = Vec::new();

        for group in or_groups {
            let mut positives = Vec::new();
            let mut negatives = Vec::new();
            let mut regexes = Vec::new();

            for term in group.split_whitespace() {
                if term.is_empty() { continue; }
                
                let is_neg = term.starts_with('-') && term.len() > 1;
                let clean_term = if is_neg { &term[1..] } else { term };

                if clean_term.contains('*') || clean_term.contains('?') {
                    // Turn wildcard to regex
                    let pattern = format!("^{}$", regex::escape(clean_term).replace("\\*", ".*").replace("\\?", "."));
                    if let Ok(re) = Regex::new(&pattern) {
                        regexes.push(re);
                    }
                } else {
                    if is_neg {
                        negatives.push(clean_term.to_string());
                    } else {
                        positives.push(clean_term.to_string());
                    }
                }
            }
            groups.push(QueryGroup { positives, negatives, regexes });
        }
        Matcher { groups }
    }

    fn is_match(&self, filename: &str) -> bool {
        let f_norm = filename.nfkc().collect::<String>().to_lowercase();
        
        for group in &self.groups {
            let mut group_match = true;
            
            // Check positives (AND)
            for p in &group.positives {
                if !f_norm.contains(p) {
                    group_match = false;
                    break;
                }
            }
            if !group_match { continue; }

            // Check regexes (AND)
            for re in &group.regexes {
                if !re.is_match(&f_norm) {
                    group_match = false;
                    break;
                }
            }
            if !group_match { continue; }

            // Check negatives (AND MUST NOT MATCH)
            for n in &group.negatives {
                if f_norm.contains(n) {
                    group_match = false;
                    break;
                }
            }

            if group_match {
                return true;
            }
        }
        false
    }
}

/// 超高速並列検索エンジン
#[pyfunction]
fn start_native_search(
    py: Python<'_>,
    root_path: String,
    query: String,
    batch_size: usize,
    callback: PyObject,
) -> PyResult<()> {
    let matcher = Matcher::new(&query);
    let (tx, rx) = mpsc::channel();

    // スキャンスレッドを裏で立ち上げる
    // PythonのGILを解放して、Rustの並列処理を全力で回す
    py.allow_threads(move || {
        let walker = WalkBuilder::new(&root_path)
            .threads(num_cpus::get()) // マルチコアフル活用
            .hidden(true)             // 隠しファイル除外
            .git_ignore(true)         // .gitignore 考慮
            .build_parallel();

        walker.run(|| {
            let tx = tx.clone();
            let matcher = &matcher;
            Box::new(move |entry| {
                if let Ok(entry) = entry {
                    if entry.file_type().map_or(false, |ft| ft.is_file()) {
                        let filename = entry.file_name().to_string_lossy();
                        if matcher.is_match(&filename) {
                            if let Ok(meta) = entry.metadata() {
                                let res = SearchResult {
                                    name: filename.to_string(),
                                    path: entry.path().to_string_lossy().to_string(),
                                    size: meta.len(),
                                    mtime: meta.modified().map_or(0, |st| {
                                        st.duration_since(std::time::UNIX_EPOCH)
                                            .unwrap_or_default()
                                            .as_secs() as i64
                                    }),
                                };
                                let _ = tx.send(res);
                            }
                        }
                    }
                }
                ignore::WalkState::Continue
            })
        });
    });

    // 結果をバッチで Python に送り返す
    let mut buffer = Vec::with_capacity(batch_size);
    while let Ok(res) = rx.recv() {
        buffer.push(res);
        if buffer.len() >= batch_size {
            emit_results(py, &callback, &buffer)?;
            buffer.clear();
        }
    }
    
    // 残りを送る
    if !buffer.is_empty() {
        emit_results(py, &callback, &buffer)?;
    }

    Ok(())
}

fn emit_results(py: Python<'_>, callback: &PyObject, results: &[SearchResult]) -> PyResult<()> {
    let py_list = PyList::empty_bound(py);
    for res in results {
        let tuple = PyTuple::new_bound(py, &[
            res.name.to_object(py),
            res.path.to_object(py),
            res.size.to_object(py),
            res.mtime.to_object(py),
        ]);
        py_list.append(tuple)?;
    }
    callback.call1(py, (py_list,))?;
    Ok(())
}

#[pymodule]
fn chainflow_search_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(start_native_search, m)?)?;
    Ok(())
}
