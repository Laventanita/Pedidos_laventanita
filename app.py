import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="La Ventanita & Tacos Mixi", page_icon="🌮", layout="centered")

# --- CREDENCIALES DESDE SECRETOS ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- CONTRASEÑA DEL ADMINISTRADOR ---
PASSWORD_ADMIN = "1984" 

# --- CONFIGURACIÓN MAESTRA DE CÓDIGOS POSTALES (MÁXIMO 10 KM) ---
MAPA_CODIGOS_POSTALES = {
    # --- ZONA 1: Cercana Tecámac (0 a 3 km) - $25.00 ---
    "55763": {"nombre": "Vitalia / Ojo de Agua / Los Héroes Tecámac", "costo": 25.0},
    "55764": {"nombre": "Los Héroes Tecámac II / Los Héroes Ozumbilla / Margarito F. Ayala", "costo": 25.0},
    "55766": {"nombre": "Ampliación Ozumbilla", "costo": 25.0},
    "55770": {"nombre": "Ojo de Agua / San Pedro Atzompa / Rinconada San Pedro", "costo": 25.0},
    "55773": {"nombre": "Hacienda Provenzal", "costo": 25.0},
    "55776": {"nombre": "Lomas de San Pedro Atzompa", "costo": 25.0},
    "55778": {"nombre": "Ampliación de la Concepción", "costo": 25.0},

    # --- ZONA 2: Media Tecámac (3 a 7 km) - $40.00 ---
    "55740": {"nombre": "Tecámac Centro / Ejido Santa Ana / El Calvario / Galaxias el Llano", "costo": 40.0},
    "55743": {"nombre": "Real Granada / Isidro Fabela / Rancho la Luz / La Palma / Hacienda del Bosque / San Nicolás la Redonda", "costo": 40.0},
    "55744": {"nombre": "San Pedro Potzohuacan", "costo": 40.0},
    "55745": {"nombre": "Real Granada IV / Reserva Castilla / San Jerónimo Xonacahuacan / Ampliación San Jerónimo", "costo": 40.0},
    "55748": {"nombre": "San Martín Azcatepec / San José / Jema / San Mateo Tecalco / Ejido de Tecámac / Los Olivos", "costo": 40.0},
    "55749": {"nombre": "Villa del Real / Sierra Hermosa / Montecarlo / 5 de Mayo / Hueyotenco / Jardines de Tecámac", "costo": 40.0},
    "55760": {"nombre": "San Francisco Cuautliquixca / Santa María Ozumbilla / Portal Ojo de Agua / Atlautenco / El Calvario", "costo": 40.0},
    "55768": {"nombre": "Lomas de Ozumbilla / San Antonio / Cuauhtémoc / La Azteca", "costo": 40.0},

    # --- ZONA 3: Lejana Tecámac / Ecatepec Norte Colindante (7 a 10 km) - $55.00 ---
    "55746": {"nombre": "Rancho la Capilla / Santa Cruz Tecámac / Real Belmonte / Ex Hacienda San Miguel", "costo": 55.0},
    "55747": {"nombre": "San Pablo Tecalco / San Isidro Citlalcóatl", "costo": 55.0},
    "55750": {"nombre": "Santa María Ajoloapan / El Tanque", "costo": 55.0},
    "55752": {"nombre": "San Juan Pueblo Nuevo", "costo": 55.0},
    "55754": {"nombre": "Paseos de Tecámac / Santo Domingo Ajoloapan / Loma de San Jerónimo", "costo": 55.0},
    "55755": {"nombre": "Los Reyes Acozac / Buenavista / San Miguel / Progreso / La Campiña", "costo": 55.0},
    "55757": {"nombre": "San Lucas Xolox / Ejidal", "costo": 55.0},
    "55758": {"nombre": "Ampliación la Palma (Zona Industrial)", "costo": 55.0},
    "55765": {"nombre": "Los Héroes San Pablo / Lomas de Tecámac / La Cañada / México Independiente", "costo": 55.0},
    
    # Únicos sectores de Ecatepec aceptados dentro del radio límite de 10 km
    "55060": {"nombre": "Venta de Carpio / La Guadalupana / Los Héroes Ecatepec V", "costo": 55.0},
    "55063": {"nombre": "Ciudad Cuauhtémoc (Chiconautla 3000)", "costo": 55.0},
    "55064": {"nombre": "San Isidro Atlautenco / Cd. Cuauhtémoc (Nopalera)", "costo": 55.0},
    "55065": {"nombre": "Santa Cruz Venta de Carpio", "costo": 55.0},
    "55066": {"nombre": "Santa María Chiconautla / Santo Tomás Chiconautla / Portal Chiconautla", "costo": 55.0},
    "55067": {"nombre": "Ciudad Cuauhtémoc (Geo 2000 / Tlaloc / Cuitlahuac)", "costo": 55.0},
    "55068": {"nombre": "Santo Tomás Chiconautla (Ejido / El Mirador)", "costo": 55.0},
    "55069": {"nombre": "La Preciosa / Los Pajaritos / La Garita", "costo": 55.0},
}

