$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $env:PATH = "$PSScriptRoot/tools;E:/New Folder;" + $env:PATH
    $env:HYPERFRAMES_BROWSER_PATH = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    $env:DO_NOT_TRACK = '1'
    & 'E:/New Folder/node.exe' node_modules/hyperframes/bin/hyperframes.mjs check
    if ($LASTEXITCODE -ne 0) { throw '动画检查未通过，请先检查输出。' }
    & 'E:/New Folder/node.exe' node_modules/hyperframes/bin/hyperframes.mjs render -o 'renders/商业车险产品地图.mp4' --fps 30 --quality looks --workers 2
    if ($LASTEXITCODE -ne 0) { throw '视频导出未完成。' }
} finally {
    Pop-Location
}
