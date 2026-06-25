import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time
import json
import re
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")

# --- LÓGICA DE SCROLL ---
if "scroll_al_top" not in st.session_state:
    st.session_state.scroll_al_top = False

if st.session_state.scroll_al_top:
    components.html(
        """<script>window.parent.document.querySelector('section.main').scrollTo({ top: 0, behavior: 'smooth' });</script>""",
        height=0,
    )
    st.session_state.scroll_al_top = False

# --- CREDENCIALES ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
PASSWORD_ADMIN = "admin123" 

# --- DATOS BANCARIOS ---
DATOS_BANCO = """
💰 **DATOS PARA TRANSFERENCIA:**
- **Banco:** BBVA Bancomer
- **Cuenta:** 1514123852
- **Cuenta CLABE:** 012180015141238524
- **Beneficiario:** Javier Gonzalez Regalado
"""

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

# --- MENÚ COMPLETO ---
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
        "Licuado de Fresa": 35.0, "Licuado de Chocolate": 35.0, "Licuado de Plátano": 35.0
    },
    "🍹 Aguas Frescas": {
        "Agua de Café": 25.0, "Agua de Mazapán": 25.0, "Agua de Fresa": 25.0,
        "Agua de Limón": 25.0, "Agua de Melón": 25.0, "Agua de Piña": 25.0,
        "Agua de Sandía": 25.0, "Agua de Guayaba": 25.0, "Agua de Avena": 25.0
    },
    "🥤 Jugos Naturales": {
        "Jugo Verde": 35.0, "Jugo de Naranja": 35.0, "Jugo Combinado": 40.0
    }
}

# --- PERSISTENCIA ---
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'notas_productos' not in st.session_state: st.session_state.notas_productos = {}
if 'datos_cliente_persistentes' not in st.session_state:
    st.session_state.datos_cliente_persistentes = {"nombre": "", "tel": "", "dir": "", "cp": ""}

