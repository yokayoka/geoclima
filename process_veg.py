"""
植生データ処理スクリプト
veg05mesh.csv と veg_gunraku.csv を統合し、以下の群落を抽出する:
  オオシラビソ・トウヒ・コメツガ・ブナ・イヌブナ・ハイマツ・ミヤマナラ（偽高山帯）
"""
import csv
import json

# wi.dat の範囲を取得
wi_lats, wi_lons = [], []
with open('wi.dat', 'r', encoding='utf-8') as f:
    next(f)
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3:
            wi_lons.append(float(parts[1]))
            wi_lats.append(float(parts[2]))
lat_min, lat_max = min(wi_lats), max(wi_lats)
lon_min, lon_max = min(wi_lons), max(wi_lons)
print(f"wi.dat 範囲: lat {lat_min:.4f} - {lat_max:.4f}, lon {lon_min:.4f} - {lon_max:.4f}")

# veg_gunraku.csv 読み込み（vegcode -> (name, syuyaku, ku)）
gunraku_map = {}
with open('veg/veg_gunraku.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) >= 4:
            ku      = row[0].strip()
            vegcode = row[1].strip()
            name    = row[2].strip()
            syuyaku = row[3].strip()
            gunraku_map[vegcode] = (name, syuyaku, ku)

print(f"群落コード数: {len(gunraku_map)}")

# ── 樹種別コードセットの定義 ──────────────────────────────────
# オオシラビソ（アオモリトドマツ）
aomori_codes = {c for c, (n, s, k) in gunraku_map.items()
                if 'オオシラビソ' in n or 'アオモリトドマツ' in n}

# トウヒ
touhi_codes = {c for c, (n, s, k) in gunraku_map.items() if 'トウヒ' in n}

# コメツガ（亜高山帯・山地帯）
kometuga_codes = {c for c, (n, s, k) in gunraku_map.items()
                  if 'コメツガ' in n and k in ('02', '04')}

# ブナ（集約コード 401xx / 402xx / 40214 / 50100 系、イヌブナ・オオシラビソ除く）
BUNA_SYUYAKU = {'40100','40101','40102','40103','40104',
                '40200','40201','40202','40204','40214','50100'}
buna_codes = ({c for c, (n, s, k) in gunraku_map.items() if s in BUNA_SYUYAKU}
              - aomori_codes)

# イヌブナ
inubuna_codes = {c for c, (n, s, k) in gunraku_map.items() if 'イヌブナ' in n}

# ハイマツ（名前に「ハイマツ」を含む群落のみ）
haimatsu_codes = {c for c, (n, s, k) in gunraku_map.items() if 'ハイマツ' in n}

# ミヤマナラ・偽高山帯（集約コード 21300 系）
miyamana_codes = {c for c, (n, s, k) in gunraku_map.items() if s == '21300'}

for label, codes in [
    ('オオシラビソ', aomori_codes), ('トウヒ', touhi_codes), ('コメツガ', kometuga_codes),
    ('ブナ', buna_codes), ('イヌブナ', inubuna_codes),
    ('ハイマツ', haimatsu_codes), ('ミヤマナラ', miyamana_codes),
]:
    print(f"  {label}: {len(codes)} codes")

# ── veg05mesh.csv を1パスで抽出 ─────────────────────────────────
species_map = {}
for grp, codes in [
    ('aomori',   aomori_codes),
    ('touhi',    touhi_codes),
    ('kometuga', kometuga_codes),
    ('buna',     buna_codes),
    ('inubuna',  inubuna_codes),
    ('haimatsu', haimatsu_codes),
    ('miyamana', miyamana_codes),
]:
    for c in codes:
        species_map[c] = grp

meshes = {grp: [] for grp in ['aomori','touhi','kometuga','buna','inubuna','haimatsu','miyamana']}


def meshcode_to_latlon(mc):
    mc = str(mc)
    if len(mc) != 8:
        return None, None
    p, u = int(mc[0:2]), int(mc[2:4])
    q, v = int(mc[4]),   int(mc[5])
    r, w = int(mc[6]),   int(mc[7])
    lat = (p * 40 + q * 5 + r * 0.5 + 0.25) / 60
    lon = u + 100 + v * 0.125 + w * 0.0125 + 0.00625
    return lat, lon


print("\nveg05mesh.csv を読み込み中...")
all_count = 0
with open('veg/veg05mesh.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) < 2:
            continue
        meshcode = row[0].strip().strip('"')
        vegcode  = row[1].strip().strip('"')
        all_count += 1
        grp = species_map.get(vegcode)
        if grp is None:
            continue
        lat, lon = meshcode_to_latlon(meshcode)
        if lat is None:
            continue
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            meshes[grp].append({
                'lat': round(lat, 6), 'lon': round(lon, 6),
                'vegcode': vegcode,
                'name': gunraku_map[vegcode][0],
            })

print(f"veg05mesh.csv 総メッシュ数: {all_count}")
for grp, lst in meshes.items():
    print(f"  {grp}: {len(lst)} メッシュ（wi.dat 範囲内）")

# ── JSON 出力 ──────────────────────────────────────────────────
OUTPUTS = {
    'aomori':   ('veg/aomori_todomatsu.json', 'aomori_todomatsu',
                 'オオシラビソ（アオモリトドマツ）分布メッシュ'),
    'touhi':    ('veg/touhi.json',    'touhi',    'トウヒ（シラビソ−トウヒ群団）分布メッシュ'),
    'kometuga': ('veg/kometuga.json', 'kometuga', 'コメツガ分布メッシュ'),
    'buna':     ('veg/buna.json',     'buna',     'ブナ林分布メッシュ'),
    'inubuna':  ('veg/inubuna.json',  'inubuna',  'イヌブナ林分布メッシュ'),
    'haimatsu': ('veg/haimatsu.json', 'haimatsu', 'ハイマツ分布メッシュ'),
    'miyamana': ('veg/miyamana.json', 'miyamana', 'ミヤマナラ等偽高山帯群落分布メッシュ'),
}

for grp, (path, type_name, desc) in OUTPUTS.items():
    data = {
        'type': type_name,
        'description': desc,
        'meshes': [[m['lat'], m['lon'], m['vegcode'], m['name']] for m in meshes[grp]]
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"出力: {path} ({len(meshes[grp])} メッシュ)")
