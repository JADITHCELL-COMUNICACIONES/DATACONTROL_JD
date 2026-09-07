import streamlit as st
import sqlite3
import datetime
import os
import csv
import re
from pathlib import Path
import pandas as pd
from urllib.parse import quote
import streamlit.components.v1 as components
import shutil
import base64
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
    "pattern_drawer",
    path=str(_COMPONENT_DIR)
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
    "signature_pad",
    path=str(_SIGN_DIR)
)


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DATACONTROL JD - JADITHCELL COMUNICACIONES",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VERSION_ACTUAL = "1.8.28"

TAMANO_LETRA_IMPRESION = "13px"
INTERLINEADO_IMPRESION = "1.3"

def obtener_tiempo_colombia():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5)

# --- ESTILOS VISUALES Y MÓDULOS EN VERDE CON ACTIVO EN ROJO ---
st.markdown("""
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
""", unsafe_allow_html=True)

# --- SISTEMA DE AUTENTICACIÓN Y SESIÓN PERSISTENTE ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🔐 DATACONTROL JD - ACCESO SEGURO</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        usuario_ingresado = st.text_input("Usuario")
        password_ingresado = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if usuario_ingresado == "JADITHCELL" and password_ingresado == "19892026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()
else:
    with st.sidebar:
        st.markdown("### ⚙️ Control de Sesión")
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

