import streamlit as st
import sqlite3
import requests
from datetime import datetime, date
import time
import json
import re
import urllib.parse
# Importamos componentes para el JavaScript
import streamlit.components.v1 as components

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")

# --- LÓGICA DE SCROLL AUTOMÁTICO ---
if "scroll_al_top" not in st.session_state:
    st.session_state.scroll_al_top = False

# Si la señal de scroll está activa, inyectamos el JS
if st.session_state.scroll_al_top:
    components.html(
        """
        <script>
            var mainSection = window.parent.document.querySelector('section.main');
            if (mainSection) {
                mainSection.scrollTo({ top: 0, behavior: 'smooth' });
            }
        </script>
        """,
        height=0,
    )
    st.session_state.scroll_al_top = False

# --- CREDENCIALES DESDE SECRETOS ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- CONTRASEÑA DEL ADMINISTRADOR ---
PASSWORD_ADMIN = "admin123" 

# --- CONFIGURACIÓN MAESTRA DE CÓDIGOS POSTALES ---
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

# --- PERSISTENCIA AUTOMÁTICA Y ESTADOS MAESTROS ---
if 'carrito' not in st.session_state:
    if "rec_cart" in st.query_params:
        try: st.session_state.carrito = json.loads(st.query_params["rec_cart"])
        except: st.session_state.carrito = {}
    else: st.session_state.carrito = {}

if 'notas_productos' not in st.session_state:
    if "rec_notes" in st.query_params:
        try: st.session_state.notas_productos = json.loads(st.query_params["rec_notes"])
        except: st.session_state.notas_productos = {}
    else: st.session_state.notas_productos = {}

if 'datos_cliente_persistentes' not in st.session_state:
    if "rec_user" in st.query_params:
        try: st.session_state.datos_cliente_persistentes = json.loads(st.query_params["rec_user"])
        except: st.session_state.datos_cliente_persistentes = {"nombre": "", "tel": "", "dir": "", "cp": ""}
    else: st.session_state.datos_cliente_persistentes = {"nombre": "", "tel": "", "dir": "", "cp": ""}

