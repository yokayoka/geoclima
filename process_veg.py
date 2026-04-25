"""
植生データ処理スクリプト
veg05mesh.csv と veg_gunraku.csv を統合し、亜高山帯針葉樹（オオシラビソ・トウヒ・コメツガ）の
メッシュデータを抽出する
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
    for row in reader:
        if len(row) >= 4:
            vegcode = row[1].strip()
            gunraku_name = row[2].strip()
            syuyaku_code = row[3].strip()
            gunraku_map[vegcode] = (gunraku_name, syuyaku_code)

print(f"群落コード数: {len(gunraku_map)}")

# 各樹種の群落コードを特定
def find_codes(keywords):
    codes = []
    for code, (name, syuyaku) in gunraku_map.items():
        if any(kw in name for kw in keywords):
            print(f"  発見: {code} -> {name} (集約: {syuyaku})")
            codes.append(code)
    return codes

print("\nオオシラビソ関連群落コード:")
aomori_codes = set(find_codes(['オオシラビソ', 'アオモリトドマツ']))

print("\nトウヒ関連群落コード:")
touhi_codes = set(find_codes(['トウヒ']))

print("\nコメツガ関連群落コード（亜高山帯限定）:")
# コメツガのうち亜高山帯（植生区分コード02）に属するものに限定
kometuga_codes = set()
with open('veg/veg_gunraku.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) >= 4:
            shokusei_ku = row[0].strip()  # 植生区分コード
            vegcode = row[1].strip()
            gunraku_name = row[2].strip()
            # 亜高山帯針葉樹林（02）または山地針葉樹林（04）のコメツガ
            if 'コメツガ' in gunraku_name and shokusei_ku in ('02', '04'):
                print(f"  発見: {vegcode} -> {gunraku_name} (区分: {shokusei_ku})")
                kometuga_codes.add(vegcode)


def meshcode_to_latlon(meshcode):
    """3次メッシュコードから中心緯度経度を計算"""
    mc = str(meshcode)
    if len(mc) != 8:
        return None, None
    p = int(mc[0:2])
    u = int(mc[2:4])
    q = int(mc[4])
    v = int(mc[5])
    r = int(mc[6])
    w = int(mc[7])
    lat = (p * 40 + q * 5 + r * 0.5 + 0.25) / 60
    lon = u + 100 + v * 0.125 + w * 0.0125 + 0.00625
    return lat, lon


# veg05mesh.csv を1パスで全樹種を抽出
aomori_meshes   = []
touhi_meshes    = []
kometuga_meshes = []
all_count = 0

print("\nveg05mesh.csv を読み込み中...")
with open('veg/veg05mesh.csv', 'r', encoding='shift_jis') as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if len(row) < 2:
            continue
        meshcode = row[0].strip().strip('"')
        vegcode  = row[1].strip().strip('"')
        all_count += 1

        target = None
        if vegcode in aomori_codes:
            target = aomori_meshes
        elif vegcode in touhi_codes:
            target = touhi_meshes
        elif vegcode in kometuga_codes:
            target = kometuga_meshes

        if target is not None:
            lat, lon = meshcode_to_latlon(meshcode)
            if lat is None:
                continue
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                target.append({
                    'meshcode': meshcode,
                    'vegcode': vegcode,
                    'name': gunraku_map[vegcode][0],
                    'lat': round(lat, 6),
                    'lon': round(lon, 6)
                })

print(f"veg05mesh.csv 総メッシュ数: {all_count}")
print(f"オオシラビソメッシュ数（wi.dat範囲内）: {len(aomori_meshes)}")
print(f"トウヒメッシュ数（wi.dat範囲内）: {len(touhi_meshes)}")
print(f"コメツガメッシュ数（wi.dat範囲内）: {len(kometuga_meshes)}")


def save_json(meshes, output_path, type_name, description):
    output = {
        'type': type_name,
        'description': description,
        'meshes': [[m['lat'], m['lon'], m['vegcode'], m['name']] for m in meshes]
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    print(f"出力: {output_path} ({len(meshes)} メッシュ)")


save_json(aomori_meshes,   'veg/aomori_todomatsu.json', 'aomori_todomatsu',
          'オオシラビソ（アオモリトドマツ）分布メッシュ（第3次メッシュ中心点）')
save_json(touhi_meshes,    'veg/touhi.json',            'touhi',
          'トウヒ（シラビソ−トウヒ群団）分布メッシュ（第3次メッシュ中心点）')
save_json(kometuga_meshes, 'veg/kometuga.json',         'kometuga',
          'コメツガ分布メッシュ（第3次メッシュ中心点）')
