#!/bin/bash

if [ -d "doc-dist" ]; then
	rm -rf doc-dist
fi

if [ -z "$SPHINXBUILD" ]; then
	SPHINXBUILD=sphinx-build
fi

if [ -z "$SPHINXAPIDOC" ]; then
	SPHINXAPIDOC=sphinx-apidoc
fi

mkdir -p doc-dist/logs

$SPHINXAPIDOC -o doc/source/apis src/doFolder --separate --templatedir doc/source/_templates -f >> doc-dist/logs/sphinx-api-doc.log 2>&1
$SPHINXBUILD -b html doc/source doc-dist >> doc-dist/logs/sphinx-build.log 2>&1
