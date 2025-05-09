if (Test-Path "doc-dist") {
    Remove-Item -Recurse -Force "doc-dist"
}

$env:LANG = "en_US.UTF-8"

if (-not $env:SPHINXBUILD) {
    $env:SPHINXBUILD = "sphinx-build"
}
if (-not $env:SPHINXAPIDOC) {
    $env:SPHINXAPIDOC = "sphinx-apidoc"
}

New-Item -ItemType Directory -Path "doc-dist" | Out-Null
New-Item -ItemType Directory -Path "doc-dist\logs" | Out-Null

& $env:SPHINXAPIDOC -o "doc/source/apis" "src/doFolder" --separate --templatedir "doc/source/_templates" -f *> "doc-dist/logs/sphinx-api-doc.log" 2>&1
& $env:SPHINXBUILD --no-color -b html "doc/source" "doc-dist" *> "doc-dist/logs/sphinx-build.log" 2>&1