# --- INICIALIZAR INVENTARIO EN ESTADO DE SESIÓN ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        "Chilaquiles chicos (80g)": True, "Chilaquiles medianos (170g)": True, "Chilaquiles para acompañar (250g)": True,
        "Cuernito sencillo": True, "Cuernito con fruta": True,
        "Licuado de Fresa (1/2 L)": True, "Licuado de Chocolate (1/2 L)": True, "Licuado de Plátano (1/2 L)": True,
        "Licuado de Fresa (1 L)": True, "Licuado de Chocolate (1 L)": True, "Licuado de Plátano (1 L)": True,
        "Agua de Café (1 L)": True, "Agua de Mazapán (1 L)": True, "Agua de Fresa (1 L)": True,
        "Agua de Limón (1 L)": True, "Agua de Melón (1 L)": True, "Agua de Piña (1 L)": True,
        "Agua de Sandía (1 L)": True, "Agua de Guayaba (1 L)": True, "Agua de Avena (1 L)": True
    }

# --- MENÚ DE PLATILLOS ---
MENU = {
    "☕ Desayunos": {
        "Chilaquiles chicos (80g)": 50.0,
        "Chilaquiles medianos (170g)": 65.0,
        "Chilaquiles para acompañar (250g)": 100.0,
        "Cuernito sencillo": 45.0,
        "Cuernito con fruta": 75.0
    },
    "🥤 Licuados (1/2 Litro)": {
        "Licuado de Fresa (1/2 L)": 35.0,
        "Licuado de Chocolate (1/2 L)": 35.0,
        "Licuado de Plátano (1/2 L)": 35.0
    },
    "🥤 Licuados (1 Litro)": {
        "Licuado de Fresa (1 L)": 70.0,
        "Licuado de Chocolate (1 L)": 70.0,
        "Licuado de Plátano (1 L)": 70.0
    },
    "🍹 Aguas Frescas (1 Litro)": {
        "Agua de Café (1 L)": 40.0, "Agua de Mazapán (1 L)": 40.0, "Agua de Fresa (1 L)": 40.0,
        "Agua de Limón (1 L)": 40.0, "Agua de Melón (1 L)": 40.0, "Agua de Piña (1 L)": 40.0,
        "Agua de Sandía (1 L)": 40.0, "Agua de Guayaba (1 L)": 40.0, "Agua de Avena (1 L)": 40.0
    }
}