# --- INICIALIZACIÓN Y MIGRACIÓN SEGURA DE BD ---
def inicializar_bd():
    conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        codigo TEXT,
                        nombre TEXT, 
                        precio_compra REAL, 
                        precio_venta REAL, 
                        stock INTEGER,
                        proveedor TEXT,
                        categoria TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ordenes_servicio (
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
                        fecha TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo TEXT,
                        nombre TEXT,
                        cantidad INTEGER,
                        total REAL,
                        imei1 TEXT,
                        imei2 TEXT,
                        prestamo INTEGER DEFAULT 0,
                        notas TEXT,
                        fecha TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre_empresa TEXT,
                        propietario TEXT,
                        nit TEXT,
                        direccion TEXT,
                        telefono TEXT,
                        garantia_dias TEXT,
                        garantia_taller TEXT,
                        logo_path TEXT,
                        modo_taller INTEGER)''')

    cursor.execute("SELECT COUNT(*) FROM configuracion")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO configuracion (nombre_empresa, propietario, nit, direccion, telefono, garantia_dias, garantia_taller, logo_path, modo_taller) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        ("JADITHCELL COMUNICACIONES", "GADIEL NOVOA GUTIERREZ", "N/A", "Los Andes, Magdalena", "321 676 5590", "30 días de garantía en accesorios", "30 días de garantía en reparaciones (No cubre humedad o golpes)", "", 1))
    
    for col_sql in [
        "ALTER TABLE configuracion ADD COLUMN modo_taller INTEGER DEFAULT 1",
        "ALTER TABLE ventas ADD COLUMN prestamo INTEGER DEFAULT 0",
        "ALTER TABLE ventas ADD COLUMN imei1 TEXT",
        "ALTER TABLE ventas ADD COLUMN imei2 TEXT",
        "ALTER TABLE ventas ADD COLUMN notas TEXT",
        "ALTER TABLE ordenes_servicio ADD COLUMN firma_path TEXT"
    ]:
        try:
            cursor.execute(col_sql)
            conn.commit()
        except:
            pass

    conn.commit()
    conn.close()

inicializar_bd()

def obtener_datos_config():
    try:
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_empresa, propietario, nit, direccion, telefono, garantia_dias, garantia_taller, logo_path, modo_taller FROM configuracion WHERE id = 1")
        row = cursor.fetchone()
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
                "modo_taller": int(row[8]) if row[8] is not None else 1
            }
    except: pass
    return {
        "empresa": "JADITHCELL COMUNICACIONES",
        "propietario": "GADIEL NOVOA GUTIERREZ",
        "nit": "N/A",
        "direccion": "Los Andes, Magdalena",
        "telefono": "321 676 5590",
        "garantia": "30 días de garantía en accesorios",
        "garantia_taller": "30 días de garantía en reparaciones",
        "logo_path": "",
        "modo_taller": 1
    }

cfg = obtener_datos_config()

if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'recibo_generado' not in st.session_state: st.session_state.recibo_generado = None
if 'recibo_taller' not in st.session_state: st.session_state.recibo_taller = None
if 'ficha_orden_id' not in st.session_state: st.session_state.ficha_orden_id = None
if 'patron_secuencia' not in st.session_state: st.session_state.patron_secuencia = ""
if 'firma_secuencia' not in st.session_state: st.session_state.firma_secuencia = ""
if 'form_counter' not in st.session_state: st.session_state.form_counter = 0
if 'confirmar_borrado_inv' not in st.session_state: st.session_state.confirmar_borrado_inv = False

st.markdown(f"### ⚙️ DATACONTROL JD v{VERSION_ACTUAL} - {cfg['empresa']}")

tabs_labels = ["🛒 Módulo de Ventas", "📦 Inventario"]
if cfg['modo_taller'] == 1:
    tabs_labels.append("🛠️ Órdenes de Servicio (Taller)")
tabs_labels.append("⚙️ Configuración Negocio")

tabs = st.tabs(tabs_labels)

# =========================================================
# 🛒 MÓDULO DE VENTAS
# =========================================================
with tabs[0]:
    if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
        col_lg1, col_lg2, col_lg3 = st.columns([2, 1, 2])
        with col_lg2:
            st.image(cfg['logo_path'], width=120)

    st.markdown('<div class="jd-card">', unsafe_allow_html=True)
    c_col1, c_col2, c_col3 = st.columns(3)
    with c_col1:
        st.markdown('<div class="lbl-amarillo">Identificación Cliente</div>', unsafe_allow_html=True)
        v_cedula = st.text_input("Cédula", placeholder="Cédula o NIT...", label_visibility="collapsed", key="v_ced")
    with c_col2:
        st.markdown('<div class="lbl-amarillo">Nombre Cliente</div>', unsafe_allow_html=True)
        v_nombre_cliente = st.text_input("Nombre", placeholder="Nombre completo...", label_visibility="collapsed", key="v_nom")
    with c_col3:
        st.markdown('<div class="lbl-amarillo">Teléfono Cliente</div>', unsafe_allow_html=True)
        v_telefono = st.text_input("Teléfono", placeholder="Número de contacto...", label_visibility="collapsed", key="v_tel")
    st.markdown('</div>', unsafe_allow_html=True)

    col_izq, col_der = st.columns([2.8, 1.2])

    with col_izq:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, codigo, nombre, precio_venta, stock FROM productos WHERE stock > 0 ORDER BY categoria ASC, nombre ASC")
        lista_prods = cursor.fetchall()
        conn.close()

        dict_por_codigo = {str(p[1]): p for p in lista_prods if p[1]}
        dict_por_nombre = {f"{p[2]} (Stock: {p[4]} | ${p[3]:,.0f})": p for p in lista_prods}

        with st.form(key="form_agregar_carrito", clear_on_submit=False):
            b_col1, b_col2, b_col3, b_col4 = st.columns([1.5, 2.5, 0.8, 0.8])
            with b_col1:
                cod_buscado = st.text_input("Búsqueda por Código", placeholder="Código...", key="v_cod_busc")
            with b_col2:
                prod_seleccionado_txt = st.selectbox("Búsqueda por nombre...", options=["-- Seleccione producto --"] + list(dict_por_nombre.keys()), key="v_sel_nom")
            with b_col3:
                v_cantidad = st.number_input("Cant", min_value=1, value=1, step=1, key="v_cant_num")
            with b_col4:
                st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
                btn_add = st.form_submit_button("➕ Agregar")
                st.markdown("</div>", unsafe_allow_html=True)

        producto_a_agregar = None
        if btn_add:
            if cod_buscado and cod_buscado in dict_por_codigo:
                producto_a_agregar = dict_por_codigo[cod_buscado]
            elif prod_seleccionado_txt != "-- Seleccione producto --":
                producto_a_agregar = dict_por_nombre[prod_seleccionado_txt]
            
            if producto_a_agregar:
                p_id, p_cod, p_nom, p_pre, p_stk = producto_a_agregar
                p_v_real = p_pre
                if v_cantidad > p_stk:
                    st.warning(f"Stock insuficiente para {p_nom}. Disponible: {p_stk}")
                else:
                    encontrado = False
                    for item in st.session_state.carrito:
                        if item['id'] == p_id:
                            if item['cantidad'] + v_cantidad > p_stk:
                                st.warning(f"Excede stock total disponible ({p_stk}).")
                                encontrado = True
                                break
                            item['cantidad'] += v_cantidad
                            item['total'] = item['cantidad'] * item['precio']
                            encontrado = True
                            break
                    if not encontrado:
                        st.session_state.carrito.append({
                            'id': p_id,
                            'codigo': p_cod or "N/A",
                            'nombre': p_nom,
                            'cantidad': v_cantidad,
                            'precio': p_v_real,
                            'total': p_v_real * v_cantidad
                        })
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- TABLA DE CARRITO ESTILO POS INTEGRADA ---
        st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
        st.markdown('<div class="lbl-celeste">🛒 DETALLE DE VENTA (CARRITO)</div>', unsafe_allow_html=True)
        
        if st.session_state.carrito:
            c_h1, c_h2, c_h3, c_h4, c_h5, c_h6, c_h7 = st.columns([0.6, 1.8, 3.2, 1.0, 1.6, 1.6, 1.2])
            with c_h1: st.markdown("<b style='font-size:11px; color:#94a3b8;'>#</b>", unsafe_allow_html=True)
            with c_h2: st.markdown("<b style='font-size:11px; color:#94a3b8;'>CÓDIGO</b>", unsafe_allow_html=True)
            with c_h3: st.markdown("<b style='font-size:11px; color:#94a3b8;'>PRODUCTO</b>", unsafe_allow_html=True)
            with c_h4: st.markdown("<b style='font-size:11px; color:#94a3b8;'>CANT</b>", unsafe_allow_html=True)
            with c_h5: st.markdown("<b style='font-size:11px; color:#94a3b8;'>PRECIO</b>", unsafe_allow_html=True)
            with c_h6: st.markdown("<b style='font-size:11px; color:#94a3b8;'>TOTAL</b>", unsafe_allow_html=True)
            with c_h7: st.markdown("<b style='font-size:11px; color:#94a3b8;'>ACCIONES</b>", unsafe_allow_html=True)

            st.markdown("<hr style='margin: 4px 0 8px 0; border-color: #1f293d;'>", unsafe_allow_html=True)

            for idx, item in enumerate(st.session_state.carrito):
                r_c1, r_c2, r_c3, r_c4, r_c5, r_c6, r_c7 = st.columns([0.6, 1.8, 3.2, 1.0, 1.6, 1.6, 1.2])
                with r_c1: st.markdown(f"<span style='font-size: 12px; color:#e2e8f0;'>{idx+1}</span>", unsafe_allow_html=True)
                with r_c2: st.markdown(f"<span style='font-size: 12px; color:#38bdf8;'>{item['codigo']}</span>", unsafe_allow_html=True)
                with r_c3: st.markdown(f"<span style='font-size: 12px; color:#ffffff;'><b>{item['nombre']}</b></span>", unsafe_allow_html=True)
                with r_c4: st.markdown(f"<span style='font-size: 12px; color:#00ffcc;'><b>{item['cantidad']}</b></span>", unsafe_allow_html=True)
                with r_c5: st.markdown(f"<span style='font-size: 12px; color:#e2e8f0;'>${item['precio']:,.0f}</span>", unsafe_allow_html=True)
                with r_c6: st.markdown(f"<span style='font-size: 12px; color:#00ffcc;'><b>${item['total']:,.0f}</b></span>", unsafe_allow_html=True)
                
                with r_c7:
                    sub_b1, sub_b2 = st.columns(2)
                    with sub_b1:
                        if st.button("➖", key=f"b_restar_{idx}", help="Restar 1 unidad"):
                            if item['cantidad'] > 1:
                                item['cantidad'] -= 1
                                item['total'] = item['cantidad'] * item['precio']
                            else:
                                st.session_state.carrito.pop(idx)
                            st.rerun()
                    with sub_b2:
                        if st.button("❌", key=f"b_quitar_{idx}", help="Quitar producto"):
                            st.session_state.carrito.pop(idx)
                            st.rerun()
                st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)
        else:
            st.info("El carrito de compras está vacío. Agregue productos arriba.")
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
        st.markdown('<div class="lbl-celeste">Notas del pedido:</div>', unsafe_allow_html=True)
        v_notas = st.text_area("Notas", value="Los cambios se realizan únicamente por defectos de fabricación.", height=68, label_visibility="collapsed", key="v_txt_notas")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_der:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        subtotal_calc = sum(item['total'] for item in st.session_state.carrito)
        
        st.markdown("**Sub Total**")
        st.markdown(f'<div class="val-subtotal">${subtotal_calc:,.2f}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="lbl-amarillo" style="font-size: 15px; margin-top: 10px;">Total</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="val-total">${subtotal_calc:,.2f}</div>', unsafe_allow_html=True)

        st.markdown("<br>**Recibido (Opcional)**", unsafe_allow_html=True)
        v_recibido = st.number_input("Recibido", min_value=0.0, value=0.0, step=1000.0, label_visibility="collapsed", key="v_num_recibido")

        if cfg['modo_taller'] == 1:
            st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
            st.markdown('<div class="lbl-celeste">📱 IMEI / Seriales del Equipo:</div>', unsafe_allow_html=True)
            v_imei1 = st.text_input("IMEI 1", placeholder="IMEI 1", label_visibility="collapsed", key="v_imei1_input")
            v_imei2 = st.text_input("IMEI 2", placeholder="IMEI 2 (Opcional)", label_visibility="collapsed", key="v_imei2_input")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            v_imei1, v_imei2 = "", ""

        check_prestamo = st.checkbox("¿PRESTAMO?", key="v_chk_prestamo")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("VENTA", type="primary", use_container_width=True, key="v_btn_procesar_venta"):
            if not st.session_state.carrito:
                st.error("El carrito está vacío.")
            else:
                try:
                    conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                    cursor = conn.cursor()
                    fecha_ahora = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")

                    for itm in st.session_state.carrito:
                        cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (itm['cantidad'], itm['id']))
                        cursor.execute("INSERT INTO ventas (codigo, nombre, cantidad, total, imei1, imei2, prestamo, notas, fecha) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                       (itm['codigo'], itm['nombre'], itm['cantidad'], itm['total'], v_imei1, v_imei2, 1 if check_prestamo else 0, v_notas, fecha_ahora))
                    conn.commit()
                    conn.close()

                    recibido_final = v_recibido if v_recibido > 0 else subtotal_calc
                    vuelto_calc = recibido_final - subtotal_calc
                    
                    st.session_state.recibo_generado = {
                        "fecha": fecha_ahora,
                        "cliente": v_nombre_cliente or "CONSUMIDOR FINAL",
                        "cedula": v_cedula or "N/A",
                        "telefono": v_telefono or "N/A",
                        "items": list(st.session_state.carrito),
                        "subtotal": subtotal_calc,
                        "recibido": recibido_final,
                        "vuelto": vuelto_calc if vuelto_calc > 0 else 0.0,
                        "imei1": v_imei1,
                        "imei2": v_imei2,
                        "notas": v_notas
                    }
                    st.session_state.carrito = []
                    st.success("¡Venta procesada con éxito!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error procesando venta: {ex}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📊 Cierre de Caja", use_container_width=True, key="v_btn_cierre_caja"):
            hoy = obtener_tiempo_colombia().strftime("%Y-%m-%d")
            conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total) FROM ventas WHERE fecha LIKE ?", (hoy + '%',))
            c_ventas = cursor.fetchone()[0] or 0.0
            try:
                cursor.execute("SELECT SUM(abono) FROM ordenes_servicio WHERE fecha LIKE ?", (hoy + '%',))
                c_abonos = cursor.fetchone()[0] or 0.0
            except: c_abonos = 0.0
            conn.close()
            st.info(f"**Ventas Accesorios:** ${c_ventas:,.2f}\n\n**Abonos Taller:** ${c_abonos:,.2f}\n\n**TOTAL EN CAJA:** ${c_ventas + c_abonos:,.2f}")

        st.markdown('</div>', unsafe_allow_html=True)

    # VISTA PREVIA Y IMPRESIÓN (MARCO ORIGINAL DE 78MM CON ESPACIADO INTERNO APRETADO PARA EVITAR CORTE DERECHO)
    if st.session_state.recibo_generado:
        rg = st.session_state.recibo_generado

        with st.expander("🧾 VISTA PREVIA TICKET POS DE VENTA (80MM)", expanded=True):
            fecha_actual_ticket = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
            
            lineas_ticket = [
                f"==========================================",
                f"        {cfg['empresa']}",
                f"       {cfg['propietario']}",
                f"       NIT / CC: {cfg['nit']}",
                f"        {cfg['direccion']}",
                f"        Cel: {cfg['telefono']}",
                f"==========================================",
                f" TICKET DE VENTA",
                f" FECHA: {fecha_actual_ticket}",
                f"------------------------------------------",
                f" CLIENTE: {rg['cliente']}",
                f" CÉDULA:  {rg['cedula']} | TEL: {rg['telefono']}",
                f"------------------------------------------",
                f" CANT PRODUCTO             TOTAL",
                f"------------------------------------------"
            ]
            for itm in rg['items']:
                lineas_ticket.append(f" {itm['cantidad']:<4} {itm['nombre'][:18]:<19} ${itm['total']:>11,.2f}")
            lineas_ticket.extend([
                f"------------------------------------------",
                f" TOTAL:             ${rg['subtotal']:>18,.2f}",
                f" RECIBIDO:          ${rg['recibido']:>18,.2f}",
                f" CAMBIO:            ${rg['vuelto']:>18,.2f}",
                f"==========================================",
                f" IMEI 1: {rg['imei1']}" if rg['imei1'] else "",
                f" {cfg['garantia']}",
                f"------------------------------------------",
                f"         ¡GRACIAS POR PREFERIRNOS!",
                f"=========================================="
            ])
            ticket_limpio = "\n".join([l for l in lineas_ticket if l is not None and l != ""])
            st.text_area("Ticket POS Venta", value=ticket_limpio.strip(), height=260, disabled=True, key="v_txt_ticket_pos_venta")
            
            logo_base64_str = ""
            if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
                try:
                    with open(cfg['logo_path'], "rb") as img_file:
                        logo_base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                except:
                    logo_base64_str = ""

            col_pr1, col_pr2 = st.columns(2)
            with col_pr1:
                if st.button("🖨️ Imprimir Ticket POS", use_container_width=True, key="btn_imprimir_recibo_venta_directo"):
                    fecha_impresion_real = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
                    ticket_impresion_final = ticket_limpio.replace(fecha_actual_ticket, fecha_impresion_real)
                    
                    logo_html = f'<div style="text-align: center; margin-top: 2px; margin-bottom: 6px;"><img src="data:image/png;base64,{logo_base64_str}" style="width: 90px; height: 90px; object-fit: contain; display: block; margin: 0 auto;" /></div>' if logo_base64_str else ''
                    components.html(f"""
                        <html>
                        <head>
                        <style>
                            @page {{
                                size: 80mm auto;
                                margin: 0;
                            }}
                            html, body {{
                                margin: 0;
                                padding: 0;
                                width: 80mm;
                                background-color: #ffffff;
                                height: auto !important;
                            }}
                            .print-wrapper {{
                                width: 78mm;
                                margin: 0 auto;
                                text-align: center;
                                height: auto !important;
                                padding-bottom: 2mm;
                            }}
                            .ticket-container {{ 
                                text-align: left; 
                                font-family: 'Courier New', Courier, monospace; 
                                font-size: 13px; 
                                line-height: 1.25; 
                                font-weight: bold; 
                                white-space: pre; 
                                display: inline-block;
                                letter-spacing: -0.2px;
                            }}
                        </style>
                        </head>
                        <body onload="window.print()">
                            <div class="print-wrapper">
                                {logo_html}
                                <div class="ticket-container">{ticket_impresion_final}</div>
                            </div>
                        </body>
                        </html>
                    """, height=0)
            with col_pr2:
                if st.button("Cerrar Ticket de Venta", use_container_width=True, key="v_btn_cerrar_ticket"):
                    st.session_state.recibo_generado = None
                    st.rerun()

# =========================================================
# 📦 PESTAÑA: INVENTARIO
# =========================================================
with tabs[1]:
    col_inv_izq, col_inv_der = st.columns([1, 2])

    with col_inv_izq:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.markdown("##### 🔍 BUSCAR PRODUCTO")
        inv_busqueda = st.text_input("Nombre o código...", placeholder="Nombre o código...", label_visibility="collapsed", key="inv_busq_input")

        st.markdown("##### GESTIÓN DE INVENTARIO")
        inv_codigo = st.text_input("Código", placeholder="Código", label_visibility="collapsed", key="inv_cod")
        inv_nombre = st.text_input("Nombre", placeholder="Nombre", label_visibility="collapsed", key="inv_nom")
        inv_compra = st.text_input("Precio Compra", placeholder="Precio Compra", label_visibility="collapsed", key="inv_com")
        inv_venta = st.text_input("Precio Venta", placeholder="Precio Venta", label_visibility="collapsed", key="inv_ven")
        inv_stock = st.text_input("Stock", placeholder="Stock", label_visibility="collapsed", key="inv_stk")
        inv_prov = st.text_input("Proveedor", placeholder="Proveedor", label_visibility="collapsed", key="inv_prov")
        inv_cat = st.text_input("Categoría", placeholder="Categoría", label_visibility="collapsed", key="inv_cat")

        b_col_1, b_col_2 = st.columns(2)
        with b_col_1:
            btn_guardar_inv = st.button("Guardar", use_container_width=True, key="inv_btn_guardar")
        with b_col_2:
            btn_actualizar_inv = st.button("Actualizar", use_container_width=True, key="inv_btn_act")

        b_col_3, b_col_4 = st.columns(2)
        with b_col_3:
            btn_limpiar_inv = st.button("Limpiar", use_container_width=True, key="inv_btn_limp")
        with b_col_4:
            pass

        st.markdown("---")
        st.markdown('<div class="lbl-celeste">📂 Importar Archivo Excel (.xlsx):</div>', unsafe_allow_html=True)
        archivo_subido = st.file_uploader("Cargar archivo", type=["xlsx", "xls", "csv", "html", "htm"], key="uploader_inventario_general", label_visibility="collapsed")

        conn_db = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cur_db = conn_db.cursor()

        if archivo_subido is not None:
            nombre_archivo = archivo_subido.name.lower()
            try:
                importados = 0
                if nombre_archivo.endswith((".xlsx", ".xls")):
                    df_raw = pd.read_excel(archivo_subido, header=None)
                    fila_inicio = 0
                    for idx, row in df_raw.iterrows():
                        fila_str = str(row.values).lower()
                        if 'código' in fila_str or 'nombre' in fila_str:
                            fila_inicio = idx + 1
                            break
                    
                    df_datos = pd.read_excel(archivo_subido, skiprows=fila_inicio, header=None)
                    cur_db.execute("DELETE FROM productos")

                    for _, row in df_datos.iterrows():
                        try:
                            val_codigo = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                            if not val_codigo or val_codigo.lower() == "nan" or val_codigo.lower() == "código":
                                continue

                            c_code = val_codigo
                            c_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                            if not c_name or c_name.lower() == "nan": continue

                            def limpiar_entero(v):
                                try:
                                    if pd.isna(v): return 0
                                    return int(float(str(v).replace('$', '').replace(',', '.')))
                                except: return 0

                            c_comp = limpiar_entero(row.iloc[2])
                            c_vent = limpiar_entero(row.iloc[3])
                            
                            try: c_stk = int(row.iloc[4]) if pd.notna(row.iloc[4]) else 0
                            except: c_stk = 0

                            c_prov = str(row.iloc[7]).strip().upper() if len(row) > 7 and pd.notna(row.iloc[7]) and str(row.iloc[7]).lower() != "nan" else ""
                            c_cate = str(row.iloc[8]).strip().upper() if len(row) > 8 and pd.notna(row.iloc[8]) and str(row.iloc[8]).lower() != "nan" else "GENERAL"

                            cur_db.execute("INSERT INTO productos (codigo, nombre, precio_compra, precio_venta, stock, proveedor, categoria) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                           (c_code, c_name, c_comp, c_vent, c_stk, c_prov, c_cate))
                            importados += 1
                        except: pass

                conn_db.commit()
                st.success(f"¡Inventario importado con éxito! {importados} productos cargados.")
                st.rerun()
            except Exception as err:
                st.error(f"Error procesando el archivo: {err}")

        if btn_limpiar_inv: st.rerun()

        if btn_guardar_inv:
            if inv_nombre:
                try:
                    c_val = int(float(inv_compra)) if inv_compra else 0
                    v_val = int(float(inv_venta)) if inv_venta else 0
                    s_val = int(inv_stock) if inv_stock else 0
                    cur_db.execute("INSERT INTO productos (codigo, nombre, precio_compra, precio_venta, stock, proveedor, categoria) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (inv_codigo, inv_nombre, c_val, v_val, s_val, inv_prov.upper(), inv_cat.upper()))
                    conn_db.commit()
                    st.success("¡Producto guardado exitosamente!")
                    st.rerun()
                except Exception as ex: st.error(f"Error: {ex}")
            else: st.error("El nombre es obligatorio.")

        if btn_actualizar_inv:
            if inv_codigo or inv_nombre:
                try:
                    c_val = int(float(inv_compra)) if inv_compra else 0
                    v_val = int(float(inv_venta)) if inv_venta else 0
                    s_val = int(inv_stock) if inv_stock else 0
                    cur_db.execute("UPDATE productos SET precio_compra=?, precio_venta=?, stock=?, proveedor=?, categoria=?, nombre=? WHERE codigo=? OR nombre=?",
                                   (c_val, v_val, s_val, inv_prov.upper(), inv_cat.upper(), inv_nombre, inv_codigo, inv_nombre))
                    conn_db.commit()
                    st.success("¡Actualizado correctamente!")
                    st.rerun()
                except Exception as ex: st.error(f"Error: {ex}")
            else: st.error("Ingrese código o nombre.")

        cur_db.execute("SELECT precio_compra, precio_venta, stock FROM productos")
        todos_p = cur_db.fetchall()
        total_invertido = sum((p[0] or 0) * (p[2] or 0) for p in todos_p)
        total_valor_venta = sum((p[1] or 0) * (p[2] or 0) for p in todos_p)
        conn_db.close()

        st.markdown(f"""
            <div style="background-color: #161b22; padding: 10px; border-radius: 6px; margin-top: 10px;">
                <div style="color: #ffcc00; font-weight: bold; font-size: 12px;">Invertido: ${total_invertido:,.2f}</div>
                <div style="color: #00ffcc; font-weight: bold; font-size: 12px; margin-top: 4px;">VALOR TOTAL : ${total_valor_venta:,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_inv_der:
        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        query_inv = "SELECT id as ID, codigo as Código, nombre as Nombre, precio_compra as 'Precio Compra', precio_venta as 'Precio Venta', stock as Stock, proveedor as Proveedor, categoria as Categoría FROM productos"
        if inv_busqueda:
            query_inv += f" WHERE nombre LIKE '%{inv_busqueda}%' OR codigo LIKE '%{inv_busqueda}%'"
        query_inv += " ORDER BY categoria ASC, nombre ASC"
        df_inventario_tabla = pd.read_sql(query_inv, conn)
        conn.close()

        if not df_inventario_tabla.empty:
            df_inventario_tabla['Precio Compra'] = df_inventario_tabla['Precio Compra'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
            df_inventario_tabla['Precio Venta'] = df_inventario_tabla['Precio Venta'].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")

        def resaltar_stock_bajo(row):
            try:
                if int(str(row['Stock']).replace(',', '')) <= 1:
                    return ['background-color: #7f1d1d; color: white; font-weight: bold;'] * len(row)
            except: pass
            return [''] * len(row)

        df_styled = df_inventario_tabla.style.apply(resaltar_stock_bajo, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True, height=600)
        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 🛠️ PESTAÑA: ÓRDENES DE SERVICIO (TALLER)
# =========================================================
if cfg['modo_taller'] == 1:
    with tabs[2]:
        if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
            col_tlg1, col_tlg2, col_tlg3 = st.columns([2, 1, 2])
            with col_tlg2:
                st.image(cfg['logo_path'], width=120)

        st.markdown('<div class="jd-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Órdenes de Servicio y Ficha Técnica")
        
        # Lienzo interactivo real para patrón
        def renderizar_lienzo_patron(secuencia_actual):
            secuencia_inicial = "".join(
                c for c in str(secuencia_actual or "") if c in "123456789"
            )
            secuencia = pattern_drawer_component(
                sequence=secuencia_inicial,
                key=f"pattern_drawer_{st.session_state.form_counter}"
            )
            if secuencia is None:
                secuencia = secuencia_inicial
            secuencia = "".join(c for c in str(secuencia) if c in "123456789")
            st.session_state.patron_secuencia = secuencia
            st.caption(f"Secuencia actual: {secuencia or '—'}")
            return secuencia

        # Pad de firma automático (idéntico al funcionamiento del patrón)
        def renderizar_pad_firma(secuencia_actual):
            sec_inicial = str(secuencia_actual or "")
            secuencia = signature_pad_component(
                sequence=sec_inicial,
                key=f"signature_pad_{st.session_state.form_counter}"
            )
            if secuencia is None:
                secuencia = sec_inicial
            st.session_state.firma_secuencia = secuencia
            return secuencia

        fc = st.session_state.form_counter

        with st.expander("📋 REGISTRAR ORDEN DE SERVICIO - JADITHCELL COMUNICACIONES", expanded=True):
            col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
            
            with col_b1:
                st.markdown('<div class="lbl-amarillo">DATOS DEL CLIENTE</div>', unsafe_allow_html=True)
                ot_cliente = st.text_input("Nombre del cliente *", placeholder="* Nombre del cliente", key=f"t_cli_{fc}")
                ot_cedula = st.text_input("Cédula / NIT", placeholder="* Cédula / NIT / ID", key=f"t_ced_{fc}")
                ot_tel = st.text_input("Teléfono *", placeholder="* Teléfono", key=f"t_tel_{fc}")
                ot_dir = st.text_input("Dirección", placeholder="Dirección", key=f"t_dir_{fc}")

            with col_b2:
                st.markdown('<div class="lbl-amarillo">DATOS DEL SERVICIO Y EQUIPO</div>', unsafe_allow_html=True)
                ot_falla = st.text_input("Falla reportada *", placeholder="* Falla reportada", key=f"t_fa_{fc}")
                ot_equipo = st.text_input("Modelo del equipo *", placeholder="* Modelo del equipo", key=f"t_eq_{fc}")
                ot_imei = st.text_input("IMEI / Serial", placeholder="IMEI / Serial", key=f"t_im_{fc}")
                st.markdown("<br>", unsafe_allow_html=True)

            with col_b3:
                st.markdown('<div class="lbl-amarillo">COSTOS Y SEGURIDAD</div>', unsafe_allow_html=True)
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    ot_costo_str = st.text_input("Precio", placeholder="Precio", key=f"t_cos_{fc}")
                with sub_c2:
                    ot_abono_str = st.text_input("Abono", placeholder="Abono", key=f"t_abo_{fc}")
                
                ot_patron_txt = st.text_input("Patrón, PIN o Contraseña", placeholder="Patrón, PIN o Contraseña", key=f"t_pat_{fc}")

            st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
            st.markdown("<div class='lbl-celeste'>🔐 Dibujar Patrón de Desbloqueo (Opcional)</div>", unsafe_allow_html=True)
            patron_col_1, patron_col_2 = st.columns([3, 1])
            with patron_col_1:
                val_lienzo_canvas = renderizar_lienzo_patron(st.session_state.patron_secuencia)
                if val_lienzo_canvas and isinstance(val_lienzo_canvas, str):
                    st.session_state.patron_secuencia = val_lienzo_canvas
            with patron_col_2:
                if st.button("🧹 Limpiar Patrón", key=f"btn_limpiar_pat_{fc}", use_container_width=True):
                    st.session_state.patron_secuencia = ""
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # --- PAD DE FIRMA DIGITAL AUTOMÁTICO (MULTITRAZO) ---
            st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
            st.markdown("<div class='lbl-celeste'>✍️ Firma del Cliente (Digital / Táctil / Mouse)</div>", unsafe_allow_html=True)
            st.caption("Firme con tranquilidad trazo por trazo (puede levantar el dedo o mouse sin perder la firma):")
            
            firma_col_1, firma_col_2 = st.columns([3, 1])
            with firma_col_1:
                val_firma_canvas = renderizar_pad_firma(st.session_state.firma_secuencia)
                if val_firma_canvas and isinstance(val_firma_canvas, str):
                    st.session_state.firma_secuencia = val_firma_canvas
            with firma_col_2:
                if st.button("🧹 Limpiar Firma", key=f"btn_limpiar_firma_{fc}", use_container_width=True):
                    st.session_state.firma_secuencia = ""
                    st.rerun()

            if st.session_state.firma_secuencia:
                st.success("✓ Firma capturada correctamente")

            ot_notas = st.text_input("Notas adicionales / Chequeo físico", placeholder="Notas adicionales / Chequeo físico", key=f"t_not_{fc}")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_btn_reg1, col_btn_reg2 = st.columns([4, 1])
            with col_btn_reg1:
                if st.button("💾 Guardar Orden", type="primary", use_container_width=True, key=f"t_btn_save_{fc}"):
                    patron_guardar = ot_patron_txt.strip() if ot_patron_txt else st.session_state.patron_secuencia.strip()
                    firma_guardar = st.session_state.firma_secuencia if isinstance(st.session_state.firma_secuencia, str) else ""
                    
                    def limpiar_monto(val_txt):
                        if not val_txt: return 0.0
                        try:
                            limpio = str(val_txt).replace('$', '').strip()
                            if '.' in limpio and ',' in limpio:
                                limpio = limpio.replace('.', '').replace(',', '.')
                            elif limpio.count('.') > 1:
                                limpio = limpio.replace('.', '', limpio.count('.') - 1)
                            elif ',' in limpio and '.' not in limpio:
                                limpio = limpio.replace(',', '.')
                            return float(limpio)
                        except:
                            return 0.0

                    val_costo = limpiar_monto(ot_costo_str)
                    val_abono = limpiar_monto(ot_abono_str)

                    if ot_cliente and ot_equipo and ot_falla:
                        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                        cursor = conn.cursor()
                        fecha_ahora = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute('''INSERT INTO ordenes_servicio (cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, foto_path, fecha, firma_path)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                       (ot_cliente, ot_cedula, ot_tel, ot_dir, ot_equipo, ot_imei, ot_falla, val_costo, val_abono, "PENDIENTE", patron_guardar, ot_notas, "", fecha_ahora, firma_guardar))
                        conn.commit()
                        
                        cursor.execute("SELECT last_insert_rowid()")
                        nueva_id = cursor.fetchone()[0]
                        conn.close()

                        st.success("¡Orden de servicio guardada con éxito!")
                        
                        st.session_state.patron_secuencia = ""
                        st.session_state.firma_secuencia = ""
                        st.session_state.form_counter += 1
                        
                        st.session_state.recibo_taller = {
                            "id": nueva_id, "cliente": ot_cliente, "cedula": ot_cedula, "telefono": ot_tel,
                            "equipo": ot_equipo, "imei": ot_imei, "falla": ot_falla, "costo": val_costo,
                            "abono": val_abono, "estado": "PENDIENTE", "patron": patron_guardar,
                            "chequeo": ot_notas, "fecha": fecha_ahora, "firma": firma_guardar
                        }
                        st.rerun()
                    else:
                        st.error("Cliente, modelo del equipo y falla son requeridos.")
            
            with col_btn_reg2:
                if st.button("🛠️ Ficha Técnica", use_container_width=True, key=f"btn_ficha_rapida_{fc}"):
                    conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM ordenes_servicio ORDER BY id DESC LIMIT 1")
                    ultima_o = cursor.fetchone()
                    conn.close()
                    if ultima_o:
                        st.session_state.ficha_orden_id = ultima_o[0]
                        st.rerun()

        if st.session_state.recibo_taller:
            rt = st.session_state.recibo_taller
            fecha_taller_actual = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
            saldo_r = rt['costo'] - rt['abono']

            with st.expander(f"🧾 RECIBO BÁSICO ORDEN #{rt['id']:04d} — LISTO PARA IMPRIMIR", expanded=True):
                if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
                    col_tr1, col_tr2, col_tr3 = st.columns([2, 1, 2])
                    with col_tr2:
                        st.image(cfg['logo_path'], width=100)

                ticket_taller_str = f"""
==========================================
        {cfg['empresa']}
       {cfg['propietario']}
       NIT / CC: {cfg['nit']}
        {cfg['direccion']}
        Cel: {cfg['telefono']}
==========================================
 ORDEN DE SERVICIO N°: {rt['id']:04d}
 FECHA: {fecha_taller_actual}
------------------------------------------
 CLIENTE: {rt['cliente']}
 CÉDULA:  {rt['cedula']} | TEL: {rt['telefono']}
 EQUIPO:  {rt['equipo']}
 IMEI:    {rt['imei']}
 FALLA:   {rt['falla']}
 SEGURIDAD/PATRÓN: {rt['patron']}
 NOTAS:   {rt['chequeo']}
------------------------------------------
 COSTO TOTAL:       ${rt['costo']:,.2f}
 TOTAL ABONADO:     ${rt['abono']:,.2f}
 SALDO PENDIENTE:   ${saldo_r:,.2f}
 ESTADO ACTUAL:     {rt['estado']}
==========================================
{cfg['garantia_taller']}
------------------------------------------
   ¡GRACIAS POR PREFERIRNOS!
==========================================
                """

                ticket_cliente_impresion = f"""
==========================================
        {cfg['empresa']}
       {cfg['propietario']}
       NIT / CC: {cfg['nit']}
        {cfg['direccion']}
        Cel: {cfg['telefono']}
==========================================
 ORDEN DE SERVICIO N°: {rt['id']:04d}
 FECHA: {fecha_taller_actual}
------------------------------------------
 CLIENTE: {rt['cliente']}
 CÉDULA:  {rt['cedula']} | TEL: {rt['telefono']}
 EQUIPO:  {rt['equipo']}
 IMEI:    {rt['imei']}
 FALLA:   {rt['falla']}
 NOTAS:   {rt['chequeo']}
------------------------------------------
 COSTO TOTAL:       ${rt['costo']:,.2f}
 TOTAL ABONADO:     ${rt['abono']:,.2f}
 SALDO PENDIENTE:   ${saldo_r:,.2f}
 ESTADO ACTUAL:     {rt['estado']}
==========================================
{cfg['garantia_taller']}
------------------------------------------
"""

                st.text_area("Ticket Taller", value=ticket_taller_str.strip(), height=260, disabled=True, key="txt_ticket_tall_gen")
                
                logo_base64_str = ""
                if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
                    try:
                        with open(cfg['logo_path'], "rb") as img_file:
                            logo_base64_str = base64.b64encode(img_file.read()).decode('utf-8')
                    except:
                        logo_base64_str = ""

                col_imp1, col_imp2 = st.columns(2)
                with col_imp1:
                    if st.button("🖨️ Imprimir Recibo de Orden", type="primary", use_container_width=True, key="btn_imprimir_recibo_taller_directo"):
                        logo_html = f'<div style="text-align: center; margin-top: 2px; margin-bottom: 6px;"><img src="data:image/png;base64,{logo_base64_str}" style="width: 90px; height: 90px; object-fit: contain; display: block; margin: 0 auto;" /></div>' if logo_base64_str else ''
                        
                        conn_f = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                        cur_f = conn_f.cursor()
                        cur_f.execute("SELECT firma_path FROM ordenes_servicio WHERE id = ?", (rt['id'],))
                        res_f = cur_f.fetchone()
                        conn_f.close()
                        
                        firma_url_final = res_f[0] if res_f and res_f[0] else rt.get('firma', '')
                        
                        firma_html = ""
                        if firma_url_final and str(firma_url_final).startswith('data:image'):
                            firma_html = f'<div style="margin-top: 10px; margin-bottom: 10px; text-align: center;"><p style="font-size: 12px; margin: 0 0 4px 0;">Firma del Cliente:</p><img src="{firma_url_final}" style="max-width: 130px; height: auto; border-bottom: 1px solid #000;" /></div>'

                        cierre_html = '<div style="text-align: center; font-weight: bold; margin-top: 5px;">COPIA PARA EL CLIENTE<br>¡GRACIAS POR PREFERIRNOS!</div>'

                        components.html(f"""
                            <html>
                            <head>
                            <style>
                                @page {{
                                    size: 80mm auto;
                                    margin: 0;
                                }}
                                html, body {{
                                    margin: 0;
                                    padding: 0;
                                    width: 80mm;
                                    background-color: #ffffff;
                                    height: auto !important;
                                }}
                                .print-wrapper {{
                                    width: 78mm;
                                    margin: 0 auto;
                                    text-align: center;
                                    height: auto !important;
                                    padding-bottom: 2mm;
                                }}
                                .ticket-container {{ 
                                    text-align: left; 
                                    font-family: 'Courier New', Courier, monospace; 
                                    font-size: 13px; 
                                    line-height: 1.3; 
                                    font-weight: bold; 
                                    white-space: pre; 
                                    display: inline-block;
                                    letter-spacing: -0.2px;
                                }}
                            </style>
                            </head>
                            <body onload="window.print()">
                                <div class="print-wrapper">
                                    {logo_html}
                                    <div class="ticket-container">{ticket_cliente_impresion}</div>
                                    {firma_html}
                                    {cierre_html}
                                </div>
                            </body>
                            </html>
                        """, height=0)
                with col_imp2:
                    if st.button("Cerrar Recibo", key="btn_cerrar_recibo_tall"):
                        st.session_state.recibo_taller = None
                        st.rerun()

        st.markdown("---")
        
        col_sel_1, col_sel_2 = st.columns([3, 1])
        with col_sel_1:
            conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, equipo, falla, estado, fecha FROM ordenes_servicio ORDER BY id DESC")
            todas_ordenes = cursor.fetchall()
            conn.close()

            opciones_ord = {f"Orden #{o[0]:04d} — {o[1]} ({o[2]}) [Estado: {o[4]}]": o[0] for o in todas_ordenes} if todas_ordenes else {}
            sel_orden_str = st.selectbox("Seleccione una orden de servicio:", options=list(opciones_ord.keys()) if opciones_ord else ["No hay órdenes registradas"])
        
        with col_sel_2:
            st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
            if st.button("🛠️ Ver Ficha Técnica", use_container_width=True):
                if opciones_ord and sel_orden_str in opciones_ord:
                    st.session_state.ficha_orden_id = opciones_ord[sel_orden_str]
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        df_ordenes_tabla = pd.read_sql("SELECT id as ID, cliente as Cliente, cedula as Cédula, telefono as Tel, direccion as Dirección, equipo as Equipo, imei as IMEI, falla as Falla, costo as Costo, abono as Abono, estado as Estado, pin_patron as 'Pin/Patron', detalles_chequeo as Chequeo, fecha as Fecha FROM ordenes_servicio ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_ordenes_tabla, use_container_width=True, hide_index=True)

        # BANCO DE REPARACIÓN (FICHA TÉCNICA Y SEGURIDAD)
        if st.session_state.ficha_orden_id:
            oid = st.session_state.ficha_orden_id
            conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, fecha, firma_path FROM ordenes_servicio WHERE id = ?", (oid,))
            ord_data = cursor.fetchone()
            conn.close()

            if ord_data:
                c_tot = float(ord_data[8]) if ord_data[8] else 0.0
                c_abo = float(ord_data[9]) if ord_data[9] else 0.0
                c_pen = c_tot - c_abo

                st.markdown(f"""
                    <div style="background-color: #111822; padding: 20px; border-radius: 10px; border: 2px solid #38bdf8; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.6);">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f293d; padding-bottom: 10px; margin-bottom: 15px;">
                            <h3 style="color: #38bdf8; margin: 0;">🛠️ BANCO DE REPARACIÓN - ORDEN #{ord_data[0]:04d}</h3>
                        </div>
                        <p style="margin: 4px 0;"><b>Fecha:</b> {ord_data[13]} &nbsp;|&nbsp; <b>Cliente:</b> {ord_data[1]} (CC: {ord_data[2]})</p>
                        <p style="margin: 4px 0;"><b>Teléfono:</b> {ord_data[3]} &nbsp;|&nbsp; <b>Dirección:</b> {ord_data[4]}</p>
                        <p style="margin: 4px 0;"><b>Equipo:</b> {ord_data[5]} &nbsp;|&nbsp; <b>IMEI:</b> {ord_data[6]}</p>
                        <p style="margin: 4px 0;"><b>Falla Reportada:</b> {ord_data[7]}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div style="background-color: #162032; padding: 12px; border-radius: 8px; border: 1px solid #1f293d; margin-top: 10px; display: flex; justify-content: space-around; text-align: center;">
                        <div><span style="color: #94a3b8; font-size: 12px;">COSTO TOTAL</span><br><span style="color: #00ffcc; font-size: 18px; font-weight: bold;">${c_tot:,.2f}</span></div>
                        <div><span style="color: #94a3b8; font-size: 12px;">ABONADO</span><br><span style="color: #38bdf8; font-size: 18px; font-weight: bold;">${c_abo:,.2f}</span></div>
                        <div><span style="color: #94a3b8; font-size: 12px;">SALDO PENDIENTE</span><br><span style="color: #facc15; font-size: 18px; font-weight: bold;">${c_pen:,.2f}</span></div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>##### 🔑 Seguridad (PIN, Patrón o Contraseña)")
                
                def renderizar_patron_imagen(secuencia_str, tamano=240):
                    secuencia = "".join(c for c in str(secuencia_str or "") if c in "123456789")
                    imagen = Image.new("RGB", (tamano, tamano), "#0b132b")
                    dibujo = ImageDraw.Draw(imagen)
                    puntos = {
                        "1": (50, 50), "2": (120, 50), "3": (190, 50),
                        "4": (50, 120), "5": (120, 120), "6": (190, 120),
                        "7": (50, 190), "8": (120, 190), "9": (190, 190)
                    }
                    escala = tamano / 240
                    puntos = {k: (int(x * escala), int(y * escala)) for k, (x, y) in puntos.items()}
                    radio = max(12, int(18 * escala))
                    grosor = max(2, int(5 * escala))

                    if len(secuencia) > 1:
                        dibujo.line(
                            [puntos[d] for d in secuencia],
                            fill="#38bdf8",
                            width=grosor,
                            joint="curve"
                        )

                    try:
                        fuente = ImageFont.truetype("DejaVuSans-Bold.ttf", max(12, int(14 * escala)))
                    except Exception:
                        fuente = ImageFont.load_default()

                    for numero, (x, y) in puntos.items():
                        activo = numero in secuencia
                        dibujo.ellipse(
                            (x - radio, y - radio, x + radio, y + radio),
                            fill="#38bdf8" if activo else "#162032",
                            outline="#ffffff" if activo else "#475569",
                            width=max(2, int(3 * escala))
                        )
                        caja = dibujo.textbbox((0, 0), numero, font=fuente)
                        dibujo.text(
                            (x - (caja[2] - caja[0]) / 2, y - (caja[3] - caja[1]) / 2 - 1),
                            numero,
                            fill="#000000" if activo else "#94a3b8",
                            font=fuente
                        )
                    return imagen

                col_pat_v1, col_pat_v2 = st.columns([1, 1])
                with col_pat_v1:
                    patron_guardado_bd = str(ord_data[11] or "")
                    
                    nuevo_patron_edit = st.text_input("Secuencia del Patrón / PIN", value=patron_guardado_bd, key=f"edit_pat_{oid}")
                    
                    estados_pos = ["PENDIENTE", "EN REVISIÓN", "REPARADO", "ENTREGADO", "SIN SOLUCIÓN", "ESPERANDO REPUESTO"]
                    est_actual_idx = estados_pos.index(ord_data[10]) if ord_data[10] in estados_pos else 0
                    nuevo_estado_edit = st.selectbox("Estado Actual", options=estados_pos, index=est_actual_idx, key=f"edit_est_{oid}")
                    
                    nuevo_abono_suma = st.number_input("Sumar Nuevo Abono ($)", min_value=0.0, step=5000.0, key=f"sum_abo_{oid}")

                with col_pat_v2:
                    st.markdown("##### Método de Desbloqueo Actual:")
                    sec_a_dibujar = nuevo_patron_edit if nuevo_patron_edit else patron_guardado_bd
                    if sec_a_dibujar and any(c in '123456789' for c in str(sec_a_dibujar)):
                        st.image(renderizar_patron_imagen(sec_a_dibujar), width=240)
                        st.caption(f"Secuencia guardada: {sec_a_dibujar}")
                    else:
                        st.info("Esta orden no tiene un patrón guardado.")
                    
                    firma_bd_url = ord_data[14] if len(ord_data) > 14 and ord_data[14] else ""
                    if firma_bd_url and str(firma_bd_url).startswith('data:image'):
                        st.markdown("<br>##### ✍️ Firma Registrada:", unsafe_allow_html=True)
                        st.image(firma_bd_url, width=220)
                
                col_btn_f1, col_btn_f2, col_btn_f3, col_btn_f4 = st.columns(4)
                with col_btn_f1:
                    if st.button("💾 Guardar Cambios de Ficha", use_container_width=True):
                        try:
                            conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                            cursor = conn.cursor()
                            total_final_abono = c_abo + nuevo_abono_suma
                            cursor.execute("UPDATE ordenes_servicio SET pin_patron=?, estado=?, abono=? WHERE id=?",
                                           (nuevo_patron_edit, nuevo_estado_edit, total_final_abono, oid))
                            conn.commit()
                            conn.close()
                            st.success("¡Ficha técnica actualizada con éxito!")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error al actualizar: {ex}")

                with col_btn_f2:
                    msg_w = quote(f"Hola *{ord_data[1]}*, le escribimos de *{cfg['empresa']}*.\n\nSu equipo *{ord_data[5]}* (Orden #{oid:04d}) se encuentra en estado: *{nuevo_estado_edit}*.\nSaldo pendiente: ${c_pen:,.2f}.\n\n¡Gracias por confiar en nosotros!")
                    st.markdown(f"<a href='https://wa.me/57{ord_data[3].replace(' ', '')}?text={msg_w}' target='_blank' style='background-color: #25d366; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; display: block; text-align: center; margin-top: 4px;'>💬 Enviar WhatsApp</a>", unsafe_allow_html=True)

                with col_btn_f3:
                    if st.button("❌ Cerrar Banco de Reparación", use_container_width=True):
                        st.session_state.ficha_orden_id = None
                        st.rerun()

                with col_btn_f4:
                    if st.button("🖨️ Imprimir Copia", type="primary", use_container_width=True, key=f"btn_imprimir_copia_{oid}"):
                        fecha_copia = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
                        saldo_copia = c_tot - c_abo
                        logo_copia_base64 = ""
                        if cfg['logo_path'] and os.path.exists(cfg['logo_path']):
                            try:
                                with open(cfg['logo_path'], "rb") as archivo_logo:
                                    logo_copia_base64 = base64.b64encode(archivo_logo.read()).decode("utf-8")
                            except Exception:
                                logo_copia_base64 = ""
                        logo_copia_html = (
                            f'<div style="text-align: center; margin-top: 2px; margin-bottom: 6px;"><img src="data:image/png;base64,{logo_copia_base64}" style="width: 90px; height: 90px; object-fit: contain; display: block; margin: 0 auto;" /></div>'
                            if logo_copia_base64 else ""
                        )
                        ticket_copia_cliente = f"""
==========================================
        {cfg['empresa']}
       {cfg['propietario']}
       NIT / CC: {cfg['nit']}
        {cfg['direccion']}
        Cel: {cfg['telefono']}
==========================================
 ORDEN DE SERVICIO N°: {oid:04d}
 FECHA DE COPIA: {fecha_copia}
------------------------------------------
 CLIENTE: {ord_data[1]}
 CÉDULA:  {ord_data[2]} | TEL: {ord_data[3]}
 EQUIPO:  {ord_data[5]}
 IMEI:    {ord_data[6]}
 FALLA:   {ord_data[7]}
 NOTAS:   {ord_data[12]}
------------------------------------------
 COSTO TOTAL:       ${c_tot:,.2f}
 TOTAL ABONADO:     ${c_abo:,.2f}
 SALDO PENDIENTE:   ${saldo_copia:,.2f}
 ESTADO ACTUAL:     {nuevo_estado_edit}
==========================================
{cfg['garantia_taller']}
------------------------------------------
""".strip()
                        
                        firma_bd_url = ord_data[14] if len(ord_data) > 14 and ord_data[14] else ""
                        firma_html = ""
                        if firma_bd_url and str(firma_bd_url).startswith('data:image'):
                            firma_html = f'<div style="margin-top: 10px; margin-bottom: 10px; text-align: center;"><p style="font-size: 12px; margin: 0 0 4px 0;">Firma del Cliente:</p><img src="{firma_bd_url}" style="max-width: 130px; height: auto; border-bottom: 1px solid #000;" /></div>'

                        cierre_html = '<div style="text-align: center; font-weight: bold; margin-top: 5px;">COPIA PARA EL CLIENTE<br>¡GRACIAS POR PREFERIRNOS!</div>'

                        components.html(f"""
                            <html>
                            <head>
                            <style>
                                @page {{
                                    size: 80mm auto;
                                    margin: 0;
                                }}
                                html, body {{
                                    margin: 0;
                                    padding: 0;
                                    width: 80mm;
                                    background-color: #ffffff;
                                    height: auto !important;
                                }}
                                .print-wrapper {{
                                    width: 78mm;
                                    margin: 0 auto;
                                    text-align: center;
                                    height: auto !important;
                                    padding-bottom: 2mm;
                                }}
                                .ticket-container {{ 
                                    text-align: left; 
                                    font-family: 'Courier New', Courier, monospace; 
                                    font-size: 13px; 
                                    line-height: 1.3; 
                                    font-weight: bold; 
                                    white-space: pre; 
                                    display: inline-block;
                                    letter-spacing: -0.2px;
                                }}
                            </style>
                            </head>
                            <body onload="window.print()">
                                <div class="print-wrapper">
                                    {logo_copia_html}
                                    <div class="ticket-container">{ticket_copia_cliente}</div>
                                    {firma_html}
                                    {cierre_html}
                                </div>
                            </body>
                            </html>
                        """, height=0)

        st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# ⚙️ PESTAÑA: CONFIGURACIÓN
# =========================================================
with tabs[-1]:
    st.markdown('<div class="jd-card">', unsafe_allow_html=True)
    st.subheader("⚙️ Configuración del Negocio")
    
    st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
    st.markdown("##### 🟩 Estado de la Licencia")
    st.info("**Licencia Profesional Activa** — Quedan **336 días** restantes de servicio ininterrumpido.")
    st.markdown('</div>', unsafe_allow_html=True)

    c_empresa = st.text_input("Nombre de la Empresa", value=cfg['empresa'], key="cfg_emp")
    c_prop = st.text_input("Propietario", value=cfg['propietario'], key="cfg_prop")
    c_nit = st.text_input("NIT / CC", value=cfg['nit'], key="cfg_nit")
    c_dir = st.text_input("Dirección", value=cfg['direccion'], key="cfg_dir")
    c_tel = st.text_input("Número Telefónico", value=cfg['telefono'], key="cfg_tel")
    c_gar = st.text_input("Garantía (Ventas)", value=cfg['garantia'], key="cfg_gar")
    c_gart = st.text_input("Garantía (Taller)", value=cfg['garantia_taller'], key="cfg_gart")

    modo_t_val = st.checkbox("🛠️ Habilitar Módulo de Órdenes de Servicio (Taller)", value=True if cfg['modo_taller'] == 1 else False, key="cfg_modo_taller_chk")

    st.markdown("##### 🖼️ Logotipo del Negocio (Formato PNG)")
    logo_subido = st.file_uploader("Subir logotipo en PNG", type=["png", "jpg"], key="cfg_logo_uploader")
    
    logo_path_final = cfg['logo_path']
    if logo_subido is not None:
        os.makedirs("assets", exist_ok=True)
        logo_path_final = os.path.join("assets", "logo_negocio.png")
        with open(logo_path_final, "wb") as f:
            f.write(logo_subido.getbuffer())
        st.success("¡Logotipo cargado y guardado con éxito!")

    if st.button("💾 Guardar Configuración", key="cfg_btn_save"):
        val_taller_int = 1 if modo_t_val else 0
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE configuracion SET nombre_empresa=?, propietario=?, nit=?, direccion=?, telefono=?, garantia_dias=?, garantia_taller=?, logo_path=?, modo_taller=? WHERE id=1",
                       (c_empresa, c_prop, c_nit, c_dir, c_tel, c_gar, c_gart, logo_path_final, val_taller_int))
        conn.commit()
        conn.close()
        st.success("Configuración guardada correctamente. Actualizando interfaz...")
        st.rerun()

    st.markdown("---")
    st.markdown("##### 🛡️ Mantenimiento y Seguridad (Respaldos en la Nube)")
    
    col_resp1, col_resp2 = st.columns(2)
    with col_resp1:
        if os.path.exists("jadithcell_comunicaciones.db"):
            with open("jadithcell_comunicaciones.db", "rb") as f:
                db_bytes = f.read()
            fecha_b = obtener_tiempo_colombia().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Descargar Respaldo Directo (.db)",
                data=db_bytes,
                file_name=f"backup_jadithcell_{fecha_b}.db",
                mime="application/octet-stream",
                use_container_width=True
            )
        else:
            st.warning("No se encontró la base de datos.")

    with col_resp2:
        if st.button("💾 Guardar Respaldo en Servidor Cloud", use_container_width=True):
            os.makedirs("backups", exist_ok=True)
            fecha_b = obtener_tiempo_colombia().strftime("%Y%m%d_%H%M%S")
            backup_name = os.path.join("backups", f"backup_jadithcell_{fecha_b}.db")
            try:
                shutil.copyfile("jadithcell_comunicaciones.db", backup_name)
                st.success("¡Respaldo interno creado en backups/!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🔄 Restaurar Sistema desde Archivo de Respaldo (.db)")
    archivo_respaldo_subido = st.file_uploader("Elige un archivo de base de datos desde cualquier ubicación de tu equipo (.db)", type=["db"], key="uploader_restaurar_db")
    
    if archivo_respaldo_subido is not None:
        if st.button("⚠️ Confirmar y Restaurar Base de Datos", type="primary"):
            try:
                with open("jadithcell_comunicaciones.db", "wb") as f:
                    f.write(archivo_respaldo_subido.getbuffer())
                st.success("¡Base de datos restaurada con éxito! Recargando sistema...")
                st.rerun()
            except Exception as ex:
                st.error(f"Error al restaurar el respaldo: {ex}")

    st.markdown("---")
    st.markdown("##### ⚠️ ZONA DE PELIGRO")
    
    if st.button("🗑️ Eliminar Todo el Inventario", key="btn_trigger_del"):
        st.session_state.confirmar_borrado_inv = True

    if st.session_state.confirmar_borrado_inv:
        st.warning("Estás a punto de borrar todo el inventario actual. Inserta la contraseña maestra para confirmar:")
        pass_ingresada = st.text_input("Contraseña maestra:", type="password", key="pass_del_inv")
        
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            if st.button("Confirmar Borrado Total", key="btn_confirm_del"):
                if pass_ingresada == "JADITHCELL COMUNICACIONES":
                    try:
                        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM productos")
                        conn.commit()
                        conn.close()
                        st.session_state.confirmar_borrado_inv = False
                        st.success("¡Inventario eliminado correctamente! Ya puedes cargar tu archivo Excel limpio.")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al borrar inventario: {ex}")
                else:
                    st.error("Contraseña incorrecta.")
        with c_d2:
            if st.button("Cancelar", key="btn_cancel_del"):
                st.session_state.confirmar_borrado_inv = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- BARRA 인FERIOR DE LICENCIA ---
st.markdown(f'<div class="status-bar">🟩 LICENCIA PROFESIONAL ACTIVA (Quedan 336 días)</div>', unsafe_allow_html=True)
