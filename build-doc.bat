if exist doc-dist (
	rmdir /s /q doc-dist
)

set LANG=en_US.UTF-8

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
if "%SPHINXAPIDOC%" == "" (
	set SPHINXAPIDOC=sphinx-apidoc
)

mkdir doc-dist
mkdir doc-dist\logs

%SPHINXAPIDOC% -o doc/source/apis src/doFolder --separate --templatedir doc/source/_templates -f >> doc-dist/logs/sphinx-api-doc.log 2>&1
%SPHINXBUILD% --no-color -b html doc/source doc-dist >> doc-dist/logs/sphinx-build.log 2>&1