# --- FUNCIONES DE BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT, 
                  metodo_pago TEXT, archivado INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion 
                 (clave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('sistema_abierto', 'True')")
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_disponibilidad 
                 (producto TEXT PRIMARY KEY, disponible TEXT)''')
    conn.commit()
    conn.close()

def obtener_estado_sistema_db():
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracion WHERE clave = 'sistema_abierto'")
    res = c.fetchone()
    conn.close()
    return res[0] == 'True' if res else True

def actualizar_estado_sistema_db(abierto):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('sistema_abierto', ?)", (str(abierto),))
    conn.commit()
    conn.close()

def obtener_inventario_db():
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT producto, disponible FROM inventario_disponibilidad")
    filas = c.fetchall()
    conn.close()
    return {f[0]: (f[1] == 'True') for f in filas}

def actualizar_producto_inventario_db(producto, disponible):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO inventario_disponibilidad (producto, disponible) VALUES (?, ?)", (producto, str(disponible)))
    conn.commit()
    conn.close()

def guardar_pedido_db(fecha, nombre, telefono, direccion, pedido, total, metodo_pago):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago, archivado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)",
              (fecha, nombre, telefono, direccion, pedido, total, "Pendiente", metodo_pago))
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

def buscar_pedidos_por_telefono(telefono):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT id, fecha, estado, total, pedido FROM pedidos WHERE telefono = ? ORDER BY id DESC LIMIT 10", (telefono,))
    res = c.fetchall()
    conn.close()
    return res

def enviar_pedido_telegram(id_pedido, nombre, telefono, direccion, tipo_entrega, costo_envio, propina_txt, detalle, total, metodo_pago):
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO CONFIRMADO (Folio: #{id_pedido})!*\n"
        f"----------------------------------------\n"
        f"👤 *Cliente:* {nombre}\n"
        f"📞 *Teléfono:* {telefono}\n"
        f"🛵 *Tipo Entrega:* {tipo_entrega}\n"
        f"📍 *Dirección:* {direccion}\n"
        f"----------------------------------------\n"
        f"💳 *Método de Pago:* {metodo_pago}\n"
        f"----------------------------------------\n"
        f"📝 *Detalle del Pedido:*\n"
        f"{detalle}\n"
        f"----------------------------------------\n"
        f"💵 *Costo Envío:* ${costo_envio:.2f}\n"
        f"🚴‍♂️ *Propina Repartidor:* {propina_txt}\n"
        f"💰 *TOTAL A COBRAR:* ${total:.2f}\n"
    )
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try: 
        requests.post(url, json=payload, timeout=5)
    except Exception: 
        pass

init_db()
sistema_abierto_real = obtener_estado_sistema_db()
inventario_real = obtener_inventario_db()
st.session_state.inventario = {prod: inventario_real.get(prod, True) for cat in MENU.values() for prod in cat}

def actualizar_memoria_navegador():
    try:
        st.query_params["rec_cart"] = json.dumps(st.session_state.carrito)
        st.query_params["rec_notes"] = json.dumps(st.session_state.notas_productos)
        st.query_params["rec_user"] = json.dumps(st.session_state.datos_cliente_persistentes)
    except Exception:
        pass

# --- CREACIÓN DE PESTAÑAS ---
tab_cliente, tab_mis_pedidos, tab_admin = st.tabs(["📋 Menú para Clientes", "🛵 Mis Pedidos", "🔐 Panel Administrador"])

# =====================================================================
# 📋 VISTA DEL CLIENTE (MENÚ)
# =====================================================================
with tab_cliente:
    st.title("La Ventanita & Tacos Mixi")
    
    if not sistema_abierto_real:
        st.error("🛑 **LO SENTIMOS, NUESTRA COCINA SE ENCUENTRA CERRADA POR EL MOMENTO.**")
    else:
        st.write("Arma tu pedido aquí abajo combinando lo mejor de nuestros dos menús.")

    for category, productos in MENU.items():
        al_menos_uno_disponible = any(st.session_state.inventario.get(p, True) for p in productos)
        if al_menos_uno_disponible:
            with st.expander(f"{category}", expanded=True):
                for prod, precio in productos.items():
                    if not st.session_state.inventario.get(prod, True):
                        continue
                        
                    col_info, col_controles = st.columns([2, 2])
                    agregado_texto = ""
                    precio_final_prod = precio
                    
                    with col_info:
                        # --- LÓGICA DE PERSONALIZACIÓN COMPLETA ---
                        if "Chilaquiles" in prod:
                            salsa_elegida = st.selectbox("Salsa:", ["Verdes", "Rojos"], key=f"mod_{prod}")
                            agregado_texto = f" ({salsa_elegida})"
                        
                        elif "Coctel de Mango" in prod:
                            tamanio_fruta = st.selectbox("Tamaño:", ["Chico ($35.00)", "Grande (+$15.00)"], key=f"tam_{prod}")
                            if "Grande" in tamanio_fruta: precio_final_prod = 50.0
                            agregado_texto = f" [{tamanio_fruta}]"

                        elif "Taco de" in prod and prod != "Taco de Chuleta":
                            con_q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"mod_{prod}")
                            guarnicion = st.selectbox("Acompañado con:", ["Con papas", "Con nopales", "Papas y Nopales", "Sin guarnición"], key=f"guar_{prod}")
                            if con_q: precio_final_prod = 31.0; agregado_texto += " (Con Quesillo)"
                            agregado_texto += f" [{guarnicion}]"
                                
                        elif "Taco Campechano" in prod:
                            con_q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"mod_{prod}")
                            guarnicion = st.selectbox("Acompañado con:", ["Con papas", "Con nopales", "Papas y Nopales", "Sin guarnición"], key=f"guar_{prod}")
                            if con_q: precio_final_prod = 31.0; agregado_texto += " (Con Quesillo)"
                            agregado_texto += f" [{guarnicion}]"

                        elif "Quesadilla" in prod or "Gordita" in prod:
                            con_q = st.checkbox("¿Con Quesillo?", key=f"mod_{prod}")
                            if con_q:
                                precio_final_prod = 33.0 if "Gordita" in prod else 31.0
                                agregado_texto = " (Con Quesillo)"

                        elif "Pambazo Especial" in prod:
                            ing_pambazo = st.text_input("¿Ingrediente pambazo?", placeholder="Ej. Tinga", key=f"ing_pamba_{prod}")
                            if ing_pambazo: agregado_texto = f" de {ing_pambazo}"

                        elif "Licuado" in prod:
                            tamanio_licuado = st.selectbox("Tamaño:", ["1/2 Litro ($35.00)", "1 Litro (+$35.00)"], key=f"tam_{prod}")
                            if "1 Litro" in tamanio_licuado: precio_final_prod = 70.0
                            agregado_texto = f" ({tamanio_licuado.split(' ')[0]} L)"

                        elif "Agua" in prod:
                            tamanio_agua = st.selectbox("Tamaño:", ["1/2 Litro ($25.00)", "1 Litro (+$15.00)"], key=f"tam_{prod}")
                            if "1 Litro" in tamanio_agua: precio_final_prod = 40.0
                            agregado_texto = f" ({tamanio_agua.split(' ')[0]} L)"

                        elif "Jugo" in prod:
                            tamanio_jugo = st.selectbox("Tamaño:", ["Chico (1/2 L)", "Grande (1 L) (+$20.00)"], key=f"tam_{prod}")
                            if "Grande" in tamanio_jugo: precio_final_prod = precio + 20.0
                            agregado_texto = f" ({tamanio_jugo})"

                        st.write(f"**{prod}{agregado_texto}**\n${precio_final_prod:.2f}")

                    with col_controles:
                        if sistema_abierto_real: 
                            nombre_clave_carrito = f"{prod}|||{agregado_texto}|||{precio_final_prod}"
                            cant_actual = st.session_state.carrito.get(nombre_clave_carrito, 0)
                            
                            if cant_actual == 0:
                                if st.button("🛒 Agregar", key=f"init_btn_{prod}_{agregado_texto}", use_container_width=True):
                                    st.session_state.carrito[nombre_clave_carrito] = 1
                                    actualizar_memoria_navegador()
                                    st.rerun()
                            else:
                                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                                if btn_col1.button("➖", key=f"sub_{prod}_{agregado_texto}", use_container_width=True):
                                    st.session_state.carrito[nombre_clave_carrito] -= 1
                                    actualizar_memoria_navegador()
                                    st.rerun()
                                btn_col2.markdown(f"<h4 style='text-align: center; margin: 0;'>{cant_actual}</h4>", unsafe_allow_html=True)
                                if btn_col3.button("➕", key=f"add_{prod}_{agregado_texto}", use_container_width=True):
                                    st.session_state.carrito[nombre_clave_carrito] = cant_actual + 1
                                    actualizar_memoria_navegador()
                                    st.rerun()
                                    
                                vieja_nota = st.session_state.notas_productos.get(nombre_clave_carrito, "")
                                nueva_nota = st.text_input("Especificación:", value=vieja_nota, key=f"nota_input_{nombre_clave_carrito}")
                                if nueva_nota != vieja_nota:
                                    st.session_state.notas_productos[nombre_clave_carrito] = nueva_nota
                                    actualizar_memoria_navegador()
                        else: st.write("🔒 No disponible")

    # --- RENDERIZADO DEL CARRITO ---
    productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}
    if productos_seleccionados and sistema_abierto_real:
        st.markdown("---")
        st.subheader("🛒 Tu Pedido")
        total_productos = 0.0
        detalle_ticket_texto = ""
        
        for clave_carrito, cant in productos_seleccionados.items():
            p_nombre, p_extra, p_precio_str = clave_carrito.split("|||")
            precio_item = float(p_precio_str)
            subtotal = precio_item * cant
            total_productos += subtotal
            nota = st.session_state.notas_productos.get(clave_carrito, "").strip()
            st.write(f"• {cant}x {p_nombre}{p_extra} {'['+nota+']' if nota else ''} — ${subtotal:.2f}")
            detalle_ticket_texto += f"• {cant}x {p_nombre}{p_extra} {'['+nota+']' if nota else ''} — ${subtotal:.2f}\n"
            
        # Costo de Envío y Datos
        metodo_envio = st.selectbox("Método de Entrega *", ["🛵 Envío a Domicilio", "🛍️ Pasar a recoger al local"])
        costo_envio = 0.0
        tipo_entrega_txt = "Recoger en Local"
        
        if metodo_envio == "🛵 Envío a Domicilio":
            cp_actual = st.text_input("Código Postal (5 dígitos) *", value=st.session_state.datos_cliente_persistentes.get("cp", ""), max_chars=5)
            if cp_actual in MAPA_CODIGOS_POSTALES:
                costo_envio = MAPA_CODIGOS_POSTALES[cp_actual]["costo"]
                tipo_entrega_txt = f"Domicilio (CP {cp_actual})"
                st.success(f"📍 Zona: {MAPA_CODIGOS_POSTALES[cp_actual]['nombre']}")
            elif cp_actual:
                costo_envio = None
                st.error("❌ Fuera de Cobertura.")
        
        propina_opcion = st.radio("🚴‍♂️ Propina", ["No agregar", "$10.00", "$15.00", "$20.00", "En efectivo"], horizontal=True)
        valor_propina = 10.0 if "$10" in propina_opcion else 15.0 if "$15" in propina_opcion else 20.0 if "$20" in propina_opcion else 0.0
        
        tipo_pago = st.radio("Método de Pago", ["💵 Efectivo", "💳 Tarjeta"], horizontal=True)
        cambio_txt = tipo_pago
        if tipo_pago == "💵 Efectivo":
            cambio_de = st.text_input("¿Con cuánto pagas? (Para cambio)")
            cambio_txt = f"Efectivo (Cambio de {cambio_de})" if cambio_de else "Efectivo"

        total_final = total_productos + (costo_envio if costo_envio else 0.0) + valor_propina
        st.markdown(f"## **Total Final: ${total_final:.2f}**")

        with st.form("formulario_confirmacion"):
            nombre_cli = st.text_input("Nombre Completo *", value=st.session_state.datos_cliente_persistentes.get("nombre", ""))
            telefono_cli = st.text_input("Teléfono (10 dígitos) *", value=st.session_state.datos_cliente_persistentes.get("tel", ""))
            direccion_cli = st.text_area("Dirección Completa *", value=st.session_state.datos_cliente_persistentes.get("dir", "")) if metodo_envio == "🛵 Envío a Domicilio" else ""
            
            if st.form_submit_button("🚀 CONFIRMAR Y ENVIAR PEDIDO"):
                tel_limpio = re.sub(r"\D", "", telefono_cli)
                if len(tel_limpio) == 10 and nombre_cli and (direccion_cli or metodo_envio != "🛵 Envío a Domicilio") and costo_envio is not None:
                    st.session_state.datos_cliente_persistentes = {"nombre": nombre_cli, "tel": tel_limpio, "dir": direccion_cli, "cp": cp_actual if metodo_envio == "🛵 Envío a Domicilio" else ""}
                    id_p = guardar_pedido_db(datetime.now().strftime("%Y-%m-%d %H:%M"), nombre_cli, tel_limpio, direccion_cli, detalle_ticket_texto, total_final, cambio_txt)
                    enviar_pedido_telegram(id_p, nombre_cli, tel_limpio, direccion_cli, tipo_entrega_txt, (costo_envio or 0.0), propina_opcion, detalle_ticket_texto, total_final, cambio_txt)
                    
                    st.session_state.carrito = {}
                    st.session_state.notas_productos = {}
                    actualizar_memoria_navegador()
                    st.success(f"¡Pedido Folio #{id_p} enviado con éxito! Puedes revisarlo en la pestaña 'Mis Pedidos'.")
                    time.sleep(2)
                    st.rerun()
                else: st.error("Revisa que los campos asterisco (*) estén llenos y el teléfono sea de 10 dígitos.")

# =====================================================================
# 🛵 PESTAÑA: MIS PEDIDOS (RASTREO)
# =====================================================================
with tab_mis_pedidos:
    st.header("🔍 Rastrea el estado de tu cocina")
    tel_recuperado = st.session_state.datos_cliente_persistentes.get("tel", "")
    buscar_tel = st.text_input("Ingresa tu número telefónico para ver tus pedidos actuales:", value=tel_recuperado)
    
    if buscar_tel:
        tel_limpio_b = re.sub(r"\D", "", buscar_tel)
        if len(tel_limpio_b) == 10:
            mis_pedidos = buscar_pedidos_por_telefono(tel_limpio_b)
            if not mis_pedidos:
                st.info("No se encontraron pedidos recientes con este número.")
            else:
                for p_id, p_fecha, p_estado, p_total, p_detalle in mis_pedidos:
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.markdown(f"### Folio: #{p_id}")
                            st.caption(f"Fecha: {p_fecha}")
                        with c2:
                            # Barra de progreso visual
                            st.write(f"**Estado actual:** {p_estado}")
                            prog_val = 0.15 if p_estado=="Pendiente" else 0.5 if p_estado=="En Cocina" else 0.8 if p_estado=="En Camino" else 1.0
                            if p_estado == "Cancelado": 
                                st.error("❌ Pedido Cancelado")
                            else:
                                st.progress(prog_val)
                        
                        with st.expander("Ver detalle de la orden"):
                            st.text(p_detalle)
                            st.markdown(f"**Total Pagado: ${p_total:.2f}**")
                
                if st.button("🔄 Actualizar Estados"):
                    st.rerun()
        else: st.warning("El teléfono debe tener 10 dígitos.")
    else: st.info("Introduce tu teléfono para ver tus pedidos.")

# =====================================================================
# 🔐 PESTAÑA: ADMIN
# =====================================================================
with tab_admin:
    st.title("⚙️ Panel de Control")
    pwd = st.text_input("Contraseña", type="password")
    if pwd == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        
        # Switch Maestro
        st.header("🚨 Estado del Local")
        toggle_abierto = st.toggle("¿Sistema Abierto?", value=sistema_abierto_real)
        if toggle_abierto != sistema_abierto_real:
            actualizar_estado_sistema_db(toggle_abierto)
            st.rerun()
            
        # Gestión de Pedidos
        st.header("📦 Pedidos Recientes")
        ver_arch = st.checkbox("Ver Archivados")
        conn = sqlite3.connect('pedidos_negocio.db')
        c = conn.cursor()
        if ver_arch: c.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 1 ORDER BY id DESC")
        else: c.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 0 ORDER BY id DESC")
        datos_admin = c.fetchall()
        conn.close()

        for pid, pf, pnom, ptel, pdir, pdet, ptot, pest, ppag in datos_admin:
            with st.container(border=True):
                st.write(f"**Folio #{pid}** | {pf} | {pnom} ({ptel})")
                st.text(pdet)
                st.write(f"Total: ${ptot} | Pago: {ppag}")
                
                c_btn = st.columns(5)
                if c_btn[0].button("🍳 Cocina", key=f"btn1_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='En Cocina' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_btn[1].button("🛵 Camino", key=f"btn2_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='En Camino' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_btn[2].button("✅ OK", key=f"btn3_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='Entregado' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                if c_btn[3].button("❌ Cancel", key=f"btn4_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET estado='Cancelado' WHERE id=?", (pid,)); conn.commit(); conn.close(); st.rerun()
                txt_a = "Desarchivar" if ver_arch else "Archivar"
                val_a = 0 if ver_arch else 1
                if c_btn[4].button(txt_a, key=f"btn5_{pid}"):
                    conn=sqlite3.connect('pedidos_negocio.db'); conn.cursor().execute("UPDATE pedidos SET archivado=? WHERE id=?", (val_a, pid)); conn.commit(); conn.close(); st.rerun()

        # Inventario
        st.header("🍏 Disponibilidad")
        for cat, prods in MENU.items():
            st.subheader(cat)
            for pr in prods:
                check = st.checkbox(pr, value=st.session_state.inventario.get(pr, True), key=f"inv_{pr}")
                if check != st.session_state.inventario.get(pr, True):
                    actualizar_producto_inventario_db(pr, check)
                    st.rerun()
    elif pwd != "": st.error("Clave incorrecta")
