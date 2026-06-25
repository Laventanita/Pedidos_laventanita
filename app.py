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

# --- PERSISTENCIA Y ESTADOS ---
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

# =====================================================================
# 📋 VISTA DEL MENÚ
# =====================================================================
with tab_menu:
    st.title("La Ventanita & Tacos Mixi")
    
    if not sistema_abierto:
        st.error("🛑 **LO SENTIMOS, NUESTRA COCINA SE ENCUENTRA CERRADA POR EL MOMENTO.**")
    else:
        st.write("Selecciona tus platillos favoritos abajo.")

    # Generación dinámica del menú con botón "Agregar"
    for categoria, productos in MENU.items():
        with st.expander(f"{categoria}", expanded=True):
            for prod, precio in productos.items():
                if not inventario_actual.get(prod, True):
                    continue
                
                col_i, col_c = st.columns([3, 1])
                col_i.write(f"**{prod}** — ${precio:.2f}")
                
                # Estado del carrito para este producto
                cant = st.session_state.carrito.get(prod, 0)
                
                if cant == 0:
                    if col_c.button("🛒 Agregar", key=f"add_btn_{prod}"):
                        st.session_state.carrito[prod] = 1
                        st.rerun()
                else:
                    with col_c:
                        c1, c2, c3 = st.columns([1, 1, 1])
                        if c1.button("➖", key=f"min_{prod}"):
                            st.session_state.carrito[prod] = max(0, cant - 1)
                            st.rerun()
                        c2.write(f"**{cant}**")
                        if c3.button("➕", key=f"pls_{prod}"):
                            st.session_state.carrito[prod] += 1
                            st.rerun()
                    
                    # Opciones de personalización que aparecen SOLO al agregar
                    st.write("---")
                    col_opt, col_nota = st.columns(2)
                    
                    extra_txt = ""
                    p_final = precio
                    
                    with col_opt:
                        if "Chilaquiles" in prod:
                            salsa = st.radio("Elige salsa:", ["Verdes", "Rojos"], key=f"opt_{prod}", horizontal=True)
                            extra_txt = f" ({salsa})"
                        elif "Taco" in prod:
                            q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"opt_{prod}")
                            g = st.selectbox("Guarnición:", ["Papas", "Nopales", "Papas y Nopales", "Sin nada"], key=f"g_{prod}")
                            if q: p_final += 3.0; extra_txt = " (Con Quesillo)"
                            extra_txt += f" [{g}]"
                        elif "Coctel de Mango" in prod:
                            t = st.radio("Tamaño:", ["Chico ($35.00)", "Grande (+$15.00)"], key=f"opt_{prod}", horizontal=True)
                            if "Grande" in t: p_final = 50.0
                            extra_txt = f" [{t}]"
                        elif "Licuado" in prod or "Agua" in prod or "Jugo" in prod:
                            t = st.radio("Tamaño:", ["Chico", "Grande"], key=f"opt_{prod}", horizontal=True)
                            if t == "Grande": p_final += 20.0 # Ajuste de precio por tamaño grande
                            extra_txt = f" ({t})"
                        elif "Pambazo Especial" in prod:
                            ing = st.text_input("¿Ingrediente?", key=f"opt_{prod}", placeholder="Tinga, Suadero...")
                            if ing: extra_txt = f" de {ing}"
                    
                    with col_nota:
                        nota = st.text_input("Instrucciones especiales:", key=f"not_{prod}", placeholder="Sin cebolla, muy picante...")
                        # Guardamos en sesión la combinación específica
                        st.session_state.notas_productos[prod] = {"extra": extra_txt, "precio_v": p_final, "nota_v": nota}

    # --- PROCESO DE COMPRA ---
    sel = {k: v for k, v in st.session_state.carrito.items() if v > 0}
    if sel:
        st.divider()
        st.subheader("🛒 Resumen y Pago")
        
        tot_articulos = 0.0
        ticket_resumen = ""
        
        # Generar ticket visual
        with st.container(border=True):
            for p, v in sel.items():
                data = st.session_state.notas_productos.get(p, {"extra": "", "precio_v": MENU.get(p, 0), "nota_v": ""})
                sub = data["precio_v"] * v
                st.write(f"• **{v}x {p}{data['extra']}** — ${sub:.2f}")
                if data['nota_v']: st.caption(f"  └ Nota: {data['nota_v']}")
                ticket_resumen += f"• {v}x {p}{data['extra']} ({data['nota_v']}) — ${sub:.2f}\n"
                tot_articulos += sub

        # Configuración de Envío
        col_env1, col_env2 = st.columns(2)
        with col_env1:
            m_envio = st.selectbox("¿Cómo recibes?", ["🛵 Envío a Domicilio", "🛍️ Recoger en local"])
        
        c_envio = 0.0
        if m_envio == "🛵 Envío a Domicilio":
            with col_env2:
                cp = st.text_input("Introduce tu Código Postal (5 dígitos):", value=st.session_state.datos_cliente_persistentes["cp"], max_chars=5)
                if cp in MAPA_CODIGOS_POSTALES:
                    c_envio = MAPA_CODIGOS_POSTALES[cp]["costo"]
                    st.success(f"📍 Zona: {MAPA_CODIGOS_POSTALES[cp]['nombre']} (Envío: ${c_envio})")
                elif cp: 
                    c_envio = None
                    st.error("❌ Código Postal fuera de zona de cobertura.")
        
        # Propina y Pago
        prop = st.radio("🚴‍♂️ Propina para el repartidor:", ["No agregar", "$10.00", "$15.00", "$20.00", "En efectivo"], horizontal=True)
        v_prop = 10.0 if "$10" in prop else 15.0 if "$15" in prop else 20.0 if "$20" in prop else 0.0
        
        m_pago = st.radio("💳 Método de Pago:", ["💵 Efectivo", "💳 Tarjeta (Terminal)", "📲 Transferencia"], horizontal=True)
        
        if m_pago == "📲 Transferencia":
            st.warning(DATOS_BANCO)
        
        det_pago = m_pago
        if m_pago == "💵 Efectivo":
            cambio = st.text_input("¿Con cuánto pagas? (Para llevarte cambio):")
            if cambio: det_pago = f"Efectivo (Cambio de {cambio})"

        # TOTAL FINAL
        total_final = tot_articulos + (c_envio if c_envio else 0.0) + v_prop
        st.markdown(f"## **Total Final: ${total_final:.2f}**")

        # FORMULARIO FINAL
        with st.form("form_pedido"):
            st.subheader("👤 Datos del Cliente")
            nom_c = st.text_input("Nombre Completo *", value=st.session_state.datos_cliente_persistentes["nombre"])
            tel_c = st.text_input("Teléfono de contacto (10 dígitos) *", value=st.session_state.datos_cliente_persistentes["tel"])
            dir_c = st.text_area("Dirección Completa (Calle, No, Colonia, Referencias) *", value=st.session_state.datos_cliente_persistentes["dir"]) if m_envio == "🛵 Envío a Domicilio" else ""
            
            if st.form_submit_button("🚀 CONFIRMAR Y ENVIAR PEDIDO"):
                t_limpio = re.sub(r"\D", "", tel_c)
                if len(t_limpio) == 10 and nom_c and (dir_c or m_envio != "🛵 Envío a Domicilio") and c_envio is not None:
                    # Guardar en sesión
                    st.session_state.datos_cliente_persistentes = {"nombre": nom_c, "tel": t_limpio, "dir": dir_c, "cp": cp if 'cp' in locals() else ""}
                    
                    # Guardar en DB
                    conn = sqlite3.connect('pedidos_negocio.db')
                    id_pedido = conn.cursor().execute(
                        "INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago) VALUES (?,?,?,?,?,?,?,?)",
                        (datetime.now().strftime("%d/%m %H:%M"), nom_c, t_limpio, dir_c, ticket_resumen, total_final, "Pendiente", det_pago)
                    ).lastrowid
                    conn.commit(); conn.close()
                    
                    # Telegram
                    enviar_pedido_telegram(id_pedido, nom_c, t_limpio, dir_c, m_envio, (c_envio or 0.0), prop, ticket_resumen, total_final, det_pago)
                    
                    # Limpiar y Notificar
                    st.session_state.carrito = {}
                    st.success(f"✅ ¡Pedido recibido con éxito! Tu Folio es el #{id_pedido}")
                    if m_pago == "📲 Transferencia": st.info(DATOS_BANCO)
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("⚠️ Error: Revisa que tu teléfono tenga 10 dígitos y que los campos marcados con (*) no estén vacíos.")

