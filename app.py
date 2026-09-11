import base64
import csv
import datetime
import io
import os
from pathlib import Path
import re
from urllib.parse import quote
import libsql_client
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont

# --- COMPONENTE DE PATRÓN SEGURO ---
_COMPONENT_DIR = Path(__file__).resolve().parent / "pattern_drawer"
_COMPONENT_DIR.mkdir(parents=True, exist_ok=True)
_COMPONENT_FILE = _COMPONENT_DIR / "index.html"

_HTML_PATRON_CONTENIDO = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <style>
    html, body { margin: 0; padding: 0; background: transparent; }
    canvas { display: block; width: 220px; height: 200px; background: #0f172a; border: 0; cursor: crosshair; touch-action: none; }
  </style>
</head>
<body>
  <canvas id="canvas" width="220" height="200"></canvas>
  <script>
    const READY = 'streamlit:componentReady';
    const RENDER = 'streamlit:render';
    const VALUE = 'streamlit:setComponentValue';
    const HEIGHT = 'streamlit:setFrameHeight';
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    const nodes = [
      {id:'1',x:40,y:40},{id:'2',x:110,y:40},{id:'3',x:180,y:40},
      {id:'4',x:40,y:100},{id:'5',x:110,y:100},{id:'6',x:180,y:100},
      {id:'7',x:40,y:160},{id:'8',x:110,y:160},{id:'9',x:180,y:160}
    ];
    let sequence = [];
    let drawing = false;

    function send(type, data) {
      window.parent.postMessage(Object.assign({isStreamlitMessage:true, type:type}, data || {}), '*');
    }
    function setValue() { send(VALUE, {value:sequence.join(''), dataType:'json'}); }
    function draw() {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      if (sequence.length > 1) {
        const coords = sequence.map(id => nodes.find(n => n.id === id));
        ctx.beginPath(); ctx.moveTo(coords[0].x, coords[0].y);
        coords.slice(1).forEach(n => ctx.lineTo(n.x,n.y));
        ctx.strokeStyle='#0284c7'; ctx.lineWidth=5; ctx.lineCap='round'; ctx.lineJoin='round'; ctx.stroke();
        ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2.5; ctx.stroke();
      }
      nodes.forEach(n => {
        const active = sequence.includes(n.id);
        if (active) { ctx.beginPath(); ctx.arc(n.x,n.y,18,0,Math.PI*2); ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.stroke(); }
        ctx.beginPath(); ctx.arc(n.x,n.y,active?14:9,0,Math.PI*2);
        ctx.fillStyle=active?'#22c55e':'#1e293b'; ctx.fill(); ctx.strokeStyle='#38bdf8'; ctx.lineWidth=2; ctx.stroke();
        ctx.fillStyle=active?'white':'#94a3b8'; ctx.font='bold 10px Arial'; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(n.id,n.x,n.y);
      });
    }
    function findPoint(e) {
      const r=canvas.getBoundingClientRect();
      const x=(e.clientX-r.left)*canvas.width/r.width, y=(e.clientY-r.top)*canvas.height/r.height;
      return nodes.find(n => Math.abs(x-n.x)<25 && Math.abs(y-n.y)<25);
    }
    canvas.addEventListener('pointerdown', e => {
      e.preventDefault(); drawing=true; sequence=[]; const n=findPoint(e); if(n) sequence.push(n.id); draw(); setValue();
    });
    canvas.addEventListener('pointermove', e => {
      if(!drawing) return; e.preventDefault(); const n=findPoint(e);
      if(n && !sequence.includes(n.id)) { sequence.push(n.id); draw(); setValue(); }
    });
    window.addEventListener('pointerup', () => { if(drawing){ drawing=false; setValue(); } });
    window.addEventListener('message', e => {
      if(e.data && e.data.type===RENDER) {
        const incoming=String((e.data.args||{}).sequence||'').replace(/[^1-9]/g,'');
        if(!drawing) sequence=incoming.split(''); draw();
      }
    });
    send(READY, {apiVersion:1});
    send(HEIGHT, {height:205});
    draw();
  </script>
</body>
</html>"""

_COMPONENT_FILE.write_text(_HTML_PATRON_CONTENIDO, encoding="utf-8")

pattern_drawer_component = components.declare_component(
    "pattern_drawer", path=str(_COMPONENT_DIR)
)


# --- COMPONENTE DE FIRMA AUTOMÁTICO ---
_SIGN_DIR = Path(__file__).resolve().parent / "signature_pad"
_SIGN_DIR.mkdir(parents=True, exist_ok=True)
_SIGN_FILE = _SIGN_DIR / "index.html"

_HTML_FIRMA_CONTENIDO = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <style>
    html, body { margin: 0; padding: 0; background: transparent; text-align: center; }
    canvas { display: block; width: 420px; height: 130px; background: #ffffff; border: 2px dashed #38bdf8; border-radius: 8px; cursor: crosshair; touch-action: none; margin: 0 auto; }
  </style>
</head>
<body>
  <canvas id="canvas" width="420" height="130"></canvas>
  <script>
    const READY = 'streamlit:componentReady';
    const RENDER = 'streamlit:render';
    const VALUE = 'streamlit:setComponentValue';
    const HEIGHT = 'streamlit:setFrameHeight';
    const canvas = document.getElementById('canvas');
    const ctx = canvas.getContext('2d');
    let drawing = false;

    function send(type, data) {
      window.parent.postMessage(Object.assign({isStreamlitMessage:true, type:type}, data || {}), '*');
    }
    function setValue(val) { send(VALUE, {value:val, dataType:'json'}); }

    function getPos(e) {
      const r = canvas.getBoundingClientRect();
      return {
        x: (e.clientX - r.left) * (canvas.width / r.width),
        y: (e.clientY - r.top) * (canvas.height / r.height)
      };
    }

    canvas.addEventListener('pointerdown', e => {
      e.preventDefault(); drawing = true;
      const p = getPos(e);
      ctx.beginPath(); ctx.moveTo(p.x, p.y);
    });

    canvas.addEventListener('pointermove', e => {
      if (!drawing) return;
      e.preventDefault();
      const p = getPos(e);
      ctx.lineTo(p.x, p.y);
      ctx.strokeStyle = '#000000'; ctx.lineWidth = 2.5;
      ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
      setValue(canvas.toDataURL('image/png'));
    });

    window.addEventListener('pointerup', () => {
      if (drawing) {
        drawing = false;
        setValue(canvas.toDataURL('image/png'));
      }
    });

    window.addEventListener('message', e => {
      if(e.data && e.data.type===RENDER) {
        const incoming = (e.data.args||{}).sequence;
        if(!incoming) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      }
    });

    send(READY, {apiVersion:1});
    send(HEIGHT, {height:140});
  </script>
</body>
</html>"""

_SIGN_FILE.write_text(_HTML_FIRMA_CONTENIDO, encoding="utf-8")

signature_pad_component = components.declare_component(
    "signature_pad", path=str(_SIGN_DIR)
)


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DATACONTROL JD - JADITHCELL COMUNICACIONES",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

VERSION_ACTUAL = "1.8.58"

TAMANO_LETRA_IMPRESION = "14px"
INTERLINEADO_IMPRESION = "1.35"


def obtener_tiempo_colombia():
  return datetime.datetime.utcnow() - datetime.timedelta(hours=5)


# --- CONEXIÓN UNIVERSAL A TURSO / SQLITE ---
def obtener_conexion():
  if (
      hasattr(st, "secrets")
      and "TURSO_DATABASE_URL" in st.secrets
      and "TURSO_AUTH_TOKEN" in st.secrets
  ):
    url = st.secrets["TURSO_DATABASE_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]
    return libsql_client.connect(url=url, auth_token=token)
  else:
    import sqlite3

    return sqlite3.connect(
        "jadithcell_comunicaciones.db", check_same_thread=False
    )


# --- ESTILOS VISUALES ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d131f;
        color: #ffffff;
    }
    .jd-card {
        background-color: #111822;
        border: 2px solid #1f293d;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .jd-card-inner {
        background-color: #162032;
        border-radius: 6px;
        padding: 10px;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .lbl-amarillo {
        color: #facc15;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 8px;
    }
    .val-subtotal {
        font-family: 'Consolas', monospace;
        font-size: 18px;
        color: #00ffcc;
        font-weight: bold;
        text-align: right;
    }
    .val-total {
        font-family: 'Consolas', monospace;
        font-size: 26px;
        color: #00ffcc;
        font-weight: bold;
        text-align: right;
    }
    .status-bar {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0f172a;
        color: #10b981;
        padding: 6px 20px;
        font-weight: bold;
        font-size: 12px;
        border-top: 1px solid #1f293d;
        z-index: 999;
    }
    div.stButton > button {
        background-color: #1f293d !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 4px !important;
        height: 30px !important;
        font-size: 11px !important;
        padding: 0px 4px !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #16a34a !important;
        color: white !important;
        font-size: 16px !important;
        height: 45px !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] button div p,
    .stTabs [data-baseweb="tab-list"] button {
        color: #22c55e !important;
        font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] div p,
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #ef4444 !important;
        font-weight: bold !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #ef4444 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SISTEMA DE AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False

if not st.session_state.autenticado:
  st.markdown("<br><br>", unsafe_allow_html=True)
  st.markdown(
      "<h2 style='text-align: center; color: #38bdf8;'>🔐 DATACONTROL JD -"
      " ACCESO SEGURO</h2>",
      unsafe_allow_html=True,
  )
  col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
  with col_l2:
    st.markdown('<div class="jd-card">', unsafe_allow_html=True)
    with st.form(key="form_login"):
      usuario_ingresado = st.text_input("Usuario", value="JADITHCELL")
      password_ingresado = st.text_input(
          "Contraseña", type="password", value="19892026"
      )
      btn_ingresar = st.form_submit_button(
          "Ingresar al Sistema", type="primary", use_container_width=True
      )

      if btn_ingresar:
        if (
            usuario_ingresado == "JADITHCELL"
            and password_ingresado == "19892026"
        ):
          st.session_state.autenticado = True
          st.rerun()
        else:
          st.error("Usuario o contraseña incorrectos.")
    st.markdown("</div>", unsafe_allow_html=True)
  st.stop()
else:
  with st.sidebar:
    st.markdown("### ⚙️ Control de Sesión")
    if st.button("🚪 Cerrar Sesión"):
      st.session_state.autenticado = False
      st.rerun()


# --- INICIALIZACIÓN Y MIGRACIÓN DE BD ---
def inicializar_bd():
  conn = obtener_conexion()
  cursor = conn.cursor()

  cursor.execute("""CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        codigo TEXT,
                        nombre TEXT, 
                        precio_compra REAL, 
                        precio_venta REAL, 
                        stock INTEGER,
                        proveedor TEXT,
                        categoria TEXT)""")

  cursor.execute("""CREATE TABLE IF NOT EXISTS ordenes_servicio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente TEXT,
                        cedula TEXT,
                        telefono TEXT,
                        direccion TEXT,
                        equipo TEXT,
                        imei TEXT,
                        falla TEXT,
                        costo REAL,
                        abono REAL,
                        estado TEXT,
                        pin_patron TEXT,
                        detalles_chequeo TEXT,
                        foto_path TEXT,
                        fecha TEXT)""")

  cursor.execute("""CREATE TABLE IF NOT EXISTS ventas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT,
                        nombre TEXT,
                        cantidad INTEGER,
                        total REAL,
                        imei1 TEXT,
                        imei2 TEXT,
                        prestamo INTEGER DEFAULT 0,
                        notas TEXT,
                        fecha TEXT)""")

  cursor.execute("""CREATE TABLE IF NOT EXISTS configuracion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_empresa TEXT,
                        propietario TEXT,
                        nit TEXT,
                        direccion TEXT,
                        telefono TEXT,
                        garantia_dias TEXT,
                        garantia_taller TEXT,
                        logo_path TEXT,
                        modo_taller INTEGER)""")

  cursor.execute("SELECT COUNT(*) FROM configuracion")
  res = cursor.fetchone()
  count_cfg = res[0] if res else 0
  if count_cfg == 0:
    cursor.execute(
        "INSERT INTO configuracion (nombre_empresa, propietario, nit,"
        " direccion, telefono, garantia_dias, garantia_taller, logo_path,"
        " modo_taller) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "JADITHCELL COMUNICACIONES",
            "GADIEL NOVOA GUTIERREZ",
            "N/A",
            "Los Andes, Magdalena",
            "321 676 5590",
            "30 días de garantía en accesorios",
            "30 días de garantía en reparaciones (No cubre humedad o golpes)",
            "",
            1,
        ),
    )

  for col_sql in [
      "ALTER TABLE configuracion ADD COLUMN modo_taller INTEGER DEFAULT 1",
      "ALTER TABLE ventas ADD COLUMN prestamo INTEGER DEFAULT 0",
      "ALTER TABLE ventas ADD COLUMN imei1 TEXT",
      "ALTER TABLE ventas ADD COLUMN imei2 TEXT",
      "ALTER TABLE ventas ADD COLUMN notas TEXT",
      "ALTER TABLE ordenes_servicio ADD COLUMN firma_path TEXT",
  ]:
    try:
      cursor.execute(col_sql)
    except:
      pass

  if hasattr(conn, "commit"):
    conn.commit()
  if hasattr(conn, "close"):
    conn.close()


inicializar_bd()


def obtener_datos_config():
  try:
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nombre_empresa, propietario, nit, direccion, telefono,"
        " garantia_dias, garantia_taller, logo_path, modo_taller FROM"
        " configuracion WHERE id = 1"
    )
    row = cursor.fetchone()
    if hasattr(conn, "close"):
      conn.close()
    if row:
      return {
          "empresa": row[0] or "JADITHCELL COMUNICACIONES",
          "propietario": row[1] or "GADIEL NOVOA GUTIERREZ",
          "nit": row[2] or "N/A",
          "direccion": row[3] or "Los Andes, Magdalena",
          "telefono": row[4] or "321 676 5590",
          "garantia": row[5] or "30 días de garantía en accesorios",
          "garantia_taller": row[6] or "30 días de garantía en reparaciones",
          "logo_path": row[7] or "",
          "modo_taller": int(row[8]) if row[8] is not None else 1,
      }
  except:
    pass
  return {
      "empresa": "JADITHCELL COMUNICACIONES",
      "propietario": "GADIEL NOVOA GUTIERREZ",
      "nit": "N/A",
      "direccion": "Los Andes, Magdalena",
      "telefono": "321 676 5590",
      "garantia": "30 días de garantía en accesorios",
      "garantia_taller": "30 días de garantía en reparaciones",
      "logo_path": "",
      "modo_taller": 1,
  }


