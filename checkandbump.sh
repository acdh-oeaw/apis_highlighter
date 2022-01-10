#!/bin/sh
# Shell script to check the apis-core version on pypi and bump it

CURRENTLY_BUILT_VER=$(sed -n '3s/.*= "\(.*\)"/\1/p' pyproject.toml)
LASTVER=$(lastversion apis-highlighter --at pip -gt ${CURRENTLY_BUILT_VER})
echo $LASTVER
echo $CURRENTLY_BUILT_VER
if [[ $? -eq 0 ]]; then
    echo "patching version"
    LASTVER_PYPI=$(lastversion apis-highlighter --at pip)
    sed -i "3s/\".*$/\"${LASTVER_PYPI}\"/" pyproject.toml
    poetry version patch; else
    echo "version already newer"
fi