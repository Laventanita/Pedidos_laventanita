import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time
import json
import re
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")

# --- LÓGICA DE SCROLL AUTOMÁTICO ---
if "scroll_al_top" not in st.session_state:
    st.session_state.scroll_al_top = False

if st.session_state.scroll_al_top:
    components.html(
        """
        <script>
            var mainSection = window.parent.document.querySelector('section.main');
            if (mainSection) { mainSection.scrollTo({ top: 0, behavior: 'smooth' }); }
        </script>
        """, height=0,
    )
    st.session_state.scroll_al_top = False

# --- CREDENCIALES (Asegúrate de tenerlas en st.secrets) ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
PASSWORD_ADMIN = "admin123" 

# --- CONFIGURACIÓN DE CÓDIGOS POSTALES ---
MAPA_CODIGOS_POSTALES = {
    "55763": {"nombre": "Vitalia / Ojo de Agua / Los Héroes Tecámac", "costo": 25.0},
    "55764": {"nombre": "Los Héroes Tecámac II / Los Héroes Ozumbilla / Margarito F. Ayala", "costo": 25.0},
    "55766": {"nombre": "Ampliación Ozumbilla", "costo": 25.0},
    "55770": {"nombre": "Ojo de Agua / San Pedro Atzompa / Rinconada San Pedro", "costo": 25.0},
    "55773": {"nombre": "Hacienda Provenzal", "costo": 25.0},
    "55776": {"nombre": "Lomas de San Pedro Atzompa", "costo": 25.0},
    "55778": {"nombre": "Ampliación de la Concepción", "costo": 25.0},
    "55740": {"nombre": "Tecámac Centro / Ejido Santa Ana / El Calvario / Galaxias el Llano", "costo": 40.0},
    "55743": {"nombre": "Rancho la Luz / Hacienda del Bosque", "costo": 40.0},
    "55744": {"nombre": "San Pedro Potzohuacan", "costo": 40.0},
    "55745": {"nombre": "Real Granada IV / San Jerónimo Xonacahuacan", "costo": 40.0},
    "55748": {"nombre": "San Martín Azcatepec / San Mateo Tecalco / Los Olivos", "costo": 40.0},
    "55749": {"nombre": "Villa del Real / Sierra Hermosa / Montecarlo", "costo": 40.0},
    "55760": {"nombre": "San Francisco Cuautliquixca / Santa María Ozumbilla", "costo": 40.0},
    "55768": {"nombre": "Lomas de Ozumbilla / Cuauhtémoc / La Azteca", "costo": 40.0},
    "55746": {"nombre": "Rancho la Capilla / Real Belmonte", "costo": 55.0},
    "55747": {"nombre": "San Pablo Tecalco / San Isidro Citlalcóatl", "costo": 55.0},
    "55750": {"nombre": "Santa María Ajoloapan / El Tanque", "costo": 55.0},
    "55752": {"nombre": "San Juan Pueblo Nuevo", "costo": 55.0},
    "55754": {"nombre": "Paseos de Tecámac / Santo Domingo Ajoloapan", "costo": 55.0},
    "55755": {"nombre": "Los Reyes Acozac / Buenavista / San Miguel", "costo": 55.0},
    "55757": {"nombre": "San Lucas Xolox / Ejidal", "costo": 55.0},
    "55758": {"nombre": "Ampliación la Palma (Zona Industrial)", "costo": 55.0},
    "55765": {"nombre": "Los Héroes San Pablo / Lomas de Tecámac / La Cañada", "costo": 55.0},
    "55060": {"nombre": "Venta de Carpio / La Guadalupana / Los Héroes Ecatepec V", "costo": 55.0},
    "55063": {"nombre": "Ciudad Cuauhtémoc (Chiconautla 3000)", "costo": 55.0},
    "55064": {"nombre": "San Isidro Atlautenco / Cd. Cuauhtémoc (Nopalera)", "costo": 55.0},
    "55065": {"nombre": "Santa Cruz Venta de Carpio", "costo": 55.0},
    "55066": {"nombre": "Santa María Chiconautla / Santo Tomás Chiconautla", "costo": 55.0},
    "55067": {"nombre": "Ciudad Cuauhtémoc (Geo 2000 / Tlaloc)", "costo": 55.0},
    "55068": {"nombre": "Santo Tomás Chiconautla (Ejido / El Mirador)", "costo": 55.0},
    "55069": {"nombre": "La Preciosa / Los Pajaritos / La Garita", "costo": 55.0},
}

