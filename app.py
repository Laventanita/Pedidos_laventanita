import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time
import json
import re
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
PASSWORD_ADMIN = "admin123"
TELEFONO_NEGOCIO = "5574977297"

MAPA_CODIGOS_POSTALES = {
    "55763": {"nombre": "Vitalia / Ojo de Agua", "costo": 25.0}, "55764": {"nombre": "Los Héroes Tecámac II", "costo": 25.0},
    "55766": {"nombre": "Ampliación Ozumbilla", "costo": 25.0}, "55770": {"nombre": "Ojo de Agua / San Pedro", "costo": 25.0},
    "55773": {"nombre": "Hacienda Provenzal", "costo": 25.0}, "55776": {"nombre": "Lomas de San Pedro", "costo": 25.0},
    "55778": {"nombre": "Ampliación de la Concepción", "costo": 25.0}, "55740": {"nombre": "Tecámac Centro", "costo": 40.0},
    "55743": {"nombre": "Rancho la Luz", "costo": 40.0}, "55744": {"nombre": "San Pedro Potzohuacan", "costo": 40.0},
    "55745": {"nombre": "Real Granada IV", "costo": 40.0}, "55748": {"nombre": "San Martín Azcatepec", "costo": 40.0},
    "55749": {"nombre": "Villa del Real", "costo": 40.0}, "55760": {"nombre": "San Francisco Cuautliquixca", "costo": 40.0},
    "55768": {"nombre": "Lomas de Ozumbilla", "costo": 40.0}, "55746": {"nombre": "Rancho la Capilla", "costo": 55.0},
    "55747": {"nombre": "San Pablo Tecalco", "costo": 55.0}, "55750": {"nombre": "Santa María Ajoloapan", "costo": 55.0},
    "55752": {"nombre": "San Juan Pueblo Nuevo", "costo": 55.0}, "55754": {"nombre": "Paseos de Tecámac", "costo": 55.0},
    "55755": {"nombre": "Los Reyes Acozac", "costo": 55.0}, "55757": {"nombre": "San Lucas Xolox", "costo": 55.0},
    "55758": {"nombre": "Ampliación la Palma", "costo": 55.0}, "55765": {"nombre": "Los Héroes San Pablo", "costo": 55.0},
    "55060": {"nombre": "Venta de Carpio", "costo": 55.0}, "55063": {"nombre": "Ciudad Cuauhtémoc", "costo": 55.0},
    "55064": {"nombre": "San Isidro Atlautenco", "costo": 55.0}, "55065": {"nombre": "Santa Cruz Venta de Carpio", "costo": 55.0},
    "55066": {"nombre": "Santa María Chiconautla", "costo": 55.0}, "55067": {"nombre": "Ciudad Cuauhtémoc Geo", "costo": 55.0},
    "55068": {"nombre": "Santo Tomás Chiconautla", "costo": 55.0}, "55069": {"nombre": "La Preciosa", "costo": 55.0}
}

MENU = {
    "☕ Desayunos": {"Chilaquiles chicos": 50.0, "Chilaquiles medianos": 65.0, "Chilaquiles para acompañar": 100.0, "Cuernito sencillo": 45.0, "Cuernito con fruta": 75.0},
    "🍓 Frutas": {"Coctel de Mango": 35.0, "Vaso de Mango": 35.0, "Vaso de Uva": 35.0, "Vaso de Jícama": 35.0, "Vaso de Piña": 35.0, "Vaso de Sandía": 35.0, "Vaso de Melón": 35.0, "Vaso de Papaya": 35.0},
    "🌮 Los Tacos": {"Taco de Pastor": 28.0, "Taco de Suadero": 28.0, "Taco de Enchilada": 28.0, "Taco de Bisteck": 28.0, "Taco de Chuleta": 28.0, "Taco Campechano": 28.0},
    "🫓 Quesadillas": {"Quesadilla de Queso": 25.0, "Quesadilla de Suadero": 28.0, "Quesadilla de Tinga": 25.0, "Quesadilla de Chicharrón": 25.0, "Quesadilla de Champiñón": 25.0, "Quesadilla de Mollejas": 25.0, "Quesadilla de Pancita": 25.0},
    "✨ Especialidades": {"Gordita": 30.0, "Pambazo de Papa con Longaniza": 30.0, "Pambazo Especial": 35.0},
    "🥤 Licuados": {"Licuado de Fresa": 35.0, "Licuado de Chocolate": 35.0, "Licuado de Plátano": 35.0},
    "🍹 Aguas Frescas": {"Agua de Café": 25.0, "Agua de Mazapán": 25.0, "Agua de Fresa": 25.0, "Agua de Limón": 25.0, "Agua de Melón": 25.0, "Agua de Piña": 25.0, "Agua de Sandía": 25.0, "Agua de Guayaba": 25.0, "Agua de Avena": 25.0},
    "🥤 Jugos": {"Jugo Verde": 35.0, "Jugo de Naranja": 35.0, "Jugo Combinado": 40.0}
}

