<#
    deploy_suite.ps1
    v23.9: ChainFlow Suite (配布一式) を組み立てる。

    Suite は「各ツールのビルド成果物を1か所に集めたもの」で、ソースではない。
    ここへ集約しておくと、フォルダごとコピーするだけで別マシンへ持ち出せる。

    ■ なぜこの配置なのか
    Filer は tools.json に書かれた相対パスで兄弟ツールを探す。EXE 版のとき
    起点は EXE のある場所、つまり <Suite>\ChainFlowFiler\Internal になるため、
    "../../ChainFlowWriter/ChainFlowWriter.exe" は
    <Suite>\ChainFlowWriter\ChainFlowWriter.exe を指す。
    したがって Suite 直下は「ツール名のフォルダ」が並ぶ形でなければならない。

        ChainFlow_V23_Suite\
            ChainFlowFiler\Internal\main.exe      <- 司令塔
            ChainFlowFiler\ChainFlowFiler_V23.7.vbs
            ChainFlowWriter\ChainFlowWriter.exe
            ChainFlowPad\Internal\ChainFlowPad.exe
            ChainFlowZipper\target\release\ChainFlowZipper.exe
            ...

    PyInstaller のツールは dist\<名前>\ の中身を、Pad は Internal\ を、
    Zipper は Rust の target\ 構成を保ったまま運ぶ。

    ■ 使い方
        powershell -ExecutionPolicy Bypass -File deploy_suite.ps1
        powershell -ExecutionPolicy Bypass -File deploy_suite.ps1 -WhatIf

    Filer だけは build_nuitka.bat が Suite の存在を見て自動コピーするので、
    通常の開発中はそちらに任せてよい。
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$SuiteName = "ChainFlow_V23_Suite"
)

$ErrorActionPreference = "Stop"
$Root  = $PSScriptRoot
$Suite = Join-Path $Root $SuiteName

# 送り元(Root からの相対) -> Suite 内の配置先
# Source に指定したフォルダの「中身」が Dest フォルダへ入る。
$Manifest = @(
    @{ Name = "ChainFlow Filer";       Source = "ChainFlowFiler\build_nuitka\Internal";        Dest = "ChainFlowFiler\Internal" }
    @{ Name = "ChainFlow Writer";      Source = "ChainFlowWriter\dist\ChainFlowWriter";              Dest = "ChainFlowWriter" }
    @{ Name = "ChainFlow Tool";        Source = "ChainFlowTool\dist\ChainFlowTool";                  Dest = "ChainFlowTool" }
    @{ Name = "Quick Image Tool";      Source = "ChainFlowImage\dist\ChainFlowImage";                Dest = "ChainFlowImage" }
    @{ Name = "ChainFlow Sniper";      Source = "ChainFlowSniper\dist\ChainFlowSniper";              Dest = "ChainFlowSniper" }
    @{ Name = "ChainFlow Pad";         Source = "ChainFlowPad\Internal";                             Dest = "ChainFlowPad\Internal" }
    @{ Name = "Global Search";         Source = "ChainFlowSearch\dist\ChainFlowSearch";              Dest = "ChainFlowSearch" }
    @{ Name = "ChainFlow Designer";    Source = "ChainFlowDesigner\dist\ChainFlowDesigner";          Dest = "ChainFlowDesigner" }
    @{ Name = "ChainFlow ToDo";        Source = "ChainFlowToDo\dist\ChainFlowToDo";                  Dest = "ChainFlowToDo" }
    @{ Name = "ChainFlow PDF Studio";  Source = "ChainFlowPDFStudio\dist\ChainFlowPDFStudio";        Dest = "ChainFlowPDFStudio" }
    @{ Name = "ChainFlow PDF Compare"; Source = "ChainFlowPDFCompare\dist\ChainFlowPDFCompare";      Dest = "ChainFlowPDFCompare" }
)

# Zipper だけは EXE を名指しで運ぶ(target\ 配下には巨大なビルド中間物があり、
# 丸ごとコピーすると数GBになるため)。Filer は release を優先し、無ければ
# debug を見るので、両方置ければ両方置く。
$ZipperFiles = @(
    @{ Source = "ChainFlowZipper\target\release\ChainFlowZipper.exe"; Dest = "ChainFlowZipper\target\release" }
    @{ Source = "ChainFlowZipper\target\debug\ChainFlowZipper.exe";   Dest = "ChainFlowZipper\target\debug" }
)

