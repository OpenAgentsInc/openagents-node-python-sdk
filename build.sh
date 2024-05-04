#!/bin/bash

if [ "$TAG" = "" ];
then
    TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$TAG" ]]; then
        TAG=${TAG#v}
        export TAG
    else
        export TAG="0.1"
    fi
fi

echo "$TAG" > VERSION
echo "Building version $TAG"

if [ "$DEBUG" = "1" ] ;
then
    pip install -e .
else 
    python setup.py sdist
fi