def init_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT)''')
    conn.commit()
    conn.close()

def enviar_pedido_telegram(nombre, telefono, direccion, tipo_entrega, costo_envio, propina_txt, detalle, total):
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO CONFIRMADO!*\n"
        f"----------------------------------------\n"
        f"👤 *Cliente:* {nombre}\n"
        f"📞 *Teléfono:* {telefono}\n"
        f"🛵 *Tipo Entrega:* {tipo_entrega}\n"
        f"📍 *Dirección:* {direccion}\n"
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
        requests.post(url, json=payload)
    except Exception as e: 
        st.error(f"Error en Telegram: {e}")

init_db()

tab_cliente, tab_admin = st.tabs(["📋 Menú para Clientes", "🔐 Panel Administrador"])

# =====================================================================
# 📋 VISTA DEL CLIENTE
# =====================================================================
with tab_cliente:
    st.title("La Ventanita & Tacos Mixi")
    st.write("Arma tu pedido aquí abajo y te lo llevamos hasta tu hogar.")

    if 'carrito' not in st.session_state:
        st.session_state.carrito = {}

    for categoria, productos in MENU.items():
        al_menos_uno_disponible = any(st.session_state.inventario.get(p, True) for p in productos)
        if al_menos_uno_disponible:
            with st.expander(f"{categoria}", expanded=True):
                for prod, precio in productos.items():
                    if not st.session_state.inventario.get(prod, True):
                        continue
                        
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.write(f"**{prod}**\n${precio:.2f}")
                    
                    salsa = ""
                    if "Chilaquiles" in prod:
                        salsa_elegida = col1.selectbox("Salsa:", ["Verdes", "Rojos"], key=f"salsa_{prod}")
                        salsa = f" ({salsa_elegida})"
                    
                    if col2.button("➕", key=f"add_{prod}"):
                        nombre_final = f"{prod}{salsa}"
                        st.session_state.carrito[nombre_final] = st.session_state.carrito.get(nombre_final, 0) + 1
                    
                    cant = 0
                    for k, v in st.session_state.carrito.items():
                        if k.startswith(prod):
                            cant += v
                    col3.write(f"Cant: **{cant}**")

    # Procesar estructura del carrito
    total_productos = 0.0
    detalle_ticket_telegram = ""
    productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

    if productos_seleccionados:
        st.markdown("---")
        st.subheader("🛒 Tu Pedido")
        
        for nombre_completo, cant in productos_seleccionados.items():
            nombre_base = nombre_completo.split(" (Verdes)")[0].split(" (Rojos)")[0]
            precio_unitario = next(precio for cat in MENU.values() for p, precio in cat.items() if p == nombre_base)
            subtotal = precio_unitario * cant
            total_productos += subtotal
            
            st.write(f"• {cant}x {nombre_completo} — ${subtotal:.2f}")
            if st.button("❌ Quitar uno", key=f"del_{nombre_completo}"):
                st.session_state.carrito[nombre_completo] -= 1
                st.rerun()
                
            detalle_ticket_telegram += f"• {cant}x {nombre_completo}\n"
            
        st.markdown(f"**Subtotal productos: ${total_productos:.2f}**")
        st.markdown("---")
        
        st.subheader("👤 Datos para la Entrega")
        
        with st.form("formulario_envio", clear_on_submit=True):
            nombre_cli = st.text_input("Nombre Completo *")
            telefono_cli = st.text_input("Teléfono de Contacto (WhatsApp) *")
            
            tipo_entrega_opcion = st.selectbox("Método de Entrega *", ["🛵 Envío a Domicilio", "🛍️ Pasar a recoger al local"])
            
            costo_envio = 0.0
            tipo_entrega_txt = ""
            
            if tipo_entrega_opcion == "🛵 Envío a Domicilio":
                cp_cli = st.text_input("Código Postal (5 dígitos obligatorio) *", max_chars=5)
                direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *")
                
                if cp_cli:
                    if cp_cli in MAPA_CODIGOS_POSTALES:
                        costo_envio = MAPA_CODIGOS_POSTALES[cp_cli]["costo"]
                        zona_nombre = MAPA_CODIGOS_POSTALES[cp_cli]["nombre"]
                        tipo_entrega_txt = f"Domicilio (CP {cp_cli} - {zona_nombre})"
                        st.success(f"📍 Zona de Reparto Validada: {zona_nombre} (Costo: ${costo_envio:.2f})")
                    else:
                        costo_envio = None # Bloqueado automáticamente por falta de rango
                        st.error("❌ Fuera de Cobertura: El Código Postal excede el radio máximo de 10 km permitido.")
                else:
                    costo_envio = 0.0
            else:
                cp_cli = "Local"
                direccion_cli = "Cliente pasará a recoger directamente al local"
                costo_envio = 0.0
                tipo_entrega_txt = "Recoger en Local"
                st.info("🛍️ Pasarás a recoger. No se te cobrará comisión de envío.")
            
            st.markdown("---")
            st.markdown("🚴‍♂️ **Propina para el Repartidor** (Opcional)")
            opcion_propina = st.radio(
                "¿Deseas agregar propina?",
                ["No agregar por ahora", "$10.00", "$15.00", "$20.00", "Dar en efectivo al recibir"],
                horizontal=True
            )
            
            valor_propina = 0.0
            propina_mensaje_telegram = "No asignada"
            if "10" in opcion_propina: valor_propina = 10.0; propina_mensaje_telegram = "$10.00"
            elif "15" in opcion_propina: valor_propina = 15.0; propina_mensaje_telegram = "$15.00"
            elif "20" in opcion_propina: valor_propina = 20.0; propina_mensaje_telegram = "$20.00"
            elif "efectivo" in opcion_propina: propina_mensaje_telegram = "Se entregará en efectivo"

            enviar_pedido = st.form_submit_button("🚀 Confirmar y Enviar Pedido")
            
            if enviar_pedido:
                if tipo_entrega_opcion == "🛵 Envío a Domicilio" and not cp_cli:
                    st.error("⚠️ El Código Postal es estrictamente obligatorio para envíos a domicilio.")
                elif costo_envio is None:
                    st.error("❌ No es posible procesar el pedido. La dirección se encuentra fuera de cobertura.")
                elif not nombre_cli or not telefono_cli or (tipo_entrega_opcion == "🛵 Envío a Domicilio" and not direccion_cli):
                    st.error("⚠️ Por favor completa los campos marcados con asterisco (*).")
                else:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    total_final = total_productos + costo_envio + valor_propina
                    
                    conn = sqlite3.connect('pedidos_negocio.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (fecha_actual, nombre_cli, telefono_cli, f"[{tipo_entrega_txt}] {direccion_cli}", detalle_ticket_telegram, total_final, "Pendiente"))
                    conn.commit()
                    conn.close()
                    
                    enviar_pedido_telegram(nombre_cli, telefono_cli, direccion_cli, tipo_entrega_txt, costo_envio, propina_mensaje_telegram, detalle_ticket_telegram, total_final)
                    st.success("¡Tu pedido ha sido enviado a la cocina con éxito!")
                    st.session_state.carrito = {}
                    time.sleep(2)
                    st.rerun()

        # Resumen del cobro en vivo
        if costo_envio is not None:
            total_informativo = total_productos + costo_envio + valor_propina
            st.markdown(f"**Resumen de Cuenta:**")
            st.write(f"• Productos: ${total_productos:.2f}")
            if tipo_entrega_opcion == "🛵 Envío a Domicilio" and cp_cli in MAPA_CODIGOS_POSTALES:
                st.write(f"• Envío (CP {cp_cli}): ${costo_envio:.2f}")
            if valor_propina > 0: st.write(f"• Propina: ${valor_propina:.2f}")
            st.markdown(f"### **Total Final: ${total_informativo:.2f}**")

    else:
        st.info("El carrito está vacío. Agrega tus platillos usando el botón ➕ de arriba.")

# =====================================================================
# 🔐 PANEL ADMINISTRADOR
# =====================================================================
with tab_admin:
    st.title("⚙️ Control de Inventario")
    password_input = st.text_input("Introduce la contraseña de Administrador", type="password")
    
    if password_input == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        st.write("Desactiva los productos agotados para ocultarlos temporalmente del menú de los clientes:")
        
        for categoria, productos in MENU.items():
            st.markdown(f"### {categoria}")
            for prod in productos.keys():
                estado_actual = st.session_state.inventario.get(prod, True)
                nuevo_estado = st.toggle(f"Disponible: {prod}", value=estado_actual, key=f"switch_{prod}")
                st.session_state.inventario[prod] = nuevo_estado
    elif password_input != "":
        st.error("Contraseña incorrecta.")
