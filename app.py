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


# Crear automaticamente el componente si se distribuye solo app.py.
_COMPONENT_DIR = Path(__file__).resolve().parent / "pattern_drawer"
_COMPONENT_FILE = _COMPONENT_DIR / "index.html"
_COMPONENT_HTML_B64 = "PCFkb2N0eXBlIGh0bWw+CjxodG1sIGxhbmc9ImVzIj4KPGhlYWQ+CiAgPG1ldGEgY2hhcnNldD0idXRmLTgiIC8+CiAgPHN0eWxlPgogICAgaHRtbCwgYm9keSB7IG1hcmdpbjogMDsgcGFkZGluZzogMDsgYmFja2dyb3VuZDogdHJhbnNwYXJlbnQ7IH0KICAgICNjYW52YXMgeyBkaXNwbGF5OiBibG9jazsgd2lkdGg6IDIyMHB4OyBoZWlnaHQ6IDIwMHB4OyBiYWNrZ3JvdW5kOiAjMGYxNzJhOyBib3JkZXI6IDA7IGN1cnNvcjogY3Jvc3NoYWlyOyB0b3VjaC1hY3Rpb246IG5vbmU7IH0KICA8L3N0eWxlPgo8L2hlYWQ+Cjxib2R5PgogIDxjYW52YXMgaWQ9ImNhbnZhcyIgd2lkdGg9IjIyMCIgaGVpZ2h0PSIyMDAiPjwvY2FudmFzPgogIDxzY3JpcHQ+CiAgICAvLyBJbXBsZW1lbnRhY2nDs24gbcOtbmltYSBkZWwgcHJvdG9jb2xvIG9maWNpYWwgZGUgU3RyZWFtbGl0IENvbXBvbmVudHMuCiAgICBjb25zdCBSRUFEWSA9ICdzdHJlYW1saXQ6Y29tcG9uZW50UmVhZHknOwogICAgY29uc3QgUkVOREVSID0gJ3N0cmVhbWxpdDpyZW5kZXInOwogICAgY29uc3QgVkFMVUUgPSAnc3RyZWFtbGl0OnNldENvbXBvbmVudFZhbHVlJzsKICAgIGNvbnN0IEhFSUdIVCA9ICdzdHJlYW1saXQ6c2V0RnJhbWVIZWlnaHQnOwogICAgY29uc3QgY2FudmFzID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2NhbnZhcycpOwogICAgY29uc3QgY3R4ID0gY2FudmFzLmdldENvbnRleHQoJzJkJyk7CiAgICBjb25zdCBub2RlcyA9IFsKICAgICAge2lkOicxJyx4OjQwLHk6NDB9LHtpZDonMicseDoxMTAseTo0MH0se2lkOiczJyx4OjE4MCx5OjQwfSwKICAgICAge2lkOic0Jyx4OjQwLHk6MTAwfSx7aWQ6JzUnLHg6MTEwLHk6MTAwfSx7aWQ6JzYnLHg6MTgwLHk6MTAwfSwKICAgICAge2lkOic3Jyx4OjQwLHk6MTYwfSx7aWQ6JzgnLHg6MTEwLHk6MTYwfSx7aWQ6JzknLHg6MTgwLHk6MTYwfQogICAgXTsKICAgIGxldCBzZXF1ZW5jZSA9IFtdOwogICAgbGV0IGRyYXdpbmcgPSBmYWxzZTsKCiAgICBmdW5jdGlvbiBzZW5kKHR5cGUsIGRhdGEpIHsKICAgICAgd2luZG93LnBhcmVudC5wb3N0TWVzc2FnZShPYmplY3QuYXNzaWduKHtpc1N0cmVhbWxpdE1lc3NhZ2U6dHJ1ZSwgdHlwZTp0eXBlfSwgZGF0YSB8fCB7fSksICcqJyk7CiAgICB9CiAgICBmdW5jdGlvbiBzZXRWYWx1ZSgpIHsgc2VuZChWQUxVRSwge3ZhbHVlOnNlcXVlbmNlLmpvaW4oJycpLCBkYXRhVHlwZTonanNvbid9KTsgfQogICAgZnVuY3Rpb24gZHJhdygpIHsKICAgICAgY3R4LmNsZWFyUmVjdCgwLDAsY2FudmFzLndpZHRoLGNhbnZhcy5oZWlnaHQpOwogICAgICBpZiAoc2VxdWVuY2UubGVuZ3RoID4gMSkgewogICAgICAgIGNvbnN0IGNvb3JkcyA9IHNlcXVlbmNlLm1hcChpZCA9PiBub2Rlcy5maW5kKG4gPT4gbi5pZCA9PT0gaWQpKTsKICAgICAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5tb3ZlVG8oY29vcmRzWzBdLngsIGNvb3Jkc1swXS55KTsKICAgICAgICBjb29yZHMuc2xpY2UoMSkuZm9yRWFjaChuID0+IGN0eC5saW5lVG8obi54LG4ueSkpOwogICAgICAgIGN0eC5zdHJva2VTdHlsZT0nIzAyODRjNyc7IGN0eC5saW5lV2lkdGg9NTsgY3R4LmxpbmVDYXA9J3JvdW5kJzsgY3R4LmxpbmVKb2luPSdyb3VuZCc7IGN0eC5zdHJva2UoKTsKICAgICAgICBjdHguc3Ryb2tlU3R5bGU9JyMzOGJkZjgnOyBjdHgubGluZVdpZHRoPTIuNTsgY3R4LnN0cm9rZSgpOwogICAgICB9CiAgICAgIG5vZGVzLmZvckVhY2gobiA9PiB7CiAgICAgICAgY29uc3QgYWN0aXZlID0gc2VxdWVuY2UuaW5jbHVkZXMobi5pZCk7CiAgICAgICAgaWYgKGFjdGl2ZSkgeyBjdHguYmVnaW5QYXRoKCk7IGN0eC5hcmMobi54LG4ueSwxOCwwLE1hdGguUEkqMik7IGN0eC5zdHJva2VTdHlsZT0nIzM4YmRmOCc7IGN0eC5saW5lV2lkdGg9MjsgY3R4LnN0cm9rZSgpOyB9CiAgICAgICAgY3R4LmJlZ2luUGF0aCgpOyBjdHguYXJjKG4ueCxuLnksYWN0aXZlPzE0OjksMCxNYXRoLlBJKjIpOwogICAgICAgIGN0eC5maWxsU3R5bGU9YWN0aXZlPycjMjJjNTVlJzonIzFlMjkzYic7IGN0eC5maWxsKCk7IGN0eC5zdHJva2VTdHlsZT0nIzM4YmRmOCc7IGN0eC5saW5lV2lkdGg9MjsgY3R4LnN0cm9rZSgpOwogICAgICAgIGN0eC5maWxsU3R5bGU9YWN0aXZlPyd3aGl0ZSc6JyM5NGEzYjgnOyBjdHguZm9udD0nYm9sZCAxMHB4IEFyaWFsJzsgY3R4LnRleHRBbGlnbj0nY2VudGVyJzsgY3R4LnRleHRCYXNlbGluZT0nbWlkZGxlJzsgY3R4LmZpbGxUZXh0KG4uaWQsbi54LG4ueSk7CiAgICAgIH0pOwogICAgfQogICAgZnVuY3Rpb24gZmluZFBvaW50KGUpIHsKICAgICAgY29uc3Qgcj1jYW52YXMuZ2V0Qm91bmRpbmdDbGllbnRSZWN0KCk7CiAgICAgIGNvbnN0IHg9KGUuY2xpZW50WC1yLmxlZnQpKmNhbnZhcy53aWR0aC9yLndpZHRoLCB5PShlLmNsaWVudFktci50b3ApKmNhbnZhcy5oZWlnaHQvci5oZWlnaHQ7CiAgICAgIHJldHVybiBub2Rlcy5maW5kKG4gPT4gTWF0aC5hYnMoeC1uLngpPDI1ICYmIE1hdGguYWJzKHktbi55KTwyNSk7CiAgICB9CiAgICBjYW52YXMuYWRkRXZlbnRMaXN0ZW5lcigncG9pbnRlcmRvd24nLCBlID0+IHsKICAgICAgZS5wcmV2ZW50RGVmYXVsdCgpOyBkcmF3aW5nPXRydWU7IHNlcXVlbmNlPVtdOyBjb25zdCBuPWZpbmRQb2ludChlKTsgaWYobikgc2VxdWVuY2UucHVzaChuLmlkKTsgZHJhdygpOyBzZXRWYWx1ZSgpOwogICAgfSk7CiAgICBjYW52YXMuYWRkRXZlbnRMaXN0ZW5lcigncG9pbnRlcm1vdmUnLCBlID0+IHsKICAgICAgaWYoIWRyYXdpbmcpIHJldHVybjsgZS5wcmV2ZW50RGVmYXVsdCgpOyBjb25zdCBuPWZpbmRQb2ludChlKTsKICAgICAgaWYobiAmJiAhc2VxdWVuY2UuaW5jbHVkZXMobi5pZCkpIHsgc2VxdWVuY2UucHVzaChuLmlkKTsgZHJhdygpOyBzZXRWYWx1ZSgpOyB9CiAgICB9KTsKICAgIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKCdwb2ludGVydXAnLCAoKSA9PiB7IGlmKGRyYXdpbmcpeyBkcmF3aW5nPWZhbHNlOyBzZXRWYWx1ZSgpOyB9IH0pOwogICAgd2luZG93LmFkZEV2ZW50TGlzdGVuZXIoJ21lc3NhZ2UnLCBlID0+IHsKICAgICAgaWYoZS5kYXRhICYmIGUuZGF0YS50eXBlPT09UkVOREVSKSB7CiAgICAgICAgY29uc3QgaW5jb21pbmc9U3RyaW5nKChlLmRhdGEuYXJnc3x8e30pLnNlcXVlbmNlfHwnJykucmVwbGFjZSgvW14xLTldL2csJycpOwogICAgICAgIGlmKCFkcmF3aW5nKSBzZXF1ZW5jZT1pbmNvbWluZy5zcGxpdCgnJyk7IGRyYXcoKTsKICAgICAgfQogICAgfSk7CiAgICBzZW5kKFJFQURZLCB7YXBpVmVyc2lvbjoxfSk7CiAgICBzZW5kKEhFSUdIVCwge2hlaWdodDoyMDV9KTsKICAgIGRyYXcoKTsKICA8L3NjcmlwdD4KPC9ib2R5Pgo8L2h0bWw+Cg=="
_COMPONENT_DIR.mkdir(parents=True, exist_ok=True)
_COMPONENT_FILE.write_bytes(base64.b64decode(_COMPONENT_HTML_B64))