# --- FUNCIONES DE BASE DE DATOS (REVISADAS) ---
def init_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT, 
                  metodo_pago TEXT, archivado INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO configuracion VALUES ('sistema_abierto', 'True')")
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_disponibilidad (producto TEXT PRIMARY KEY, disponible TEXT)''')
    conn.commit()
    conn.close()

def obtener_estado_sistema():
    conn = sqlite3.connect('pedidos_negocio.db')
    res = conn.cursor().execute("SELECT valor FROM configuracion WHERE clave='sistema_abierto'").fetchone()
    conn.close()
    return res[0] == 'True' if res else True

def actualizar_estado_sistema(val):
    conn = sqlite3.connect('pedidos_negocio.db')
    conn.cursor().execute("INSERT OR REPLACE INTO configuracion VALUES ('sistema_abierto', ?)", (str(val),))
    conn.commit()
    conn.close()

def obtener_inventario():
    conn = sqlite3.connect('pedidos_negocio.db')
    filas = conn.cursor().execute("SELECT producto, disponible FROM inventario_disponibilidad").fetchall()
    conn.close()
    return {f[0]: (f[1] == 'True') for f in filas}

def actualizar_producto_inventario(prod, disp):
    conn = sqlite3.connect('pedidos_negocio.db')
    conn.cursor().execute("INSERT OR REPLACE INTO inventario_disponibilidad VALUES (?, ?)", (prod, str(disp)))
    conn.commit()
    conn.close()

# ESTA ES LA FUNCIÓN QUE FALTABA
def buscar_pedidos_por_telefono(telefono):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("SELECT id, fecha, estado, total, pedido FROM pedidos WHERE telefono = ? ORDER BY id DESC LIMIT 5", (telefono,))
    res = c.fetchall()
    conn.close()
    return res

def enviar_pedido_telegram(id_p, nom, tel, dir, env, c_env, prop, det, tot, pago):
    mensaje = (
        f"🔔 *NUEVO PEDIDO CONFIRMADO #{id_p}*\n"
        f"👤 *Cliente:* {nom} ({tel})\n"
        f"🛵 *Entrega:* {env} | 📍 {dir if dir else 'Recoge en Local'}\n"
        f"💳 *Pago:* {pago}\n"
        f"---------------------------\n"
        f"📝 *Detalle:*\n{det}\n"
        f"---------------------------\n"
        f"💵 *Envío:* ${c_env:.2f} | 🚴‍♂️ *Propina:* {prop}\n"
        f"💰 *TOTAL A COBRAR: ${tot:.2f}*"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=5)
    except: pass

init_db()
sistema_abierto = obtener_estado_sistema()
inventario_actual = obtener_inventario()

# --- INTERFAZ ---
tab_menu, tab_rastreo, tab_admin = st.tabs(["📋 Menú para Clientes", "🛵 Mis Pedidos", "🔐 Panel Administrador"])

# ================= TAB 1: MENÚ =================
with tab_menu:
    st.title("La Ventanita & Tacos Mixi")
    if not sistema_abierto:
        st.error("🛑 **LO SENTIMOS, COCINA CERRADA**")
    else:
        for cat, prods in MENU.items():
            with st.expander(cat, expanded=True):
                for p, pre in prods.items():
                    if not inventario_actual.get(p, True): continue
                    
                    col_info, col_btn = st.columns([3, 1])
                    col_info.write(f"**{p}** — ${pre:.2f}")
                    
                    cant = st.session_state.carrito.get(p, 0)
                    if cant == 0:
                        if col_btn.button("🛒 Agregar", key=f"btn_{p}"):
                            st.session_state.carrito[p] = 1
                            st.rerun()
                    else:
                        with col_btn:
                            c1, c2, c3 = st.columns([1,1,1])
                            if c1.button("➖", key=f"m_{p}"):
                                st.session_state.carrito[p] = max(0, cant - 1)
                                st.rerun()
                            c2.write(f"**{cant}**")
                            if c3.button("➕", key=f"p_{p}"):
                                st.session_state.carrito[p] += 1
                                st.rerun()
                        
                        # Opciones de personalización
                        col_opt, col_not = st.columns(2)
                        ext = ""; p_f = pre
                        with col_opt:
                            if "Chilaquiles" in p:
                                s = st.radio("Salsa:", ["Verdes", "Rojos"], key=f"s_{p}", horizontal=True)
                                ext = f" ({s})"
                            elif "Taco" in p:
                                q = st.checkbox("¿Con Quesillo? (+$3)", key=f"q_{p}")
                                g = st.selectbox("Guarnición:", ["Papas", "Nopales", "Ambos", "Nada"], key=f"g_{p}")
                                if q: p_f += 3.0; ext = " (Con Quesillo)"
                                ext += f" [{g}]"
                            elif "Licuado" in p or "Agua" in p or "Jugo" in p:
                                t = st.radio("Tamaño:", ["Chico", "Grande"], key=f"t_{p}", horizontal=True)
                                if t == "Grande": p_f += 20.0
                                ext = f" ({t})"
                        with col_not:
                            nota = st.text_input("Nota:", key=f"n_{p}", placeholder="Ej. sin cebolla")
                            st.session_state.notas_productos[p] = {"extra": ext, "p_final": p_f, "nota": nota}

    # PROCESO DE PAGO
    sel = {k: v for k, v in st.session_state.carrito.items() if v > 0}
    if sel:
        st.divider()
        st.subheader("🛒 Resumen de Compra")
        tot_art = 0.0; ticket = ""
        with st.container(border=True):
            for p, v in sel.items():
                data = st.session_state.notas_productos.get(p, {"extra": "", "p_final": MENU[next(c for c in MENU if p in MENU[c])][p], "nota": ""})
                sub = data["p_final"] * v
                st.write(f"• **{v}x {p}{data['extra']}** — ${sub:.2f}")
                ticket += f"• {v}x {p}{data['extra']} ({data['nota']}) — ${sub:.2f}\n"
                tot_art += sub

        col_env1, col_env2 = st.columns(2)
        m_envio = col_env1.selectbox("Entrega:", ["Domicilio", "Recoger"])
        c_envio = 0.0
        if m_envio == "Domicilio":
            cp = col_env2.text_input("CP (5 dígitos):", value=st.session_state.datos_cliente_persistentes["cp"], max_chars=5)
            if cp in MAPA_CODIGOS_POSTALES:
                c_envio = MAPA_CODIGOS_POSTALES[cp]["costo"]
                st.success(f"📍 Zona: {MAPA_CODIGOS_POSTALES[cp]['nombre']}")
            elif cp: c_envio = None; st.error("Sin cobertura")

        prop = st.radio("🚴‍♂️ Propina:", ["No", "$10", "$15", "$20", "Efectivo"], horizontal=True)
        v_prop = 10.0 if "$10" in prop else 15.0 if "$15" in prop else 20.0 if "$20" in prop else 0.0
        
        m_pago = st.radio("💳 Pago:", ["💵 Efectivo", "💳 Tarjeta", "📲 Transferencia"], horizontal=True)
        if m_pago == "📲 Transferencia": st.warning(DATOS_BANCO)
        
        total_f = tot_art + (c_envio or 0.0) + v_prop
        st.markdown(f"## **Total: ${total_f:.2f}**")

        with st.form("f_final"):
            nom = st.text_input("Nombre *", value=st.session_state.datos_cliente_persistentes["nombre"])
            tel = st.text_input("Teléfono *", value=st.session_state.datos_cliente_persistentes["tel"])
            dir_c = st.text_area("Dirección *") if m_envio == "Domicilio" else ""
            if st.form_submit_button("🚀 ENVIAR PEDIDO"):
                t_l = re.sub(r"\D", "", tel)
                if len(t_l) >= 10 and nom and c_envio is not None:
                    st.session_state.datos_cliente_persistentes = {"nombre": nom, "tel": t_l, "dir": dir_c, "cp": cp if 'cp' in locals() else ""}
                    conn = sqlite3.connect('pedidos_negocio.db')
                    id_p = conn.cursor().execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago) VALUES (?,?,?,?,?,?,?,?)", (datetime.now().strftime("%H:%M"), nom, t_l, dir_c, ticket, total_f, "Pendiente", m_pago)).lastrowid
                    conn.commit(); conn.close()
                    enviar_pedido_telegram(id_p, nom, t_l, dir_c, m_envio, (c_envio or 0.0), prop, ticket, total_f, m_pago)
                    st.session_state.carrito = {}; st.success(f"✅ Folio #{id_p}"); time.sleep(2); st.rerun()
                else: st.error("Revisa tus datos.")

# ================= TAB 2: MIS PEDIDOS =================
with tab_rastreo:
    st.header("🔍 Rastrea tus pedidos")
    t_ras = st.session_state.datos_cliente_persistentes.get("tel", "")
    tel_busqueda = st.text_input("Teléfono:", value=t_ras)
    if tel_busqueda:
        historial = buscar_pedidos_por_telefono(tel_busqueda)
        if not historial: st.info("Sin pedidos recientes.")
        for pid, pfe, pest, ptot, pdet in historial:
            with st.container(border=True):
                col_h1, col_h2 = st.columns([1, 2])
                col_h1.markdown(f"### Folio #{pid}"); col_h1.caption(pfe)
                col_h2.write(f"**Estado:** {pest}")
                prog = 0.2 if pest=="Pendiente" else 0.5 if pest=="En Cocina" else 0.8 if pest=="En Camino" else 1.0
                if pest == "Cancelado": st.error("❌ Cancelado")
                else: st.progress(prog)
                with st.expander("Ticket"): st.text(pdet); st.write(f"**Total: ${ptot:.2f}**")
        if st.button("🔄 Actualizar"): st.rerun()

# ================= TAB 3: ADMIN =================
with tab_admin:
    pwd = st.text_input("Clave:", type="password")
    if pwd == PASSWORD_ADMIN:
        actualizar_estado_sistema(st.toggle("Cocina Abierta", value=sistema_abierto))
        st.subheader("📦 Pedidos Activos")
        conn = sqlite3.connect('pedidos_negocio.db')
        p_raw = conn.cursor().execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado=0 ORDER BY id DESC").fetchall()
        conn.close()
        for pid, pf, pnom, ptel, pdir, pdet, ptot, pest, ppag in p_raw:
            with st.container(border=True):
                st.write(f"**#{pid} - {pnom} ({ptel})** | Total: ${ptot}")
                st.text(pdet)
                st.write("Cambiar a:")
                c_a = st.columns(5)
                ests = ["Pendiente", "En Cocina", "En Camino", "Entregado", "Cancelado"]
                icos = ["⏳", "🍳", "🛵", "✅", "❌"]
                for i, (e, ic) in enumerate(zip(ests, icos)):
                    lbl = f"📍 {e.upper()}" if pest == e else f"{ic} {e}"
                    if c_a[i].button(lbl, key=f"adm_{pid}_{e}"):
                        conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado=? WHERE id=?", (e, pid)); conn.commit(); conn.close(); st.rerun()
                if st.button(f"📂 Archivar #{pid}", key=f"arch_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET archivado=1 WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
        st.subheader("🍏 Inventario")
        for cat, prds in MENU.items():
            st.write(f"**{cat}**")
            for p in prds:
                disp = inventario_actual.get(p, True)
                if st.checkbox(p, value=disp, key=f"iv_{p}") != disp:
                    actualizar_producto_inventario(p, not disp); st.rerun()
