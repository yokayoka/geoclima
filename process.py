#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平年値メッシュデータから暖かさの指数（温量指数）と年最深積雪を算出するスクリプト

データソース: 国土数値情報 平年値メッシュデータ G02-22（1991-2020年平年値）
対象範囲: 中部・東海・北陸・関東・東北（佐渡島以外の島嶼部を除く）

G02-22フォーマットにおける月平均気温フィールド（単位: 0.1°C）:
  G02_017: 1月  G02_020: 2月  G02_023: 3月
  G02_026: 4月  G02_029: 5月  G02_032: 6月
  G02_035: 7月  G02_038: 8月  G02_041: 9月
  G02_044:10月  G02_047:11月  G02_050:12月

年最深積雪フィールド（単位: cm）:
  G02_058: 年最深積雪
"""

import json
import os
import zipfile
import glob

# =====================================================================
# 設定
# =====================================================================
CLIMA_DIR = os.path.join(os.path.dirname(__file__), 'clima')
MON_TEMP_FILE = os.path.join(os.path.dirname(__file__), 'mon_temp.dat')
WI_FILE = os.path.join(os.path.dirname(__file__), 'wi.dat')
SNOW_FILE = os.path.join(os.path.dirname(__file__), 'snow.dat')

# 年最深積雪フィールド（単位: cm）
SNOW_FIELD = 'G02_058'

# G02-22フォーマットの月平均気温フィールド（0.1°C単位）
# 各月の月平均気温に対応するフィールド名
TEMP_FIELDS = [
    'G02_017',  # 1月 月平均気温
    'G02_020',  # 2月 月平均気温
    'G02_023',  # 3月 月平均気温
    'G02_026',  # 4月 月平均気温
    'G02_029',  # 5月 月平均気温
    'G02_032',  # 6月 月平均気温
    'G02_035',  # 7月 月平均気温
    'G02_038',  # 8月 月平均気温
    'G02_041',  # 9月 月平均気温
    'G02_044',  # 10月 月平均気温
    'G02_047',  # 11月 月平均気温
    'G02_050',  # 12月 月平均気温
]

# 暖かさの指数のしきい値
WI_THRESHOLD = 5.0

# 対象範囲（拡大後: 中部・東海 + 石川・富山・新潟・長野北部・群馬・栃木・
#          福島・茨城・神奈川・東京・千葉）
# 佐渡島は含む。それ以外の島嶼部は下記フィルターで概ね除外する。
BBOX_LON_MIN = 135.0
BBOX_LON_MAX = 142.0   # 岩手・青森太平洋岸まで含む
BBOX_LAT_MIN = 33.5
BBOX_LAT_MAX = 42.0    # 青森北端（大間崎 41.6°N）まで含む

# 伊豆諸島などの離島を除外するための地理的フィルター
# 条件: 緯度 < 34.85°N かつ 経度 > 139.1°E の地点は離島とみなして除外
# 効果: 伊豆大島(34.74°N,139.39°E)・利島・新島などを除外し、
#       伊豆半島(138.95°E以西)や房総半島(34.9°N以北)は保持
IZU_ISLAND_EXCLUDE_LAT = 34.85
IZU_ISLAND_EXCLUDE_LON = 139.1


# =====================================================================
# メッシュコードから3次メッシュ中心座標を算出する関数
# 参考: https://github.com/hni14/jismesh
# =====================================================================
def meshcode_to_center(meshcode):
    """
    標準地域メッシュ3次メッシュコードから中心座標を算出する。

    3次メッシュコードは8桁: PPQQRSTU
      PP: 1次メッシュ 緯度成分（南西端緯度 = PP / 1.5°）
      QQ: 1次メッシュ 経度成分（南西端経度 = QQ + 100°）
      R : 2次メッシュ 南北方向インデックス (0-7)
      S : 2次メッシュ 東西方向インデックス (0-7)
      T : 3次メッシュ 南北方向インデックス (0-9)
      U : 3次メッシュ 東西方向インデックス (0-9)

    グリッドサイズ:
      1次メッシュ: 緯度40分 (2/3°) × 経度1°
      2次メッシュ: 緯度5分 (1/12°) × 経度7.5分 (1/8°)
      3次メッシュ: 緯度30秒 (1/120°) × 経度45秒 (1/80°)

    引数:
      meshcode (str): 8桁の3次メッシュコード

    戻り値:
      (lon, lat): 中心座標（10進度）
    """
    code = str(meshcode).zfill(8)
    pp = int(code[0:2])  # 1次メッシュ緯度成分
    qq = int(code[2:4])  # 1次メッシュ経度成分
    r  = int(code[4])    # 2次メッシュ南北インデックス
    s  = int(code[5])    # 2次メッシュ東西インデックス
    t  = int(code[6])    # 3次メッシュ南北インデックス
    u  = int(code[7])    # 3次メッシュ東西インデックス

    # 南西端座標
    lat_sw = pp / 1.5 + r / 12.0 + t / 120.0
    lon_sw = (qq + 100) + s / 8.0 + u / 80.0

    # 中心座標（セルサイズの半分を加算）
    lat_center = lat_sw + 1.0 / 240.0
    lon_center = lon_sw + 1.0 / 160.0

    return lon_center, lat_center


# =====================================================================
# ステップ1〜3: ZIPを解凍してGeoJSONデータを結合
# ステップ4〜5: 経度・緯度を付与してmon_temp.datを作成
# =====================================================================
def create_mon_temp():
    """
    climaフォルダ内のG02-22 ZIPファイルを読み込み、
    3次メッシュコード・中心座標・月平均気温（°C）を mon_temp.dat に出力する。
    同時に年最深積雪（cm）を snow.dat に出力する。
    """
    zip_files = sorted(glob.glob(os.path.join(CLIMA_DIR, 'G02-22_*-jgd_GML.zip')))

    if not zip_files:
        print(f"エラー: {CLIMA_DIR} 内にZIPファイルが見つかりません。")
        return False

    print(f"{len(zip_files)} 件のZIPファイルを処理します...")

    records = []

    for zip_path in zip_files:
        zip_name = os.path.basename(zip_path)
        print(f"  処理中: {zip_name}")

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # GeoJSONファイルを検索
            geojson_name = None
            for name in zf.namelist():
                if name.endswith('.geojson'):
                    geojson_name = name
                    break

            if not geojson_name:
                print(f"  警告: {zip_name} にGeoJSONが見つかりません。スキップします。")
                continue

            with zf.open(geojson_name) as f:
                data = json.load(f)

        for feature in data['features']:
            props = feature['properties']
            meshcode = str(props.get('G02_001', ''))

            if len(meshcode) != 8:
                continue

            # メッシュコードから中心座標を算出
            lon, lat = meshcode_to_center(meshcode)

            # バウンディングボックスによる対象範囲フィルタリング
            if not (BBOX_LON_MIN <= lon <= BBOX_LON_MAX and
                    BBOX_LAT_MIN <= lat <= BBOX_LAT_MAX):
                continue

            # 伊豆諸島などの離島を除外
            # （緯度 < 34.85°N かつ 経度 > 139.1°E → 離島とみなす）
            if lat < IZU_ISLAND_EXCLUDE_LAT and lon > IZU_ISLAND_EXCLUDE_LON:
                continue

            # 月平均気温を取得（0.1°C → °C に変換）
            temps = []
            valid = True
            for field in TEMP_FIELDS:
                val = props.get(field)
                if val is None:
                    valid = False
                    break
                # 欠損値（999999 または -9999 等）を除外
                if isinstance(val, (int, float)) and (val >= 999990 or val < -900):
                    valid = False
                    break
                temps.append(int(val) / 10.0)

            if not valid:
                continue

            # 年最深積雪を取得（cm）
            snow_raw = props.get(SNOW_FIELD)
            snow = None
            if snow_raw is not None and isinstance(snow_raw, (int, float)):
                if not (snow_raw >= 999990 or snow_raw < -900):
                    snow = int(round(snow_raw))

            records.append((meshcode, lon, lat, temps, snow))

    print(f"合計 {len(records)} メッシュのデータを出力します...")

    # mon_temp.dat に出力（フィールドセパレーター: 半角スペース）
    with open(MON_TEMP_FILE, 'w', encoding='utf-8') as f:
        # ヘッダー行
        header = 'meshcode x y t1 t2 t3 t4 t5 t6 t7 t8 t9 t10 t11 t12'
        f.write(header + '\n')
        for meshcode, lon, lat, temps, snow in records:
            temp_str = ' '.join(f'{t:.1f}' for t in temps)
            f.write(f'{meshcode} {lon:.8f} {lat:.8f} {temp_str}\n')

    print(f"mon_temp.dat を作成しました: {MON_TEMP_FILE}")

    # snow.dat に出力
    snow_records = [(m, x, y, s) for m, x, y, t, s in records if s is not None]
    print(f"年最深積雪 {len(snow_records)} メッシュのデータを出力します...")
    with open(SNOW_FILE, 'w', encoding='utf-8') as f:
        f.write('meshcode x y snow\n')
        for meshcode, lon, lat, snow in snow_records:
            f.write(f'{meshcode} {lon:.8f} {lat:.8f} {snow}\n')
    print(f"snow.dat を作成しました: {SNOW_FILE}")

    return True


# =====================================================================
# ステップ6: 暖かさの指数（温量指数）を算出して wi.dat を作成
# =====================================================================
def create_wi():
    """
    mon_temp.dat を読み込み、暖かさの指数（WI）を算出して wi.dat に出力する。

    暖かさの指数 WI = Σ(Ti - threshold) for Ti > threshold
    しきい値 = 5°C
    """
    if not os.path.exists(MON_TEMP_FILE):
        print(f"エラー: {MON_TEMP_FILE} が存在しません。先に create_mon_temp() を実行してください。")
        return False

    records_wi = []

    with open(MON_TEMP_FILE, 'r', encoding='utf-8') as f:
        # ヘッダー行を読み飛ばし
        header = f.readline()

        for line in f:
            parts = line.strip().split(' ')
            if len(parts) < 15:
                continue

            meshcode = parts[0]
            x = float(parts[1])  # 経度
            y = float(parts[2])  # 緯度
            temps = [float(parts[i]) for i in range(3, 15)]

            # 暖かさの指数を算出
            wi = sum(max(t - WI_THRESHOLD, 0.0) for t in temps)
            records_wi.append((meshcode, x, y, wi))

    print(f"{len(records_wi)} メッシュの暖かさの指数を算出しました。")

    # wi.dat に出力（フィールドセパレーター: 半角スペース）
    with open(WI_FILE, 'w', encoding='utf-8') as f:
        f.write('meshcode x y wi\n')
        for meshcode, x, y, wi in records_wi:
            f.write(f'{meshcode} {x:.8f} {y:.8f} {wi:.1f}\n')

    print(f"wi.dat を作成しました: {WI_FILE}")

    # 統計情報を表示
    wi_values = [r[3] for r in records_wi]
    print(f"WI 統計: 最小={min(wi_values):.1f}, 最大={max(wi_values):.1f}, "
          f"平均={sum(wi_values)/len(wi_values):.1f}")

    return True


# =====================================================================
# メイン処理
# =====================================================================
if __name__ == '__main__':
    print("=== 暖かさの指数・年最深積雪 算出スクリプト ===")
    print()

    print("【ステップ1-5】月平均気温データ・年最深積雪データの作成...")
    if create_mon_temp():
        print()
        print("【ステップ6】暖かさの指数の算出...")
        create_wi()
        print()
        print("処理が完了しました。")
    else:
        print("処理が中断されました。")
