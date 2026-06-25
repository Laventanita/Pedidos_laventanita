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

# Si la señal de scroll está activa, inyectamos el JS y la apagamos
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

if 'rastreo_id' not in st.session_state:
    if "tracking_id" in st.query_params:
        try: 
            st.session_state.rastreo_id = int(st.query_params["tracking_id"])
            del st.query_params["tracking_id"]
        except: 
            pass

def init_db():
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion 
                 (clave TEXT PRIMARY KEY, valor TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('sistema_abierto', 'True')")
    
    # Tabla para el control granular de disponibilidad de platillos
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_disponibilidad 
                 (producto TEXT PRIMARY KEY, disponible TEXT)''')
    
    c.execute("PRAGMA table_info(pedidos)")
    columnas = [col[1] for col in c.fetchall()]
    if "metodo_pago" not in columnas:
        c.execute("ALTER TABLE pedidos ADD COLUMN metodo_pago TEXT DEFAULT 'No especificado'")
    if "archivado" not in columnas:
        c.execute("ALTER TABLE pedidos ADD COLUMN archivado INTEGER DEFAULT 0")
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

def consultar_estado_pedido(id_pedido):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT estado, nombre, total, fecha FROM pedidos WHERE id = ?", (id_pedido,))
    res = c.fetchone()
    conn.close()
    return res

def buscar_pedidos_por_telefono(telefono):
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT id, fecha, estado, total, pedido FROM pedidos WHERE telefono = ? ORDER BY id DESC LIMIT 5", (telefono,))
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
    except Exception as e: 
        st.error(f"Error en comunicación con Telegram: {e}")

init_db()

# Cargar estados dinámicos desde la BD en cada ejecución limpia
sistema_abierto_real = obtener_estado_sistema_db()
inventario_real = obtener_inventario_db()

# Sincronizar session_state local con el almacenamiento de la DB
st.session_state.inventario = {}
for categoria, productos in MENU.items():
    for prod in productos.keys():
        st.session_state.inventario[prod] = inventario_real.get(prod, True)

def actualizar_memoria_navegador():
    try:
        st.query_params["rec_cart"] = json.dumps(st.session_state.carrito)
        st.query_params["rec_notes"] = json.dumps(st.session_state.notas_productos)
        st.query_params["rec_user"] = json.dumps(st.session_state.datos_cliente_persistentes)
    except Exception:
        pass

tab_cliente, tab_mis_pedidos, tab_admin = st.tabs(["📋 Menú para Clientes", "📍 Mis Pedidos", "🔐 Panel Administrador"])

# =====================================================================
# 📋 VISTA DEL CLIENTE
# =====================================================================
with tab_cliente:
    if 'rastreo_id' in st.session_state:
        id_actual = st.session_state.rastreo_id
        datos_p = consultar_estado_pedido(id_actual)
        
        if datos_p:
            estado_actual, nombre_c, total_c, fecha_c = datos_p
            st.title("🛵 Rastreador de tu Pedido")
            st.subheader(f"Hola {nombre_c}, ¡aquí puedes ver el estatus de tu orden!")
            st.info(f"**Folio del Pedido:** #{id_actual} | **Fecha:** {fecha_c}")
            
            estados_map = {"Pendiente": 0.15, "En Cocina": 0.50, "En Camino": 0.80, "Entregado": 1.0, "Cancelado": 0.0}
            progreso = estados_map.get(estado_actual, 0.0)
            
            if estado_actual == "Cancelado":
                st.error("❌ Lo sentimos, este pedido ha sido cancelado por el establecimiento.")
            else:
                st.progress(progreso)
                if estado_actual == "Pendiente":
                    st.warning("🕒 **Estado:** Esperando confirmación de la cocina... Tu pedido ya fue recibido.")
                elif estado_actual == "En Cocina":
                    st.info("🍳 **Estado:** ¡El chef tiene tu pedido! Tus platillos se están preparando en este momento.")
                elif estado_actual == "En Camino":
                    st.success("🛵 **Estado:** ¡Tu pedido va en camino! El repartidor se dirige a tu domicilio.")
                elif estado_actual == "Entregado":
                    st.success("✅ **Estado:** ¡Pedido entregado con éxito! Muchas gracias por tu preferencia. ¡Buen provecho!")

            st.write(f"**Monto a pagar al recibir:** ${total_c:.2f}")
            st.markdown("---")
            
            col_refrescar, col_nuevo = st.columns(2)
            if col_refrescar.button("🔄 Actualizar Estatus Ahora", use_container_width=True):
                st.rerun()
                
            if col_nuevo.button("🛒 Hacer un nuevo pedido", use_container_width=True):
                del st.session_state.rastreo_id
                st.query_params.clear()
                st.rerun()
        else:
            del st.session_state.rastreo_id
            st.rerun()
            
    else:
        st.title("La Ventanita & Tacos Mixi")
        
        if not sistema_abierto_real:
            st.error("🛑 **LO SENTIMOS, NUESTRA COCINA SE ENCUENTRA CERRADA POR EL MOMENTO.**")
            st.info("Puedes revisar nuestro menú aquí abajo, pero la toma de pedidos y el envío de carritos están deshabilitados hasta nuestra próxima apertura. ¡Gracias por tu comprensión!")
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
                            if "Chilaquiles" in prod:
                                salsa_elegida = st.selectbox("Salsa:", ["Verdes", "Rojos"], key=f"mod_{prod}")
                                agregado_texto = f" ({salsa_elegida})"
                            
                            elif "Coctel de Mango" in prod:
                                tamanio_fruta = st.selectbox("Tamaño:", ["Chico ($35.00)", "Grande (+$15.00)"], key=f"tam_{prod}")
                                if "Grande" in tamanio_fruta:
                                    precio_final_prod = 50.0
                                agregado_texto = f" [{tamanio_fruta} - Con chantilly, miel, granola, fresa y plátano]"

                            elif "Taco de" in prod and prod != "Taco de Chuleta":
                                con_q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"mod_{prod}")
                                guarnicion = st.selectbox("Acompañado con:", ["Con papas", "Con nopales", "Papas y Nopales", "Sin guarnición"], key=f"guar_{prod}")
                                if con_q:
                                    precio_final_prod = 31.0
                                    agregado_texto += " (Con Quesillo)"
                                agregado_texto += f" [{guarnicion}]"
                                    
                            elif "Taco Campechano" in prod:
                                con_q = st.checkbox("¿Con Quesillo? (+$3.00)", key=f"mod_{prod}")
                                guarnicion = st.selectbox("Acompañado con:", ["Con papas", "Con nopales", "Papas y Nopales", "Sin guarnición"], key=f"guar_{prod}")
                                if con_q:
                                    precio_final_prod = 31.0
                                    agregado_texto += " (Con Quesillo)"
                                agregado_texto += f" [{guarnicion}]"

                            elif "Quesadilla" in prod or "Gordita" in prod:
                                con_q = st.checkbox("¿Con Quesillo?", key=f"mod_{prod}")
                                if con_q:
                                    precio_final_prod = 33.0 if "Gordita" in prod else 31.0
                                    agregado_texto = " (Con Quesillo)"

                            elif "Pambazo Especial" in prod:
                                ing_pambazo = st.text_input("¿De qué ingrediente quieres tu pambazo especial? (Ej. Tinga, Suadero)", placeholder="Escribe el ingrediente aquí", key=f"ing_pamba_{prod}")
                                if ing_pambazo:
                                    agregado_texto = f" de {ing_pambazo}"

                            elif "Licuado" in prod:
                                tamanio_licuado = st.selectbox("Tamaño:", ["1/2 Litro ($35.00)", "1 Litro (+$35.00)"], key=f"tam_{prod}")
                                if "1 Litro" in tamanio_licuado:
                                    precio_final_prod = 70.0
                                agregado_texto = f" ({tamanio_licuado.split(' ')[0]} L)"

                            elif "Agua" in prod:
                                tamanio_agua = st.selectbox("Tamaño:", ["1/2 Litro ($25.00)", "1 Litro (+$15.00)"], key=f"tam_{prod}")
                                if "1 Litro" in tamanio_agua:
                                    precio_final_prod = 40.0
                                agregado_texto = f" ({tamanio_agua.split(' ')[0]} L)"

                            elif "Jugo" in prod:
                                tamanio_jugo = st.selectbox("Tamaño:", ["Chico (1/2 L)", "Grande (1 L) (+$20.00)"], key=f"tam_{prod}")
                                if "Grande" in tamanio_jugo:
                                    precio_final_prod = precio + 20.0
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
                                    nueva_nota = st.text_input("Especificación:", value=vieja_nota, key=f"nota_input_{nombre_clave_carrito}", placeholder="Ej: sin hielo")
                                    if nueva_nota != vieja_nota:
                                        st.session_state.notas_productos[nombre_clave_carrito] = nueva_nota
                                        actualizar_memoria_navegador()
                            else:
                                st.write("🔒 No disponible")

        productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

        if productos_seleccionados and not sistema_abierto_real:
            st.session_state.carrito = {}
            st.rerun()

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
                
                nota_especifica = st.session_state.notas_productos.get(clave_carrito, "").strip()
                nota_pantalla = f" *[Nota: {nota_especifica}]*" if nota_especifica else ""
                
                col_p, col_b = st.columns([3, 1])
                col_p.write(f"• {cant}x {p_nombre}{p_extra}{nota_pantalla} — ${subtotal:.2f}")
                
                if col_b.button("❌ Quitar Todo", key=f"del_all_{clave_carrito}"):
                    st.session_state.carrito[clave_carrito] = 0
                    actualizar_memoria_navegador()
                    st.rerun()
                    
                detalle_ticket_texto += f"• {cant}x {p_nombre}{p_extra}{nota_pantalla} (${precio_item:.2f} c/u) — ${subtotal:.2f}\n"
                
            st.markdown(f"**Subtotal de Productos:** ${total_productos:.2f}")
            st.markdown("---")
            
            st.subheader("👤 Datos para la Entrega")
            
            if 'metodo_envio' not in st.session_state: st.session_state.metodo_envio = "🛵 Envío a Domicilio"
            if 'propina_opcion' not in st.session_state: st.session_state.propina_opcion = "No agregar por ahora"

            st.session_state.metodo_envio = st.selectbox("Método de Entrega *", ["🛵 Envío a Domicilio", "🛍️ Pasar a recoger al local"])
            
            costo_envio = 0.0
            tipo_entrega_txt = "Recoger en Local"
            
            if st.session_state.metodo_envio == "🛵 Envío a Domicilio":
                cp_actual = st.text_input("Código Postal (5 dígitos) *", value=st.session_state.datos_cliente_persistentes.get("cp", ""), max_chars=5)
                if cp_actual != st.session_state.datos_cliente_persistentes.get("cp", ""):
                    st.session_state.datos_cliente_persistentes["cp"] = cp_actual
                    actualizar_memoria_navegador()

                if cp_actual:
                    if cp_actual in MAPA_CODIGOS_POSTALES:
                        costo_envio = MAPA_CODIGOS_POSTALES[cp_actual]["costo"]
                        zona_nombre = MAPA_CODIGOS_POSTALES[cp_actual]["nombre"]
                        tipo_entrega_txt = f"Domicilio (CP {cp_actual} - {zona_nombre})"
                        st.success(f"📍 Zona de Reparto Validada: {zona_nombre}")
                    else:
                        costo_envio = None
                        st.error("❌ Fuera de Cobertura: El Código Postal excede el radio límite de 10 km.")
                else:
                    costo_envio = 0.0
                    st.warning("⚠️ Introduce tu Código Postal para calcular el costo de envío.")
            else:
                st.info("🛍️ Recoges en local. Sin costo de envío.")

            st.session_state.propina_opcion = st.radio(
                "🚴‍♂️ Propina para el Repartidor (Opcional)",
                ["No agregar por ahora", "$10.00", "$15.00", "$20.00", "Dar en efectivo al recibir"],
                horizontal=True
            )
            
            valor_propina = 0.0
            propina_mensaje_telegram = "No asignada"
            if "10" in st.session_state.propina_opcion: valor_propina = 10.0; propina_mensaje_telegram = "$10.00"
            elif "15" in st.session_state.propina_opcion: valor_propina = 15.0; propina_mensaje_telegram = "$15.00"
            elif "20" in st.session_state.propina_opcion: valor_propina = 20.0; propina_mensaje_telegram = "$20.00"
            elif "efectivo" in st.session_state.propina_opcion: propina_mensaje_telegram = "Se entregará en efectivo"

            st.markdown("---")
            st.subheader("💳 Método de Pago")
            tipo_pago = st.radio("¿Cómo deseas pagar tu pedido al recibir?", ["💵 Efectivo", "💳 Tarjeta", "📲 Transferencia"], horizontal=True)
            
            cambio_txt = ""
            if tipo_pago == "💵 Efectivo":
                cambio_de = st.text_input("¿Con cuánto vas a pagar? (Para que el repartidor lleve cambio exacto)", placeholder="Ej. Con un billete de $200")
                cambio_txt = f"Efectivo (Requiere cambio de: {cambio_de})" if cambio_de else "Efectivo (Importe exacto)"
            elif tipo_pago == "💳 Tarjeta":
                st.info("💡 **Nota:** El repartidor llevará la terminal física para realizar su cobro al recibir.")
                cambio_txt = "Tarjeta (Llevar terminal física)"
            elif tipo_pago == "📲 Transferencia":
            
                st.warning(
                    "🏛️ **DATOS PARA TRANSFERENCIA:**\n\n"
                    "**Banco:** BBVA Bancomer\n"
                    "**Cuenta:** 1514123852\n"
                    "**Cuenta CLABE:** 012180015141238524\n"
                    "**Beneficiario:** Javier Gonzalez Regalado\n"
                    "**Enviar Comprobante:** 5574277297"
                )
                cambio_txt = "Transferencia (Confirmar comprobante)"               
               

            st.markdown("### 📋 Resumen Detallado de tu Cuenta")
            with st.container(border=True):
                st.markdown("**Artículos solicitados:**")
                for clave_carrito, cant in productos_seleccionados.items():
                    p_nombre, p_extra, _ = clave_carrito.split("|||")
                    nota_especifica = st.session_state.notas_productos.get(clave_carrito, "").strip()
                    nota_pantalla = f" *[Nota: {nota_especifica}]*" if nota_especifica else ""
                    st.write(f"   • {cant}x {p_nombre}{p_extra}{nota_pantalla}")
                
                st.write(f"• **Subtotal Platillos:** ${total_productos:.2f}")
                st.write(f"• **Costo de Envío:** ${costo_envio:.2f}" if costo_envio is not None else "**• Costo de Envío:** [BLOQUEADO]")
                st.write(f"• **Propina Repartidor:** ${valor_propina:.2f} ({st.session_state.propina_opcion})")
                st.write(f"• **Forma de Pago:** {cambio_txt}")
                
                total_informativo = total_productos + (costo_envio if costo_envio is not None else 0.0) + valor_propina
                st.markdown(f"## **Total Final: ${total_informativo:.2f}**")

            with st.form("formulario_confirmacion"):
                nombre_cli = st.text_input("Nombre Completo *", value=st.session_state.datos_cliente_persistentes.get("nombre", ""))
                telefono_cli = st.text_input("Teléfono de Contacto (WhatsApp) *", value=st.session_state.datos_cliente_persistentes.get("tel", ""))
                
                if st.session_state.metodo_envio == "🛵 Envío a Domicilio":
                    direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *", value=st.session_state.datos_cliente_persistentes.get("dir", ""))
                else:
                    direccion_cli = ""
                
                enviar_pedido = st.form_submit_button("🚀 CONFIRMAR Y ENVIAR PEDIDO A LA COCINA")
                
                if enviar_pedido:
                    estado_actual_db = obtener_estado_sistema_db()
                    
                    if not estado_actual_db:
                        st.error("🛑 ¡LO SENTIMOS! La cocina acaba de cerrar mientras armabas tu carrito. El pedido no pudo ser enviado. Por favor intenta de nuevo en nuestra próxima apertura.")
                    else:
                        telefono_limpio = re.sub(r"\D", "", telefono_cli)
                        
                        if st.session_state.metodo_envio == "🛵 Envío a Domicilio" and not cp_actual:
                            st.error("⚠️ El Código Postal es estrictamente obligatorio para envíos a domicilio.")
                        elif costo_envio is None:
                            st.error("❌ No se puede enviar. Tu Código Postal está fuera de la cobertura de 10 km.")
                        elif not nombre_cli or not telefono_cli or (st.session_state.metodo_envio == "🛵 Envío a Domicilio" and not direccion_cli):
                            st.error("⚠️ Por favor completa tu nombre, teléfono y dirección antes de enviar.")
                        elif len(telefono_limpio) != 10:
                            st.error("❌ Teléfono Inválido: Debe tener exactamente 10 números (Ej: 5512345678) sin letras.")
                        else:
                            st.session_state.datos_cliente_persistentes = {"nombre": nombre_cli, "tel": telefono_limpio, "dir": direccion_cli, "cp": cp_actual if st.session_state.metodo_envio == "🛵 Envío a Domicilio" else ""}
                            
                            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            total_final = total_productos + costo_envio + valor_propina
                            dir_final = f"[{tipo_entrega_txt}] {direccion_cli}" if st.session_state.metodo_envio == "🛵 Envío a Domicilio" else "Cliente recoge en Local"
                            
                            id_nuevo_pedido = guardar_pedido_db(fecha_actual, nombre_cli, telefono_limpio, dir_final, detalle_ticket_texto, total_final, cambio_txt)
                            enviar_pedido_telegram(id_nuevo_pedido, nombre_cli, telefono_limpio, direccion_cli if direccion_cli else "Recoge en Local", tipo_entrega_txt, costo_envio, propina_mensaje_telegram, detalle_ticket_texto, total_final, cambio_txt)
                            
                            st.session_state.rastreo_id = id_nuevo_pedido
                            st.session_state.carrito = {}
                            st.session_state.notas_productos = {}
                            
                            st.query_params.clear()
                            st.query_params["rec_user"] = json.dumps(st.session_state.datos_cliente_persistentes)
                            st.rerun()
        elif sistema_abierto_real:
            st.info("El carrito está vacío. Agrega tus platillos usando los botones de arriba.")

# =====================================================================
# 📍 MIS PEDIDOS (RASTREO)
# =====================================================================
with tab_mis_pedidos:
    st.header("🔍 Rastrea tus pedidos")
    tel_prellenado = st.session_state.datos_cliente_persistentes.get("tel", "")
    b_tel = st.text_input("Ingresa tu número telefónico para buscar tus pedidos:", value=tel_prellenado, key="rastreo_input_tel")
    
    if b_tel:
        tel_limp = re.sub(r"\D", "", b_tel)
        if len(tel_limp) == 10:
            historial = buscar_pedidos_por_telefono(tel_limp)
            if not historial:
                st.info("No tienes pedidos registrados con este número.")
            else:
                for pid, pfe, pest, ptot, pdet in historial:
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 2])
                        c1.markdown(f"### Folio: #{pid}")
                        c1.caption(f"Fecha: {pfe}")
                        
                        # Visualización del estado actual con color
                        st.markdown(f"**Estado actual:** {pest}")
                        prog_map = {"Pendiente": 0.15, "En Cocina": 0.5, "En Camino": 0.8, "Entregado": 1.0, "Cancelado": 0.0}
                        prog_val = prog_map.get(pest, 0.0)
                        
                        if pest == "Cancelado": 
                            st.error("❌ Pedido Cancelado")
                        else:
                            st.progress(prog_val)
                        
                        with st.expander("Ver detalle de la orden"):
                            st.text(pdet)
                            st.markdown(f"**Total Pagado: ${ptot:.2f}**")
                
                if st.button("🔄 Actualizar Estatus Ahora", key="btn_actualizar_hist"):
                    st.rerun()
        else:
            st.warning("El teléfono debe tener 10 dígitos.")

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
