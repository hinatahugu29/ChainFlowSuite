use anyhow::Result;
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::io::{self, Write};
use std::path::Path;
use std::sync::atomic::{AtomicUsize, Ordering};
use walkdir::WalkDir;
use rayon::prelude::*;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct FileRecord {
    pub path: String,
    pub size: u64,
    pub mtime: i64,
    pub hash: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum SyncAction {
    Create { path: String, size: u64 },
    Update { path: String, size: u64 },
    NoChange { path: String },
    Conflict { path: String },
}

pub fn init_db(db_path: &Path) -> Result<Connection> {
    let conn = Connection::open(db_path)?;
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            size INTEGER NOT NULL,
            mtime INTEGER NOT NULL,
            hash TEXT
        )",
        [],
    )?;
    Ok(conn)
}

pub fn scan_directory(root: &Path) -> Vec<FileRecord> {
    // Phase 1: Quick count
    let mut total_files = 0;
    for entry in WalkDir::new(root).into_iter().filter_map(|e| e.ok()) {
        if entry.file_type().is_file() {
            let file_name = entry.file_name().to_str().unwrap_or("");
            if file_name != ".cfs_index.db" {
                total_files += 1;
            }
        }
    }
    println!("PROGRESS:TOTAL:{}", total_files);
    let _ = io::stdout().flush();

    // Phase 2: Actual metadata sweep
    let mut records = Vec::new();
    let mut count = 0;
    
    for entry in WalkDir::new(root).into_iter().filter_map(|e| e.ok()) {
        if entry.file_type().is_file() {
            let full_path = entry.path();
            let rel_path = full_path.strip_prefix(root).unwrap_or(full_path);
            
            if let Ok(metadata) = fs::metadata(full_path) {
                let file_name = full_path.file_name().and_then(|n| n.to_str()).unwrap_or("");
                if file_name == ".cfs_index.db" {
                    continue;
                }
                
                let mtime = metadata
                    .modified()
                    .ok()
                    .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                    .map(|d| d.as_secs() as i64)
                    .unwrap_or(0);

                records.push(FileRecord {
                    path: rel_path.to_string_lossy().to_string(),
                    size: metadata.len(),
                    mtime,
                    hash: None,
                });
                
                count += 1;
                let interval = (total_files / 100).max(1).min(1000);
                if count % interval == 0 || count == total_files {
                    println!("PROGRESS:SCANNED:{}", count);
                    let _ = io::stdout().flush();
                }
            }
        }
    }
    records
}

pub fn load_from_db(conn: &Connection) -> Result<HashMap<String, FileRecord>> {
    let mut stmt = conn.prepare("SELECT path, size, mtime, hash FROM files")?;
    let rows = stmt.query_map([], |row| {
        Ok(FileRecord {
            path: row.get(0)?,
            size: row.get(1)?,
            mtime: row.get(2)?,
            hash: row.get(3)?,
        })
    })?;

    let mut map = HashMap::new();
    for row in rows {
        let rec = row?;
        map.insert(rec.path.clone(), rec);
    }
    Ok(map)
}

pub fn save_to_db(conn: &Connection, records: &[FileRecord]) -> Result<()> {
    conn.execute("DELETE FROM files", [])?;
    let mut stmt = conn.prepare(
        "INSERT OR REPLACE INTO files (path, size, mtime, hash) VALUES (?1, ?2, ?3, ?4)",
    )?;
    for rec in records {
        stmt.execute(params![rec.path, rec.size, rec.mtime, rec.hash])?;
    }
    Ok(())
}

fn execute_plan(actions: &[SyncAction], src_root: &Path, dst_root: &Path) -> Result<()> {
    let total = actions.len();
    println!("PROGRESS:TOTAL:{}", total);
    let _ = io::stdout().flush();
    
    let counter = AtomicUsize::new(0);
    let interval = (total / 100).max(1).min(50); // Emit more frequently for copy updates

    actions.par_iter().for_each(|action| {
        match action {
            SyncAction::Create { path, .. } | SyncAction::Update { path, .. } => {
                let src_path = src_root.join(path);
                let dst_path = dst_root.join(path);
                
                if let Some(parent) = dst_path.parent() {
                    let _ = fs::create_dir_all(parent);
                }
                
                // Show filename for visual feedback (as requested by user for "working" feel)
                println!("Syncing: {}", path);
                let _ = io::stdout().flush();

                let current = counter.fetch_add(1, Ordering::SeqCst) + 1;
                if current % interval == 0 || current == total {
                    // Print progress (briefly)
                    println!("PROGRESS:SCANNED:{}", current);
                    let _ = io::stdout().flush();
                }

                if let Err(e) = fs::copy(&src_path, &dst_path) {
                    eprintln!("Error copying {}: {}", path, e);
                }
            },
            _ => {
                let current = counter.fetch_add(1, Ordering::SeqCst) + 1;
                if current % interval == 0 || current == total {
                    println!("PROGRESS:SCANNED:{}", current);
                    let _ = io::stdout().flush();
                }
            }
        }
    });

    Ok(())
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        println!(r#"Usage:
  sync-engine scan <path_to_scan> <db_path>
  sync-engine diff <src_db> <dst_db>
  sync-engine apply <plan_json> <src_root> <dst_root>"#);
        return Ok(());
    }

    let cmd = &args[1];

    match cmd.as_str() {
        "scan" => {
            if args.len() < 4 { return Ok(()); }
            let scan_path = Path::new(&args[2]);
            let db_path = Path::new(&args[3]);
            let records = scan_directory(scan_path);
            let conn = init_db(db_path)?;
            save_to_db(&conn, &records)?;
            let summary = serde_json::json!({ "status": "success", "count": records.len() });
            println!("{}", serde_json::to_string(&summary)?);
        },
        "diff" => {
            if args.len() < 4 { return Ok(()); }
            let src_db = Path::new(&args[2]);
            let dst_db = Path::new(&args[3]);
            let src_conn = Connection::open(src_db)?;
            let dst_conn = Connection::open(dst_db)?;
            let src_map = load_from_db(&src_conn)?;
            let dst_map = load_from_db(&dst_conn)?;
            let mut actions = Vec::new();
            
            for (path, src_rec) in &src_map {
                match dst_map.get(path) {
                    Some(dst_rec) => {
                        if src_rec.mtime > dst_rec.mtime || src_rec.size != dst_rec.size {
                            actions.push(SyncAction::Update { path: path.clone(), size: src_rec.size });
                        } else {
                            actions.push(SyncAction::NoChange { path: path.clone() });
                        }
                    },
                    None => {
                        actions.push(SyncAction::Create { path: path.clone(), size: src_rec.size });
                    }
                }
            }
            println!("{}", serde_json::to_string(&actions)?);
        },
        "apply" => {
            if args.len() < 5 { return Ok(()); }
            let plan_json = &args[2];
            let src_root = Path::new(&args[3]);
            let dst_root = Path::new(&args[4]);
            
            let json_content = if Path::new(plan_json).exists() {
                fs::read_to_string(plan_json)?
            } else {
                plan_json.to_string()
            };
            
            let actions: Vec<SyncAction> = serde_json::from_str(&json_content)?;
            execute_plan(&actions, src_root, dst_root)?;
            println!(r#"{{"status": "complete"}}"#);
        }
        _ => println!("Unknown command"),
    }

    Ok(())
}
