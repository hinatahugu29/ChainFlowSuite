use std::fs::File;
use std::io::{self, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::time::{Instant, Duration};
use ignore::WalkBuilder;
use zip::write::FileOptions;
use zip::ZipWriter;
use rayon::prelude::*;
use crate::config::ZipConfig;

pub fn compress_files<P: AsRef<Path>>(
    target_paths: &[PathBuf],
    output_zip: P,
    config: &ZipConfig,
    progress_callback: impl Fn(usize, usize) + Send + Sync,
) -> io::Result<()> {
    // 1. 対象ファイル・フォルダの全リストアップ (ignoreクレートを利用)
    let mut file_entries = Vec::new();

    for target in target_paths {
        if !target.exists() {
            continue;
        }

        let base_dir = if target.is_dir() {
            target.parent().unwrap_or(target).to_path_buf()
        } else {
            target.parent().unwrap_or(target).to_path_buf()
        };

        let mut builder = WalkBuilder::new(target);
        // .gitignore などの自動適用を行わず、全ファイルをスキャン対象にする
        builder.standard_filters(false);
        builder.hidden(false); // 隠しファイルもデフォルトでスキャン対象とする
        
        // カスタム除外パターンの適用 (configで指定されたもの)
        let checker = config.create_exclude_checker();

        for result in builder.build() {
            match result {
                Ok(entry) => {
                    let path = entry.path();
                    
                    // 除外リストにマッチするか判定
                    if checker.is_excluded(path) {
                        continue;
                    }

                    let rel_path = path.strip_prefix(&base_dir)
                        .unwrap_or(path)
                        .to_string_lossy()
                        .replace('\\', "/"); // ZIP規格はスラッシュ区切り

                    if rel_path.is_empty() {
                        continue;
                    }

                    file_entries.push((path.to_path_buf(), rel_path, entry.file_type().map(|ft| ft.is_dir()).unwrap_or(false)));
                }
                Err(e) => eprintln!("スキャンエラー: {}", e),
            }
        }
    }

    let total_files = file_entries.len();
    if total_files == 0 {
        return Err(io::Error::new(io::ErrorKind::NotFound, "圧縮対象のファイルが見つかりません。"));
    }

    // 2. Rayon を使用した小ファイルの並列プリロード＆バッファリング
    // 2MB以下の小ファイルを並列にロードしてメモリにキャッシュし、ディスクI/O競合を解消
    let preloaded_data: Vec<Option<Vec<u8>>> = file_entries.par_iter().map(|(abs_path, _, is_dir)| {
        if *is_dir {
            None
        } else {
            if let Ok(metadata) = std::fs::metadata(abs_path) {
                if metadata.len() > 0 && metadata.len() < 2 * 1024 * 1024 {
                    if let Ok(f) = File::open(abs_path) {
                        let mut reader = BufReader::new(f);
                        let mut buf = Vec::with_capacity(metadata.len() as usize);
                        if reader.read_to_end(&mut buf).is_ok() {
                            return Some(buf);
                        }
                    }
                }
            }
            None
        }
    }).collect();

    // 3. 順次書き出しと圧縮
    let file = File::create(output_zip)?;
    let mut zip = ZipWriter::new(file);

    // 圧縮方式の選択
    let method = match config.compression_method {
        crate::config::CompressionMethod::Deflate => zip::CompressionMethod::Deflated,
        crate::config::CompressionMethod::Zstd => zip::CompressionMethod::Zstd,
    };

    let options = FileOptions::default()
        .compression_method(method)
        .compression_level(Some(config.compress_level as i32))
        .last_modified_time(zip::DateTime::default());

    let mut last_update = Instant::now();
    let update_interval = Duration::from_millis(100); // 100msごとに更新判定
    let mut stream_buffer = Vec::new();

    for (idx, (abs_path, rel_path, is_dir)) in file_entries.iter().enumerate() {
        // 進捗表示の間引き (最終ファイル、または50ファイルごと、または100ms経過時のみ通知)
        let is_last = idx + 1 == total_files;
        if is_last || idx % 50 == 0 || last_update.elapsed() >= update_interval {
            progress_callback(idx + 1, total_files);
            last_update = Instant::now();
        }

        if *is_dir {
            // ディレクトリは末尾スラッシュが必要
            let dir_path = format!("{}/", rel_path.trim_end_matches('/'));
            zip.add_directory(&dir_path, options.clone())?;
        } else {
            zip.start_file(rel_path, options.clone())?;
            
            if let Some(cached_data) = &preloaded_data[idx] {
                zip.write_all(cached_data)?;
            } else {
                // キャッシュ対象外の大容量ファイルは BufReader を使ってストリーミング読み込み
                let f = File::open(abs_path)?;
                let mut reader = BufReader::new(f);
                stream_buffer.clear();
                reader.read_to_end(&mut stream_buffer)?;
                zip.write_all(&stream_buffer)?;
            }
        }
    }

    zip.finish()?;
    Ok(())
}

/// ZIPファイルを指定されたディレクトリに展開するヘルパー
pub fn extract_zip<P: AsRef<Path>, O: AsRef<Path>>(zip_path: P, output_dir: O) -> io::Result<()> {
    extract_zip_with_progress(zip_path, output_dir, |_, _| {})
}

/// 進捗率通知付きでZIPファイルを指定されたディレクトリに展開するヘルパー
pub fn extract_zip_with_progress<P: AsRef<Path>, O: AsRef<Path>>(
    zip_path: P,
    output_dir: O,
    progress_callback: impl Fn(usize, usize) + Send + Sync,
) -> io::Result<()> {
    let file = File::open(zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;
    let out_dir = output_dir.as_ref();
    
    if !out_dir.exists() {
        std::fs::create_dir_all(out_dir)?;
    }

    let total = archive.len();
    let mut last_update = Instant::now();
    let update_interval = Duration::from_millis(100);

    for i in 0..total {
        let is_last = i + 1 == total;
        if is_last || i % 50 == 0 || last_update.elapsed() >= update_interval {
            progress_callback(i + 1, total);
            last_update = Instant::now();
        }

        let mut file = archive.by_index(i)?;
        let outpath = match file.enclosed_name() {
            Some(path) => out_dir.join(path),
            None => continue,
        };

        if file.name().ends_with('/') {
            std::fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                if !p.exists() {
                    std::fs::create_dir_all(p)?;
                }
            }
            let mut outfile = File::create(&outpath)?;
            io::copy(&mut file, &mut outfile)?;
        }
    }
    Ok(())
}

fn uuid_like_id() -> u128 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}