cfg = obtener_datos_config()

if "carrito" not in st.session_state:
  st.session_state.carrito = []
if "recibo_generado" not in st.session_state:
  st.session_state.recibo_generado = None
if "recibo_taller" not in st.session_state:
  st.session_state.recibo_taller = None
if "ficha_orden_id" not in st.session_state:
  st.session_state.ficha_orden_id = None
if "patron_secuencia" not in st.session_state:
  st.session_state.patron_secuencia = ""
if "firma_secuencia" not in st.session_state:
  st.session_state.firma_secuencia = ""
if "form_counter" not in st.session_state:
  st.session_state.form_counter = 0
if "confirmar_borrado_inv" not in st.session_state:
  st.session_state.confirmar_borrado_inv = False

fc = st.session_state.form_counter

if "val_ced" not in st.session_state:
  st.session_state.val_ced = ""
if "val_nom" not in st.session_state:
  st.session_state.val_nom = ""
if "val_tel" not in st.session_state:
  st.session_state.val_tel = ""
if "val_dir" not in st.session_state:
  st.session_state.val_dir = ""

st.markdown(f"### ⚙️ DATACONTROL JD v{VERSION_ACTUAL} - {cfg['empresa']}")

tabs_labels = ["🛒 Módulo de Ventas", "📦 Inventario"]
if cfg["modo_taller"] == 1:
  tabs_labels.append("➕ Crear Orden")
  tabs_labels.append("🛠️ Servicios")
