"""
植生データ処理スクリプト
veg05mesh.csv と veg_gunraku.csv を統合し、オオシラビソメッシュデータを抽出する
"""
import csv
import json

# wi.dat の範囲を取得（lat/lon の min/max）
wi_lats = []
wi_lons = []
with open('wi.dat', 'r', encoding='utf-8') as f:
    next(f)  # ヘッダースキップ
    for line in f:
        parts = line.strip().split()
        if len(parts) >= 3:
            wi_lons.append(float(parts[1]))
            wi_lats.append(float(parts[2]))

lat_min, lat_max = min(wi_lats), max(wi_lats)
lon_min, lon_max = min(wi_lons), max(wi_lons)
print(f"wi.dat 範囲: lat {lat_min:.4f} - {lat_max:.4f}, lon {lon_min:.4f} - {lon_max:.4f}")

# veg_gunraku.csv を読み込み（群落コード -> 群落名 のマッピング）
gunraku_map = {}  # vegcode -> (gunraku_name, syuyaku_code)
with open('veg/veg_gunraku.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"veg_gunraku.csv ヘッダー: {header}")
    for row in reader:
        if len(row) >= 4:
            # アリア群落コード, 群落コード, 群落名, 集約群落コード
            vegcode = row[1].strip()
            gunraku_name = row[2].strip()
            syuyaku_code = row[3].strip()
            gunraku_map[vegcode] = (gunraku_name, syuyaku_code)

print(f"群落コード数: {len(gunraku_map)}")

# オオシラビソを含む群落コードを特定
aomori_codes = []
for code, (name, syuyaku) in gunraku_map.items():
    if 'オオシラビソ' in name or 'アオモリトドマツ' in name:
        print(f"  発見: {code} -> {name} (集約: {syuyaku})")
        aomori_codes.append(code)

print(f"オオシラビソ関連群落コード: {aomori_codes}")

# veg05mesh.csv を読み込みフィルタリング
def meshcode_to_latlon(meshcode):
    """3次メッシュコードから中心緯度経度を計算"""
    mc = str(meshcode)
    if len(mc) != 8:
        return None, None

    # 1次メッシュ
    p = int(mc[0:2])
    u = int(mc[2:4])
    # 2次メッシュ
    q = int(mc[4])
    v = int(mc[5])
    # 3次メッシュ
    r = int(mc[6])
    w = int(mc[7])

    lat = (p * 40 + q * 5 + r * 0.5 + 0.25) / 60
    lon = u + 100 + v * 0.125 + w * 0.0125 + 0.00625
    return lat, lon

aomori_meshes = []
all_count = 0
with open('veg/veg05mesh.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"\nveg05mesh.csv ヘッダー: {header}")

    for row in reader:
        if len(row) < 2:
            continue
        meshcode = row[0].strip().strip('"')
        vegcode = row[1].strip().strip('"')
        all_count += 1

        # オオシラビソコードかチェック
        if vegcode in aomori_codes:
            lat, lon = meshcode_to_latlon(meshcode)
            if lat is None:
                continue
            # wi.dat の範囲内かチェック
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                aomori_meshes.append({
                    'meshcode': meshcode,
                    'vegcode': vegcode,
                    'name': gunraku_map[vegcode][0],
                    'lat': round(lat, 6),
                    'lon': round(lon, 6)
                })

print(f"\nveg05mesh.csv 総メッシュ数: {all_count}")
print(f"オオシラビソメッシュ数（wi.dat範囲内）: {len(aomori_meshes)}")
if aomori_meshes:
    print("サンプル:", aomori_meshes[:3])

# JSON として保存
output = {
    'type': 'aomori_todomatsu',
    'description': 'オオシラビソ（アオモリトドマツ）分布メッシュ（第3次メッシュ中心点）',
    'meshes': [[m['lat'], m['lon'], m['vegcode'], m['name']] for m in aomori_meshes]
}

with open('veg/aomori_todomatsu.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

print(f"\n出力: veg/aomori_todomatsu.json ({len(aomori_meshes)} メッシュ)")
