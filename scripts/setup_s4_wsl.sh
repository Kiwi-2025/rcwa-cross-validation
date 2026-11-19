#!/usr/bin/env bash
set -euo pipefail

revision=9569f5e555b967a4324eb1ea593d0f9f40761a61
source_dir="${RCWA_S4_SOURCE:-$HOME/.local/src/rcwa-s4}"
python="${RCWA_S4_PYTHON:-/usr/bin/python3}"

# Ubuntu prerequisites:
# sudo apt install build-essential git python3-dev python3-numpy libopenblas-dev libfftw3-dev libboost-serialization-dev
if [[ ! -d "$source_dir/.git" ]]; then
    git clone https://github.com/phoebe-p/S4.git "$source_dir"
fi
cd "$source_dir"
git checkout --detach "$revision"
make objdir
make -j"${RCWA_S4_JOBS:-4}" all CHOLMOD_LIB= BOOST_INC=
includes=$("$python" -c 'import sysconfig; print(sysconfig.get_path("include"))')
numpy_includes=$("$python" -c 'import numpy; print(numpy.get_include())')
site=$("$python" -c 'import site; print(site.getusersitepackages())')
suffix=$("$python" -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')
mkdir -p "$site"
gcc -O3 -fPIC -I"$includes" -I"$numpy_includes" -I. -IS4 -c S4/main_python.c -o build/main_python.o
g++ -shared build/main_python.o build/libS4.a -lopenblas -lfftw3 -lboost_serialization -o "$site/S4$suffix"
"$python" -c 'import S4; print("S4 ready")'