# --- LÓGICA DE WHATSAPP ---
def generar_link_whatsapp(nombre, pedido, total, metodo_pago):
    mensaje = f"¡Hola! Quiero confirmar mi pedido:\n\n*Cliente:* {nombre}\n*Pedido:*\n{pedido}\n*Total:* ${total:.2f}\n*Pago:* {metodo_pago}"
    return f"https://wa.me/{TELEFONO_NEGOCIO}?text={urllib.parse.quote(mensaje)}"

# --- FUNCIONES DB Y UTILIDADES ---
def init_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT, metodo_pago TEXT, archivado INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('sistema_abierto', 'True')")
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_disponibilidad (producto TEXT PRIMARY KEY, disponible TEXT)''')
    conn.commit(); conn.close()

def obtener_estado_sistema_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'sistema_abierto'")
    res = c.fetchone()
    conn.close()
    return res[0] == 'True' if res else True

def guardar_pedido_db(fecha, nombre, tel, dir, detalle, total, pago):
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (fecha, nombre, tel, dir, detalle, total, "Pendiente", pago))
    id_pedido = c.lastrowid
    conn.commit(); conn.close()
    return id_pedido

def enviar_pedido_telegram(id_pedido, nombre, telefono, direccion, tipo_entrega, costo_envio, propina_txt, detalle, total, metodo_pago):
    mensaje = f"🔔 *¡NUEVO PEDIDO CONFIRMADO (Folio: #{id_pedido})!*\n👤 *Cliente:* {nombre}\n📞 *Teléfono:* {telefono}\n🛵 *Entrega:* {tipo_entrega}\n💳 *Pago:* {metodo_pago}\n📝 *Detalle:*\n{detalle}\n💵 *Envío:* ${costo_envio:.2f}\n🚴‍♂️ *Propina:* {propina_txt}\n💰 *TOTAL:* ${total:.2f}"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}, timeout=5)
    except: pass

# --- INICIALIZACIÓN ---
init_db()
if 'carrito' not in st.session_state: st.session_state.carrito = {}
if 'notas_productos' not in st.session_state: st.session_state.notas_productos = {}
if 'datos_cliente_persistentes' not in st.session_state: st.session_state.datos_cliente_persistentes = {"nombre": "", "tel": "", "dir": ""}

# --- INTERFAZ ---
tab_cliente, tab_mis_pedidos, tab_admin = st.tabs(["📋 Menú", "📍 Mis Pedidos", "🔐 Admin"])

with tab_cliente:
    st.title("La Ventanita & Tacos Mixi")
    sistema_abierto_real = obtener_estado_sistema_db()
    
    if not sistema_abierto_real:
        st.error("🛑 COCINA CERRADA")
    else:
        # AQUÍ VA TU LÓGICA DE MENÚ Y FORMULARIO (st.form)
        # Una vez que presiones el botón de "Confirmar":
        if st.button("Confirmar Pedido"):
            id_nuevo = guardar_pedido_db(...)
            enviar_pedido_telegram(...)
            st.success("✅ Pedido recibido")
            # BOTÓN WHATSAPP
            link_wa = generar_link_whatsapp("Nombre", "Detalle", 100.0, "Efectivo")
            st.markdown(f'<a href="{link_wa}" target="_blank">📲 Confirmar por WhatsApp</a>', unsafe_allow_html=True)

with tab_mis_pedidos:
    st.header("🔍 Rastreo")
    # ... tu lógica de rastreo

# =====================================================================
# 🔐 PANEL ADMINISTRADOR
# =====================================================================
with tab_admin:
    st.title("⚙️ Panel de Control Interno")
    password_input = st.text_input("Introduce la contraseña de Administrador", type="password", key="pass_admin")
    
    if password_input == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        st.markdown("---")
        
        # --- INTERRUPTOR MAESTRO PERSISTENTE ---
        st.header("🚨 Estado del Establecimiento")
        texto_estado_actual = "🟢 Abierto (Recibiendo pedidos)" if sistema_abierto_real else "🔴 Cerrado (No recibir pedidos)"
        st.markdown(f"**Estatus actual en Base de Datos:** {texto_estado_actual}")
        
        estado_toggle = st.toggle("Modificar estado de la cocina", value=sistema_abierto_real, help="Apaga este botón para pausar de inmediato la entrada de pedidos de todos los usuarios.")
        
        if estado_toggle != sistema_abierto_real:
            actualizar_estado_sistema_db(estado_toggle)
            st.success(f"Sistema cambiado exitosamente a: {'ABIERTO' if estado_toggle else 'CERRADO'}")
            st.rerun()
            
        st.markdown("---")
        
        # --- GESTIÓN DE PEDIDOS ---
        st.header("📦 Monitor y Gestión de Pedidos")
        
        # Filtros de visualización
        ver_archivados = st.checkbox("Ver pedidos archivados/históricos")
        
        conn = sqlite3.connect('pedidos_negocio.db')
        c = conn.cursor()
        if ver_archivados:
            c.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 1 ORDER BY id DESC")
        else:
            c.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 0 ORDER BY id DESC")
        
        pedidos_raw = c.fetchall()
        conn.close()
        
        if not pedidos_raw:
            st.info("No hay pedidos registrados bajo este criterio de filtro.")
        else:
            for pedido_id, p_fecha, p_nombre, p_tel, p_dir, p_detalle, p_total, p_estado, p_pago in pedidos_raw:
                with st.container(border=True):
                    col_id, col_info_p = st.columns([1, 4])
                    
                    with col_id:
                        st.markdown(f"### #{pedido_id}")
                        # Badge visual del estado
                        if p_estado == "Pendiente": st.warning("Pendiente")
                        elif p_estado == "En Cocina": st.info("En Cocina")
                        elif p_estado == "En Camino": st.success("En Camino")
                        elif p_estado == "Entregado": st.markdown("✅ Entregado")
                        elif p_estado == "Cancelado": st.error("Cancelado")
                        
                    with col_info_p:
                        st.write(f"📅 **Fecha:** {p_fecha} | 👤 **Cliente:** {p_nombre} | 📞 **Tel:** {p_tel}")
                        st.write(f"📍 **Entrega:** {p_dir}")
                        st.write(f"💳 **Pago:** {p_pago}")
                        
                    st.text_area("🛒 Contenido de la Orden", value=p_detalle, height=110, key=f"det_view_{pedido_id}", disabled=True)
                    st.markdown(f"### **Total Cobro: ${p_total:.2f}**")
                    
                    # Controles de actualización de estatus
                    c1, c2, c3, c4, c5 = st.columns(5)
                    
                    # Función para generar botones que resaltan el estado actual
                    def btn_status(col, label, target, current, pid):
                        # Marcamos visualmente el botón si es el estado actual
                        btn_label = f"📍 {label.upper()}" if current == target else label
                        if col.button(btn_label, key=f"adm_{pid}_{target}"):
                            conn_btn = sqlite3.connect('pedidos_negocio.db')
                            conn_btn.cursor().execute("UPDATE pedidos SET estado=? WHERE id=?", (target, pid))
                            conn_btn.commit(); conn_btn.close()
                            st.rerun()

                    btn_status(c1, "🍳 Cocina", "En Cocina", p_estado, pedido_id)
                    btn_status(c2, "🛵 Camino", "En Camino", p_estado, pedido_id)
                    btn_status(c3, "✅ Entregado", "Entregado", p_estado, pedido_id)
                    btn_status(c4, "❌ Cancelar", "Cancelado", p_estado, pedido_id)
                        
                    # Lógica de archivado
                    txt_archivo = "📂 Archivar" if not ver_archivados else "📥 Desarchivar"
                    val_archivo = 1 if not ver_archivados else 0
                    if c5.button(txt_archivo, key=f"btn_archiver_{pedido_id}"):
                        conn_arc = sqlite3.connect('pedidos_negocio.db')
                        conn_arc.cursor().execute("UPDATE pedidos SET archivado = ? WHERE id = ?", (val_archivo, pedido_id))
                        conn_arc.commit(); conn_arc.close()
                        st.success(f"Pedido #{pedido_id} actualizado.")
                        st.rerun()

        st.markdown("---")
        
        # --- CONTROL DE DISPONIBILIDAD DE PRODUCTOS ---
        st.header("🍏 Disponibilidad de Platillos (Inventario)")
        st.write("Desmarca un platillo si se ha agotado en la cocina.")
        
        for category, productos in MENU.items():
            st.subheader(category)
            cols_inv = st.columns(2)
            
            for index, (prod, precio) in enumerate(productos.items()):
                target_col = cols_inv[0] if index % 2 == 0 else cols_inv[1]
                estado_actual_prod = st.session_state.inventario.get(prod, True)
                chk_dispo = target_col.checkbox(f"{prod} (${precio:.2f})", value=estado_actual_prod, key=f"inv_chk_{prod}")
                
                if chk_dispo != estado_actual_prod:
                    actualizar_producto_inventario_db(prod, chk_dispo)
                    st.session_state.inventario[prod] = chk_dispo
                    st.rerun()
                    
    elif password_input != "":
        st.error("🔑 Contraseña incorrecta. Introduce la clave válida de administrador para ver las operaciones internas.")
