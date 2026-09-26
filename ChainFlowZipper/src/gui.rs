use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::thread;
use eframe::egui;
use crate::config::{ZipConfig, CompressionMethod};
use crate::zipper;

#[derive(PartialEq, Clone, Copy)]
enum ActiveTab {
    Compress, // ①新規圧縮
    Merge,    // ②ZIPマージ
    Append,   // ③ZIPファイル追加
    Extract,  // ④ZIP解凍
}

pub struct ZipperApp {
    active_tab: ActiveTab,
    targets: Vec<PathBuf>,          // 対象リスト (新規圧縮時のファイル/フォルダ、またはマージ・解凍時のZIPファイル)
    base_zip_path: String,          // ファイル追加時の元ZIP
    output_path: String,            // 出力先ZIPパス、または展開先フォルダパス
    compress_level: u32,
    compression_method: CompressionMethod,
    custom_excludes: String,
    
    // スレッド同期用
    is_compressing: Arc<Mutex<bool>>,
    progress: Arc<Mutex<Option<(usize, usize)>>>,
    status_message: Arc<Mutex<Option<Result<String, String>>>>,
}

impl Default for ZipperApp {
    fn default() -> Self {
        Self {
            active_tab: ActiveTab::Compress,
            targets: Vec::new(),
            base_zip_path: String::new(),
            output_path: String::new(),
            compress_level: 5,
            compression_method: CompressionMethod::Deflate,
            custom_excludes: String::new(),
            is_compressing: Arc::new(Mutex::new(false)),
            progress: Arc::new(Mutex::new(None)),
            status_message: Arc::new(Mutex::new(None)),
        }
    }
}

impl ZipperApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        setup_custom_fonts(&cc.egui_ctx);
        Self::default()
    }
}

fn setup_custom_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    // Windows標準のメイリオ（meiryo.ttc）を読み込む
    let font_path = "C:\\Windows\\Fonts\\meiryo.ttc";
    if let Ok(font_data) = std::fs::read(font_path) {
        fonts.font_data.insert(
            "japanese".to_owned(),
            egui::FontData::from_owned(font_data),
        );

        fonts
            .families
            .entry(egui::FontFamily::Proportional)
            .or_default()
            .insert(0, "japanese".to_owned());

        fonts
            .families
            .entry(egui::FontFamily::Monospace)
            .or_default()
            .insert(0, "japanese".to_owned());

        ctx.set_fonts(fonts);
    }
}

