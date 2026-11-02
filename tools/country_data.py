"""Make src/main/resources/country/<country>: a country version's game files that differ from BCU's.

BCU's game data is the Japanese game's (version 15.5 in core 0.7.20.0's asset packs). The game's other versions
(English, Taiwanese, Korean) differ in places, and newer versions change some files. This compares one country's
DataLocal (from fieryhenry's BCData, see SOURCE) with BCU's packs, file by file, and copies the files that differ
into src/main/resources/country/<country>/ (same paths as in BCU's packs, without "./org/"), listed in files.json
there. BCU puts the chosen country's files into the core's file tree (io/CountryData.java). (The same tool as in
BCU KR for Android, books4jy-art/BCU-Android-Update, which writes app/src/main/assets/<country>.)

Only files the app can use safely are taken:
- stage files (./org/stage/...), when every enemy they name and their background exist in BCU and the enemy base
  is BCU's (a stage of a newer version may need things BCU's packs don't have yet);
- cat stats (./org/unit/NNN/unitNNN.csv; the game numbers these from 1, BCU from 0) with the same number of forms
  as BCU's (not a 4th form BCU has no pictures for), and not the placeholder the game ships for cats it hasn't
  released or has removed (a copy of the basic Cat; e.g. Japan 15.6 for finished collaborations);
- enemy stats (t_unit.csv), cat prices and levels (unitbuy.csv, unitlevel.csv), read row by row: only when the
  file has a row for every cat or enemy BCU has;
- talents (SkillAcquisition.csv) when they only use talent types core 0.7.20.0 knows; orb slots
  (equipmentslot.csv); combos (NyancomboData.csv) when they only name cats BCU has.
Everything else (event schedules, missions, gacha...) isn't used by BCU's battles and stays BCU's.

Usage: python3 tools/country_data.py COUNTRY [--version 15.6.0] [--keep-images]
  COUNTRY: en, jp, kr or tw. --keep-images keeps the pictures already listed (./org/img/..., e.g. the Korean enemy
  bases from the Korean server packs), which aren't in DataLocal.
Needs Python 3 with `cryptography`. Downloads are cached in tools/.cache/.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import struct
import sys
import time
import urllib.request

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(ROOT, "tools", ".cache")
SOURCE = ("https://git.battlecatsmodding.org/fieryhenry/BCData/{kind}/commit/"
          "2a49665d0135283dc5c86e8d5825bb120b2849d7/game_data/{country}/{version}/DataLocal")

# BCU's asset packs (as tools/build_index.py of the Battle Cats Emulator website, and the core's AssetLoader)
UPDATE_URL = "https://raw.githubusercontent.com/battlecatsultimate/bcu-page/master/api/updateInfo.json"
ASSET_URL = "https://raw.githubusercontent.com/battlecatsultimate/bcu-assets/master/assets/{id}.asset.bcuzip"
CORE_VER = "0.7.20.0"  # AssetLoader.CORE_VER of the core this app uses
HEAD = hashlib.md5(b"battlecatsultimate").digest()
TALENT_TYPES = 70  # Data.PC_CORRES in core 0.7.20.0 knows talent types 0-69

SEQUENTIAL = {"t_unit.csv": "enemy", "unitbuy.csv": "unit", "unitlevel.csv": "unit"}
DATA_FILES = {"t_unit.csv", "unitbuy.csv", "unitlevel.csv", "SkillAcquisition.csv", "equipmentslot.csv",
              "NyancomboData.csv"}


def get_ver(v: str) -> int:
    ans = 0
    for n in re.findall(r"\d+", v):
        ans = ans * 100 + int(n)
    return ans


def fetch(url: str, start: int | None = None, length: int | None = None, tries: int = 6) -> bytes:
    headers = {"User-Agent": "bcu-kr-country-data"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{start + length - 1}"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
                data = r.read()
            if start is not None and len(data) != length:
                raise IOError(f"short read {len(data)} != {length}")
            return data
        except Exception as e:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            print(f"  retry {url} ({e})", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise AssertionError


def regulate(n: int) -> int:
    return n if n % 16 == 0 else (n | 0xF) + 1


def decrypt(key: bytes, data: bytes) -> bytes:
    d = Cipher(algorithms.AES(key), modes.CBC(HEAD)).decryptor()
    return d.update(data) + d.finalize()


def read_pack(asset_id: str) -> dict:
    url = ASSET_URL.format(id=asset_id)
    zh = fetch(url, 0, 36)
    key = zh[16:32]
    (dn,) = struct.unpack("<i", zh[32:36])
    desc = json.loads(decrypt(key, fetch(url, 36, regulate(dn)))[:dn].decode("utf-8"))
    return {"id": desc["desc"]["id"], "ver": desc["desc"].get("BCU_VERSION", "0.0.0"), "url": url, "key": key,
            "base": 36 + regulate(dn), "files": desc["files"]}


def bcu_index() -> dict[str, tuple]:
    """path -> (pack url, key, start, size) for every file in BCU's packs (later packs win, as AssetLoader)."""
    cached = os.path.join(CACHE, f"bcu-index-{CORE_VER}.json")
    if os.path.exists(cached):
        with open(cached) as fh:
            return {p: (u, bytes.fromhex(k), s, n) for p, (u, k, s, n) in json.load(fh).items()}
    info = json.loads(fetch(UPDATE_URL))
    assets = [a["id"] for a in info["assets"] if a["type"] == "core" and get_ver(a["ver"]) <= get_ver(CORE_VER)]
    with cf.ThreadPoolExecutor(8) as ex:
        packs = dict(zip(assets, ex.map(read_pack, assets)))
    zips = {}
    for asset_id in sorted(packs):
        if get_ver(packs[asset_id]["ver"]) <= get_ver(CORE_VER):
            zips[packs[asset_id]["id"]] = packs[asset_id]
    index = {}
    for zid in sorted(zips):
        z = zips[zid]
        for fd in z["files"]:
            index[fd["path"]] = (z["url"], z["key"], z["base"] + fd["offset"], fd["size"])
    os.makedirs(CACHE, exist_ok=True)
    with open(cached, "w") as fh:
        json.dump({p: (u, k.hex(), s, n) for p, (u, k, s, n) in index.items()}, fh)
    return index


