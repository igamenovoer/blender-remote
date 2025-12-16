#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXTERN_DIR="${SCRIPT_DIR}"
REPO_ROOT="$(cd "${EXTERN_DIR}/.." && pwd)"

require_cmd() {
  for c in "$@"; do
    if ! command -v "$c" >/dev/null 2>&1; then
      echo "missing required command: $c" >&2
      exit 127
    fi
  done
}

fetch_url() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url"
    return 0
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -qO- "$url"
    return 0
  fi
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
      "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; (Invoke-WebRequest -UseBasicParsing -Uri '$url').Content"
    return 0
  fi
  echo "missing required command: curl or wget (or powershell.exe on Windows)" >&2
  exit 127
}

download_file() {
  local url="$1"
  local out="$2"

  mkdir -p "$(dirname "$out")"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --retry-delay 1 -o "$out" "$url"
    return 0
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -O "$out" "$url"
    return 0
  fi
  require_cmd powershell.exe
  powershell.exe -NoProfile -Command \
    "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri '$url' -OutFile '$out'"
}

extract_zip() {
  local zip_path="$1"
  local dest_dir="$2"

  mkdir -p "$dest_dir"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q -o "$zip_path" -d "$dest_dir"
    return 0
  fi
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command \
      "Expand-Archive -Path '$zip_path' -DestinationPath '$dest_dir' -Force"
    return 0
  fi
  echo "missing required command: unzip (or powershell.exe on Windows)" >&2
  exit 127
}

latest_blender_win64_zip_url() {
  local base="https://download.blender.org/release/"

  if [[ -n "${BLENDER_DOWNLOAD_URL:-}" ]]; then
    printf '%s\n' "${BLENDER_DOWNLOAD_URL}"
    return 0
  fi

  if [[ -n "${BLENDER_VERSION:-}" ]]; then
    local version="${BLENDER_VERSION}"
    local major_minor
    major_minor="$(printf '%s\n' "$version" | awk -F. '{print $1"."$2}')"
    printf '%s\n' "${base}Blender${major_minor}/blender-${version}-windows-x64.zip"
    return 0
  fi

  local index_html rel_dir rel_html file_name
  index_html="$(fetch_url "$base")"
  rel_dir="$(
    printf '%s\n' "$index_html" \
      | grep -oE 'Blender[0-9]+\\.[0-9]+/' \
      | sed 's#^Blender##; s#/$##' \
      | sort -V \
      | tail -n 1
  )"
  if [[ -z "$rel_dir" ]]; then
    echo "failed to discover Blender release directory from ${base}" >&2
    exit 1
  fi

  rel_html="$(fetch_url "${base}Blender${rel_dir}/")"
  file_name="$(
    printf '%s\n' "$rel_html" \
      | grep -oE 'blender-[0-9]+\\.[0-9]+\\.[0-9]+-windows-x64\\.zip' \
      | sed 's#^blender-##; s#-windows-x64\\.zip$##' \
      | sort -V \
      | tail -n 1
  )"
  if [[ -z "$file_name" ]]; then
    echo "failed to discover Blender windows-x64 zip in ${base}Blender${rel_dir}/" >&2
    exit 1
  fi

  printf '%s\n' "${base}Blender${rel_dir}/blender-${file_name}-windows-x64.zip"
}

main() {
  local force=0
  if [[ "${1:-}" == "--force" ]]; then
    force=1
  fi

  require_cmd awk basename grep sed sort tail

  local tmp_dir="${REPO_ROOT}/tmp/blender-win64"
  local blender_dir="${EXTERN_DIR}/blender-win64"

  mkdir -p "$tmp_dir" "$blender_dir"

  echo "Bootstrapping externals in ${EXTERN_DIR} ..."
  echo "  - ensuring: ${tmp_dir}"
  echo "  - ensuring: ${blender_dir}"

  local url zip_name zip_path
  url="$(latest_blender_win64_zip_url)"
  zip_name="$(basename "$url")"
  zip_path="${tmp_dir}/${zip_name}"

  if [[ $force -eq 0 && -f "$zip_path" ]]; then
    echo "  - Blender zip already present; skipping download: ${zip_path}"
  else
    echo "  - downloading Blender: ${url}"
    download_file "$url" "$zip_path"
  fi

  if compgen -G "${blender_dir}/blender-*-windows-x64/blender.exe" >/dev/null; then
    echo "  - Blender already extracted; leaving as-is."
  else
    echo "  - extracting: ${zip_path}"
    extract_zip "$zip_path" "$blender_dir"
  fi

  if ! compgen -G "${blender_dir}/blender-*-windows-x64/blender.exe" >/dev/null; then
    echo "Blender extraction did not produce blender.exe under ${blender_dir}" >&2
    exit 1
  fi

  echo "Done."
}

main "$@"
