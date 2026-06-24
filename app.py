import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time
import json
import re
import urllib.parse

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")

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
    "55743": {"nombre": "Real Granada / Rancho la Luz / Hacienda del Bosque", "costo": 40.0},
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
    "🥤 Licuados (1/2 Litro)": {
        "Licuado de Fresa (1/2 L)": 35.0, "Licuado de Chocolate (1/2 L)": 35.0, "Licuado de Plátano (1/2 L)": 35.0
    },
    "🥤 Licuados (1 Litro)": {
        "Licuado de Fresa (1 L)": 70.0, "Licuado de Chocolate (1 L)": 70.0, "Licuado de Plátano (1 L)": 70.0
    },
    "🍹 Aguas Frescas (1 Litro)": {
        "Agua de Café (1 L)": 40.0, "Agua de Mazapán (1 L)": 40.0, "Agua de Fresa (1 L)": 40.0,
        "Agua de Limón (1 L)": 40.0, "Agua de Melón (1 L)": 40.0, "Agua de Piña (1 L)": 40.0,
        "Agua de Sandía (1 L)": 40.0, "Agua de Guayaba (1 L)": 40.0, "Agua de Avena (1 L)": 40.0
    },
    "🥤 Jugos Naturales": {
        "Jugo Verde": 35.0,
        "Jugo de Naranja": 35.0,
        "Jugo Combinado": 40.0
    }
}

# --- PERSISTENCIA AUTOMÁTICA ---
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
        try: st.session_state.rastreo_id = int(st.query_params["tracking_id"])
        except: pass

def actualizar_memoria_navegador():
    st.query_params["rec_cart"] = json.dumps(st.session_state.carrito)
    st.query_params["rec_notes"] = json.dumps(st.session_state.notas_productos)
    st.query_params["rec_user"] = json.dumps(st.session_state.datos_cliente_persistentes)
    if 'rastreo_id' in st.session_state:
        st.query_params["tracking_id"] = str(st.session_state.rastreo_id)

if 'inventario' not in st.session_state:
    st.session_state.inventario = {}
    for categoria, productos in MENU.items():
        for prod in productos.keys():
            st.session_state.inventario[prod] = True