def bcu_file(index: dict, path: str) -> bytes:
    url, key, start, size = index[path]
    return decrypt(key, fetch(url, start, regulate(size)))[:size]


def country_names(country: str, version: str) -> list[str]:
    html = fetch(SOURCE.format(kind="src", country=country, version=version)).decode("utf-8", "replace")
    return sorted(set(re.findall(r'title="([^"/]+\.(?:csv|tsv|json))"', html)))


def country_file(country: str, version: str, name: str) -> bytes:
    path = os.path.join(CACHE, f"{country}-{version}", name)
    if not os.path.exists(path):
        data = fetch(SOURCE.format(kind="raw", country=country, version=version) + "/" + name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(data)
    with open(path, "rb") as fh:
        return fh.read()


def rows(b: bytes) -> list[str]:
    """Data lines without comments, trailing commas and blank lines."""
    out = []
    for line in b.decode("utf-8", "replace").replace("\r", "").split("\n"):
        line = line.split("//")[0].strip().rstrip(",").strip()
        if line:
            out.append(line)
    return out


def ints(line: str) -> list[int]:
    return [int(x) if re.fullmatch(r"-?\d+", x.strip()) else 0 for x in line.split(",")]


def stage_refs(b: bytes) -> tuple[int | None, int, set[int]] | None:
    """(enemy base id or None, background id, enemy ids) of a stage file (Stage.java's layout), or None."""
    lines = [line.split("//")[0].strip() for line in b.decode("utf-8", "replace").replace("\r", "").split("\n")]
    lines = [line for line in lines if line]
    if len(lines) < 2:
        return None
    first = [x for x in lines[0].split(",") if x.strip() != ""]
    castle, params, rest = (None, lines[0], lines[1:]) if len(first) >= 7 else (ints(lines[0])[0], lines[1], lines[2:])
    p = ints(params)
    if len(p) < 7:
        return None
    enemies = set()
    for line in rest:
        if not line[:1].isdigit() or line.startswith("0,"):
            break
        enemies.add(ints(line)[0] - 2)
    return castle, p[4], enemies


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("country", choices=["en", "jp", "kr", "tw"])
    ap.add_argument("--version", default="15.6.0")
    ap.add_argument("--keep-images", action="store_true")
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "src", "main", "resources", "country", args.country)

    index = bcu_index()
    n_units = len({p.split("/")[3] for p in index if re.match(r"\./org/unit/\d{3}/", p)})
    n_enemies = len({p.split("/")[3] for p in index if re.match(r"\./org/enemy/\d{3}/", p)})
    n_bgs = len(rows(bcu_file(index, "./org/battle/bg.csv"))) - 1
    n_souls = len({p.split("/")[4] for p in index if re.match(r"\./org/battle/soul/\d{3}/", p)})
    print(f"BCU: {n_units} cats, {n_enemies} enemies, {n_bgs} backgrounds, {n_souls} souls, {len(index)} files")

    names = country_names(args.country, args.version)
    by_name: dict[str, list[str]] = {}
    for p in index:
        by_name.setdefault(p.rsplit("/", 1)[1], []).append(p)

    # BCU path -> the country's file name
    pairs: dict[str, str] = {}
    for name in names:
        m = re.fullmatch(r"unit(\d{3})\.csv", name)
        if m:  # the game's unit001.csv is BCU's cat 000
            i = int(m.group(1)) - 1
            p = f"./org/unit/{i:03d}/unit{i:03d}.csv"
            if p in index:
                pairs[p] = name
            continue
        for p in by_name.get(name, []):
            if p.startswith("./org/stage/") or (p.startswith("./org/data/") and name in DATA_FILES):
                pairs[p] = name
    print(f"{args.country} {args.version}: {len(names)} files, {len(pairs)} to compare")

    placeholder = rows(country_file(args.country, args.version, "unit001.csv")) if "unit001.csv" in names else None

    def check(p: str) -> tuple[str, str | None]:
        """(path, why it's skipped / None to take it / '' when it's the same as BCU's)."""
        mine = country_file(args.country, args.version, pairs[p])
        theirs = bcu_file(index, p)
        a, b = rows(mine), rows(theirs)
        if a == b:
            return p, ""
        name = p.rsplit("/", 1)[1]
        if p.startswith("./org/stage/") and not name.startswith("stage"):
            # a map's file (MapStageData...: one row per stage, crowns, ...): an extra row would be a stage BCU
            # doesn't have
            if len(a) != len(b):
                return p, f"{len(a)} rows, BCU has {len(b)}"
            return p, None
        if p.startswith("./org/stage/"):
            ra, rb = stage_refs(mine), stage_refs(theirs)
            if ra is None or rb is None:
                return p, "unreadable stage file"
            if ra[0] != rb[0]:
                return p, f"another enemy base ({ra[0]})"
            if not 0 <= ra[1] < n_bgs:
                return p, f"background {ra[1]} not in BCU"
            if any(not 0 <= e < n_enemies for e in ra[2] if e != -2):
                return p, "names enemies BCU doesn't have"
            return p, None
        if p.startswith("./org/unit/"):
            if len(a) != len(b):
                return p, f"{len(a)} forms, BCU has {len(b)}"
            if placeholder is not None and not p.endswith("/unit000.csv") and \
                    [ints(r)[:15] for r in a] == [ints(r)[:15] for r in placeholder[:len(a)]]:
                return p, "a placeholder in this version (cat not released yet, or removed after a collaboration)"
            for r in a:
                v = ints(r)
                if len(v) > 110 and v[110] >= n_units:  # spirit (DataUnit: ints[110])
                    return p, f"spirit {v[110]} is a cat BCU doesn't have"
                if len(v) > 67 and not -1 <= v[67] < n_souls:  # death soul (ints[67])
                    return p, f"soul {v[67]} not in BCU"
            return p, None
        if name in SEQUENTIAL:
            need = (n_units if SEQUENTIAL[name] == "unit" else n_enemies) + (2 if name == "t_unit.csv" else 0)
            if len(a) < need:
                return p, f"{len(a)} rows, BCU needs {need}"
            if a[:need] == b[:need]:
                return p, ""  # only rows for cats or enemies BCU doesn't have
            if name == "t_unit.csv":
                for r in a[2:need]:
                    v = ints(r)
                    if len(v) > 54 and not -1 <= v[54] < n_souls:  # death soul (DataEnemy: ints[54])
                        return p, f"soul {v[54]} not in BCU"
            return p, None
        if name == "SkillAcquisition.csv":
            for line in a[1:]:
                v = ints(line)
                for t in range(8):
                    if 2 + t * 14 < len(v) and v[2 + t * 14] >= TALENT_TYPES:
                        return p, f"talent type {v[2 + t * 14]} unknown to core {CORE_VER}"
            return p, None
        if name == "NyancomboData.csv":
            for line in a:
                v = ints(line)
                if len(line) >= 20 and any(v[3 + i * 2] >= n_units for i in range(5) if 3 + i * 2 < len(v)):
                    return p, "names cats BCU doesn't have"
            return p, None
        return p, None

    with cf.ThreadPoolExecutor(16) as ex:
        results = list(ex.map(check, sorted(pairs)))
    take = [p for p, why in results if why is None]
    skipped = [(p, why) for p, why in results if why]
    print(f"{len(take)} files differ and are used, {len(skipped)} differ but are skipped:")
    for p, why in skipped[:60]:
        print(f"  skip {p}: {why}")
    if len(skipped) > 60:
        print(f"  ... and {len(skipped) - 60} more")

    listing_path = os.path.join(out_dir, "files.json")
    keep = {}
    if args.keep_images and os.path.exists(listing_path):
        with open(listing_path) as fh:
            keep = {p: n for p, n in json.load(fh).items() if p.startswith("./org/img/")}
    if os.path.isdir(out_dir):
        for dirpath, _, fnames in os.walk(out_dir, topdown=False):
            for f in fnames:
                full = os.path.join(dirpath, f)
                rel = "./org/" + os.path.relpath(full, out_dir).replace(os.sep, "/")
                if rel not in keep:
                    os.remove(full)
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
    listing = dict(keep)
    for p in take:
        data = country_file(args.country, args.version, pairs[p])
        dest = os.path.join(out_dir, p[len("./org/"):])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as fh:
            fh.write(data)
        listing[p] = len(data)
    os.makedirs(out_dir, exist_ok=True)
    with open(listing_path, "w") as fh:
        json.dump(dict(sorted(listing.items())), fh, indent=0)
    kinds: dict[str, int] = {}
    for p in listing:
        k = "cat stats" if p.startswith("./org/unit/") else p.split("/")[2] if not p.startswith("./org/data/") else p.rsplit("/", 1)[1]
        kinds[k] = kinds.get(k, 0) + 1
    print(f"-> {out_dir}: {len(listing)} files {kinds}")


if __name__ == "__main__":
    main()