# Filer のランチャー(Suite 直下ではなく ChainFlowFiler\ に置く)
$LauncherFiles = @(
    @{ Source = "ChainFlowFiler\build_nuitka\ChainFlowFiler_V23.7.vbs"; Dest = "ChainFlowFiler" }
    @{ Source = "ChainFlowFiler\build_nuitka\ChainFlowFiler_V23.7.bat"; Dest = "ChainFlowFiler" }
)

# 注意: 関数内の進捗表示は Write-Host を使うこと。
# Write-Output は関数の戻り値ストリームへ流れるため、呼び出し側の
# if (Copy-Tree ...) が真偽値と一緒に飲み込んでしまい画面に出ない。
function Copy-Tree {
    param($Label, $SourceRel, $DestRel)

    $src = Join-Path $Root $SourceRel
    $dst = Join-Path $Suite $DestRel

    if (-not (Test-Path $src)) {
        Write-Host ("  [skip] {0} -- 送り元が見つかりません: {1}" -f $Label, $SourceRel) -ForegroundColor Yellow
        return $false
    }

    if ($PSCmdlet.ShouldProcess($dst, "copy from $SourceRel")) {
        # /MIR で送り元に無いものは消す(Suite を送り元と同じ状態にする)
        # /NJH /NJS /NP /NFL /NDL で出力を最小限に
        $null = robocopy $src $dst /MIR /NJH /NJS /NP /NFL /NDL /R:2 /W:1
        # robocopy は 0-7 が成功、8 以上が失敗
        if ($LASTEXITCODE -ge 8) {
            Write-Host ("  [FAIL] {0} -- robocopy exit {1}" -f $Label, $LASTEXITCODE) -ForegroundColor Red
            return $false
        }
    }
    Write-Host ("  [ok]   {0}" -f $Label) -ForegroundColor Green
    return $true
}

function Copy-One {
    param($SourceRel, $DestRel)

    $src = Join-Path $Root $SourceRel
    if (-not (Test-Path $src)) {
        Write-Host ("  [skip] {0} -- 見つかりません" -f $SourceRel) -ForegroundColor Yellow
        return $false
    }
    $dst = Join-Path $Suite $DestRel
    if ($PSCmdlet.ShouldProcess($dst, "copy $SourceRel")) {
        if (-not (Test-Path $dst)) { $null = New-Item -ItemType Directory -Path $dst -Force }
        Copy-Item $src $dst -Force
    }
    Write-Host ("  [ok]   {0}" -f (Split-Path $SourceRel -Leaf)) -ForegroundColor Green
    return $true
}

Write-Output "ChainFlow Suite deploy"
Write-Output ("  root  : {0}" -f $Root)
Write-Output ("  suite : {0}" -f $Suite)
Write-Output ""

if (-not (Test-Path $Suite)) {
    if ($PSCmdlet.ShouldProcess($Suite, "create suite root")) {
        $null = New-Item -ItemType Directory -Path $Suite -Force
    }
    Write-Output "Suite ルートを新規作成しました"
    Write-Output ""
}

Write-Output "== ツール =="
$okCount = 0
foreach ($entry in $Manifest) {
    if (Copy-Tree -Label $entry.Name -SourceRel $entry.Source -DestRel $entry.Dest) { $okCount++ }
}

Write-Output ""
Write-Output "== Zipper (EXE のみ) =="
foreach ($z in $ZipperFiles) { $null = Copy-One -SourceRel $z.Source -DestRel $z.Dest }

Write-Output ""
Write-Output "== ランチャー =="
foreach ($l in $LauncherFiles) { $null = Copy-One -SourceRel $l.Source -DestRel $l.Dest }

Write-Output ""
if (-not $WhatIfPreference -and (Test-Path $Suite)) {
    $size = (Get-ChildItem $Suite -Recurse -File -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum).Sum
    Write-Output ("完了: {0}/{1} ツール / 合計 {2:N0} MB" -f $okCount, $Manifest.Count, ($size / 1MB))
    Write-Output ("起動: {0}\ChainFlowFiler\ChainFlowFiler_V23.7.vbs" -f $Suite)
} else {
    Write-Output "(WhatIf: 実際のコピーは行っていません)"
}