impl eframe::App for ZipperApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.vertical_centered(|ui| {
                ui.heading("ChainFlow Zipper - 超高速並列圧縮＆展開");
            });
            ui.add_space(10.0);

            // モード切り替えタブ
            ui.horizontal(|ui| {
                if ui.selectable_label(self.active_tab == ActiveTab::Compress, "新規圧縮").clicked() {
                    self.active_tab = ActiveTab::Compress;
                    self.targets.clear();
                    self.status_message.lock().unwrap().take();
                }
                if ui.selectable_label(self.active_tab == ActiveTab::Merge, "ZIPマージ").clicked() {
                    self.active_tab = ActiveTab::Merge;
                    self.targets.clear();
                    self.status_message.lock().unwrap().take();
                }
                if ui.selectable_label(self.active_tab == ActiveTab::Append, "ファイル追加").clicked() {
                    self.active_tab = ActiveTab::Append;
                    self.targets.clear();
                    self.status_message.lock().unwrap().take();
                }
                if ui.selectable_label(self.active_tab == ActiveTab::Extract, "ZIP解凍").clicked() {
                    self.active_tab = ActiveTab::Extract;
                    self.targets.clear();
                    self.status_message.lock().unwrap().take();
                }
            });
            ui.add_space(10.0);

            // ドラッグ＆ドロップの検出
            ctx.input(|i| {
                if !i.raw.dropped_files.is_empty() {
                    for file in &i.raw.dropped_files {
                        if let Some(path) = &file.path {
                            if self.active_tab == ActiveTab::Merge || self.active_tab == ActiveTab::Extract {
                                // ZIPマージおよび解凍時はZIPファイルのみ許可
                                if path.extension().map_or(false, |ext| ext.to_ascii_lowercase() == "zip") {
                                    if !self.targets.contains(path) {
                                        self.targets.push(path.clone());
                                    }
                                }
                            } else if self.active_tab == ActiveTab::Append && self.base_zip_path.is_empty() && path.extension().map_or(false, |ext| ext.to_ascii_lowercase() == "zip") {
                                self.base_zip_path = path.to_string_lossy().to_string();
                            } else {
                                if !self.targets.contains(path) {
                                    self.targets.push(path.clone());
                                }
                            }
                        }
                    }
                }
            });

            // 1. 追加先ZIP指定 (ファイル追加モードのみ)
            if self.active_tab == ActiveTab::Append {
                ui.group(|ui| {
                    ui.set_min_width(ui.available_width());
                    ui.label("【追加先（元）となるZIPファイル】");
                    ui.horizontal(|ui| {
                        let edit_width = ui.available_width() - 80.0;
                        ui.add(egui::TextEdit::singleline(&mut self.base_zip_path).desired_width(edit_width));
                        if ui.button("参照...").clicked() {
                            if let Some(file_path) = rfd::FileDialog::new().add_filter("ZIP Archive", &["zip"]).pick_file() {
                                self.base_zip_path = file_path.to_string_lossy().to_string();
                                if self.output_path.is_empty() {
                                    self.output_path = file_path.to_string_lossy().to_string();
                                }
                            }
                        }
                    });
                });
                ui.add_space(10.0);
            }

            // 2. 対象ファイルリスト
            ui.group(|ui| {
                ui.set_min_width(ui.available_width());
                match self.active_tab {
                    ActiveTab::Compress => ui.label("【圧縮対象ファイル・フォルダ】 (ここにドラッグ＆ドロップ可能)"),
                    ActiveTab::Merge => ui.label("【マージ元ZIPファイル】 (複数選択・ドラッグ＆ドロップ可能)"),
                    ActiveTab::Append => ui.label("【追加するファイル・フォルダ】 (ここにドラッグ＆ドロップ可能)"),
                    ActiveTab::Extract => ui.label("【解凍対象のZIPファイル】 (複数選択・ドラッグ＆ドロップ可能)"),
                };
                
                let scroll_width = ui.available_width();
                egui::ScrollArea::vertical()
                    .max_height(140.0)
                    .min_scrolled_width(scroll_width)
                    .show(ui, |ui| {
                        if self.targets.is_empty() {
                            ui.weak("対象がありません。ドラッグ＆ドロップするか追加してください。");
                        } else {
                            let mut to_remove = None;
                            for (idx, path) in self.targets.iter().enumerate() {
                                ui.horizontal(|ui| {
                                    ui.with_layout(egui::Layout::left_to_right(egui::Align::Center), |ui| {
                                        ui.label(path.to_string_lossy());
                                        ui.allocate_space(egui::vec2(ui.available_width() - 60.0, 0.0));
                                        if ui.button("削除").clicked() {
                                            to_remove = Some(idx);
                                        }
                                    });
                                });
                            }
                            if let Some(idx) = to_remove {
                                self.targets.remove(idx);
                            }
                        }
                    });
                
                ui.add_space(5.0);
                ui.horizontal(|ui| {
                    if self.active_tab == ActiveTab::Merge || self.active_tab == ActiveTab::Extract {
                        if ui.button("ZIPファイルを追加...").clicked() {
                            if let Some(files) = rfd::FileDialog::new().add_filter("ZIP Archive", &["zip"]).pick_files() {
                                for file in files {
                                    if !self.targets.contains(&file) {
                                        self.targets.push(file);
                                    }
                                }
                            }
                        }
                    } else {
                        if ui.button("ファイルを追加...").clicked() {
                            if let Some(files) = rfd::FileDialog::new().pick_files() {
                                for file in files {
                                    if !self.targets.contains(&file) {
                                        self.targets.push(file);
                                    }
                                }
                            }
                        }
                        if ui.button("フォルダを追加...").clicked() {
                            if let Some(folder) = rfd::FileDialog::new().pick_folder() {
                                if !self.targets.contains(&folder) {
                                    self.targets.push(folder);
                                }
                            }
                        }
                    }
                    if ui.button("リストをクリア").clicked() {
                        self.targets.clear();
                    }
                });
            });
            ui.add_space(10.0);

            // 3. 出力先 / 展開先指定
            ui.group(|ui| {
                ui.set_min_width(ui.available_width());
                let label = if self.active_tab == ActiveTab::Extract {
                    "【展開先フォルダのパス】"
                } else {
                    "【出力先ZIPファイルのパス】"
                };
                ui.label(label);
                ui.horizontal(|ui| {
                    let edit_width = ui.available_width() - 200.0;
                    ui.add(egui::TextEdit::singleline(&mut self.output_path).desired_width(edit_width));
                    
                    if ui.button("参照...").clicked() {
                        if self.active_tab == ActiveTab::Extract {
                            if let Some(folder_path) = rfd::FileDialog::new().pick_folder() {
                                self.output_path = folder_path.to_string_lossy().to_string();
                            }
                        } else {
                            let mut dialog = rfd::FileDialog::new().add_filter("ZIP Archive", &["zip"]);
                            if let Some(first) = self.targets.first() {
                                if let Some(parent) = first.parent() {
                                    dialog = dialog.set_directory(parent);
                                }
                            }
                            if let Some(file_path) = dialog.save_file() {
                                self.output_path = file_path.to_string_lossy().to_string();
                            }
                        }
                    }
                    if ui.button("デフォルト設定").clicked() {
                        match self.active_tab {
                            ActiveTab::Compress | ActiveTab::Merge => {
                                if let Some(first) = self.targets.first() {
                                    let mut path = first.clone();
                                    if path.is_dir() {
                                        path.set_extension("zip");
                                    } else {
                                        if let Some(parent) = path.parent() {
                                            path = parent.join("archive.zip");
                                        }
                                    }
                                    self.output_path = path.to_string_lossy().to_string();
                                }
                            }
                            ActiveTab::Append => {
                                if !self.base_zip_path.is_empty() {
                                    self.output_path = self.base_zip_path.clone();
                                }
                            }
                            ActiveTab::Extract => {
                                if let Some(first) = self.targets.first() {
                                    if let Some(parent) = first.parent() {
                                        let mut stem = first.file_stem().unwrap_or_default().to_os_string();
                                        stem.push("_extracted");
                                        self.output_path = parent.join(stem).to_string_lossy().to_string();
                                    }
                                }
                            }
                        }
                    }
                });
            });
            ui.add_space(10.0);

            // 4. 圧縮設定 (解凍タブ以外で表示)
            if self.active_tab != ActiveTab::Extract {
                ui.group(|ui| {
                    ui.set_min_width(ui.available_width());
                    ui.label("【圧縮設定】");
                    ui.horizontal(|ui| {
                        ui.label("圧縮方式:");
                        ui.radio_value(&mut self.compression_method, CompressionMethod::Deflate, "Deflate (高互換)");
                        ui.radio_value(&mut self.compression_method, CompressionMethod::Zstd, "Zstd (超高速)");
                    });
                    ui.add_space(5.0);
                    ui.horizontal(|ui| {
                        ui.label("圧縮レベル (0-9):");
                        ui.add(egui::Slider::new(&mut self.compress_level, 0..=9));
                    });
                    ui.add_space(5.0);
                    ui.label("除外パターン (カンマ区切り):");
                    let edit_width = ui.available_width();
                    ui.add(egui::TextEdit::singleline(&mut self.custom_excludes).desired_width(edit_width));
                    ui.weak("例: *.tmp, *.log, target/");
                });
                ui.add_space(15.0);
            }

            // 圧縮・解凍処理実行と進行状況
            let is_compressing = *self.is_compressing.lock().unwrap();

            if is_compressing {
                ui.horizontal(|ui| {
                    ui.spinner();
                    let active_msg = if self.active_tab == ActiveTab::Extract {
                        "ZIP解凍処理を実行中..."
                    } else {
                        "圧縮・マージ処理を実行中..."
                    };
                    ui.label(active_msg);
                });
                
                if let Some((curr, tot)) = *self.progress.lock().unwrap() {
                    let pct = curr as f32 / tot as f32;
                    ui.add(egui::ProgressBar::new(pct).text(format!("{}% ({}/{})", (pct * 100.0) as i32, curr, tot)));
                }
                
                ctx.request_repaint();
            } else {
                if let Some(res) = &*self.status_message.lock().unwrap() {
                    match res {
                        Ok(msg) => ui.colored_label(egui::Color32::from_rgb(0, 200, 0), msg),
                        Err(err) => ui.colored_label(egui::Color32::from_rgb(200, 0, 0), err),
                    };
                }

                ui.horizontal(|ui| {
                    let is_ready = match self.active_tab {
                        ActiveTab::Compress => !self.targets.is_empty() && !self.output_path.is_empty(),
                        ActiveTab::Merge => !self.targets.is_empty() && !self.output_path.is_empty(),
                        ActiveTab::Append => !self.base_zip_path.is_empty() && !self.targets.is_empty() && !self.output_path.is_empty(),
                        ActiveTab::Extract => !self.targets.is_empty() && !self.output_path.is_empty(),
                    };

                    let btn_label = match self.active_tab {
                        ActiveTab::Compress => "ZIP圧縮を実行",
                        ActiveTab::Merge => "ZIPマージを実行",
                        ActiveTab::Append => "ファイルをZIPに追加",
                        ActiveTab::Extract => "ZIP解凍を実行",
                    };

                    if ui.add_enabled(is_ready, egui::Button::new(btn_label).min_size(egui::vec2(140.0, 30.0))).clicked() {
                        let mut config = ZipConfig::default();
                        config.compress_level = self.compress_level;
                        config.compression_method = self.compression_method;
                        if !self.custom_excludes.is_empty() {
                            for pat in self.custom_excludes.split(',') {
                                let trimmed = pat.trim();
                                if !trimmed.is_empty() {
                                    config.exclude_patterns.push(trimmed.to_string());
                                }
                            }
                        }

                        let active_tab = self.active_tab;
                        let targets = self.targets.clone();
                        let base_zip = PathBuf::from(&self.base_zip_path);
                        let output = PathBuf::from(&self.output_path);
                        
                        let is_compressing_clone = Arc::clone(&self.is_compressing);
                        let progress_clone = Arc::clone(&self.progress);
                        let status_clone = Arc::clone(&self.status_message);
                        let ctx_clone = ctx.clone();

                        *self.is_compressing.lock().unwrap() = true;
                        *self.progress.lock().unwrap() = None;
                        *self.status_message.lock().unwrap() = None;

                        thread::spawn(move || {
                            let result = match active_tab {
                                ActiveTab::Compress => zipper::compress_files(&targets, &output, &config, |curr, tot| {
                                    *progress_clone.lock().unwrap() = Some((curr, tot));
                                    ctx_clone.request_repaint();
                                }),
                                ActiveTab::Merge => zipper::merge_zips(&targets, &output, &config, |curr, tot| {
                                    *progress_clone.lock().unwrap() = Some((curr, tot));
                                    ctx_clone.request_repaint();
                                }),
                                ActiveTab::Append => zipper::append_to_zip(&base_zip, &targets, &output, &config, |curr, tot| {
                                    *progress_clone.lock().unwrap() = Some((curr, tot));
                                    ctx_clone.request_repaint();
                                }),
                                ActiveTab::Extract => {
                                    let mut err_occurred = None;
                                    for target in &targets {
                                        let res = zipper::extract_zip_with_progress(target, &output, |curr, tot| {
                                            *progress_clone.lock().unwrap() = Some((curr, tot));
                                            ctx_clone.request_repaint();
                                        });
                                        if let Err(e) = res {
                                            err_occurred = Some(e);
                                            break;
                                        }
                                    }
                                    match err_occurred {
                                        Some(e) => Err(e),
                                        None => Ok(()),
                                    }
                                }
                            };

                            *is_compressing_clone.lock().unwrap() = false;
                            match result {
                                Ok(_) => {
                                    *status_clone.lock().unwrap() = Some(Ok(format!("処理が正常に完了しました！\n出力先: {:?}", output)));
                                }
                                Err(e) => {
                                    *status_clone.lock().unwrap() = Some(Err(format!("エラーが発生しました: {}", e)));
                                }
                            }
                            ctx_clone.request_repaint();
                        });
                    }
                });
            }
        });
    }
}

pub fn run() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions {
        initial_window_size: Some(egui::vec2(520.0, 560.0)),
        ..Default::default()
    };
    eframe::run_native(
        "ChainFlow Zipper v4",
        options,
        Box::new(|cc| Box::new(ZipperApp::new(cc))),
    )
}