# --- MENÚ ---
MENU = {
    "☕ Desayunos (La Ventanita)": {
        "Chilaquiles chicos (80g)": 50.0,
        "Chilaquiles medianos (170g)": 65.0,
        "Chilaquiles para acompañar (250g)": 100.0,
        "Cuernito sencillo": 45.0,
        "Cuernito con fruta": 75.0
    },
    "🍓 Frutas y Cocteles (La Ventanita)": {
        "Coctel de Mango con Chantilly": 35.0,
        "Vaso de Mango": 35.0,
        "Vaso de Uva": 35.0,
        "Vaso de Jícama": 35.0,
        "Vaso de Piña": 35.0,
        "Vaso de Sandía": 35.0,
        "Vaso de Melón": 35.0,
        "Vaso de Papaya": 35.0,
        "Vaso de Mango con Papaya": 35.0,
        "Vaso de Mango con Uvas": 35.0
    },
    "🌮 Los Tacos Mixi": {
        "Taco de Pastor": 28.0,
        "Taco de Suadero": 28.0,
        "Taco de Enchilada": 28.0,
        "Taco de Bisteck": 28.0,
        "Taco de Chuleta": 28.0,
        "Taco Campechano": 28.0
    },
    "🫓 Quesadillas": {
        "Quesadilla de Queso": 25.0,
        "Quesadilla de Suadero": 28.0,
        "Quesadilla de Tinga de pollo": 25.0,
        "Quesadilla de Chicharrón": 25.0,
        "Quesadilla de Champiñón": 25.0,
        "Quesadilla de Mollejas": 25.0,
        "Quesadilla de Pancita": 25.0
    },
    "✨ Especialidades Mixi": {
        "Gordita": 30.0,
        "Pambazo de Papa con Longaniza": 30.0,
        "Pambazo Especial (Otro ingrediente)": 35.0
    },
    "🥤 Licuados": {
        "Licuado de Fresa": 35.0, 
        "Licuado de Chocolate": 35.0, 
        "Licuado de Plátano": 35.0
    },
    "🍹 Aguas Frescas": {
        "Agua de Café": 25.0, "Agua de Mazapán": 25.0, "Agua de Fresa": 25.0,
        "Agua de Limón": 25.0, "Agua de Melón": 25.0, "Agua de Piña": 25.0,
        "Agua de Sandía": 25.0, "Agua de Guayaba": 25.0, "Agua de Avena": 25.0
    },
    "🥤 Jugos Naturales": {
        "Jugo Verde": 35.0,
        "Jugo de Naranja": 35.0,
        "Jugo Combinado": 40.0
    }
}