# =====================================================================
# 🛵 RASTREO DE PEDIDOS (MULTI-USUARIO)
# =====================================================================
with tab_rastreo:
    st.header("🔍 Rastrea tus pedidos")
    t_rastreo = st.session_state.datos_cliente_persistentes.get("tel", "")
    input_tel = st.text_input("Introduce tu número de teléfono para buscar tus pedidos:", value=t_rastreo)
    
    if input_tel:
        tel_busqueda = re.sub(r"\D", "", input_tel)
        if len(tel_busqueda) == 10:
            historial = buscar_pedidos_por_telefono(tel_busqueda)
            if not historial:
                st.info("No se encontraron pedidos recientes vinculados a este número.")
            else:
                for pid, pfe, pest, ptot, pdet in historial:
                    with st.container(border=True):
                        col_h1, col_h2 = st.columns([1, 2])
                        with col_h1:
                            st.markdown(f"### Folio #{pid}")
                            st.caption(f"Fecha: {pfe}")
                        with col_h2:
                            # Visualización de estado
                            if pest == "Pendiente": 
                                st.warning("⏳ Pendiente: Esperando que la cocina reciba tu orden.")
                                st.progress(0.2)
                            elif pest == "En Cocina":
                                st.info("🍳 En Cocina: El chef está preparando tus platillos.")
                                st.progress(0.5)
                            elif pest == "En Camino":
                                st.success("🛵 En Camino: ¡Tu pedido va hacia tu domicilio!")
                                st.progress(0.8)
                            elif pest == "Entregado":
                                st.success("✅ Entregado: ¡Buen provecho!")
                                st.progress(1.0)
                            elif pest == "Cancelado":
                                st.error("❌ Cancelado: Este pedido ha sido cancelado.")
                        
                        with st.expander("Ver detalles de lo que pediste"):
                            st.text(pdet)
                            st.write(f"**Monto total:** ${ptot:.2f}")
                
                if st.button("🔄 Actualizar Estatus"): st.rerun()

