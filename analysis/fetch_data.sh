#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
data_root="$repo_root/data/repos"
mkdir -p "$data_root"

fetch_repo() {
  local name="$1"
  local url="$2"
  local sha="$3"
  local target="$data_root/$name"

  if [[ -d "$target/.git" ]]; then
    echo "$name already exists"
    return
  fi

  git init -q "$target"
  git -C "$target" remote add origin "$url"
  git -C "$target" fetch -q --filter=blob:none --depth=1000 origin "$sha"
  git -C "$target" update-ref refs/heads/snapshot FETCH_HEAD
  git -C "$target" symbolic-ref HEAD refs/heads/snapshot
  echo "fetched $name"
}

fetch_repo cpython  https://github.com/python/cpython.git           2ac2b93ca763170efeca0482b09455e0ae6afa3d
fetch_repo react    https://github.com/facebook/react.git          ce01166db71f77c703f778d5aa2c6e8daa597f45
fetch_repo django   https://github.com/django/django.git           b3997c604720ff061e9d3588c86a9bf7ca07fa32
fetch_repo go       https://github.com/golang/go.git               908f2642cb0fab5d4238d1bb8b5b08837344acfc
fetch_repo node     https://github.com/nodejs/node.git             1a2b5114273503f87ea7ee6b4dbd1a4aad4a6185
fetch_repo pytorch  https://github.com/pytorch/pytorch.git          735a2ec9b17c91c93d6714f88115f97394b836c9
fetch_repo flask    https://github.com/pallets/flask.git            49943b5a94413a530761350f04e896f76e8d620e
fetch_repo requests https://github.com/psf/requests.git             3c7baaa05ab4aa49cc819ce3a819d260de19c157
fetch_repo numpy    https://github.com/numpy/numpy.git              ee35f3baaf51a3c08072f0bf366dd85dfa6c26c3
fetch_repo pandas   https://github.com/pandas-dev/pandas.git        249a3e4845e574629d8f8aa6f1461fb47b02b02d
fetch_repo fastapi  https://github.com/fastapi/fastapi.git          1ca09c13584ca45aa0921e5e40b31d49c5e3135a
fetch_repo vue      https://github.com/vuejs/core.git               8b479a89445868d474f17e2d837765e7c9ece5e4
fetch_repo svelte   https://github.com/sveltejs/svelte.git          7775f73b7cbe32de3bb566f3515113208887e961
fetch_repo httpx    https://github.com/encode/httpx.git             b5addb64f0161ff6bfe94c124ef76f6a1fba5254
