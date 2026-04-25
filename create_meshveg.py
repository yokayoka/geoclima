#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wi.dat / snow.dat / veg/*.json から
Leaflet Web地図（meshveg.html）を生成するスクリプト

wi.html に加えてオオシラビソ・トウヒ・コメツガの植生レイヤーを追加。
"""

import os
import json

WI_FILE       = os.path.join(os.path.dirname(__file__), 'wi.dat')
SNOW_FILE     = os.path.join(os.path.dirname(__file__), 'snow.dat')
VEG_AOMORI    = os.path.join(os.path.dirname(__file__), 'veg', 'aomori_todomatsu.json')
VEG_TOUHI     = os.path.join(os.path.dirname(__file__), 'veg', 'touhi.json')
VEG_KOMETUGA  = os.path.join(os.path.dirname(__file__), 'veg', 'kometuga.json')
HTML_FILE     = os.path.join(os.path.dirname(__file__), 'meshveg.html')

CELL_HEIGHT = 1.0 / 120.0
CELL_WIDTH  = 1.0 / 80.0


def load_wi_data():
    records = []
    with open(WI_FILE, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                records.append([round(float(parts[2]), 6), round(float(parts[1]), 6), round(float(parts[3]), 1)])
    return records


def load_snow_data():
    records = []
    with open(SNOW_FILE, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                snow = int(float(parts[3]))
                if snow > 0:
                    records.append([round(float(parts[2]), 6), round(float(parts[1]), 6), snow])
    return records


def load_veg_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['meshes']


def create_html(wi_records, snow_records, aomori_records, touhi_records, kometuga_records):
    wi_json       = json.dumps(wi_records,       separators=(',', ':'), ensure_ascii=False)
    snow_json     = json.dumps(snow_records,     separators=(',', ':'), ensure_ascii=False)
    aomori_json   = json.dumps(aomori_records,   separators=(',', ':'), ensure_ascii=False)
    touhi_json    = json.dumps(touhi_records,    separators=(',', ':'), ensure_ascii=False)
    kometuga_json = json.dumps(kometuga_records, separators=(',', ':'), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>植生WebGIS – 亜高山帯針葉樹・気候指数</title>

  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

  <style>
    html, body {{
      margin: 0; padding: 0; height: 100%;
      font-family: 'メイリオ', 'Meiryo', sans-serif;
    }}
    #map {{
      position: absolute; top: 0; bottom: 0; width: 100%;
    }}
    #loading {{
      position: absolute; top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(255,255,255,0.9);
      padding: 20px 30px; border-radius: 8px;
      font-size: 16px; z-index: 9999;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }}
    .legend {{
      background: white; padding: 10px 14px;
      border-radius: 6px; box-shadow: 0 1px 5px rgba(0,0,0,0.4);
      font-size: 12px; line-height: 1.6;
    }}
    .legend h4 {{ margin: 0 0 6px 0; font-size: 13px; font-weight: bold; }}
    .legend h5 {{ margin: 6px 0 3px 0; font-size: 12px; font-weight: bold; color: #555; }}
    .legend-item {{ display: flex; align-items: center; margin-bottom: 2px; }}
    .legend-color {{
      width: 16px; height: 16px; margin-right: 7px;
      border: 1px solid #888; flex-shrink: 0;
    }}
    .info-panel {{
      background: white; padding: 8px 12px;
      border-radius: 6px; box-shadow: 0 1px 5px rgba(0,0,0,0.4);
      font-size: 12px; max-width: 240px; line-height: 1.5;
    }}
    .info-panel h4 {{ margin: 0 0 4px 0; font-size: 13px; }}
    .share-btn {{
      display: block; width: 30px; height: 30px;
      line-height: 30px; text-align: center;
      text-decoration: none; color: #444;
      cursor: pointer;
    }}
    .share-btn:hover {{ background: #f4f4f4; border-radius: 2px; }}
    .share-toast {{
      position: absolute; bottom: 40px; left: 50%;
      transform: translateX(-50%);
      background: rgba(0,0,0,0.75); color: white;
      padding: 7px 18px; border-radius: 4px;
      font-size: 13px; z-index: 9999;
      pointer-events: none;
      transition: opacity 0.5s;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="loading">データを読み込み中...</div>

  <!-- Leaflet JS -->
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <script>
    // =====================================================================
    // データ（3次メッシュ中心座標と値）
    // WI/積雪: [緯度, 経度, 値]
    // 植生:    [緯度, 経度, 群落コード, 群落名]
    // =====================================================================
    const wiData       = {wi_json};
    const snowData     = {snow_json};
    const aomoriData   = {aomori_json};
    const touhiData    = {touhi_json};
    const kometugaData = {kometuga_json};

    const CELL_H = {CELL_HEIGHT:.10f};
    const CELL_W = {CELL_WIDTH:.10f};

    // =====================================================================
    // 色設定
    // =====================================================================
    const WI_BREAKS = [15, 45, 85, 130, 180];
    const WI_COLORS = ['#2166ac', '#74add1', '#abdda4', '#fdae61', '#f46d43', '#d73027'];
    const WI_LABELS = [
      '高山帯（WI < 15）',
      '亜高山帯（15〜45）',
      '冷温帯（45〜85）',
      '暖温帯上部（85〜130）',
      '暖温帯下部（130〜180）',
      '亜熱帯（WI ≥ 180）'
    ];

    function getWiColor(wi) {{
      for (let i = 0; i < WI_BREAKS.length; i++) {{
        if (wi < WI_BREAKS[i]) return WI_COLORS[i];
      }}
      return WI_COLORS[WI_COLORS.length - 1];
    }}

    const SNOW_BREAKS = [30, 100, 200, 300];
    const SNOW_COLORS = ['#c6dbef', '#9ecae1', '#6baed6', '#2171b5', '#084594'];
    const SNOW_LABELS = [
      '1〜30 cm',
      '30〜100 cm',
      '100〜200 cm',
      '200〜300 cm',
      '300 cm以上'
    ];

    function getSnowColor(snow) {{
      if (snow <= 0) return null;
      if (snow <  30) return SNOW_COLORS[0];
      if (snow < 100) return SNOW_COLORS[1];
      if (snow < 200) return SNOW_COLORS[2];
      if (snow < 300) return SNOW_COLORS[3];
      return SNOW_COLORS[4];
    }}

    // オオシラビソ: 緑系
    const AOMORI_CODE_COLORS = {{
      '20501':  '#006400',
      '20501A': '#006400',
      '20501B': '#228B22',
      '20501C': '#2E8B57',
      '20502':  '#3CB371',
      '20502A': '#3CB371',
      '21400':  '#8FBC8F',
      '40100D': '#90EE90'
    }};
    function getAomoriColor(vegcode) {{
      return AOMORI_CODE_COLORS[vegcode] || '#228B22';
    }}

    // トウヒ: 青系
    const TOUHI_CODE_COLORS = {{
      '20500': '#1565c0'
    }};
    function getTouhiColor(vegcode) {{
      return TOUHI_CODE_COLORS[vegcode] || '#1976d2';
    }}

    // コメツガ: 紫系
    const KOMETUGA_CODE_COLORS = {{
      '20503':  '#7b1fa2',
      '20503A': '#7b1fa2',
      '43300':  '#ab47bc',
      '43300B': '#ce93d8'
    }};
    function getKometugaColor(vegcode) {{
      return KOMETUGA_CODE_COLORS[vegcode] || '#9c27b0';
    }}

    // =====================================================================
    // 地図の初期化
    // =====================================================================
    function getInitialView() {{
      const hash = window.location.hash.slice(1);
      if (hash) {{
        const parts = hash.split('/');
        if (parts.length === 3) {{
          const zoom = parseInt(parts[0]);
          const lat  = parseFloat(parts[1]);
          const lon  = parseFloat(parts[2]);
          if (!isNaN(zoom) && !isNaN(lat) && !isNaN(lon))
            return {{ center: [lat, lon], zoom: zoom }};
        }}
      }}
      return {{ center: [38.0, 138.5], zoom: 6 }};
    }}

    const initialView = getInitialView();
    const map = L.map('map', {{ center: initialView.center, zoom: initialView.zoom }});

    // =====================================================================
    // ベースレイヤー
    // =====================================================================
    const googleHybrid = L.tileLayer(
      'https://mt{{s}}.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}',
      {{ attribution: '&copy; <a href="https://maps.google.com/">Google Maps</a>', maxZoom: 21, subdomains: '0123' }}
    );
    const gsiStd = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/std/{{z}}/{{x}}/{{y}}.png',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>', maxZoom: 18 }}
    );
    const gsiRelief = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/relief/{{z}}/{{x}}/{{y}}.png',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>', maxZoom: 15, opacity: 0.7 }}
    );
    const gsiHillshade = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{{z}}/{{x}}/{{y}}.png',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>', maxZoom: 16, opacity: 0.5 }}
    );
    const gsiPhoto1970 = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/gazo1/{{z}}/{{x}}/{{y}}.jpg',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル（1970年代空中写真）</a>', maxZoom: 17, opacity: 1.0 }}
    );
    const gsiOrt = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/ort/{{z}}/{{x}}/{{y}}.jpg',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル（電子国土基本図オルソ画像）</a>', minZoom: 14, maxZoom: 18 }}
    );
    const gsiStdOverlay = L.tileLayer(
      'https://cyberjapandata.gsi.go.jp/xyz/std/{{z}}/{{x}}/{{y}}.png',
      {{ attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>', maxZoom: 18, opacity: 0.5 }}
    );

    googleHybrid.addTo(map);

    // =====================================================================
    // 汎用 MeshCanvasLayer
    // =====================================================================
    const MeshCanvasLayer = L.Layer.extend({{

      initialize: function(data, colorFn, options) {{
        this._data    = data;
        this._colorFn = colorFn;
        this._visible = true;
        L.setOptions(this, options);
      }},

      onAdd: function(map) {{
        this._map = map;
        this._canvas = document.createElement('canvas');
        this._canvas.style.position = 'absolute';
        this._canvas.style.top  = '0';
        this._canvas.style.left = '0';
        this._canvas.style.pointerEvents = 'none';
        map.getPanes().overlayPane.appendChild(this._canvas);
        map.on('moveend zoomend resize', this._redraw, this);
        this._redraw();
      }},

      onRemove: function(map) {{
        map.getPanes().overlayPane.removeChild(this._canvas);
        map.off('moveend zoomend resize', this._redraw, this);
      }},

      setVisible: function(v) {{
        this._visible = v;
        this._canvas.style.display = v ? '' : 'none';
      }},

      isVisible: function() {{ return this._visible; }},

      _redraw: function() {{
        const map    = this._map;
        const canvas = this._canvas;
        const size   = map.getSize();

        const mapPanePos = L.DomUtil.getPosition(map.getPanes().mapPane) || L.point(0, 0);
        L.DomUtil.setPosition(canvas, L.point(-mapPanePos.x, -mapPanePos.y));

        canvas.width  = size.x;
        canvas.height = size.y;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, size.x, size.y);

        if (!this._visible) return;

        const bounds  = map.getBounds();
        const sw      = bounds.getSouthWest();
        const ne      = bounds.getNorthEast();
        const data    = this._data;
        const colorFn = this._colorFn;

        for (let i = 0; i < data.length; i++) {{
          const lat = data[i][0];
          const lon = data[i][1];
          const val = data[i][2];

          if (lat + CELL_H < sw.lat || lat - CELL_H > ne.lat ||
              lon + CELL_W < sw.lng || lon - CELL_W > ne.lng) continue;

          const color = colorFn(val);
          if (!color) continue;

          const ptSW = map.latLngToContainerPoint([lat - CELL_H/2, lon - CELL_W/2]);
          const ptNE = map.latLngToContainerPoint([lat + CELL_H/2, lon + CELL_W/2]);

          ctx.fillStyle   = color;
          ctx.globalAlpha = 0.75;
          ctx.fillRect(
            Math.round(ptSW.x),
            Math.round(ptNE.y),
            Math.max(1, Math.round(ptNE.x - ptSW.x)),
            Math.max(1, Math.round(ptSW.y - ptNE.y))
          );
        }}
      }},

      hitTest: function(latlng) {{
        const lat  = latlng.lat;
        const lon  = latlng.lng;
        const data = this._data;
        for (let i = 0; i < data.length; i++) {{
          if (Math.abs(data[i][0] - lat) <= CELL_H / 2 &&
              Math.abs(data[i][1] - lon) <= CELL_W / 2)
            return data[i];
        }}
        return null;
      }}
    }});

    const ToggleLayer = L.Layer.extend({{
      initialize: function(meshLayer) {{ this._meshLayer = meshLayer; }},
      onAdd:      function() {{ this._meshLayer.setVisible(true);  this._meshLayer._redraw(); }},
      onRemove:   function() {{ this._meshLayer.setVisible(false); }}
    }});

    // =====================================================================
    // レイヤーインスタンス
    // =====================================================================
    const wiLayer = new MeshCanvasLayer(wiData, getWiColor);
    wiLayer.addTo(map);

    const snowLayer = new MeshCanvasLayer(snowData, getSnowColor);
    snowLayer.addTo(map);
    snowLayer.setVisible(false);

    const aomoriLayer   = new MeshCanvasLayer(aomoriData,   getAomoriColor);
    const touhiLayer    = new MeshCanvasLayer(touhiData,    getTouhiColor);
    const kometugaLayer = new MeshCanvasLayer(kometugaData, getKometugaColor);
    aomoriLayer.addTo(map);   aomoriLayer.setVisible(false);
    touhiLayer.addTo(map);    touhiLayer.setVisible(false);
    kometugaLayer.addTo(map); kometugaLayer.setVisible(false);

    const wiToggle       = new ToggleLayer(wiLayer);       wiToggle.addTo(map);
    const snowToggle     = new ToggleLayer(snowLayer);
    const aomoriToggle   = new ToggleLayer(aomoriLayer);
    const touhiToggle    = new ToggleLayer(touhiLayer);
    const kometugaToggle = new ToggleLayer(kometugaLayer);

    // =====================================================================
    // クリックイベント
    // =====================================================================
    map.on('click', function(e) {{
      const parts = [];
      let coordHit = null;

      if (wiLayer.isVisible()) {{
        const h = wiLayer.hitTest(e.latlng);
        if (h) {{
          coordHit = h;
          parts.push('<b>暖かさの指数（WI）</b><br>値: <b>' + h[2].toFixed(1) + '</b> °C·月');
        }}
      }}

      if (snowLayer.isVisible()) {{
        const h = snowLayer.hitTest(e.latlng);
        if (h) {{
          if (!coordHit) coordHit = h;
          parts.push('<b>年最深積雪</b><br>深さ: <b>' + h[2] + '</b> cm');
        }}
      }}

      const vegLayers = [
        [aomoriLayer,   'オオシラビソ'],
        [touhiLayer,    'トウヒ'],
        [kometugaLayer, 'コメツガ']
      ];
      for (const [layer, label] of vegLayers) {{
        if (layer.isVisible()) {{
          const h = layer.hitTest(e.latlng);
          if (h) {{
            if (!coordHit) coordHit = h;
            parts.push('<b>植生（' + label + '）</b><br>群落名: <b>' + h[3] + '</b><br>群落コード: ' + h[2]);
          }}
        }}
      }}

      if (coordHit) {{
        const coord = '経度: ' + coordHit[1].toFixed(4) + '°, 緯度: ' + coordHit[0].toFixed(4) + '°';
        L.popup()
          .setLatLng(e.latlng)
          .setContent(parts.join('<hr style="margin:4px 0;">') + '<br><small>' + coord + '</small>')
          .openOn(map);
      }}
    }});

    // =====================================================================
    // レイヤーコントロール
    // =====================================================================
    const baseLayers = {{
      'Google Hybrid（衛星写真）':          googleHybrid,
      '地理院地図（標準地図）':              gsiStd,
      '地理院地図（電子国土基本図オルソ）':  gsiOrt,
      '1970年代空中写真（地理院）':          gsiPhoto1970
    }};

    const overlayLayers = {{
      'オオシラビソ（アオモリトドマツ）':      aomoriToggle,
      'トウヒ（シラビソ−トウヒ群団）':        touhiToggle,
      'コメツガ':                             kometugaToggle,
      '暖かさの指数（WI）':                   wiToggle,
      '年最深積雪':                           snowToggle,
      '色別標高図（地理院・50%）':            gsiRelief,
      '陰影起伏図（地理院・50%）':            gsiHillshade,
      '地理院地図（標準地図・50%）':          gsiStdOverlay
    }};

    L.control.layers(baseLayers, overlayLayers, {{ collapsed: false }}).addTo(map);

    // =====================================================================
    // 植生凡例（右下）
    // =====================================================================
    const vegLegend = L.control({{ position: 'bottomright' }});
    vegLegend.onAdd = function() {{
      const div = L.DomUtil.create('div', 'legend');
      div.innerHTML =
        '<h4>亜高山帯針葉樹</h4>' +
        '<h5>オオシラビソ（アオモリトドマツ）</h5>' +
        '<div class="legend-item"><div class="legend-color" style="background:#006400;"></div><span>オオシラビソ群集</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#228B22;"></div><span>アオモリトドマツ群落</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#2E8B57;"></div><span>オオシラビソ-ブナ群落</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#3CB371;"></div><span>シラビソ-オオシラビソ群集</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#8FBC8F;"></div><span>オオシラビソ-ダケカンバ</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#90EE90;"></div><span>その他のオオシラビソ群落</span></div>' +
        '<h5>トウヒ（シラビソ−トウヒ群団）</h5>' +
        '<div class="legend-item"><div class="legend-color" style="background:#1565c0;"></div><span>シラビソ−トウヒ群団</span></div>' +
        '<h5>コメツガ</h5>' +
        '<div class="legend-item"><div class="legend-color" style="background:#7b1fa2;"></div><span>コメツガ群落</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#ab47bc;"></div><span>ウラジロモミ−コメツガ群落</span></div>' +
        '<div class="legend-item"><div class="legend-color" style="background:#ce93d8;"></div><span>ウラジロモミ−コメツガ・ハリモミ群落</span></div>' +
        '<hr style="margin:5px 0;"><small>出典: 環境省 植生調査<br>（第3次メッシュ植生データ）<br>表示範囲: wi.dat の範囲に限定</small>';
      return div;
    }};
    vegLegend.addTo(map);

    // =====================================================================
    // WI 凡例（左下）
    // =====================================================================
    const wiLegend = L.control({{ position: 'bottomleft' }});
    wiLegend.onAdd = function() {{
      const div = L.DomUtil.create('div', 'legend');
      let html = '<h4>暖かさの指数（WI）</h4>';
      for (let i = 0; i < WI_COLORS.length; i++) {{
        html += `<div class="legend-item"><div class="legend-color" style="background:${{WI_COLORS[i]}};"></div><span>${{WI_LABELS[i]}}</span></div>`;
      }}
      html += '<hr style="margin:5px 0;"><small>しきい値: 5°C<br>出典: 国土数値情報 G02-22<br>（1991–2020年平年値）</small>';
      div.innerHTML = html;
      return div;
    }};
    wiLegend.addTo(map);

    // =====================================================================
    // 情報パネル（右上）
    // =====================================================================
    const info = L.control({{ position: 'topright' }});
    info.onAdd = function() {{
      const div = L.DomUtil.create('div', 'info-panel');
      div.innerHTML =
        '<h4>植生 WebGIS</h4>' +
        '<p style="margin:0;">' +
        '<b>オオシラビソ</b>・<b>トウヒ</b>・<b>コメツガ</b>:<br>' +
        '亜高山帯に分布する針葉樹。<br>' +
        '第3次メッシュ植生データより抽出。<br>' +
        '<b>暖かさの指数（WI）</b>: 月平均気温が<br>' +
        '5°Cを超える月の (月平均気温 − 5°C) の総和。<br>' +
        'レイヤーコントロールで切り替え。<br>' +
        '<b>地図上のセルをクリック</b>すると値を表示。' +
        '</p>';
      return div;
    }};
    info.addTo(map);

    // =====================================================================
    // URL ハッシュ更新
    // =====================================================================
    map.on('moveend', function() {{
      const c = map.getCenter();
      history.replaceState(null, '',
        '#' + map.getZoom() + '/' + c.lat.toFixed(5) + '/' + c.lng.toFixed(5));
    }});

    // =====================================================================
    // 共有ボタン
    // =====================================================================
    function showToast(msg) {{
      const toast = document.createElement('div');
      toast.className = 'share-toast';
      toast.textContent = msg;
      document.getElementById('map').appendChild(toast);
      setTimeout(function() {{
        toast.style.opacity = '0';
        setTimeout(function() {{ toast.remove(); }}, 500);
      }}, 2000);
    }}

    const ShareControl = L.Control.extend({{
      options: {{ position: 'topleft' }},
      onAdd: function() {{
        const container = L.DomUtil.create('div', 'leaflet-bar');
        const btn = L.DomUtil.create('a', 'share-btn', container);
        btn.href  = '#';
        btn.title = 'この地図を共有（URLをコピー）';
        btn.innerHTML =
          '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" ' +
          'viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
          'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
          '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/>' +
          '<circle cx="18" cy="19" r="3"/>' +
          '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>' +
          '<line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>';
        L.DomEvent.on(btn, 'click', function(e) {{
          L.DomEvent.preventDefault(e);
          const c = map.getCenter();
          const hash = '#' + map.getZoom() + '/' + c.lat.toFixed(5) + '/' + c.lng.toFixed(5);
          history.replaceState(null, '', hash);
          const url = window.location.href;
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(url).then(function() {{
              showToast('URLをクリップボードにコピーしました');
            }}).catch(function() {{
              prompt('以下のURLをコピーしてください:', url);
            }});
          }} else {{
            prompt('以下のURLをコピーしてください:', url);
          }}
        }});
        return container;
      }}
    }});
    new ShareControl().addTo(map);

    document.getElementById('loading').style.display = 'none';

  </script>
</body>
</html>
"""
    return html


def main():
    print("wi.dat を読み込み中...")
    wi_records = load_wi_data()
    print(f"  {len(wi_records)} 件のWIデータ")

    print("snow.dat を読み込み中...")
    snow_records = load_snow_data()
    print(f"  {len(snow_records)} 件の積雪データ（0 cm 除く）")

    print("aomori_todomatsu.json を読み込み中...")
    aomori_records = load_veg_json(VEG_AOMORI)
    print(f"  {len(aomori_records)} 件のオオシラビソメッシュ")

    print("touhi.json を読み込み中...")
    touhi_records = load_veg_json(VEG_TOUHI)
    print(f"  {len(touhi_records)} 件のトウヒメッシュ")

    print("kometuga.json を読み込み中...")
    kometuga_records = load_veg_json(VEG_KOMETUGA)
    print(f"  {len(kometuga_records)} 件のコメツガメッシュ")

    print("meshveg.html を生成中...")
    html = create_html(wi_records, snow_records, aomori_records, touhi_records, kometuga_records)

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    file_size_mb = os.path.getsize(HTML_FILE) / (1024 * 1024)
    print(f"完了: {HTML_FILE} ({file_size_mb:.1f} MB)")


if __name__ == '__main__':
    main()
