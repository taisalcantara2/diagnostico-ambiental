"""
================================================================================
DIAGNÓSTICO AMBIENTAL DE IMÓVEIS RURAIS - PARÁ
Plataforma pública de consulta PRODES, DETER e Focos de Calor via CAR
Desenvolvido com Streamlit + APIs públicas INPE/SICAR
================================================================================
"""

import streamlit as st
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import folium
from folium.plugins import MiniMap
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import json
import re
from datetime import datetime, date
import warnings
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Diagnóstico Ambiental | Imóvel Rural - Pará",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# ESTILOS CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --verde:    #1a7a4a;
    --verde-claro: #2ecc71;
    --amarelo:  #f39c12;
    --vermelho: #e74c3c;
    --azul:     #2980b9;
    --cinza-bg: #f4f6f4;
    --cinza-card: #ffffff;
    --texto:    #1a2e1a;
    --borda:    #d4e6d4;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--texto);
    background-color: var(--cinza-bg);
}

/* Header */
.hero-header {
    background: linear-gradient(135deg, #0d3d22 0%, #1a7a4a 60%, #2ecc71 100%);
    padding: 2.5rem 2rem 2rem;
    border-radius: 0 0 2rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    border-radius: 50%;
    background: rgba(46,204,113,0.08);
    pointer-events: none;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    line-height: 1.1;
}
.hero-subtitle {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.75);
    margin-top: 0.4rem;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-bottom: 1rem;
    letter-spacing: 0.05em;
}

/* Search box */
.search-container {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    box-shadow: 0 4px 24px rgba(26,122,74,0.12);
    border: 1px solid var(--borda);
    margin-bottom: 1.5rem;
}

/* Info card do imóvel */
.imovel-card {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    border-left: 5px solid var(--verde);
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    margin-bottom: 1.5rem;
}
.imovel-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--verde);
    margin-bottom: 0.25rem;
}

/* Metric pill */
.metric-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 1rem;
}
.metric-pill {
    background: var(--cinza-bg);
    border: 1px solid var(--borda);
    border-radius: 0.6rem;
    padding: 0.5rem 1rem;
    font-size: 0.82rem;
}
.metric-pill strong {
    display: block;
    font-size: 1.05rem;
    color: var(--verde);
}