# --- PERSISTENCIA ---
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'notas_productos' not in st.session_state: st.session_state.notas_productos = {}
if 'datos_cliente_persistentes' not in st.session_state:
    st.session_state.datos_cliente_persistentes = {"nombre": "", "tel": "", "dir": "", "cp": ""}

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT, 
                  metodo_pago TEXT, archivado INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('sistema_abierto', 'True')")
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_disponibilidad (producto TEXT PRIMARY KEY, disponible TEXT)''')
    conn.commit()
    conn.close()

def obtener_estado_sistema_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'sistema_abierto'")
    res = c.fetchone()
    conn.close()
    return res[0] == 'True' if res else True

def actualizar_estado_sistema_db(abierto):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('sistema_abierto', ?)", (str(abierto),))
    conn.commit()
    conn.close()

def obtener_inventario_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("SELECT producto, disponible FROM inventario_disponibilidad")
    filas = c.fetchall()
    conn.close()
    return {f[0]: (f[1] == 'True') for f in filas}

def actualizar_producto_inventario_db(producto, disponible):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO inventario_disponibilidad (producto, disponible) VALUES (?, ?)", (producto, str(disponible)))
    conn.commit()
    conn.close()

def guardar_pedido_db(fecha, nombre, telefono, direccion, pedido, total, metodo_pago):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago, archivado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
              (fecha, nombre, telefono, direccion, pedido, total, "Pendiente", metodo_pago))
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

def buscar_pedidos_por_telefono(telefono):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("SELECT id, fecha, estado, total, pedido FROM pedidos WHERE telefono = ? ORDER BY id DESC LIMIT 5", (telefono,))
    res = c.fetchall()
    conn.close()
    return res

def enviar_pedido_telegram(id_pedido, nombre, telefono, direccion, tipo_entrega, costo_envio, propina_txt, detalle, total, metodo_pago):
    mensaje = (
        f"🔔 *NUEVO PEDIDO #{id_pedido}*\n"
        f"👤 {nombre} ({telefono})\n"
        f"🛵 {tipo_entrega} | 📍 {direccion}\n"
        f"💳 Pago: {metodo_pago}\n"
        f"---------------------------\n"
        f"📝 *Pedido:*\n{detalle}\n"
        f"---------------------------\n"
        f"💵 Envío: ${costo_envio:.2f}\n"
        f"🚴‍♂️ Propina: {propina_txt}\n"
        f"💰 *TOTAL: ${total:.2f}*"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

init_db()
sistema_abierto_real = obtener_estado_sistema_db()
inventario_real = obtener_inventario_db()
st.session_state.inventario = {p: inventario_real.get(p, True) for cat in MENU.values() for p in cat}

# --- PESTAÑAS ---
tab_menu, tab_rastreo, tab_admin = st.tabs(["📋 Menú", "🛵 Mis Pedidos", "🔐 Admin"])

# =====================================================================
# 📋 TAB 1: MENÚ PARA CLIENTES
# =====================================================================
with tab_menu:
    st.title("La Ventanita & Tacos Mixi")
    
    if not sistema_abierto_real:
        st.error("🛑 COCINA CERRADA POR EL MOMENTO.")
    else:
        st.write("¡Haz tu pedido!")

    # Bucle del Menú con TODA la lógica de personalización
    for category, productos in MENU.items():
        if any(st.session_state.inventario.get(p, True) for p in productos):
            with st.expander(f"{category}", expanded=True):
                for prod, precio in productos.items():
                    if not st.session_state.inventario.get(prod, True): continue
                    
                    col_i, col_c = st.columns([2, 2])
                    extra_txt = ""
                    p_final = precio
                    
                    with col_i:
                        # --- Lógica de Precios y Opciones ---
                        if "Chilaquiles" in prod:
                            s = st.selectbox("Salsa:", ["Verdes", "Rojos"], key=f"s_{prod}")
                            extra_txt = f" ({s})"
                        elif "Coctel de Mango" in prod:
                            t = st.selectbox("Tamaño:", ["Chico ($35.00)", "Grande (+$15.00)"], key=f"t_{prod}")
                            if "Grande" in t: p_final = 50.0
                            extra_txt = f" [{t}]"
                        elif "Taco" in prod:
                            con_q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"q_{prod}")
                            guar = st.selectbox("Guarnición:", ["Con papas", "Con nopales", "Ambos", "Sin nada"], key=f"g_{prod}")
                            if con_q: p_final += 3.0; extra_txt += " (Con Quesillo)"
                            extra_txt += f" [{guar}]"
                        elif "Quesadilla" in prod or "Gordita" in prod:
                            con_q = st.checkbox("¿Con Quesillo?", key=f"q_{prod}")
                            if con_q: 
                                p_final = 33.0 if "Gordita" in prod else 31.0
                                extra_txt = " (Con Quesillo)"
                        elif "Pambazo Especial" in prod:
                            ing = st.text_input("¿Ingrediente?", key=f"i_{prod}", placeholder="Ej. Tinga")
                            if ing: extra_txt = f" de {ing}"
                        elif "Licuado" in prod:
                            t = st.selectbox("Tamaño:", ["1/2 Litro ($35.00)", "1 Litro (+$35.00)"], key=f"l_{prod}")
                            if "1 Litro" in t: p_final = 70.0
                            extra_txt = f" ({t})"
                        elif "Agua" in prod:
                            t = st.selectbox("Tamaño:", ["1/2 Litro ($25.00)", "1 Litro (+$15.00)"], key=f"a_{prod}")
                            if "1 Litro" in t: p_final = 40.0
                            extra_txt = f" ({t})"
                        elif "Jugo" in prod:
                            t = st.selectbox("Tamaño:", ["Chico (1/2 L)", "Grande (1 L) (+$20.00)"], key=f"j_{prod}")
                            if "Grande" in t: p_final = precio + 20.0
                            extra_txt = f" ({t})"

                        st.write(f"**{prod}{extra_txt}**\n${p_final:.2f}")

                    with col_c:
                        key_c = f"{prod}|||{extra_txt}|||{p_final}"
                        cant = st.session_state.carrito.get(key_c, 0)
                        btn_c1, btn_c2, btn_c3 = st.columns([1,1,1])
                        if btn_c1.button("➖", key=f"mn_{key_c}"):
                            st.session_state.carrito[key_c] = max(0, cant - 1)
                            st.rerun()
                        btn_c2.markdown(f"<h4 style='text-align:center;'>{cant}</h4>", unsafe_allow_html=True)
                        if btn_c3.button("➕", key=f"mx_{key_c}"):
                            st.session_state.carrito[key_c] = cant + 1
                            st.rerun()
                        if cant > 0:
                            st.session_state.notas_productos[key_c] = st.text_input("Nota:", key=f"nt_{key_c}", placeholder="Ej. sin cebolla")

    # --- CIERRE DE PEDIDO ---
    p_sel = {k: v for k, v in st.session_state.carrito.items() if v > 0}
    if p_sel and sistema_abierto_real:
        st.markdown("---")
        st.subheader("🛒 Entrega y Pago")
        
        # Subtotal de productos
        total_p = sum(float(k.split("|||")[2]) * v for k, v in p_sel.items())

        m_envio = st.selectbox("Método de Entrega", ["🛵 Envío a Domicilio", "🛍️ Recoger en local"])
        c_envio = 0.0
        if m_envio == "🛵 Envío a Domicilio":
            cp = st.text_input("Código Postal (5 dígitos)", value=st.session_state.datos_cliente_persistentes["cp"], max_chars=5)
            if cp in MAPA_CODIGOS_POSTALES:
                c_envio = MAPA_CODIGOS_POSTALES[cp]["costo"]
                st.success(f"📍 Zona: {MAPA_CODIGOS_POSTALES[cp]['nombre']}")
            elif cp:
                c_envio = None
                st.error("❌ Fuera de Cobertura.")
        
        prop = st.radio("🚴‍♂️ Propina", ["No agregar", "$10.00", "$15.00", "$20.00", "En efectivo"], horizontal=True)
        v_prop = 10.0 if "$10" in prop else 15.0 if "$15" in prop else 20.0 if "$20" in prop else 0.0
        
        m_pago = st.radio("💳 Pago", ["💵 Efectivo", "💳 Tarjeta (Terminal)", "📲 Transferencia"], horizontal=True)
        c_txt = m_pago
        if m_pago == "💵 Efectivo":
            cam = st.text_input("¿Con cuánto pagas?")
            c_txt = f"Efectivo (Cambio de {cam})" if cam else "Efectivo"
        elif m_pago == "📲 Transferencia":
            st.info("💡 Al confirmar, recibirás los datos de transferencia.")

        total_f = total_p + (c_envio or 0.0) + v_prop

        # --- RESUMEN DETALLADO (TICKET) ---
        st.markdown("### 📋 Resumen de tu Compra")
        with st.container(border=True):
            det_t = ""
            for k, cant in p_sel.items():
                nom, ext, pre = k.split("|||")
                sub = float(pre) * cant
                nota = st.session_state.notas_productos.get(k, "").strip()
                st.write(f"• {cant}x {nom}{ext} {'('+nota+')' if nota else ''} — **${sub:.2f}**")
                det_t += f"• {cant}x {nom}{ext} {'('+nota+')' if nota else ''} — ${sub:.2f}\n"
            st.markdown("---")
            st.write(f"🏠 Envío: ${c_envio:.2f}" if c_envio is not None else "🏠 Envío: --")
            st.write(f"🎁 Propina: ${v_prop:.2f}")
            st.write(f"💳 Pago: {m_pago}")
            st.markdown(f"## **Total Final: ${total_f:.2f}**")

        with st.form("conf_form"):
            st.subheader("👤 Datos de contacto")
            nom_f = st.text_input("Nombre Completo *", value=st.session_state.datos_cliente_persistentes["nombre"])
            tel_f = st.text_input("Teléfono (10 dígitos) *", value=st.session_state.datos_cliente_persistentes["tel"])
            dir_f = st.text_area("Dirección *", value=st.session_state.datos_cliente_persistentes["dir"]) if m_envio == "🛵 Envío a Domicilio" else ""
            
            if st.form_submit_button("🚀 CONFIRMAR Y ENVIAR PEDIDO"):
                t_limp = re.sub(r"\D", "", tel_f)
                if len(t_limp) == 10 and nom_f and (dir_f or m_envio != "🛵 Envío a Domicilio") and c_envio is not None:
                    # Guardar datos
                    st.session_state.datos_cliente_persistentes = {"nombre": nom_f, "tel": t_limp, "dir": dir_f, "cp": cp if 'cp' in locals() else ""}
                    id_ord = guardar_pedido_db(datetime.now().strftime("%Y-%m-%d %H:%M"), nom_f, t_limp, dir_f, det_t, total_f, c_txt)
                    enviar_pedido_telegram(id_ord, nom_f, t_limp, dir_f, m_envio, (c_envio or 0.0), prop, det_t, total_f, c_txt)
                    # Reset
                    st.session_state.carrito = {}
                    st.success(f"✅ ¡Pedido enviado! Folio #{id_ord}")
                    time.sleep(2)
                    st.rerun()
                else: st.error("⚠️ Verifica tus datos.")

# =====================================================================
# 🛵 TAB 2: MIS PEDIDOS (MULTI-USUARIO)
# =====================================================================
with tab_rastreo:
    st.header("🔍 Rastrea tus pedidos")
    t_sesion = st.session_state.datos_cliente_persistentes.get("tel", "")
    input_rastreo = st.text_input("Ingresa tu teléfono:", value=t_sesion)
    
    if input_rastreo:
        t_rastreo = re.sub(r"\D", "", input_rastreo)
        if len(t_rastreo) == 10:
            peds_u = buscar_pedidos_por_telefono(t_rastreo)
            if not peds_u: st.info("No hay pedidos con este número.")
            for pid, pfe, pest, ptot, pdet in peds_u:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 2])
                    c1.markdown(f"### #{pid}"); c1.caption(pfe)
                    c2.write(f"**Estado:** {pest}")
                    prog = 0.15 if pest=="Pendiente" else 0.5 if pest=="En Cocina" else 0.8 if pest=="En Camino" else 1.0
                    if pest == "Cancelado": st.error("Cancelado")
                    else: st.progress(prog)
                    with st.expander("Ver ticket"):
                        st.text(pdet); st.write(f"**Total: ${ptot:.2f}**")
            if st.button("🔄 Actualizar"): st.rerun()

# =====================================================================
# 🔐 TAB 3: ADMIN
# =====================================================================
with tab_admin:
    pw = st.text_input("Clave", type="password")
    if pw == PASSWORD_ADMIN:
        st.header("Admin Panel")
        ab = st.toggle("Local Abierto", value=sistema_abierto_real)
        if ab != sistema_abierto_real: actualizar_estado_sistema_db(ab); st.rerun()
        
        # Pedidos
        st.subheader("Pedidos Activos")
        conn = sqlite3.connect('pedidos_negocio.db')
        cur = conn.cursor()
        cur.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 0 ORDER BY id DESC")
        datos_a = cur.fetchall()
        conn.close()

        for pid, pf, pnom, ptel, pdir, pdet, ptot, pest, ppag in datos_a:
            with st.container(border=True):
                st.write(f"**#{pid} - {pnom} ({ptel})** | Total: ${ptot}")
                st.text(pdet)
                c_b = st.columns(5)
                if c_b[0].button("🍳", key=f"a1_{pid}"): 
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='En Cocina' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_b[1].button("🛵", key=f"a2_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='En Camino' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_b[2].button("✅", key=f"a3_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='Entregado' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_b[3].button("❌", key=f"a4_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='Cancelado' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_b[4].button("📂", key=f"a5_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET archivado=1 WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()

        # Inventario
        st.subheader("Disponibilidad")
        for cat, prds in MENU.items():
            st.write(f"**{cat}**")
            for p in prds:
                check = st.checkbox(p, value=st.session_state.inventario.get(p, True), key=f"iv_{p}")
                if check != st.session_state.inventario.get(p, True):
                    actualizar_producto_inventario_db(p, check); st.rerun()