tabs_labels.append("⚙️ Configuración Negocio")

tabs = st.tabs(tabs_labels)

# =========================================================
# 🛒 MÓDULO DE VENTAS
# =========================================================
with tabs[0]:
  if cfg["logo_path"] and os.path.exists(cfg["logo_path"]):
    col_lg1, col_lg2, col_lg3 = st.columns([2, 1, 2])
    with col_lg2:
      st.image(cfg["logo_path"], width=120)

  st.markdown('<div class="jd-card">', unsafe_allow_html=True)
  c_col1, c_col2, c_col3 = st.columns(3)
  with c_col1:
    st.markdown(
        '<div class="lbl-amarillo">Identificación Cliente</div>',
        unsafe_allow_html=True,
    )
    v_cedula = st.text_input(
        "Cédula",
        placeholder="Cédula o NIT...",
        label_visibility="collapsed",
        key="v_ced",
    )
  with c_col2:
    st.markdown(
        '<div class="lbl-amarillo">Nombre Cliente</div>',
        unsafe_allow_html=True,
    )
    v_nombre_cliente = st.text_input(
        "Nombre",
        placeholder="Nombre completo...",
        label_visibility="collapsed",
        key="v_nom",
    )
  with c_col3:
    st.markdown(
        '<div class="lbl-amarillo">Teléfono Cliente</div>',
        unsafe_allow_html=True,
    )
    v_telefono = st.text_input(
        "Teléfono",
        placeholder="Número de contacto...",
        label_visibility="collapsed",
        key="v_tel",
    )
  st.markdown("</div>", unsafe_allow_html=True)

  col_izq, col_der = st.columns([2.8, 1.2])

  with col_izq:
    st.markdown('<div class="jd-card">', unsafe_allow_html=True)

    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, codigo, nombre, precio_venta, stock FROM productos WHERE"
        " stock > 0 ORDER BY categoria ASC, nombre ASC"
    )
    lista_prods = cursor.fetchall()
    if hasattr(conn, "close"):
      conn.close()

    dict_por_codigo = {str(p[1]): p for p in lista_prods if p[1]}
    dict_por_nombre = {
        f"{p[2]} (Stock: {p[4]} | ${p[3]:,.0f})": p for p in lista_prods
    }

    with st.form(key="form_agregar_carrito", clear_on_submit=False):
      b_col1, b_col2, b_col3, b_col4 = st.columns([1.5, 2.5, 0.8, 0.8])
      with b_col1:
        cod_buscado = st.text_input(
            "Búsqueda por Código", placeholder="Código...", key="v_cod_busc"
        )
      with b_col2:
        prod_seleccionado_txt = st.selectbox(
            "Búsqueda por nombre...",
            options=["-- Seleccione producto --"]
            + list(dict_por_nombre.keys()),
            key="v_sel_nom",
        )
      with b_col3:
        v_cantidad = st.number_input(
            "Cant", min_value=1, value=1, step=1, key="v_cant_num"
        )
      with b_col4:
        st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
        btn_add
