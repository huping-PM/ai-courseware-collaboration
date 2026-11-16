$ErrorActionPreference = 'Stop'
$workspace = Resolve-Path (Join-Path $PSScriptRoot '../..')
$draftPath = Join-Path $workspace '05_评审与排期/2026-09-30-AI课件协作三项禅道需求提交稿.md'
$draft = Get-Content -LiteralPath $draftPath -Raw -Encoding UTF8
$pattern = '(?ms)^## 需求[一二三]：(?<title>[^\r\n]+)\r?\n(?<body>.*?)(?=^## 需求[一二三]：|^## 提交前核对|\z)'
$matches = [regex]::Matches($draft, $pattern)
if ($matches.Count -ne 3) { throw "Expected exactly 3 approved requirements; found $($matches.Count)." }
$common = @'
### 局域网原型

- [原系统入口](http://192.168.1.81:8769/)
- [独立AI工作台](http://192.168.1.81:8769/06_%E4%BA%A4%E4%BB%98%E4%B8%8E%E9%AA%8C/AI%E5%8D%8F%E4%BD%9C%E5%B7%A5%E4%BD%9C%E5%8F%B0UI%E9%A3%8E%E6%A0%BC%E6%96%B9%E6%A1%88/%E4%BA%A4%E4%BA%92Demo.html)

原型版本：release-20260930014255935；同一局域网访问，原型仅作交互依据。
'@
$payloads = @()
foreach ($match in $matches) {
    $title = $match.Groups['title'].Value.Trim()
    $body = $match.Groups['body'].Value.Trim()
    $parts = [regex]::Match($body, '(?ms)^(?<intro>.*?)^\*\*验收标准。\*\*\s*(?<verify>.*?)^\*\*开发交接。\*\*\s*(?<handoff>.*)$')
    if (-not $parts.Success) { throw "Cannot parse approved body: $title" }
    $intro = $parts.Groups['intro'].Value.Trim()
    $verify = $parts.Groups['verify'].Value.Trim()
    $handoff = $parts.Groups['handoff'].Value.Trim()
    if ($title -like '*图片画布*') { $intro = $intro.Replace('，正式规则待正文审核。', '。') }
    $specMd = $intro + "`n`n### 开发交接`n`n" + $handoff + "`n`n" + $common
    $specHtml = (ConvertFrom-Markdown -InputObject $specMd).Html
    $verifyHtml = (ConvertFrom-Markdown -InputObject ("### 验收标准`n`n" + $verify)).Html
    if ($specHtml -match '(?m)^#{1,3} |\*\*' -or $verifyHtml -match '(?m)^#{1,3} |\*\*') { throw "Unrendered Markdown: $title" }
    foreach ($link in @('http://192.168.1.81:8769/', 'AI%E5%8D%8F%E4%BD%9C')) {
        if (-not $specHtml.Contains($link)) { throw "Missing prototype link $link in $title" }
    }
    $payloads += [pscustomobject]@{
        productID = 69
        assignedTo = 'caibo'
        title = $title
        spec = $specHtml
        verify = $verifyHtml
    }
}
$out = Join-Path $PSScriptRoot '已确认提交载荷.json'
$payloads | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
$hash = (Get-FileHash -LiteralPath $draftPath -Algorithm SHA256).Hash
Write-Output ([pscustomobject]@{ draftSha256 = $hash; count = $payloads.Count; titles = $payloads.title; payload = $out } | ConvertTo-Json -Compress)