# =====================================================================
# 🔐 PANEL ADMINISTRADOR
# =====================================================================
with tab_admin:
    st.title("Panel de Control")
    password = st.text_input("Introduce la clave de acceso:", type="password")
    
    if password == PASSWORD_ADMIN:
        # Control Maestro
        st.subheader("Estado del Establecimiento")
        abierto_val = st.toggle("¿Cocina Abierta?", value=sistema_abierto)
        if abierto_val != sistema_abierto:
            actualizar_estado_sistema(abierto_val)
            st.rerun()
            
        # Pedidos Activos
        st.divider()
        st.subheader("📦 Gestión de Pedidos")
        
        conn = sqlite3.connect('pedidos_negocio.db')
        pedidos_raw = conn.cursor().execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado=0 ORDER BY id DESC").fetchall()
        conn.close()
        
        if not pedidos_raw:
            st.info("No hay pedidos activos por ahora.")
        else:
            for pid, pf, pnom, ptel, pdir, pdet, ptot, pest, ppag in pedidos_raw:
                with st.container(border=True):
                    st.write(f"### Pedido #{pid} - {pnom}")
                    st.caption(f"📅 {pf} | 📞 {ptel} | 📍 {pdir if pdir else 'Recoge en Local'}")
                    st.text(pdet)
                    st.write(f"💰 **Total: ${ptot:.2f}** | 💳 **Pago: {ppag}**")
                    
                    st.write("**Cambiar Estado:**")
                    c_btns = st.columns(5)
                    
                    # Botones con lógica de resalte
                    def btn_status(col, label, target, current, pid):
                        # Si es el estado actual, el botón se ve "activo" con un emoji diferente
                        txt = f"📍 {label.upper()}" if current == target else label
                        if col.button(txt, key=f"adm_{pid}_{target}"):
                            conn = sqlite3.connect('pedidos_negocio.db')
                            conn.cursor().execute("UPDATE pedidos SET estado=? WHERE id=?", (target, pid))
                            conn.commit(); conn.close()
                            st.rerun()

                    btn_status(c_btns[0], "⏳ Pendiente", "Pendiente", pest, pid)
                    btn_status(c_btns[1], "🍳 Cocina", "En Cocina", pest, pid)
                    btn_status(c_btns[2], "🛵 Camino", "En Camino", pest, pid)
                    btn_status(c_btns[3], "✅ OK", "Entregado", pest, pid)
                    btn_status(c_btns[4], "❌ X", "Cancelado", pest, pid)
                    
                    if st.button(f"📂 Archivar Pedido #{pid}", key=f"arch_{pid}"):
                        conn = sqlite3.connect('pedidos_negocio.db')
                        conn.cursor().execute("UPDATE pedidos SET archivado=1 WHERE id=?", (pid,))
                        conn.commit(); conn.close()
                        st.rerun()

        # Inventario
        st.divider()
        st.subheader("🍏 Disponibilidad de Platillos")
        for cat, prods in MENU.items():
            st.write(f"**{cat}**")
            cols_inv = st.columns(2)
            for i, p in enumerate(prods):
                target_col = cols_inv[0] if i % 2 == 0 else cols_inv[1]
                st_disp = inventario_actual.get(p, True)
                if target_col.checkbox(p, value=st_disp, key=f"inv_{p}") != st_disp:
                    actualizar_producto_inventario(p, not st_disp)
                    st.rerun()

    elif password != "":
        st.error("Contraseña incorrecta.")
