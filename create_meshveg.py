#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wi.dat / snow.dat / veg/*.json から Leaflet Web地図（meshveg.html）を生成。
収録レイヤー: オオシラビソ・トウヒ・コメツガ・ブナ・イヌブナ・ハイマツ・ミヤマナラ + WI・積雪
"""

import os
import json

BASE = os.path.dirname(__file__)
WI_FILE       = os.path.join(BASE, 'wi.dat')
SNOW_FILE     = os.path.join(BASE, 'snow.dat')
VEG_FILES = {
    'aomori':   os.path.join(BASE, 'veg', 'aomori_todomatsu.json'),
    'touhi':    os.path.join(BASE, 'veg', 'touhi.json'),
    'kometuga': os.path.join(BASE, 'veg', 'kometuga.json'),
    'buna':     os.path.join(BASE, 'veg', 'buna.json'),
    'inubuna':  os.path.join(BASE, 'veg', 'inubuna.json'),
    'haimatsu': os.path.join(BASE, 'veg', 'haimatsu.json'),
    'miyamana': os.path.join(BASE, 'veg', 'miyamana.json'),
}
HTML_FILE = os.path.join(BASE, 'meshveg.html')

CELL_HEIGHT = 1.0 / 120.0
CELL_WIDTH  = 1.0 / 80.0

# vegcode → hex color
AOMORI_COLORS = {
    '20501': '#006400', '20501A': '#006400',
    '20501B': '#228B22', '20501C': '#2E8B57',
    '20502': '#3CB371', '20502A': '#3CB371',
    '21400': '#8FBC8F', '40100D': '#90EE90',
}
TOUHI_COLORS = {'20500': '#1565c0'}
KOMETUGA_COLORS = {
    '20503': '#7b1fa2', '20503A': '#7b1fa2',
    '43300': '#ab47bc', '43300B': '#ce93d8',
}
BUNA_COLORS = {
    # チシマザサ-ブナ（北方）
    '40100': '#8B4513', '40100A': '#8B4513', '40100B': '#8B4513', '40100C': '#8B4513',
    # スズタケ-ブナ（日本海側）
    '40200': '#B8860B', '40200A': '#B8860B', '40200B': '#B8860B', '40210C': '#B8860B',
    # ヤマボウシ-ブナ・ツクシシャクナゲ-ブナ（太平洋側）
    '40201': '#DAA520', '40201A': '#DAA520', '40201B': '#DAA520',
    '40201C': '#DAA520', '40201D': '#DAA520',
    '40202': '#DAA520', '40202A': '#DAA520', '40202B': '#DAA520', '40202C': '#DAA520',
    # その他ブナ林（ヒメアオキ-ブナ・クロモジ-ブナ等）
    '40101': '#CD853F', '40102': '#CD853F', '40103': '#CD853F', '40104': '#CD853F',
    '40204': '#CD853F', '40204B': '#CD853F',
    '40214': '#CD853F', '40214A': '#CD853F', '40214B': '#CD853F', '40214C': '#CD853F',
    # ブナ-ミズナラ（移行帯）
    '50100': '#D2B48C', '50100A': '#D2B48C', '50100B': '#D2B48C',
}
INUBUNA_COLORS = {
    '40203': '#6B8E23', '40203A': '#6B8E23', '40203B': '#6B8E23',
    '40203C': '#6B8E23', '40203D': '#6B8E23',
}
HAIMATSU_COLORS = {
    '10101B': '#000000', '10101C': '#000000',
    '20800B': '#000000',
}
MIYAMANA_COLORS = {
    '21300': '#C0392B', '21300A': '#C0392B', '21300B': '#C0392B',
    '21300C': '#E74C3C',  # ナナカマド-ミネカエデ
}


def load_wi_data():
    records = []
    with open(WI_FILE, 'r', encoding='utf-8') as f:
        f.readline()
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                records.append([round(float(parts[2]), 6),
                                 round(float(parts[1]), 6),
                                 round(float(parts[3]), 1)])
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
                    records.append([round(float(parts[2]), 6),
                                     round(float(parts[1]), 6), snow])
    return records


def load_veg_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)['meshes']


def color_map_js(d):
    """Python dict → JS object literal"""
    return '{' + ','.join(f'"{k}":"{v}"' for k, v in d.items()) + '}'


def create_html(wi_records, snow_records, veg_data):
    wi_json   = json.dumps(wi_records,   separators=(',', ':'), ensure_ascii=False)
    snow_json = json.dumps(snow_records, separators=(',', ':'), ensure_ascii=False)
    veg_jsons = {k: json.dumps(v, separators=(',', ':'), ensure_ascii=False)
                 for k, v in veg_data.items()}

    aomori_colors_js   = color_map_js(AOMORI_COLORS)
    touhi_colors_js    = color_map_js(TOUHI_COLORS)
    kometuga_colors_js = color_map_js(KOMETUGA_COLORS)
    buna_colors_js     = color_map_js(BUNA_COLORS)
    inubuna_colors_js  = color_map_js(INUBUNA_COLORS)
    haimatsu_colors_js = color_map_js(HAIMATSU_COLORS)
    miyamana_colors_js = color_map_js(MIYAMANA_COLORS)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>植生WebGIS – 亜高山帯〜山地帯植生・気候指数</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    html, body {{ margin:0; padding:0; height:100%; font-family:'メイリオ','Meiryo',sans-serif; }}
    #map {{ position:absolute; top:0; bottom:0; width:100%; }}
    #loading {{
      position:absolute; top:50%; left:50%;
      transform:translate(-50%,-50%);
      background:rgba(255,255,255,0.9); padding:20px 30px;
      border-radius:8px; font-size:16px; z-index:9999;
      box-shadow:0 2px 10px rgba(0,0,0,0.3);
    }}
    .legend {{
      background:white; padding:10px 14px;
      border-radius:6px; box-shadow:0 1px 5px rgba(0,0,0,0.4);
      font-size:12px; line-height:1.6;
      max-height:70vh; overflow-y:auto;
    }}
    .legend h4 {{ margin:0 0 6px 0; font-size:13px; font-weight:bold; }}
    .legend h5 {{ margin:6px 0 3px 0; font-size:12px; font-weight:bold; color:#555;
                  border-top:1px solid #ddd; padding-top:4px; }}
    .legend-item {{ display:flex; align-items:center; margin-bottom:2px; }}
    .legend-color {{ width:16px; height:16px; margin-right:7px; border:1px solid #888; flex-shrink:0; }}
    .info-panel {{
      background:white; padding:8px 12px;
      border-radius:6px; box-shadow:0 1px 5px rgba(0,0,0,0.4);
      font-size:12px; max-width:240px; line-height:1.5;
    }}
    .info-panel h4 {{ margin:0 0 4px 0; font-size:13px; }}
    .share-btn {{ display:block; width:30px; height:30px; line-height:30px;
                  text-align:center; text-decoration:none; color:#444; cursor:pointer; }}
    .share-btn:hover {{ background:#f4f4f4; border-radius:2px; }}
    .share-toast {{
      position:absolute; bottom:40px; left:50%; transform:translateX(-50%);
      background:rgba(0,0,0,0.75); color:white;
      padding:7px 18px; border-radius:4px; font-size:13px; z-index:9999;
      pointer-events:none; transition:opacity 0.5s;
    }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div id="loading">データを読み込み中...</div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    // ── データ ────────────────────────────────────────────────────
    const wiData       = {wi_json};
    const snowData     = {snow_json};
    const aomoriData   = {veg_jsons['aomori']};
    const touhiData    = {veg_jsons['touhi']};
    const kometugaData = {veg_jsons['kometuga']};
    const bunaData     = {veg_jsons['buna']};
    const inubunaData  = {veg_jsons['inubuna']};
    const haimatsuData = {veg_jsons['haimatsu']};
    const miyamanaData = {veg_jsons['miyamana']};

    const CELL_H = {CELL_HEIGHT:.10f};
    const CELL_W = {CELL_WIDTH:.10f};

    // ── 色設定 ─────────────────────────────────────────────────────
    const WI_BREAKS = [15, 45, 85, 130, 180];
    const WI_COLORS = ['#2166ac','#74add1','#abdda4','#fdae61','#f46d43','#d73027'];
    const WI_LABELS = [
      '高山帯（WI < 15）','亜高山帯（15〜45）','冷温帯（45〜85）',
      '暖温帯上部（85〜130）','暖温帯下部（130〜180）','亜熱帯（WI ≥ 180）'
    ];
    function getWiColor(wi) {{
      for (let i=0; i<WI_BREAKS.length; i++) if (wi < WI_BREAKS[i]) return WI_COLORS[i];
      return WI_COLORS[WI_COLORS.length-1];
    }}

    const SNOW_BREAKS = [30,100,200,300];
    const SNOW_COLORS = ['#c6dbef','#9ecae1','#6baed6','#2171b5','#084594'];
    function getSnowColor(snow) {{
      if (snow<=0) return null;
      for (let i=0; i<SNOW_BREAKS.length; i++) if (snow < SNOW_BREAKS[i]) return SNOW_COLORS[i];
      return SNOW_COLORS[SNOW_COLORS.length-1];
    }}

    const AOMORI_COLORS   = {aomori_colors_js};
    const TOUHI_COLORS    = {touhi_colors_js};
    const KOMETUGA_COLORS = {kometuga_colors_js};
    const BUNA_COLORS     = {buna_colors_js};
    const INUBUNA_COLORS  = {inubuna_colors_js};
    const HAIMATSU_COLORS = {haimatsu_colors_js};
    const MIYAMANA_COLORS = {miyamana_colors_js};

    const makeColorFn = (map, def) => (code) => map[code] || def;
    const getAomoriColor   = makeColorFn(AOMORI_COLORS,   '#228B22');
    const getTouhiColor    = makeColorFn(TOUHI_COLORS,    '#1976d2');
    const getKometugaColor = makeColorFn(KOMETUGA_COLORS, '#9c27b0');
    const getBunaColor     = makeColorFn(BUNA_COLORS,     '#CD853F');
    const getInubunaColor  = makeColorFn(INUBUNA_COLORS,  '#6B8E23');
    const getHaimatsuColor = makeColorFn(HAIMATSU_COLORS, '#E67E22');
    const getMiyamanaColor = makeColorFn(MIYAMANA_COLORS, '#C0392B');

    // ── 地図初期化 ─────────────────────────────────────────────────
    function getInitialView() {{
      const hash = window.location.hash.slice(1);
      if (hash) {{
        const p = hash.split('/');
        if (p.length===3) {{
          const z=parseInt(p[0]), la=parseFloat(p[1]), lo=parseFloat(p[2]);
          if (!isNaN(z)&&!isNaN(la)&&!isNaN(lo)) return {{center:[la,lo],zoom:z}};
        }}
      }}
      return {{center:[38.0,138.5],zoom:6}};
    }}
    const iv  = getInitialView();
    const map = L.map('map', {{center:iv.center, zoom:iv.zoom}});

    // ── ベースレイヤー ─────────────────────────────────────────────
    const googleHybrid  = L.tileLayer('https://mt{{s}}.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}',
      {{attribution:'&copy; <a href="https://maps.google.com/">Google Maps</a>',maxZoom:21,subdomains:'0123'}});
    const gsiStd        = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{{z}}/{{x}}/{{y}}.png',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>',maxZoom:18}});
    const gsiRelief     = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/relief/{{z}}/{{x}}/{{y}}.png',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>',maxZoom:15,opacity:0.7}});
    const gsiHillshade  = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{{z}}/{{x}}/{{y}}.png',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>',maxZoom:16,opacity:0.5}});
    const gsiPhoto1970  = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/gazo1/{{z}}/{{x}}/{{y}}.jpg',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル（1970年代空中写真）</a>',maxZoom:17}});
    const gsiOrt        = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/ort/{{z}}/{{x}}/{{y}}.jpg',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>',minZoom:14,maxZoom:18}});
    const gsiStdOverlay = L.tileLayer('https://cyberjapandata.gsi.go.jp/xyz/std/{{z}}/{{x}}/{{y}}.png',
      {{attribution:'<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>',maxZoom:18,opacity:0.5}});
    googleHybrid.addTo(map);

    // ── MeshCanvasLayer ─────────────────────────────────────────────
    const MeshCanvasLayer = L.Layer.extend({{
      initialize: function(data, colorFn, opts) {{
        this._data=data; this._colorFn=colorFn; this._visible=true;
        L.setOptions(this, opts);
      }},
      onAdd: function(map) {{
        this._map=map;
        this._canvas=document.createElement('canvas');
        this._canvas.style.cssText='position:absolute;top:0;left:0;pointer-events:none;';
        map.getPanes().overlayPane.appendChild(this._canvas);
        map.on('moveend zoomend resize', this._redraw, this);
        this._redraw();
      }},
      onRemove: function(map) {{
        map.getPanes().overlayPane.removeChild(this._canvas);
        map.off('moveend zoomend resize', this._redraw, this);
      }},
      setVisible: function(v) {{ this._visible=v; this._canvas.style.display=v?'':'none'; }},
      isVisible:  function()  {{ return this._visible; }},
      _redraw: function() {{
        const map=this._map, canvas=this._canvas, size=map.getSize();
        const pp=L.DomUtil.getPosition(map.getPanes().mapPane)||L.point(0,0);
        L.DomUtil.setPosition(canvas, L.point(-pp.x,-pp.y));
        canvas.width=size.x; canvas.height=size.y;
        const ctx=canvas.getContext('2d');
        ctx.clearRect(0,0,size.x,size.y);
        if (!this._visible) return;
        const b=map.getBounds(), sw=b.getSouthWest(), ne=b.getNorthEast();
        const data=this._data, cfn=this._colorFn;
        for (let i=0; i<data.length; i++) {{
          const la=data[i][0], lo=data[i][1], v=data[i][2];
          if (la+CELL_H<sw.lat||la-CELL_H>ne.lat||lo+CELL_W<sw.lng||lo-CELL_W>ne.lng) continue;
          const col=cfn(v); if (!col) continue;
          const p1=map.latLngToContainerPoint([la-CELL_H/2,lo-CELL_W/2]);
          const p2=map.latLngToContainerPoint([la+CELL_H/2,lo+CELL_W/2]);
          ctx.fillStyle=col; ctx.globalAlpha=0.75;
          ctx.fillRect(Math.round(p1.x),Math.round(p2.y),
            Math.max(1,Math.round(p2.x-p1.x)),Math.max(1,Math.round(p1.y-p2.y)));
        }}
      }},
      hitTest: function(latlng) {{
        const la=latlng.lat, lo=latlng.lng, data=this._data;
        for (let i=0; i<data.length; i++)
          if (Math.abs(data[i][0]-la)<=CELL_H/2 && Math.abs(data[i][1]-lo)<=CELL_W/2)
            return data[i];
        return null;
      }}
    }});

    const ToggleLayer = L.Layer.extend({{
      initialize: function(ml) {{ this._ml=ml; }},
      onAdd:    function() {{ this._ml.setVisible(true);  this._ml._redraw(); }},
      onRemove: function() {{ this._ml.setVisible(false); }}
    }});

    // ── レイヤーインスタンス ────────────────────────────────────────
    const wiLayer       = new MeshCanvasLayer(wiData,       getWiColor);
    const snowLayer     = new MeshCanvasLayer(snowData,     getSnowColor);
    const aomoriLayer   = new MeshCanvasLayer(aomoriData,   getAomoriColor);
    const touhiLayer    = new MeshCanvasLayer(touhiData,    getTouhiColor);
    const kometugaLayer = new MeshCanvasLayer(kometugaData, getKometugaColor);
    const bunaLayer     = new MeshCanvasLayer(bunaData,     getBunaColor);
    const inubunaLayer  = new MeshCanvasLayer(inubunaData,  getInubunaColor);
    const haimatsuLayer = new MeshCanvasLayer(haimatsuData, getHaimatsuColor);
    const miyamanaLayer = new MeshCanvasLayer(miyamanaData, getMiyamanaColor);

    wiLayer.addTo(map);
    [snowLayer,aomoriLayer,touhiLayer,kometugaLayer,
     bunaLayer,inubunaLayer,haimatsuLayer,miyamanaLayer].forEach(l => {{
      l.addTo(map); l.setVisible(false);
    }});

    const wiToggle       = new ToggleLayer(wiLayer);       wiToggle.addTo(map);
    const snowToggle     = new ToggleLayer(snowLayer);
    const aomoriToggle   = new ToggleLayer(aomoriLayer);
    const touhiToggle    = new ToggleLayer(touhiLayer);
    const kometugaToggle = new ToggleLayer(kometugaLayer);
    const bunaToggle     = new ToggleLayer(bunaLayer);
    const inubunaToggle  = new ToggleLayer(inubunaLayer);
    const haimatsuToggle = new ToggleLayer(haimatsuLayer);
    const miyamanaToggle = new ToggleLayer(miyamanaLayer);

    // ── クリックイベント ───────────────────────────────────────────
    map.on('click', function(e) {{
      const parts=[]; let coordHit=null;
      const tests=[
        [wiLayer,   (h)=>'<b>暖かさの指数（WI）</b><br>値: <b>'+h[2].toFixed(1)+'</b> °C·月'],
        [snowLayer, (h)=>'<b>年最深積雪</b><br>深さ: <b>'+h[2]+'</b> cm'],
        [aomoriLayer,   (h)=>'<b>植生（オオシラビソ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [touhiLayer,    (h)=>'<b>植生（トウヒ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [kometugaLayer, (h)=>'<b>植生（コメツガ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [bunaLayer,     (h)=>'<b>植生（ブナ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [inubunaLayer,  (h)=>'<b>植生（イヌブナ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [haimatsuLayer, (h)=>'<b>植生（ハイマツ）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
        [miyamanaLayer, (h)=>'<b>植生（ミヤマナラ等）</b><br>'+h[3]+'<br><small>'+h[2]+'</small>'],
      ];
      for (const [layer, fmt] of tests) {{
        if (!layer.isVisible()) continue;
        const h=layer.hitTest(e.latlng);
        if (h) {{ if (!coordHit) coordHit=h; parts.push(fmt(h)); }}
      }}
      if (coordHit) {{
        const coord='経度: '+coordHit[1].toFixed(4)+'°, 緯度: '+coordHit[0].toFixed(4)+'°';
        L.popup().setLatLng(e.latlng)
          .setContent(parts.join('<hr style="margin:4px 0;">')+'<br><small>'+coord+'</small>')
          .openOn(map);
      }}
    }});

    // ── レイヤーコントロール ───────────────────────────────────────
    L.control.layers(
      {{
        'Google Hybrid（衛星写真）':          googleHybrid,
        '地理院地図（標準地図）':              gsiStd,
        '地理院地図（電子国土基本図オルソ）':  gsiOrt,
        '1970年代空中写真（地理院）':          gsiPhoto1970,
      }},
      {{
        '─── 亜高山帯針葉樹 ───':              L.layerGroup(),
        'オオシラビソ（アオモリトドマツ）':    aomoriToggle,
        'トウヒ（シラビソ−トウヒ群団）':      touhiToggle,
        'コメツガ':                            kometugaToggle,
        '─── 高山帯・低木帯 ───':              L.layerGroup(),
        'ハイマツ':                            haimatsuToggle,
        'ミヤマナラ（偽高山帯）':              miyamanaToggle,
        '─── 山地帯落葉広葉樹 ───':            L.layerGroup(),
        'ブナ林':                              bunaToggle,
        'イヌブナ林':                          inubunaToggle,
        '─── 気候指数 ───':                    L.layerGroup(),
        '暖かさの指数（WI）':                  wiToggle,
        '年最深積雪':                          snowToggle,
        '─── 地図オーバーレイ ───':            L.layerGroup(),
        '色別標高図（地理院・70%）':           gsiRelief,
        '陰影起伏図（地理院・50%）':           gsiHillshade,
        '地理院地図（標準地図・50%）':         gsiStdOverlay,
      }},
      {{collapsed: false}}
    ).addTo(map);

    // ── 植生凡例（右下）──────────────────────────────────────────
    const vegLegend = L.control({{position:'bottomleft'}});
    vegLegend.onAdd = function() {{
      const div=L.DomUtil.create('div','legend');
      div.innerHTML=
        '<h4>植生凡例</h4>'+
        '<h5>亜高山帯針葉樹</h5>'+
        '<div class="legend-item"><div class="legend-color" style="background:#006400;"></div><span>オオシラビソ群集</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#228B22;"></div><span>アオモリトドマツ群落</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#3CB371;"></div><span>シラビソ−オオシラビソ群集</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#1565c0;"></div><span>シラビソ−トウヒ群団</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#7b1fa2;"></div><span>コメツガ群落</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#ab47bc;"></div><span>ウラジロモミ−コメツガ群落</span></div>'+
        '<h5>高山帯・低木帯</h5>'+
        '<div class="legend-item"><div class="legend-color" style="background:#000000;"></div><span>ハイマツ（コケモモ−ハイマツ群集）</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#000000;"></div><span>ダケカンバ−ハイマツ群落</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#C0392B;"></div><span>ミヤマナラ群落</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#E74C3C;"></div><span>ナナカマド−ミネカエデ群落</span></div>'+
        '<h5>山地帯落葉広葉樹</h5>'+
        '<div class="legend-item"><div class="legend-color" style="background:#8B4513;"></div><span>ブナ林（北方・チシマザサ型）</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#B8860B;"></div><span>ブナ林（日本海側・スズタケ型）</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#DAA520;"></div><span>ブナ林（太平洋側・ヤマボウシ型）</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#CD853F;"></div><span>ブナ林（その他）</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#D2B48C;"></div><span>ブナ−ミズナラ移行林</span></div>'+
        '<div class="legend-item"><div class="legend-color" style="background:#6B8E23;"></div><span>イヌブナ林</span></div>'+
        '<hr style="margin:5px 0;"><small>出典: 環境省 植生調査（第3次メッシュ植生データ）</small>';
      return div;
    }};
    vegLegend.addTo(map);

    // ── WI 凡例（左下）───────────────────────────────────────────
    const wiLegend = L.control({{position:'bottomleft'}});
    wiLegend.onAdd = function() {{
      const div=L.DomUtil.create('div','legend');
      let html='<h4>暖かさの指数（WI）</h4>';
      for (let i=0; i<WI_COLORS.length; i++)
        html+=`<div class="legend-item"><div class="legend-color" style="background:${{WI_COLORS[i]}};"></div><span>${{WI_LABELS[i]}}</span></div>`;
      html+='<hr style="margin:5px 0;"><small>しきい値: 5°C<br>出典: 国土数値情報 G02-22（1991–2020年平年値）</small>';
      div.innerHTML=html;
      return div;
    }};
    wiLegend.addTo(map);

    // ── 情報パネル（右上）────────────────────────────────────────
    const info=L.control({{position:'topright'}});
    info.onAdd=function() {{
      const div=L.DomUtil.create('div','info-panel');
      div.innerHTML=
        '<h4>植生 WebGIS</h4>'+
        '<p style="margin:0;">亜高山帯針葉樹・高山帯低木・山地帯広葉樹の<br>'+
        '分布を第3次メッシュ植生データより表示。<br>'+
        '<b>暖かさの指数（WI）</b>: 月平均気温 > 5°C<br>'+
        'の月の（月平均気温 − 5°C）の総和。<br>'+
        'レイヤーコントロールで切り替え。<br>'+
        '<b>セルをクリック</b>すると値を表示。</p>';
      return div;
    }};
    info.addTo(map);

    // ── URL ハッシュ ─────────────────────────────────────────────
    map.on('moveend', function() {{
      const c=map.getCenter();
      history.replaceState(null,'','#'+map.getZoom()+'/'+c.lat.toFixed(5)+'/'+c.lng.toFixed(5));
    }});

    // ── 共有ボタン ────────────────────────────────────────────────
    function showToast(msg) {{
      const t=document.createElement('div');
      t.className='share-toast'; t.textContent=msg;
      document.getElementById('map').appendChild(t);
      setTimeout(()=>{{ t.style.opacity='0'; setTimeout(()=>t.remove(),500); }},2000);
    }}
    const ShareControl=L.Control.extend({{
      options:{{position:'topleft'}},
      onAdd:function() {{
        const c=L.DomUtil.create('div','leaflet-bar');
        const b=L.DomUtil.create('a','share-btn',c);
        b.href='#'; b.title='この地図を共有（URLをコピー）';
        b.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>';
        L.DomEvent.on(b,'click',function(e) {{
          L.DomEvent.preventDefault(e);
          const c2=map.getCenter();
          history.replaceState(null,'','#'+map.getZoom()+'/'+c2.lat.toFixed(5)+'/'+c2.lng.toFixed(5));
          const url=window.location.href;
          if (navigator.clipboard&&navigator.clipboard.writeText)
            navigator.clipboard.writeText(url)
              .then(()=>showToast('URLをクリップボードにコピーしました'))
              .catch(()=>prompt('以下のURLをコピーしてください:',url));
          else prompt('以下のURLをコピーしてください:',url);
        }});
        return c;
      }}
    }});
    new ShareControl().addTo(map);

    document.getElementById('loading').style.display='none';
  </script>
</body>
</html>
"""


def main():
    print("データを読み込み中...")
    wi_records   = load_wi_data();   print(f"  WI: {len(wi_records)} 件")
    snow_records = load_snow_data(); print(f"  積雪: {len(snow_records)} 件")
    veg_data = {}
    for key, path in VEG_FILES.items():
        veg_data[key] = load_veg_json(path)
        print(f"  {key}: {len(veg_data[key])} メッシュ")

    print("meshveg.html を生成中...")
    html = create_html(wi_records, snow_records, veg_data)
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"完了: {HTML_FILE} ({os.path.getsize(HTML_FILE)/1024/1024:.1f} MB)")


if __name__ == '__main__':
    main()
