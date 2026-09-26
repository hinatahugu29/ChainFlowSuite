mod config;
mod zipper;
mod cli;
mod gui;

use clap::Parser;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() > 1 {
        // 引数がある場合: CLIモード
        let cli_args = match cli::CliArgs::try_parse() {
            Ok(parsed) => parsed,
            Err(e) => {
                e.exit();
            }
        };

        if let Err(e) = cli::run(cli_args) {
            eprintln!("エラー: {}", e);
            std::process::exit(1);
        }
    } else {
        // 引数がない場合: GUIモード
        if let Err(e) = gui::run() {
            eprintln!("GUI起動エラー: {:?}", e);
            std::process::exit(1);
        }
    }
}
