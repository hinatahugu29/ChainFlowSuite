use std::path::PathBuf;
use clap::Parser;
use crate::config::ZipConfig;
use crate::zipper;

#[derive(Parser, Debug)]
#[command(name = "ChainFlowZipper", author, version, about = "Super fast parallel ZIP compressor", long_about = None)]
pub struct CliArgs {
    /// 圧縮対象のファイル・フォルダの絶対パスが記述されたテキストファイルのパス
    #[arg(short, long)]
    pub list: Option<PathBuf>,

    /// 圧縮対象ファイル・フォルダ（直接指定用）
    #[arg(short, long)]
    pub input: Vec<PathBuf>,

    /// 出力先のZIPファイルパス
    #[arg(short, long)]
    pub output: PathBuf,

    /// 圧縮レベル (0-9)
    #[arg(long, default_value_t = 5)]
    pub level: u32,

    /// カスタム除外パターン（カンマ区切り、例: "*.tmp,*.log"）
    #[arg(short, long)]
    pub exclude: Option<String>,

    /// 圧縮方式 (deflate, zstd)
    #[arg(long, default_value = "deflate")]
    pub method: String,

    /// 解凍モードを実行するかどうか
    #[arg(short = 'x', long)]
    pub extract: bool,
}

pub fn run(args: CliArgs) -> Result<(), Box<dyn std::error::Error>> {
    let mut targets = args.input;

    // リストファイルがある場合は読み込む
    if let Some(list_path) = args.list {
        let content = std::fs::read_to_string(list_path)?;
        for line in content.lines() {
            let trimmed = line.trim();
            if !trimmed.is_empty() {
                targets.push(PathBuf::from(trimmed));
            }
        }
    }

    // 解凍処理の実行
    if args.extract {
        if targets.is_empty() {
            return Err("解凍対象のZIPファイルが指定されていません。".into());
        }
        println!("解凍開始: 対象ZIP数={}", targets.len());
        for target in &targets {
            zipper::extract_zip_with_progress(target, &args.output, |current, total| {
                let percentage = (current * 100) / total;
                println!("PROGRESS:{}% ({}/{})", percentage, current, total);
                use std::io::Write;
                let _ = std::io::stdout().flush();
            })?;
        }
        println!("SUCCESS: 解凍が正常に完了しました -> {:?}", args.output);
        return Ok(());
    }

    if targets.is_empty() {
        return Err("圧縮対象のパスが指定されていません。".into());
    }

    let mut config = ZipConfig::default();
    config.compress_level = args.level;
    config.compression_method = match args.method.to_lowercase().as_str() {
        "zstd" => crate::config::CompressionMethod::Zstd,
        _ => crate::config::CompressionMethod::Deflate,
    };
    
    if let Some(exclude_str) = args.exclude {
        for pat in exclude_str.split(',') {
            let trimmed = pat.trim();
            if !trimmed.is_empty() {
                config.exclude_patterns.push(trimmed.to_string());
            }
        }
    }

    println!("圧縮開始: 対象オブジェクト数={}", targets.len());

    // 圧縮処理の実行と、標準出力への進捗率出力
    zipper::compress_files(&targets, &args.output, &config, |current, total| {
        let percentage = (current * 100) / total;
        println!("PROGRESS:{}% ({}/{})", percentage, current, total);
        
        // 標準出力を確実にフラッシュ
        use std::io::Write;
        let _ = std::io::stdout().flush();
    })?;

    println!("SUCCESS: 圧縮が正常に完了しました -> {:?}", args.output);
    Ok(())
}