pub fn merge_zips<P: AsRef<Path>>(
    zip_paths: &[PathBuf],
    output_zip: P,
    config: &ZipConfig,
    progress_callback: impl Fn(usize, usize) + Send + Sync,
) -> io::Result<()> {
    let temp_dir = std::env::temp_dir().join(format!("CFZipper_merge_{}", uuid_like_id()));
    std::fs::create_dir_all(&temp_dir)?;
    
    // 各ZIPを展開
    for zip in zip_paths {
        extract_zip(zip, &temp_dir)?;
    }
    
    // 展開したフォルダをまるごと圧縮
    let res = compress_files(&[temp_dir.clone()], output_zip, config, progress_callback);
    
    // 一時フォルダ削除
    let _ = std::fs::remove_dir_all(&temp_dir);
    res
}

pub fn append_to_zip<P: AsRef<Path>>(
    base_zip: P,
    add_paths: &[PathBuf],
    output_zip: P,
    config: &ZipConfig,
    progress_callback: impl Fn(usize, usize) + Send + Sync,
) -> io::Result<()> {
    let temp_dir = std::env::temp_dir().join(format!("CFZipper_append_{}", uuid_like_id()));
    std::fs::create_dir_all(&temp_dir)?;
    
    // 元ZIPを展開
    extract_zip(base_zip.as_ref(), &temp_dir)?;
    
    // 「展開先の一時フォルダ」と「追加したいファイル群」をミックスして圧縮対象にする
    let mut targets = vec![temp_dir.clone()];
    for p in add_paths {
        targets.push(p.clone());
    }
    
    // 圧縮して出力（一旦別名で出力した方が上書き時のロック衝突を防げる）
    let temp_output = std::env::temp_dir().join(format!("CFZipper_out_{}.zip", uuid_like_id()));
    let res = compress_files(&targets, &temp_output, config, progress_callback);
    
    // 一時フォルダ削除
    let _ = std::fs::remove_dir_all(&temp_dir);
    
    if res.is_ok() {
        // 成功したら本来の出力先にコピー
        std::fs::copy(&temp_output, output_zip)?;
        let _ = std::fs::remove_file(&temp_output);
    } else {
        let _ = std::fs::remove_file(&temp_output);
    }
    res
}