pattern_drawer_component = components.declare_component(
    "pattern_drawer",
    path=str(Path(__file__).resolve().parent / "pattern_drawer")
)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DATACONTROL JD - JADITHCELL COMUNICACIONES",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VERSION_ACTUAL = "1.6.5"

# --- FUNCIÓN PARA OBTENER HORA EXACTA DE COLOMBIA (UTC-5) ---
def obtener_tiempo_colombia():
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5)

# --- ESTILOS VISUALES IDÉNTICOS AL ESCRITORIO ---
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
        border-radius: 6px !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #16a34a !important;
        color: white !important;
        font-size: 16px !important;
        height: 45px !important;
        border: none !important;
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
        "ALTER TABLE ventas ADD COLUMN notas TEXT"
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
        if st.session_state.carrito:
            filas_tabla = []
            for i, item in enumerate(st.session_state.carrito, 1):
                filas_tabla.append({
                    "#": i,
                    "ID": item['id'],
                    "Código": item['codigo'],
                    "Producto": item['nombre'],
                    "Cantidad": item['cantidad'],
                    "Precio Unidad": f"${item['precio']:,.2f}",
                    "Total": f"${item['total']:,.2f}"
                })
            df_carrito = pd.DataFrame(filas_tabla)
            st.dataframe(df_carrito, use_container_width=True, hide_index=True)

            col_q1, col_q2, col_q3 = st.columns([1.2, 1.8, 2.5])
            with col_q1:
                item_a_quitar = st.number_input("Fila #", min_value=1, max_value=len(st.session_state.carrito), value=1, step=1, key="v_fila_quitar")
            with col_q2:
                st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
                if st.button("➖ Restar 1 Cantidad", key="v_btn_restar_1"):
                    idx = item_a_quitar - 1
                    if st.session_state.carrito[idx]['cantidad'] > 1:
                        st.session_state.carrito[idx]['cantidad'] -= 1
                        st.session_state.carrito[idx]['total'] = st.session_state.carrito[idx]['cantidad'] * st.session_state.carrito[idx]['precio']
                    else:
                        st.session_state.carrito.pop(idx)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with col_q3:
                st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
                if st.button("❌ Quitar Ítem Completo", key="v_btn_del_item"):
                    st.session_state.carrito.pop(item_a_quitar - 1)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            df_vacio = pd.DataFrame(columns=["#", "ID", "Código", "Producto", "Cantidad", "Precio Unidad", "Total"])
            st.dataframe(df_vacio, use_container_width=True, hide_index=True)

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

    # VISTA PREVIA Y IMPRESIÓN
    if st.session_state.recibo_generado:
        rg = st.session_state.recibo_generado

        with st.expander("🧾 VISTA PREVIA TICKET POS DE VENTA (80MM)", expanded=True):
            fecha_actual_ticket = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
            
            lineas_ticket = [
                f"{cfg['empresa']}",
                f"{cfg['propietario']}",
                f"NIT: {cfg['nit']} | Tel: {cfg['telefono']}",
                f"{cfg['direccion']}",
                "-" * 38,
                f"FECHA: {fecha_actual_ticket}",
                f"CLIENTE: {rg['cliente']} (CC: {rg['cedula']})",
                "-" * 38,
                f"{'Cant':<5}{'Producto':<21}{'Total':>12}",
                "-" * 38
            ]
            for itm in rg['items']:
                lineas_ticket.append(f"{itm['cantidad']:<5}{itm['nombre'][:20]:<21}${itm['total']:>11,.0f}")
            lineas_ticket.extend([
                "-" * 38,
                f"TOTAL: ${rg['subtotal']:,.2f}",
                f"RECIBIDO: ${rg['recibido']:,.2f}",
                f"CAMBIO: ${rg['vuelto']:,.2f}",
                "-" * 38,
                f"IMEI 1: {rg['imei1']}" if rg['imei1'] else "",
                cfg['garantia'],
                "¡GRACIAS POR SU COMPRA!"
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
                    
                    logo_html = f'<img src="data:image/png;base64,{logo_base64_str}" style="max-width: 90px; display: block; margin: 0 auto 10px auto;" />' if logo_base64_str else ''
                    components.html(f"""
                        <html>
                        <body onload="window.print()">
                            <div style="font-family: monospace; font-size: 12px; white-space: pre-wrap; text-align: center;">
                                {logo_html}
                                {ticket_impresion_final}
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
        
        # Lienzo interactivo real: devuelve la secuencia dibujada a Python.
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

            # Esta sección queda fuera de las tres columnas para que el lienzo
            # siempre sea visible durante el registro de una nueva orden.
            st.markdown('<div class="jd-card-inner">', unsafe_allow_html=True)
            st.markdown("<div class='lbl-celeste'>🔐 Dibujar Patrón de Desbloqueo (Opcional)</div>", unsafe_allow_html=True)
            st.caption("Mantenga presionado el botón del mouse o el dedo y arrástrelo por los puntos en orden.")
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

            ot_notas = st.text_input("Notas adicionales / Chequeo físico", placeholder="Notas adicionales / Chequeo físico", key=f"t_not_{fc}")

            st.markdown("<br>", unsafe_allow_html=True)
            col_btn_reg1, col_btn_reg2 = st.columns([4, 1])
            with col_btn_reg1:
                if st.button("💾 Guardar Orden", type="primary", use_container_width=True, key=f"t_btn_save_{fc}"):
                    # PRIORIDAD ABSOLUTA: Si escribiste en la casilla de texto se usa eso, de lo contrario se toma lo que se dibujó en el canvas
                    patron_guardar = ot_patron_txt.strip() if ot_patron_txt else st.session_state.patron_secuencia.strip()
                    
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
                        cursor.execute('''INSERT INTO ordenes_servicio (cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, foto_path, fecha)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                       (ot_cliente, ot_cedula, ot_tel, ot_dir, ot_equipo, ot_imei, ot_falla, val_costo, val_abono, "PENDIENTE", patron_guardar, ot_notas, "", fecha_ahora))
                        conn.commit()
                        
                        cursor.execute("SELECT last_insert_rowid()")
                        nueva_id = cursor.fetchone()[0]
                        conn.close()

                        st.success("¡Orden de servicio guardada con éxito!")
                        
                        st.session_state.patron_secuencia = ""
                        st.session_state.form_counter += 1
                        
                        st.session_state.recibo_taller = {
                            "id": nueva_id, "cliente": ot_cliente, "cedula": ot_cedula, "telefono": ot_tel,
                            "equipo": ot_equipo, "imei": ot_imei, "falla": ot_falla, "costo": val_costo,
                            "abono": val_abono, "estado": "PENDIENTE", "patron": patron_guardar,
                            "chequeo": ot_notas, "fecha": fecha_ahora
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

            with st.expander(f"🧾 RECIBO BÁSICO ORDEN #{rt['id']:04d}", expanded=True):
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
                    if st.button("🖨️ Imprimir Recibo Taller", use_container_width=True, key="btn_imprimir_recibo_taller_directo"):
                        logo_html = f'<img src="data:image/png;base64,{logo_base64_str}" style="max-width: 90px; display: block; margin: 0 auto 10px auto;" />' if logo_base64_str else ''
                        components.html(f"""
                            <html>
                            <body onload="window.print()">
                                <div style="font-family: monospace; font-size: 12px; white-space: pre-wrap; text-align: center;">
                                    {logo_html}
                                    {ticket_taller_str}
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
            cursor.execute("SELECT id, cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, fecha FROM ordenes_servicio WHERE id = ?", (oid,))
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
                
                def renderizar_patron_svg_guardado(secuencia_str, ancho=240, alto=240):
                    # El patrón se guarda como una secuencia de números, por ejemplo: 14789.
                    # Se eliminan los caracteres que no correspondan a los nueve puntos.
                    sec_limpia = "".join([c for c in str(secuencia_str or "") if c in '123456789'])
                    puntos = {
                        '1': (50, 50),   '2': (120, 50),   '3': (190, 50),
                        '4': (50, 120),  '5': (120, 120),  '6': (190, 120),
                        '7': (50, 190),  '8': (120, 190),  '9': (190, 190)
                    }
                    digitos = list(sec_limpia)
                    svg_lines = f'<svg width="{ancho}" height="{alto}" style="background-color: #0b132b; border-radius: 8px; border: 2px solid #1f293d;" viewBox="0 0 240 240">'
                    
                    if len(digitos) > 1:
                        for i in range(len(digitos) - 1):
                            d1 = str(digitos[i])
                            d2 = str(digitos[i+1])
                            if d1 in puntos and d2 in puntos:
                                p1 = puntos[d1]
                                p2 = puntos[d2]
                                svg_lines += f'<line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]}" y2="{p2[1]}" stroke="#38bdf8" stroke-width="5" stroke-linecap="round" />'
                    
                    for k, coord in puntos.items():
                        activo = k in digitos
                        fill_color = "#38bdf8" if activo else "#162032"
                        stroke_color = "#ffffff" if activo else "#475569"
                        text_color = "#000000" if activo else "#94a3b8"
                        svg_lines += f'<circle cx="{coord[0]}" cy="{coord[1]}" r="18" fill="{fill_color}" stroke="{stroke_color}" stroke-width="3" />'
                        svg_lines += f'<text x="{coord[0]}" y="{coord[1]+5}" font-family="Arial" font-size="14" font-weight="bold" fill="{text_color}" text-anchor="middle">{k}</text>'
                        
                    svg_lines += '</svg>'
                    return svg_lines

                def renderizar_patron_imagen(secuencia_str, tamano=240):
                    """Genera una imagen PNG del patrón para mostrarla sin depender del SVG/HTML."""
                    secuencia = "".join(c for c in str(secuencia_str or "") if c in "123456789")
                    imagen = Image.new("RGB", (tamano, tamano), "#0b132b")
                    dibujo = ImageDraw.Draw(imagen)
                    puntos = {
                        "1": (50, 50), "2": (120, 50), "3": (190, 50),
                        "4": (50, 120), "5": (120, 120), "6": (190, 120),
                        "7": (50, 190), "8": (120, 190), "9": (190, 190)
                    }
                    # Ajustar las coordenadas si se cambia el tamaño de la imagen.
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
                    # Streamlit puede sanitizar el SVG cuando se inserta con markdown.
                    # components.html lo renderiza como HTML real y hace visibles
                    # las líneas y los puntos del patrón guardado.
                    if sec_a_dibujar and any(c in '123456789' for c in str(sec_a_dibujar)):
                        st.image(renderizar_patron_imagen(sec_a_dibujar), width=240)
                        st.caption(f"Secuencia guardada: {sec_a_dibujar}")
                    else:
                        st.info("Esta orden no tiene un patrón guardado.")
                
                col_btn_f1, col_btn_f2, col_btn_f3 = st.columns(3)
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

    modo_taller_val = st.checkbox("🛠️ Habilitar Módulo de Órdenes de Servicio (Taller)", value=True if cfg['modo_taller'] == 1 else False, key="cfg_modo_taller_chk")

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
        val_taller_int = 1 if modo_taller_val else 0
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("UPDATE configuracion SET nombre_empresa=?, propietario=?, nit=?, direccion=?, telefono=?, garantia_dias=?, garantia_taller=?, logo_path=?, modo_taller=? WHERE id=1",
                       (c_empresa, c_prop, c_nit, c_dir, c_tel, c_gar, c_gart, logo_path_final, val_taller_int))
        conn.commit()
        conn.close()
        st.success("Configuración guardada correctamente. Actualizando interfaz...")
        st.rerun()

    st.markdown("---")
    st.markdown("##### 🛡️ Mantenimiento y Seguridad (Respaldos y Restauración)")
    
    col_resp1, col_resp2 = st.columns(2)
    with col_resp1:
        if st.button("💾 Crear Respaldo Manual Ahora", use_container_width=True):
            os.makedirs("backups", exist_ok=True)
            fecha_b = obtener_tiempo_colombia().strftime("%Y%m%d_%H%M%S")
            backup_name = os.path.join("backups", f"backup_jadithcell_{fecha_b}.db")
            try:
                shutil.copyfile("jadithcell_comunicaciones.db", backup_name)
                st.success(f"¡Respaldo creado con éxito en la carpeta backups/!")
            except Exception as e:
                st.error(f"Error creando respaldo: {e}")

    with col_resp2:
        if st.button("📂 Abrir Carpeta de Respaldos", use_container_width=True):
            os.makedirs("backups", exist_ok=True)
            ruta_absoluta = os.path.abspath("backups")
            try:
                os.startfile(ruta_absoluta)
                st.success(f"Carpeta abierta: {ruta_absoluta}")
            except:
                st.info(f"La ruta de la carpeta de respaldos es: {ruta_absoluta}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🔄 Restaurar Sistema desde Archivo de Respaldo (.db)")
    archivo_respaldo_subido = st.file_uploader("Selecciona un archivo de base de datos de respaldo (.db)", type=["db"], key="uploader_restaurar_db")
    
    if archivo_respaldo_subido is not None:
        if st.button("⚠️ Confirmar y Restaurar Base de Datos", type="primary"):
            try:
                ruta_temporal = "temp_restore.db"
                with open(ruta_temporal, "wb") as f:
                    f.write(archivo_respaldo_subido.getbuffer())
                
                shutil.copyfile(ruta_temporal, "jadithcell_comunicaciones.db")
                if os.path.exists(ruta_temporal):
                    os.remove(ruta_temporal)
                
                st.success("¡Base de datos restaurada con éxito! Recargando sistema...")
                st.rerun()
            except Exception as ex:
                st.error(f"Error al restaurar el respaldo: {ex}")

    st.markdown("---")
    st.markdown("##### ⚠️ ZONA DE PELIGRO")
    
    if st.button("🗑️ Eliminar Todo el Inventario", type="secondary", key="btn_trigger_del"):
        st.session_state.confirmar_borrado_inv = True

    if st.session_state.confirmar_borrado_inv:
        st.warning("Estás a punto de borrar todo el inventario actual.")
        pass_ingresada = st.text_input("Ingrese la contraseña maestra:", type="password", key="pass_del_inv")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
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
        with col_d2:
            if st.button("Cancelar", key="btn_cancel_del"):
                st.session_state.confirmar_borrado_inv = False
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- BARRA INFERIOR DE LICENCIA ---
st.markdown(f'<div class="status-bar">🟩 LICENCIA PROFESIONAL ACTIVA (Quedan 336 días)</div>', unsafe_allow_html=True)