/* Bloco diagnóstico */
.bloco-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    padding: 0.6rem 1rem;
    border-radius: 0.6rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.bloco-prodes { background: #e8f5e9; color: #1b5e20; border-left: 4px solid #2e7d32; }
.bloco-deter  { background: #fff3e0; color: #e65100; border-left: 4px solid #f57c00; }
.bloco-fogo   { background: #fce4ec; color: #880e4f; border-left: 4px solid #c62828; }

.stat-box {
    background: white;
    border: 1px solid var(--borda);
    border-radius: 0.75rem;
    padding: 1rem;
    text-align: center;
    margin-bottom: 0.75rem;
}
.stat-box .val {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1;
}
.stat-box .lbl {
    font-size: 0.75rem;
    color: #666;
    margin-top: 0.2rem;
}

.tag-alerta {
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    margin: 2px;
}
.tag-ativo   { background: #fde8e8; color: #c0392b; }
.tag-passado { background: #fef9e7; color: #b7770d; }

.footer-note {
    text-align: center;
    font-size: 0.75rem;
    color: #999;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--borda);
}

/* Streamlit overrides */
div[data-testid="stTextInput"] input {
    border-radius: 0.6rem !important;
    border: 2px solid var(--borda) !important;
    font-size: 1rem !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--verde) !important;
    box-shadow: 0 0 0 3px rgba(26,122,74,0.1) !important;
}
button[kind="primary"] {
    background: var(--verde) !important;
    border-radius: 0.6rem !important;
}

.stAlert { border-radius: 0.75rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CONSTANTES / ENDPOINTS
# ─────────────────────────────────────────────
SICAR_WFS      = "https://geoserver.car.gov.br/geoserver/sicar/wfs"

# Mapa UF → sufixo da camada SICAR
_UF_LAYER = {
    "AC":"ac","AL":"al","AM":"am","AP":"ap","BA":"ba","CE":"ce","DF":"df",
    "ES":"es","GO":"go","MA":"ma","MG":"mg","MS":"ms","MT":"mt","PA":"pa",
    "PB":"pb","PE":"pe","PI":"pi","PR":"pr","RJ":"rj","RN":"rn","RO":"ro",
    "RR":"rr","RS":"rs","SC":"sc","SE":"se","SP":"sp","TO":"to",
}

class _LegacyTLSAdapter(requests.adapters.HTTPAdapter):
    """Adapter que aceita TLS legado do servidor SICAR."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode    = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        ctx.options &= ~getattr(ssl, "OP_NO_TLSv1",   0)
        ctx.options &= ~getattr(ssl, "OP_NO_TLSv1_1", 0)
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)

def _sicar_session():
    s = requests.Session()
    s.mount("https://", _LegacyTLSAdapter())
    return s
SICAR_PUBL_URL = "https://www.car.gov.br/publico/imoveis/index"
PRODES_WFS = "https://terrabrasilis.dpi.inpe.br/geoserver/prodes-amz-nb/wfs"
DETER_WFS  = "https://terrabrasilis.dpi.inpe.br/geoserver/deter-amz/wfs"
FOCOS_WFS = "https://terrabrasilis.dpi.inpe.br/geoserver/bdqueimadas-light/wfs"

DETER_CLASSES = {
    "DESMATAMENTO_CR": ("Desmatamento com corte raso", "#e74c3c"),
    "DESMATAMENTO_VEG": ("Desmatamento com vegetação", "#e67e22"),
    "MINERACAO": ("Mineração", "#8e44ad"),
    "CICATRIZ_DE_QUEIMADA": ("Cicatriz de queimada", "#c0392b"),
    "DEGRADACAO": ("Degradação", "#f39c12"),
    "CS_DESORDENADO": ("Corte seletivo desordenado", "#d35400"),
    "CS_GEOMETRICO": ("Corte seletivo geométrico", "#e67e22"),
}


# ─────────────────────────────────────────────
# FUNÇÕES DE BUSCA
# ─────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def buscar_imovel_car(codigo_car: str):
    """
    Consulta WFS SICAR com adaptador TLS legado — padrão comprovado em produção.
    Usa version=1.0.0, typeName (sem 's'), filtro XML OGC e verify=False.
    Fallback para GML2 se o servidor não retornar JSON.
    """
    cod = codigo_car.strip().upper()

    # Detecta UF pelo prefixo do código (ex: PA-...)
    uf = cod.split("-")[0] if "-" in cod else "PA"
    layer = f"sicar:sicar_imoveis_{_UF_LAYER.get(uf, 'pa')}"

    filter_xml = (
        "<Filter>"
        "<PropertyIsEqualTo>"
        "<PropertyName>cod_imovel</PropertyName>"
        f"<Literal>{cod}</Literal>"
        "</PropertyIsEqualTo>"
        "</Filter>"
    )

    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer,
        "outputFormat": "application/json",
        "maxFeatures": "1",
        "FILTER": filter_xml,
    }

    session = _sicar_session()

    # ── Tentativa 1: JSON ──────────────────────────────────────────────────
    try:
        r = session.get(SICAR_WFS, params=params, timeout=40, verify=False)
        if r.status_code == 200 and r.text.strip():
            ctype = r.headers.get("Content-Type", "")
            if "json" in ctype or r.text.strip().startswith("{"):
                data = r.json()
                if data.get("features"):
                    return gpd.GeoDataFrame.from_features(
                        data["features"], crs="EPSG:4674"
                    )
    except Exception:
        pass

    # ── Tentativa 2: GML2 (fallback quando servidor não retorna JSON) ──────
    try:
        params_gml = {**params, "outputFormat": "GML2"}
        r = session.get(SICAR_WFS, params=params_gml, timeout=40, verify=False)
        if r.status_code == 200 and r.text.strip() and "<gml:" in r.text:
            import io as _io
            gdf = gpd.read_file(_io.StringIO(r.text))
            if not gdf.empty:
                if gdf.crs is None:
                    gdf = gdf.set_crs("EPSG:4674")
                return gdf.to_crs("EPSG:4674")
    except Exception:
        pass

    return None


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_prodes(bbox_wkt: str, geom_json: str):
    """
    Busca incrementos PRODES via WFS TerraBrasilis.
    - typeName sem prefixo de workspace (padrão documentado pelo INPE)
    - bbox convertido para EPSG:4326 (o servidor rejeita 4674 no bbox)
    - usa _sicar_session() para tolerância TLS
    - intersecção real com o polígono do imóvel após download
    """
    # Converte bbox de 4674 → 4326 para a query
    minx, miny, maxx, maxy = [float(v) for v in bbox_wkt.split(",")]
    # EPSG:4674 e EPSG:4326 têm coordenadas praticamente idênticas
    # (SIRGAS 2000 ≈ WGS84), mas declarar 4326 evita rejeição do servidor
    bbox_4326 = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

    # Tenta duas camadas conhecidas (o nome pode variar por versão do servidor)
    camadas = [
        "prodes-amz-nb:yearly_deforestation_biome",
        "yearly_deforestation_biome",
        "prodes-amz-nb:prodes_amz_yearly_deforestation_biome",
    ]
    session = _sicar_session()

    for camada in camadas:
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": camada,
            "outputFormat": "application/json",
            "bbox": bbox_4326,
            "maxFeatures": "5000",
        }
        try:
            r = session.get(PRODES_WFS, params=params, timeout=60, verify=False)
            if r.status_code != 200 or not r.text.strip():
                continue
            data = r.json()
            features = data.get("features", [])
            if not features:
                continue
            gdf = gpd.GeoDataFrame.from_features(features)
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4674")
            else:
                gdf = gdf.to_crs("EPSG:4674")
            imovel_geom = gpd.GeoDataFrame(
                geometry=[shape(json.loads(geom_json))], crs="EPSG:4674"
            )
            result = gpd.overlay(gdf, imovel_geom, how="intersection")
            if not result.empty:
                result["area_ha"] = result.geometry.to_crs("EPSG:32722").area / 10000
            return result
        except Exception:
            continue

    return gpd.GeoDataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_deter(bbox_wkt: str, geom_json: str):
    """
    Busca alertas DETER via WFS TerraBrasilis.
    - typeName=deter_public (sem prefixo, conforme documentação INPE)
    - bbox em EPSG:4326
    - usa _sicar_session() para tolerância TLS
    """
    minx, miny, maxx, maxy = [float(v) for v in bbox_wkt.split(",")]
    bbox_4326 = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

    camadas = [
        "deter-amz:deter_public",
        "deter_public",
        "deter-amz:deter_amz",
    ]
    session = _sicar_session()

    for camada in camadas:
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": camada,
            "outputFormat": "application/json",
            "bbox": bbox_4326,
            "maxFeatures": "5000",
        }
        try:
            r = session.get(DETER_WFS, params=params, timeout=60, verify=False)
            if r.status_code != 200 or not r.text.strip():
                continue
            data = r.json()
            features = data.get("features", [])
            if not features:
                continue
            gdf = gpd.GeoDataFrame.from_features(features)
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4674")
            else:
                gdf = gdf.to_crs("EPSG:4674")
            imovel_geom = gpd.GeoDataFrame(
                geometry=[shape(json.loads(geom_json))], crs="EPSG:4674"
            )
            result = gpd.overlay(gdf, imovel_geom, how="intersection")
            if not result.empty:
                result["area_ha"] = result.geometry.to_crs("EPSG:32722").area / 10000
            return result
        except Exception:
            continue

    return gpd.GeoDataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_focos(bbox_wkt: str, geom_json: str):
    """
    Busca focos de calor via WFS TerraBrasilis (bdqueimadas-light).
    - typeName sem prefixo
    - bbox em EPSG:4326
    - sjoin (pontos dentro do polígono do imóvel)
    - usa _sicar_session() para tolerância TLS
    """
    minx, miny, maxx, maxy = [float(v) for v in bbox_wkt.split(",")]
    bbox_4326 = f"{minx},{miny},{maxx},{maxy},EPSG:4326"

    camadas = [
        "bdqueimadas-light:focos_de_calor",
        "focos_de_calor",
    ]
    session = _sicar_session()

    for camada in camadas:
        params = {
            "service": "WFS",
            "version": "1.1.0",
            "request": "GetFeature",
            "typeName": camada,
            "outputFormat": "application/json",
            "bbox": bbox_4326,
            "maxFeatures": "50000",
        }
        try:
            r = session.get(FOCOS_WFS, params=params, timeout=60, verify=False)
            if r.status_code != 200 or not r.text.strip():
                continue
            data = r.json()
            features = data.get("features", [])
            if not features:
                continue
            gdf = gpd.GeoDataFrame.from_features(features)
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4674")
            else:
                gdf = gdf.to_crs("EPSG:4674")
            imovel_geom = gpd.GeoDataFrame(
                geometry=[shape(json.loads(geom_json))], crs="EPSG:4674"
            )
            # Focos são pontos — sjoin em vez de overlay
            result = gpd.sjoin(gdf, imovel_geom, how="inner", predicate="within")
            return result
        except Exception:
            continue

    return gpd.GeoDataFrame()


# ─────────────────────────────────────────────
# FUNÇÕES DE VISUALIZAÇÃO
# ─────────────────────────────────────────────

def criar_mapa_base(gdf_imovel, zoom=11):
    """Cria mapa Folium centralizado no imóvel."""
    centroide = gdf_imovel.geometry.centroid.iloc[0]
    m = folium.Map(
        location=[centroide.y, centroide.x],
        zoom_start=zoom,
        tiles=None,
    )
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Satélite",
        max_zoom=21,
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)

    # Polígono do imóvel
    gdf_4326 = gdf_imovel.to_crs("EPSG:4326")
    folium.GeoJson(
        gdf_4326.__geo_interface__,
        name="Imóvel CAR",
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "#00e676",
            "weight": 3,
            "dashArray": "6 3",
        },
        tooltip="Imóvel Rural",
    ).add_to(m)

    folium.LayerControl().add_to(m)
    MiniMap(toggle_display=True, tile_layer="OpenStreetMap").add_to(m)
    return m


def criar_mapa_prodes(gdf_imovel, gdf_prodes):
    """Mapa com manchas PRODES sobrepostas ao imóvel."""
    m = criar_mapa_base(gdf_imovel)
    if gdf_prodes is None or gdf_prodes.empty:
        return m

    gdf_4326 = gdf_prodes.to_crs("EPSG:4326")
    anos = sorted(gdf_4326["year"].dropna().unique()) if "year" in gdf_4326.columns else []
    colormap = px.colors.sequential.YlOrRd
    n = max(len(anos), 1)

    for i, ano in enumerate(anos):
        subset = gdf_4326[gdf_4326["year"] == ano]
        cor = colormap[int(i / n * (len(colormap) - 1))]
        folium.GeoJson(
            subset.__geo_interface__,
            name=f"PRODES {ano}",
            style_function=lambda x, c=cor: {
                "fillColor": c, "color": c,
                "weight": 1, "fillOpacity": 0.65,
            },
            tooltip=folium.GeoJsonTooltip(fields=["year", "area_ha"],
                                           aliases=["Ano", "Área (ha)"],
                                           localize=True),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def criar_mapa_deter(gdf_imovel, gdf_deter):
    """Mapa com alertas DETER sobrepostos ao imóvel."""
    m = criar_mapa_base(gdf_imovel)
    if gdf_deter is None or gdf_deter.empty:
        return m

    gdf_4326 = gdf_deter.to_crs("EPSG:4326")
    col_classe = next((c for c in ["classname", "classe", "class_name"] if c in gdf_4326.columns), None)

    cor_map = {k: v[1] for k, v in DETER_CLASSES.items()}

    folium.GeoJson(
        gdf_4326.__geo_interface__,
        name="Alertas DETER",
        style_function=lambda x: {
            "fillColor": cor_map.get(
                str(x["properties"].get(col_classe, "")), "#f39c12"
            ),
            "color": "#d35400",
            "weight": 1.5,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[col_classe, "area_ha"] if col_classe else ["area_ha"],
            aliases=["Classe", "Área (ha)"] if col_classe else ["Área (ha)"],
            localize=True,
        ),
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def grafico_prodes_anual(gdf_prodes):
    """Gráfico de barras: área desmatada por ano (PRODES)."""
    if gdf_prodes is None or gdf_prodes.empty or "year" not in gdf_prodes.columns:
        return None
    df = gdf_prodes.groupby("year")["area_ha"].sum().reset_index()
    df.columns = ["Ano", "Área (ha)"]
    df = df.sort_values("Ano")
    fig = px.bar(df, x="Ano", y="Área (ha)",
                 color="Área (ha)",
                 color_continuous_scale="YlOrRd",
                 title="Área Desmatada por Ano (ha)",
                 labels={"Área (ha)": "ha"})
    fig.update_layout(
        height=280, margin=dict(t=40, b=20, l=20, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
        coloraxis_showscale=False,
        font_family="DM Sans",
    )
    return fig


def grafico_deter_mensal(gdf_deter):
    """Gráfico de linha: alertas DETER por mês/ano."""
    if gdf_deter is None or gdf_deter.empty:
        return None
    col_data = next((c for c in ["view_date", "data", "date", "data_detec"] if c in gdf_deter.columns), None)
    if not col_data:
        return None
    df = gdf_deter.copy()
    df["data_dt"] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=["data_dt"])
    df["mes_ano"] = df["data_dt"].dt.to_period("M").astype(str)
    resumo = df.groupby("mes_ano").agg(
        n_alertas=("area_ha", "count"),
        area_ha=("area_ha", "sum")
    ).reset_index().sort_values("mes_ano")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=resumo["mes_ano"], y=resumo["area_ha"],
                         name="Área (ha)", marker_color="#f39c12", opacity=0.7), secondary_y=False)
    fig.add_trace(go.Scatter(x=resumo["mes_ano"], y=resumo["n_alertas"],
                              name="Nº Alertas", line=dict(color="#e74c3c", width=2),
                              mode="lines+markers"), secondary_y=True)
    fig.update_layout(height=280, margin=dict(t=40, b=20, l=20, r=20),
                      title="Alertas DETER por Mês",
                      plot_bgcolor="white", paper_bgcolor="white",
                      font_family="DM Sans",
                      legend=dict(orientation="h", y=-0.3))
    fig.update_yaxes(title_text="Área (ha)", secondary_y=False)
    fig.update_yaxes(title_text="Nº Alertas", secondary_y=True)
    return fig


def grafico_focos_anual(df_focos: pd.DataFrame):
    """Gráfico de barras: focos por ano."""
    if df_focos.empty or "ano" not in df_focos.columns:
        return None
    resumo = df_focos.groupby("ano")["focos"].sum().reset_index().sort_values("ano")
    fig = px.bar(resumo, x="ano", y="focos",
                 color="focos", color_continuous_scale="OrRd",
                 title="Focos de Calor por Ano",
                 labels={"focos": "Nº Focos", "ano": "Ano"})
    fig.update_layout(height=280, margin=dict(t=40, b=20, l=20, r=20),
                      plot_bgcolor="white", paper_bgcolor="white",
                      coloraxis_showscale=False, font_family="DM Sans")
    return fig


def grafico_focos_mensal(df_focos: pd.DataFrame):
    """Heatmap: focos por mês × ano."""
    if df_focos.empty or "ano" not in df_focos.columns or "mes" not in df_focos.columns:
        return None
    pivot = df_focos.pivot_table(index="mes", columns="ano", values="focos",
                                  aggfunc="sum", fill_value=0)
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    pivot.index = [meses[i-1] for i in pivot.index if 1 <= i <= 12]

    fig = px.imshow(pivot, color_continuous_scale="YlOrRd",
                    title="Focos por Mês × Ano (heatmap)",
                    labels={"x": "Ano", "y": "Mês", "color": "Focos"},
                    aspect="auto")
    fig.update_layout(height=300, margin=dict(t=40, b=20, l=60, r=20),
                      font_family="DM Sans")
    return fig


# ─────────────────────────────────────────────
# PARSING / NORMALIZAÇÃO DE DADOS
# ─────────────────────────────────────────────

def normalizar_focos(gdf) -> pd.DataFrame:
    """
    Normaliza GeoDataFrame de focos WFS para DataFrame com colunas
    padronizadas: ano, mes, focos (contagem = 1 por ponto).
    """
    if gdf is None or (hasattr(gdf, "empty") and gdf.empty):
        return pd.DataFrame()
    df = pd.DataFrame(gdf.drop(columns="geometry", errors="ignore"))
    col_data = next(
        (c for c in ["data_hora_gmt", "data_pas", "data", "datahora", "acq_date", "date"]
         if c in df.columns), None
    )
    if col_data:
        df["data_dt"] = pd.to_datetime(df[col_data], errors="coerce")
        df["ano"] = df["data_dt"].dt.year
        df["mes"] = df["data_dt"].dt.month
        df["focos"] = 1
        return df
    # Fallback: se já tiver ano/mes
    if "ano" in df.columns and "mes" in df.columns:
        df["focos"] = 1
        return df
    return pd.DataFrame()


def extrair_info_imovel(gdf: gpd.GeoDataFrame) -> dict:
    """Extrai campos relevantes do GDF do SICAR."""
    row = gdf.iloc[0]
    props = row.to_dict()
    area_ha = gdf.to_crs("EPSG:32722").geometry.area.iloc[0] / 10000

    return {
        "cod_imovel": props.get("cod_imovel", props.get("codigo", "—")),
        "nome": props.get("nom_imovel", props.get("nome", "Não informado")),
        "municipio": props.get("nom_municipio", props.get("municipio", "—")),
        "estado": props.get("sig_estado", props.get("estado", "PA")),
        "area_ha": round(area_ha, 2),
        "situacao": props.get("ind_status", props.get("situacao", "—")),
        "tipo": props.get("ind_tipo", props.get("tipo", "—")),
        "cpf_cnpj": "***.***.***-**",  # mascarado LGPD
    }


def get_bbox_str(gdf: gpd.GeoDataFrame) -> str:
    """Retorna bbox como string 'minx,miny,maxx,maxy'."""
    b = gdf.total_bounds
    return f"{b[0]},{b[1]},{b[2]},{b[3]}"


# ─────────────────────────────────────────────
# INTERFACE PRINCIPAL
# ─────────────────────────────────────────────

# HEADER
st.markdown("""
<div class="hero-header">
    <div class="hero-badge">🌿 PARÁ · AMAZÔNIA LEGAL</div>
    <div class="hero-title">Diagnóstico Ambiental<br>de Imóveis Rurais</div>
    <div class="hero-subtitle">PRODES · DETER · Focos de Calor — dados públicos INPE/SICAR</div>
</div>
""", unsafe_allow_html=True)

# BUSCA
with st.container():
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        codigo_car = st.text_input(
            "Código CAR do Imóvel",
            placeholder="Ex: PA-1500602-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            label_visibility="collapsed",
            key="car_input"
        )
    with col_btn:
        buscar = st.button("🔍 Consultar", type="primary", use_container_width=True)
    st.caption("🔒 Dados de CPF/CNPJ são exibidos de forma mascarada conforme a LGPD. "
               "As informações são obtidas diretamente das bases públicas SICAR/INPE.")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# EXECUÇÃO DA CONSULTA
# ─────────────────────────────────────────────
if buscar and codigo_car.strip():
    codigo_car = codigo_car.strip().upper()

    # Validação básica
    if not re.match(r"^PA-", codigo_car, re.IGNORECASE):
        st.warning("⚠️ Para esta versão, informe um código CAR do **estado do Pará** (iniciando com **PA-**).")
        st.stop()

    with st.spinner("🔄 Consultando SICAR — buscando imóvel..."):
        gdf_imovel = buscar_imovel_car(codigo_car)

    if gdf_imovel is None or gdf_imovel.empty:
        st.error("❌ Imóvel não encontrado. Verifique o código CAR e tente novamente.")
        st.warning(
            f"**Código consultado:** `{codigo_car}`\n\n"
            "**Possíveis causas:**\n"
            "- Código digitado com erro (verifique hífens e letras)\n"
            "- Imóvel ainda não publicado no SICAR federal\n"
            "- Serviço SICAR temporariamente indisponível\n\n"
            "💡 Confirme o código em: https://www.car.gov.br/publico/imoveis/index"
        )
        st.stop()

    info = extrair_info_imovel(gdf_imovel)
    bbox = get_bbox_str(gdf_imovel)
    geom_json = json.dumps(mapping(gdf_imovel.geometry.iloc[0]))

    # ── BLOCO: INFORMAÇÕES DO IMÓVEL ──────────────────────────────
    st.markdown('<div class="imovel-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="imovel-title">📋 {info["nome"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<small style="color:#666">{info["cod_imovel"]} · {info["municipio"]}/{info["estado"]}</small>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-pill"><strong>{info["area_ha"]:,.1f} ha</strong>Área Total</div>
        <div class="metric-pill"><strong>{info["municipio"]}</strong>Município</div>
        <div class="metric-pill"><strong>{info["situacao"]}</strong>Situação CAR</div>
        <div class="metric-pill"><strong>{info["tipo"]}</strong>Tipo</div>
        <div class="metric-pill"><strong>{info["cpf_cnpj"]}</strong>CPF/CNPJ</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Mapa geral do imóvel
    with st.expander("🗺️ Ver localização do imóvel", expanded=True):
        mapa_geral = criar_mapa_base(gdf_imovel, zoom=12)
        st_folium(mapa_geral, width="100%", height=400, key="mapa_geral",
                  returned_objects=[])

    st.divider()

    # ── CONSULTAS PARALELAS ────────────────────────────────────────
    with st.spinner("🔄 Consultando PRODES, DETER e Focos de Calor..."):
        gdf_prodes = buscar_prodes(bbox, geom_json)
        gdf_deter  = buscar_deter(bbox, geom_json)
        gdf_focos  = buscar_focos(bbox, geom_json)

    df_focos = normalizar_focos(gdf_focos)

    # ── 3 COLUNAS DE DIAGNÓSTICO ──────────────────────────────────
    col1, col2, col3 = st.columns(3)

    # ── PRODES ────────────────────────────────────────────────────
    with col1:
        st.markdown('<div class="bloco-header bloco-prodes">🌳 PRODES — Desmatamento</div>',
                    unsafe_allow_html=True)

        if gdf_prodes is not None and not gdf_prodes.empty:
            area_total_desmat = gdf_prodes["area_ha"].sum() if "area_ha" in gdf_prodes.columns else 0
            perc = (area_total_desmat / info["area_ha"] * 100) if info["area_ha"] > 0 else 0
            n_anos = gdf_prodes["year"].nunique() if "year" in gdf_prodes.columns else 0
            ultimo_ano = gdf_prodes["year"].max() if "year" in gdf_prodes.columns else "—"

            c1a, c1b = st.columns(2)
            with c1a:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#c0392b">{area_total_desmat:,.1f}</div>
                    <div class="lbl">ha desmatados</div></div>""", unsafe_allow_html=True)
            with c1b:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#e67e22">{perc:.1f}%</div>
                    <div class="lbl">da propriedade</div></div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="stat-box">
                <div class="val" style="color:#2980b9">{n_anos}</div>
                <div class="lbl">anos com registro · último: {ultimo_ano}</div></div>""",
                unsafe_allow_html=True)

            # Gráfico anual
            fig_pa = grafico_prodes_anual(gdf_prodes)
            if fig_pa:
                st.plotly_chart(fig_pa, use_container_width=True, config={"displayModeBar": False})

            # Mapa PRODES
            with st.expander("🗺️ Mapa PRODES"):
                m_prodes = criar_mapa_prodes(gdf_imovel, gdf_prodes)
                st_folium(m_prodes, width="100%", height=320, key="mapa_prodes",
                          returned_objects=[])
        else:
            st.success("✅ Nenhum registro PRODES encontrado na área do imóvel.")
            st.caption("Fonte: TerraBrasilis / INPE · Amazônia Legal")

    # ── DETER ─────────────────────────────────────────────────────
    with col2:
        st.markdown('<div class="bloco-header bloco-deter">⚠️ DETER — Alertas</div>',
                    unsafe_allow_html=True)

        if gdf_deter is not None and not gdf_deter.empty:
            n_total = len(gdf_deter)
            area_deter = gdf_deter["area_ha"].sum() if "area_ha" in gdf_deter.columns else 0
            col_data_d = next((c for c in ["view_date","data","date"] if c in gdf_deter.columns), None)

            # Alertas ativos (últimos 16 dias) vs histórico
            ativos = 0
            if col_data_d:
                gdf_deter[col_data_d] = pd.to_datetime(gdf_deter[col_data_d], errors="coerce")
                hoje = pd.Timestamp.today()
                ativos = ((hoje - gdf_deter[col_data_d]).dt.days <= 16).sum()

            c2a, c2b = st.columns(2)
            with c2a:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#e74c3c">{n_total}</div>
                    <div class="lbl">alertas totais</div></div>""", unsafe_allow_html=True)
            with c2b:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#f39c12">{area_deter:,.1f}</div>
                    <div class="lbl">ha em alerta</div></div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="stat-box">
                <span class="tag-alerta tag-ativo">● {ativos} ativos (≤16 dias)</span>
                <span class="tag-alerta tag-passado">○ {n_total - ativos} histórico</span>
                </div>""", unsafe_allow_html=True)

            # Classes DETER
            col_classe = next((c for c in ["classname","classe","class_name"] if c in gdf_deter.columns), None)
            if col_classe:
                classes = gdf_deter[col_classe].value_counts()
                fig_cl = px.pie(values=classes.values,
                                names=[DETER_CLASSES.get(c, (c,))[0] for c in classes.index],
                                title="Distribuição por Classe",
                                color_discrete_sequence=px.colors.qualitative.Set2,
                                hole=0.4)
                fig_cl.update_layout(height=250, margin=dict(t=40,b=10,l=10,r=10),
                                     font_family="DM Sans",
                                     legend=dict(font_size=9))
                st.plotly_chart(fig_cl, use_container_width=True, config={"displayModeBar": False})

            # Gráfico mensal
            fig_dm = grafico_deter_mensal(gdf_deter)
            if fig_dm:
                st.plotly_chart(fig_dm, use_container_width=True, config={"displayModeBar": False})

            # Mapa DETER
            with st.expander("🗺️ Mapa DETER"):
                m_deter = criar_mapa_deter(gdf_imovel, gdf_deter)
                st_folium(m_deter, width="100%", height=320, key="mapa_deter",
                          returned_objects=[])
        else:
            st.success("✅ Nenhum alerta DETER encontrado na área do imóvel.")
            st.caption("Fonte: TerraBrasilis / INPE · Amazônia Legal")

    # ── FOCOS DE CALOR ────────────────────────────────────────────
    with col3:
        st.markdown('<div class="bloco-header bloco-fogo">🔥 Focos de Calor</div>',
                    unsafe_allow_html=True)

        if not df_focos.empty and "ano" in df_focos.columns:
            total_focos = len(df_focos)
            ano_pico = df_focos.groupby("ano")["focos"].sum().idxmax() if "focos" in df_focos.columns else "—"
            ano_atual_focos = df_focos[df_focos["ano"] == datetime.now().year]["focos"].sum() \
                if datetime.now().year in df_focos["ano"].values else 0

            c3a, c3b = st.columns(2)
            with c3a:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#c0392b">{total_focos:,}</div>
                    <div class="lbl">focos totais</div></div>""", unsafe_allow_html=True)
            with c3b:
                st.markdown(f"""<div class="stat-box">
                    <div class="val" style="color:#e67e22">{ano_pico}</div>
                    <div class="lbl">ano de pico</div></div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class="stat-box">
                <div class="val" style="color:#2980b9">{int(ano_atual_focos):,}</div>
                <div class="lbl">focos em {datetime.now().year}</div></div>""",
                unsafe_allow_html=True)

            # Gráfico anual
            fig_fa = grafico_focos_anual(df_focos)
            if fig_fa:
                st.plotly_chart(fig_fa, use_container_width=True, config={"displayModeBar": False})

            # Heatmap mensal
            fig_fm = grafico_focos_mensal(df_focos)
            if fig_fm:
                st.plotly_chart(fig_fm, use_container_width=True, config={"displayModeBar": False})


        else:
            st.success("✅ Nenhum foco de calor encontrado para este município.")
            st.caption("Fonte: TerraBrasilis / INPE · bdqueimadas-light WFS · Todos os satélites")

    # ── RODAPÉ ────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="footer-note">
        Diagnóstico gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · 
        Dados: SICAR, PRODES/INPE, DETER/INPE, Focos/TerraBrasilis-INPE · 
        Uso dos dados sujeito às políticas de cada fonte · 
        Para uso oficial, consulte os portais institucionais
    </div>
    """, unsafe_allow_html=True)

elif buscar and not codigo_car.strip():
    st.warning("⚠️ Digite um código CAR para consultar.")

else:
    # Tela de boas-vindas
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem; color: #555;">
        <div style="font-size:4rem">🌿</div>
        <h3 style="font-family:'Syne',sans-serif; color:#1a7a4a; margin:0.5rem 0">
            Como usar esta plataforma
        </h3>
        <p style="max-width:500px; margin:0 auto; line-height:1.7">
            Digite o <strong>código CAR</strong> do imóvel rural no campo acima e clique em 
            <strong>Consultar</strong>.<br>O sistema irá buscar automaticamente os dados de 
            <strong>desmatamento PRODES</strong>, <strong>alertas DETER</strong> e 
            <strong>focos de calor</strong> da área.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        <div style="background:#e8f5e9;border-radius:1rem;padding:1.2rem;text-align:center">
            <div style="font-size:2rem">🌳</div>
            <strong style="font-family:'Syne',sans-serif;color:#2e7d32">PRODES</strong>
            <p style="font-size:0.85rem;margin-top:0.5rem;color:#555">
            Incremento anual de desmatamento com histórico desde 2000. 
            Área desmatada por ano e percentual do imóvel.
            </p>
        </div>""", unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div style="background:#fff3e0;border-radius:1rem;padding:1.2rem;text-align:center">
            <div style="font-size:2rem">⚠️</div>
            <strong style="font-family:'Syne',sans-serif;color:#e65100">DETER</strong>
            <p style="font-size:0.85rem;margin-top:0.5rem;color:#555">
            Alertas de desmatamento em tempo quase-real. Distingue alertas 
            ativos (≤16 dias) do histórico completo por classe.
            </p>
        </div>""", unsafe_allow_html=True)
    with col_c:
        st.markdown("""
        <div style="background:#fce4ec;border-radius:1rem;padding:1.2rem;text-align:center">
            <div style="font-size:2rem">🔥</div>
            <strong style="font-family:'Syne',sans-serif;color:#c62828">Focos de Calor</strong>
            <p style="font-size:0.85rem;margin-top:0.5rem;color:#555">
            Detecção de focos via satélite AQUA. Totais anuais e mensais 
            com heatmap de sazonalidade do fogo.
            </p>
        </div>""", unsafe_allow_html=True)
