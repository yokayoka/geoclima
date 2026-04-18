#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国土数値情報 G02-22 平年値メッシュデータ ダウンロードスクリプト

対象拡大（新規ダウンロード）:
  石川、富山、岐阜北部、新潟、長野北部、群馬、栃木、
  福島、茨城、神奈川、東京、千葉に重なる1次メッシュ

ダウンロード先: clima/ フォルダ
URL形式: https://nlftp.mlit.go.jp/ksj/gml/data/G02/G02-22/G02-22_{code}-jgd_GML.zip
"""

import os
import sys
import urllib.request
import urllib.error
import time

# =====================================================================
# 設定
# =====================================================================
CLIMA_DIR = os.path.join(os.path.dirname(__file__), 'clima')
BASE_URL = 'https://nlftp.mlit.go.jp/ksj/gml/data/G02/G02-22'

# 対象拡大に必要な新規1次メッシュコード
# PP=54 (lat 36.0-36.67°N): 富山・長野・群馬・栃木・茨城
# PP=55 (lat 36.67-37.33°N): 石川・富山・新潟・長野・群馬・栃木・福島・茨城
# PP=56 (lat 37.33-38.00°N): 石川北部・新潟・福島
# 東北6県追加分（以前の分は既存ファイルチェックでスキップ）
NEW_MESH_CODES = [
    # PP=54 (lat 36.00-36.67°N): 富山・長野・群馬・栃木・茨城
    5437, 5438, 5439, 5440,
    # PP=55 (lat 36.67-37.33°N): 石川・富山・新潟・長野・群馬・栃木・福島・茨城
    5536, 5537, 5538, 5539, 5540,
    # PP=56 (lat 37.33-38.00°N): 石川北部・新潟・山形南部・宮城南部・福島
    5636, 5637, 5638, 5639, 5640,
    # PP=57 (lat 38.00-38.67°N): 新潟北部・佐渡島・山形・宮城南部・福島北部
    5738, 5739, 5740, 5741,
    # PP=58 (lat 38.67-39.33°N): 山形・宮城・秋田南部・岩手南部・福島北端
    5839, 5840, 5841,
    # PP=59 (lat 39.33-40.00°N): 秋田・宮城北部・岩手中部
    5939, 5940, 5941,
    # PP=60 (lat 40.00-40.67°N): 秋田北部・青森南部・岩手北部
    6039, 6040, 6041,
    # PP=61 (lat 40.67-41.33°N): 青森中部
    6139, 6140, 6141,
    # PP=62 (lat 41.33-42.00°N): 青森北部（下北半島・津軽半島）
    6240, 6241,
]


def download_mesh(code):
    """
    指定した1次メッシュコードのZIPファイルをダウンロードする。

    戻り値:
      'ok'       : 正常ダウンロード
      'exists'   : 既にファイルが存在
      'not_found': HTTP 404（そのメッシュのデータなし）
      'error'    : その他エラー
    """
    filename = f'G02-22_{code}-jgd_GML.zip'
    dest_path = os.path.join(CLIMA_DIR, filename)

    if os.path.exists(dest_path):
        return 'exists'

    url = f'{BASE_URL}/{filename}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Python urllib)',
        'Referer': 'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-G02.html',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()

        with open(dest_path, 'wb') as f:
            f.write(data)

        size_kb = len(data) // 1024
        print(f'  ダウンロード完了: {filename} ({size_kb} KB)')
        return 'ok'

    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f'  スキップ (404): {filename} (データなし)')
            return 'not_found'
        else:
            print(f'  エラー HTTP {e.code}: {filename}')
            return 'error'

    except urllib.error.URLError as e:
        print(f'  接続エラー: {filename} - {e.reason}')
        return 'error'

    except Exception as e:
        print(f'  予期しないエラー: {filename} - {e}')
        return 'error'


def main():
    """メイン処理"""
    print('=== G02-22 追加メッシュデータ ダウンロード ===')
    print(f'保存先: {CLIMA_DIR}')
    print(f'対象メッシュ数: {len(NEW_MESH_CODES)} 件')
    print()

    results = {'ok': [], 'exists': [], 'not_found': [], 'error': []}

    for i, code in enumerate(NEW_MESH_CODES, 1):
        print(f'[{i:2d}/{len(NEW_MESH_CODES)}] メッシュ {code} ...')
        status = download_mesh(code)
        results[status].append(code)

        # サーバー負荷軽減のため少し待機
        if status == 'ok':
            time.sleep(1.0)

    print()
    print('=== 結果サマリー ===')
    print(f'  新規ダウンロード : {len(results["ok"])} 件 {results["ok"]}')
    print(f'  既存スキップ     : {len(results["exists"])} 件')
    print(f'  データなし(404)  : {len(results["not_found"])} 件 {results["not_found"]}')
    print(f'  エラー           : {len(results["error"])} 件 {results["error"]}')

    if results['error']:
        print()
        print('注意: エラーが発生したメッシュがあります。')
        print('手動ダウンロード先:')
        print('  https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-G02.html')
        print('  → G02-22 の各メッシュZIPを clima/ フォルダに保存してください。')


if __name__ == '__main__':
    main()
