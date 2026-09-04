import streamlit as st
import sqlite3
import datetime
import os
import csv
import re
import pandas as pd
from urllib.parse import quote
import streamlit.components.v1 as components
import shutil
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="DATACONTROL JD - JADITHCELL COMUNICACIONES",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VERSION_ACTUAL = "1.4.4"

# --- FUNCIÓN PARA OBTENER HORA EXACTA DE COLOMBIA (UTC-5) ---
def obtener_tiempo_colombia():
    # El servidor en la nube está en UTC, restamos 5 horas para ajustar a Colombia
    return datetime.datetime.utcnow() - datetime.timedelta(hours=5)

# --- ESTILOS VISUALES IDÉNTICOS AL ESCRITORIO (BOTONES SIEMPRE VISIBLES) ---
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
        margin-bottom: 2px;
    }
    .lbl-celeste {
        color: #38bdf8;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 2px;
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
        background-color: #dc2626 !important;
        color: white !important;
        font-size: 18px !important;
        height: 52px !important;
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

            col_q1, col_q2 = st.columns([1, 3])
            with col_q1:
                item_a_quitar = st.number_input("Fila # a quitar", min_value=1, max_value=len(st.session_state.carrito), value=1, step=1, key="v_fila_quitar")
            with col_q2:
                st.markdown("<div style='padding-top: 24px;'>", unsafe_allow_html=True)
                if st.button("❌ Quitar Ítem Seleccionado", key="v_btn_del_item"):
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

    # VISTA PREVIA Y IMPRESIÓN (Con hora exacta de Colombia sincronizada)
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
        
        def renderizar_lienzo_patron(secuencia_actual):
            html_patron = """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
                body { background-color: #0b132b; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
                canvas { background-color: #0b132b; border: 2px solid #1f293d; border-radius: 8px; cursor: crosshair; }
            </style>
            </head>
            <body>
            <canvas id="patternCanvas" width="240" height="240"></canvas>
            <script>
                const canvas = document.getElementById('patternCanvas');
                const ctx = canvas.getContext('2d');
                
                const nodes = [
                    {id: '1', x: 50, y: 50},
                    {id: '2', x: 120, y: 50},
                    {id: '3', x: 190, y: 50},
                    {id: '4', x: 50, y: 120},
                    {id: '5', x: 120, y: 120},
                    {id: '6', x: 190, y: 120},
                    {id: '7', x: 50, y: 190},
                    {id: '8', x: 120, y: 190},
                    {id: '9', x: 190, y: 190}
                ];
                
                let sequence = "SEC_VAL".split('').filter(n => n >= '1' && n <= '9');
                let isDrawing = false;
                
                function draw() {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    if (sequence.length > 1) {
                        ctx.beginPath();
                        ctx.strokeStyle = '#38bdf8';
                        ctx.lineWidth = 5;
                        ctx.lineCap = 'round';
                        for (let i = 0; i < sequence.length; i++) {
                            const node = nodes.find(n => n.id === sequence[i]);
                            if (i === 0) ctx.moveTo(node.x, node.y);
                            else ctx.lineTo(node.x, node.y);
                        }
                        ctx.stroke();
                    }
                    
                    nodes.forEach(node => {
                        const active = sequence.includes(node.id);
                        ctx.beginPath();
                        ctx.arc(node.x, node.y, 18, 0, 2 * Math.PI);
                        ctx.fillStyle = active ? '#38bdf8' : '#162032';
                        ctx.fill();
                        ctx.lineWidth = 3;
                        ctx.strokeStyle = active ? '#ffffff' : '#475569';
                        ctx.stroke();
                        
                        ctx.fillStyle = active ? '#000000' : '#94a3b8';
                        ctx.font = 'bold 14px Arial';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        ctx.fillText(node.id, node.x, node.y);
                    });
                }
                
                function getNodeAtPos(x, y) {
                    for (let node of nodes) {
                        let dx = node.x - x;
                        let dy = node.y - y;
                        if (Math.sqrt(dx * dx + dy * dy) < 22) {
                            return node.id;
                        }
                    }
                    return null;
                }
                
                canvas.addEventListener('mousedown', (e) => {
                    isDrawing = true;
                    sequence = [];
                    const rect = canvas.getBoundingClientRect();
                    const id = getNodeAtPos(e.clientX - rect.left, e.clientY - rect.top);
                    if (id && !sequence.includes(id)) sequence.push(id);
                    draw();
                });
                
                canvas.addEventListener('mousemove', (e) => {
                    if (!isDrawing) return;
                    const rect = canvas.getBoundingClientRect();
                    const id = getNodeAtPos(e.clientX - rect.left, e.clientY - rect.top);
                    if (id && !sequence.includes(id)) {
                        sequence.push(id);
                        draw();
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: sequence.join('')}, '*');
                    }
                });
                
                window.addEventListener('mouseup', () => {
                    if (isDrawing) {
                        isDrawing = false;
                        window.parent.postMessage({type: 'streamlit:setComponentValue', value: sequence.join('')}, '*');
                    }
                });
                
                draw();
            </script>
            </body>
            </html>
            """
            html_final = html_patron.replace("SEC_VAL", str(secuencia_actual))
            return components.html(html_final, height=255, scrolling=False)

        with st.expander("📋 REGISTRAR ORDEN DE SERVICIO", expanded=False):
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                ot_cliente = st.text_input("Nombre del cliente *", key="t_cli")
                ot_cedula = st.text_input("Cédula / NIT", key="t_ced")
                ot_tel = st.text_input("Teléfono *", key="t_tel")
                ot_dir = st.text_input("Dirección", key="t_dir")
            with t_col2:
                ot_equipo = st.text_input("Modelo del equipo *", key="t_eq")
                ot_imei = st.text_input("IMEI / Serial", key="t_im")
                ot_falla = st.text_input("Falla reportada *", key="t_fa")
            with t_col3:
                ot_costo = st.number_input("Costo Total ($)", min_value=0.0, value=0.0, key="t_cos")
                ot_abono = st.number_input("Abono Inicial ($)", min_value=0.0, value=0.0, key="t_abo")
                ot_patron_txt = st.text_input("Secuencia del Patrón", placeholder="Ej: 7415369", key="t_pat")

            st.markdown("##### 🔐 Dibujar Patrón de Desbloqueo (Mantén presionado y desliza el mouse sobre los puntos)")
            
            col_pat_izq, col_pat_der = st.columns([1, 1])
            with col_pat_izq:
                secuencia_dibujada = st.session_state.patron_secuencia
                renderizar_lienzo_patron(secuencia_dibujada)
                
                if st.button("🧹 Limpiar Patrón", key="btn_limpiar_pat"):
                    st.session_state.patron_secuencia = ""
                    st.rerun()

            with col_pat_der:
                sec_final = ot_patron_txt if ot_patron_txt else st.session_state.patron_secuencia
                st.markdown(f"**Secuencia registrada:** `{sec_final}`")
                st.info("💡 Consejo: También puedes escribir directamente la secuencia numérica en la casilla de arriba.")

            ot_notas = st.text_input("Notas adicionales / Chequeo físico", key="t_not")
            
            if st.button("💾 Guardar Orden de Servicio", key="t_btn_save"):
                patron_guardar = ot_patron_txt if ot_patron_txt else st.session_state.patron_secuencia
                if ot_cliente and ot_equipo and ot_falla:
                    conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
                    cursor = conn.cursor()
                    fecha_ahora = obtener_tiempo_colombia().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute('''INSERT INTO ordenes_servicio (cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, foto_path, fecha)
                                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                   (ot_cliente, ot_cedula, ot_tel, ot_dir, ot_equipo, ot_imei, ot_falla, ot_costo, ot_abono, "PENDIENTE", patron_guardar, ot_notas, "", fecha_ahora))
                    conn.commit()
                    
                    cursor.execute("SELECT last_insert_rowid()")
                    nueva_id = cursor.fetchone()[0]
                    conn.close()

                    st.success("¡Orden de servicio guardada con éxito!")
                    st.session_state.patron_secuencia = ""
                    st.session_state.recibo_taller = {
                        "id": nueva_id, "cliente": ot_cliente, "cedula": ot_cedula, "telefono": ot_tel,
                        "equipo": ot_equipo, "imei": ot_imei, "falla": ot_falla, "costo": ot_costo,
                        "abono": ot_abono, "estado": "PENDIENTE", "patron": patron_guardar,
                        "chequeo": ot_notas, "fecha": fecha_ahora
                    }
                    st.rerun()
                else:
                    st.error("Cliente, equipo y falla son requeridos.")

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
                if st.button("Cerrar Recibo", key="btn_cerrar_recibo_tall"):
                    st.session_state.recibo_taller = None
                    st.rerun()

        st.markdown("---")
        st.markdown("##### 🔍 Seleccionar Orden para Ficha Técnica y Seguridad")
        
        conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT id, cliente, equipo, falla, estado, fecha FROM ordenes_servicio ORDER BY id DESC")
        todas_ordenes = cursor.fetchall()
        conn.close()

        if todas_ordenes:
            opciones_ord = {f"Orden #{o[0]:04d} — {o[1]} ({o[2]}) [Estado: {o[4]}]": o[0] for o in todas_ordenes}
            sel_orden_str = st.selectbox("Seleccione una orden de servicio:", options=list(opciones_ord.keys()))
            id_orden_elegida = opciones_ord[sel_orden_str]

            if st.button("🛠️ Abrir Ficha Técnica y Seguridad de la Orden Seleccionada", type="secondary"):
                st.session_state.ficha_orden_id = id_orden_elegida
        else:
            st.info("No hay órdenes de servicio registradas.")

        if st.session_state.ficha_orden_id:
            oid = st.session_state.ficha_orden_id
            conn = sqlite3.connect('jadithcell_comunicaciones.db', check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("SELECT id, cliente, cedula, telefono, direccion, equipo, imei, falla, costo, abono, estado, pin_patron, detalles_chequeo, fecha FROM ordenes_servicio WHERE id = ?", (oid,))
            ord_data = cursor.fetchone()
            conn.close()

            if ord_data:
                st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 15px; border-radius: 8px; border: 2px solid #38bdf8; margin-top: 15px;">
                        <h3 style="color: #38bdf8; margin-top: 0;">🛠️ BANCO DE REPARACIÓN - ORDEN #{ord_data[0]:04d}</h3>
                        <p><b>Fecha:</b> {ord_data[13]} | <b>Cliente:</b> {ord_data[1]} (CC: {ord_data[2]})</p>
                        <p><b>Teléfono:</b> {ord_data[3]} | <b>Dirección:</b> {ord_data[4]}</p>
                        <p><b>Equipo:</b> {ord_data[5]} | <b>IMEI:</b> {ord_data[6]}</p>
                        <p><b>Falla Reportada:</b> {ord_data[7]}</p>
                    </div>
                """, unsafe_allow_html=True)

                c_tot = float(ord_data[8]) if ord_data[8] else 0.0
                c_abo = float(ord_data[9]) if ord_data[9] else 0.0
                c_pen = c_tot - c_abo

                col_ft1, col_ft2, col_ft3 = st.columns(3)
                col_ft1.metric("Costo Total", f"${c_tot:,.2f}")
                col_ft2.metric("Abonado", f"${c_abo:,.2f}", delta_color="normal")
                col_ft3.metric("Saldo Pendiente", f"${c_pen:,.2f}", delta_color="inverse")

                st.markdown("##### 🔑 Seguridad y Patrón de Desbloqueo Guardado")
                
                def renderizar_patron_svg(secuencia_str, ancho=240, alto=240):
                    puntos = {
                        '1': (50, 50),   '2': (120, 50),   '3': (190, 50),
                        '4': (50, 120),  '5': (120, 120),  '6': (190, 120),
                        '7': (50, 190),  '8': (120, 190),  '9': (190, 190)
                    }
                    digitos = [c for c in str(secuencia_str) if c in '123456789']
                    svg_lines = f'<svg width="{ancho}" height="{alto}" style="background-color: #0b132b; border-radius: 8px; border: 2px solid #1f293d;" viewBox="0 0 240 240">'
                    
                    if len(digitos) > 1:
                        for i in range(len(digitos) - 1):
                            p1 = puntos[digitos[i]]
                            p2 = puntos[digitos[i+1]]
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

                col_pat_v1, col_pat_v2 = st.columns([1, 2])
                with col_pat_v1:
                    nuevo_patron_edit = st.text_input("Secuencia del Patrón / PIN", value=str(ord_data[11] or ""), key=f"edit_pat_{oid}")
                with col_pat_v2:
                    st.markdown("##### Patrón Gráfico Actual:")
                    st.markdown(renderizar_patron_svg(ord_data[11] or ""), unsafe_allow_html=True)
                
                estados_pos = ["PENDIENTE", "EN REVISIÓN", "REPARADO", "ENTREGADO", "SIN SOLUCIÓN", "ESPERANDO REPUESTO"]
                est_actual_idx = estados_pos.index(ord_data[10]) if ord_data[10] in estados_pos else 0
                nuevo_estado_edit = st.selectbox("Estado Actual", options=estados_pos, index=est_actual_idx, key=f"edit_est_{oid}")

                nuevo_abono_suma = st.number_input("Sumar Nuevo Abono ($)", min_value=0.0, step=5000.0, key=f"sum_abo_{oid}")

                col_btn_f1, col_btn_f2, col_btn_f3 = st.columns(3)
                with col_btn_f1:
                    if st.button("💾 Guardar Cambios de Ficha"):
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
                    st.markdown(f"<br><a href='https://wa.me/57{ord_data[3].replace(' ', '')}?text={msg_w}' target='_blank' style='background-color: #25d366; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; display: block; text-align: center;'>💬 Enviar WhatsApp</a>", unsafe_allow_html=True)

                with col_btn_f3:
                    if st.button("🖨️ Imprimir Recibo Básico"):
                        st.session_state.recibo_taller = {
                            "id": ord_data[0], "cliente": ord_data[1], "cedula": ord_data[2], "telefono": ord_data[3],
                            "equipo": ord_data[5], "imei": ord_data[6], "falla": ord_data[7], "costo": c_tot,
                            "abono": c_abo + nuevo_abono_suma, "estado": nuevo_estado_edit, "patron": nuevo_patron_edit,
                            "chequeo": ord_data[12], "fecha": ord_data[13]
                        }
                        st.rerun()

                if st.button("❌ Cerrar Ficha Técnica"):
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