def init_db():
    conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT)''')
    c.execute("PRAGMA table_info(pedidos)")
    columnas = [col[1] for col in c.fetchall()]
    if "metodo_pago" not in columnas:
        c.execute("ALTER TABLE pedidos ADD COLUMN metodo_pago TEXT DEFAULT 'No especificado'")
    if "archivado" not in columnas:
        c.execute("ALTER TABLE pedidos ADD COLUMN archivado INTEGER DEFAULT 0")
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

tab_cliente, tab_admin = st.tabs(["📋 Menú para Clientes", "🔐 Panel Administrador"])

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
            if st.button("🛒 Hacer un nuevo pedido"):
                del st.session_state.rastreo_id
                st.query_params.clear()
                st.rerun()

            time.sleep(12)
            st.rerun()
        else:
            del st.session_state.rastreo_id
            if "tracking_id" in st.query_params:
                del st.query_params["tracking_id"]
            st.rerun()
            
    else:
        st.title("La Ventanita & Tacos Mixi")
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

                            elif "Jugo" in prod:
                                tamanio_jugo = st.selectbox("Tamaño:", ["Chico (1/2 L)", "Grande (1 L) (+$20.00)"], key=f"tam_{prod}")
                                if "Grande" in tamanio_jugo:
                                    precio_final_prod = precio + 20.0
                                agregado_texto = f" ({tamanio_jugo})"

                            st.write(f"**{prod}{agregado_texto}**\n${precio_final_prod:.2f}")

                        with col_controles:
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

        productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

        if productos_seleccionados:
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
            tipo_pago = st.radio("¿Cómo deseas pagar tu pedido al recibir?", ["💵 Efectivo", "💳 Tarjeta (El repartidor lleva Terminal Física)"], horizontal=True)
            
            cambio_txt = ""
            if tipo_pago == "💵 Efectivo":
                cambio_de = st.text_input("¿Con cuánto vas a pagar? (Para que el repartidor lleve cambio exacto)", placeholder="Ej. Con un billete de $200")
                cambio_txt = f"Efectivo (Requiere cambio de: {cambio_de})" if cambio_de else "Efectivo (Importe exacto)"
            else:
                cambio_txt = "Tarjeta (Llevar terminal Clip/MercadoPago)"

            st.markdown("### 📋 Resumen Detallado de tu Cuenta")
            with st.container(border=True):
                st.markdown("**Artículos solicitados:**")
                for clave_carrito, cant in productos_seleccionados.items():
                    p_nombre, p_extra, _ = clave_carrito.split("|||")
                    nota_especifica = st.session_state.notas_productos.get(clave_carrito, "").strip()
                    nota_pantalla = f" *[Nota: {nota_especifica}]*" if nota_especifica else ""
                    st.write(f"  • {cant}x {p_nombre}{p_extra}{nota_pantalla}")
                
                st.write(f"**• Subtotal Platillos:** ${total_productos:.2f}")
                st.write(f"**• Costo de Envío:** ${costo_envio:.2f}" if costo_envio is not None else "**• Costo de Envío:** [BLOQUEADO]")
                st.write(f"**• Propina Repartidor:** ${valor_propina:.2f} ({st.session_state.propina_opcion})")
                st.write(f"**• Forma de Pago:** {cambio_txt}")
                
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
                        st.query_params["tracking_id"] = str(id_nuevo_pedido)
                        st.rerun()
        else:
            st.info("El carrito está vacío. Agrega tus platillos usando los botones de arriba.")

# =====================================================================
# 🔐 PANEL ADMINISTRADOR
# =====================================================================
with tab_admin:
    st.title("⚙️ Panel de Control Interno")
    password_input = st.text_input("Introduce la contraseña de Administrador", type="password", key="pass_admin")
    
    if password_input == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        st.markdown("---")
        st.header("📥 Gestión de Pedidos Activos")
        st.write("Cambia el estado de los pedidos aquí abajo:")
        
        conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
        c = conn.cursor()
        c.execute("SELECT id, fecha, nombre, telefono, direccion, pedido, total, estado, metodo_pago FROM pedidos WHERE archivado = 0 ORDER BY id DESC")
        pedidos_activos = c.fetchall()
        conn.close()
        
        if pedidos_activos:
            for ped in pedidos_activos:
                p_id, p_fecha, p_nombre, p_tel, p_dir, p_det, p_tot, p_est, p_pago = ped
                
                with St.container(border=True):
                    col_det, col_est = st.columns([2, 1])
                    with col_det:
                        st.markdown(f"### 📦 Folio: #{p_id} — {p_nombre}")
                        st.write(f"📅 **Fecha:** {p_fecha}")
                        
                        # --- MEJORA 3: BOTÓN DINÁMICO PARA ABRIR WHATSAPP DIRECTO CON TEXTO DE CORTESÍA ---
                        msg_whatsapp = f"¡Hola {p_nombre}! Te contactamos de La Ventanita / Tacos Mixi sobre tu pedido con folio #{p_id}."
                        msg_encoded = urllib.parse.quote(msg_whatsapp)
                        url_whatsapp = f"https://wa.me/52{p_tel}?text={msg_encoded}"
                        
                        st.markdown(f"📞 **Teléfono:** {p_tel}")
                        st.sidebar.markdown(f"") # Espaciador invisible
                        st.link_button("💬 Abrir WhatsApp", url_whatsapp, type="secondary", use_container_width=False)
                        
                        st.write(f"📍 **Dirección:** {p_dir}")
                        st.write(f"💳 **Pago:** {p_pago}")
                        st.text(f"Detalle:\n{p_det}")
                        st.markdown(f"**Total a cobrar: ${p_tot:.2f}**")
                        
                    with col_est:
                        st.markdown(f"**Estado actual: `{p_est}`**")
                        
                        with st.form(key=f"form_admin_status_{p_id}"):
                            nuevo_est = st.selectbox(
                                "Modificar Estatus:", 
                                ["Pendiente", "En Cocina", "En Camino", "Entregado", "Cancelado"],
                                index=["Pendiente", "En Cocina", "En Camino", "Entregado", "Cancelado"].index(p_est)
                            )
                            guardar_cambio_estado = st.form_submit_button("💾 Actualizar", use_container_width=True)
                            
                            if guardar_cambio_estado and nuevo_est != p_est:
                                conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
                                c = conn.cursor()
                                c.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_est, p_id))
                                conn.commit()
                                conn.close()
                                st.toast(f"¡Pedido #{p_id} actualizado a {nuevo_est}!")
                                time.sleep(0.5)
                                st.rerun()
                            
                        if p_est in ["Entregado", "Cancelado"]:
                            if st.button("🗂️ Archivar Pedido", key=f"archive_btn_{p_id}", use_container_width=True):
                                conn = sqlite3.connect('pedidos_negocio.db', timeout=10)
                                c = conn.cursor()
                                c.execute("UPDATE pedidos SET archivado = 1 WHERE id = ?", (p_id,))
                                conn.commit()
                                conn.close()
                                st.toast(f"Pedido #{p_id} guardado en el archivo histórico.")
                                time.sleep(0.5)
                                st.rerun()
        else:
            st.info("No tienes ningún pedido activo en este momento.")
            
        st.markdown("---")
        st.header("🥦 Control de Disponibilidad del Menú")
        for category, productos in MENU.items():
            if productos: 
                st.markdown(f"### {category}")
                for prod in productos.keys():
                    estado_actual = st.session_state.inventario.get(prod, True)
                    nuevo_estado = st.toggle(f"Disponible: {prod}", value=estado_actual, key=f"switch_{prod}")
                    st.session_state.inventario[prod] = nuevo_estado

        time.sleep(15)
        st.rerun()
                
    elif password_input != "":
        st.error("Contraseña incorrecta.")
