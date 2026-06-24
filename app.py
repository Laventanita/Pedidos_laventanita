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
PASSWORD_ADMIN = "admin123" 

# --- CONFIGURACIÓN DE ENVÍOS POR CÓDIGO POSTAL ---
# Mapeamos los CP de Tecámac según las distancias que nos pasaste
MAPA_CODIGOS_POSTALES = {
    # ZONA 1 (0 a 3 km) - $25
    "55763": {"nombre": "Ojo de Agua / Real Verona / Real del Cid / Hacienda del Bosque", "costo": 25.0},
    "55767": {"nombre": "Ozumbilla / San Pedro Atzompa / Margarito F. Ayala", "costo": 25.0},
    "55765": {"nombre": "Los Héroes Tecámac (Secciones Ozumbilla, II, III)", "costo": 25.0},
    
    # ZONA 2 (3 a 7 km) - $40
    "55740": {"nombre": "Tecámac Centro / San Martín Azcatepec", "costo": 40.0},
    "55743": {"nombre": "Villa del Real / Real del Sol / Real Castell / Real Alcalá", "costo": 40.0},
    "55744": {"nombre": "Sierra Hermosa / San Francisco Cuautliquixca / Hueyotenco", "costo": 40.0},
    
    # ZONA 3 (7 a 10 km) - $55
    "55746": {"nombre": "San Pablo Tecalco / Los Héroes San Pablo / Real Toscana", "costo": 55.0},
    "55748": {"nombre": "Real Vizcaya / Santa Cruz Tecámac / Urbi Villa del Campo", "costo": 55.0},
    "55060": {"nombre": "Santo Tomás Chiconautla / Límites Ecatepec", "costo": 55.0}
}

# --- INICIALIZAR INVENTARIO EN SESIÓN ---
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

# --- ESTRUCTURA DEL MENÚ REAL ---
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
    "🍹 Aguas Frescas (1 Litro) - $40.00": {
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
    try: requests.post(url, json=payload)
    except Exception as e: st.error(f"Error en Telegram: {e}")

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

    # Procesar Carrito
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
        
        # Formulario Unificado
        with st.form("formulario_envio", clear_on_submit=True):
            nombre_cli = st.text_input("Nombre Completo *")
            telefono_cli = st.text_input("Teléfono de Contacto (WhatsApp) *")
            
            # Selector de tipo de servicio primero
            tipo_entrega_opcion = st.selectbox("Método de Entrega *", ["--- Selecciona método ---", "🛵 Envío a Domicilio", "🛍️ Pasar a recoger al local"])
            
            costo_envio = 0.0
            zona_detectada = ""
            cp_cli = ""
            direccion_cli = ""
            
            if tipo_entrega_opcion == "🛵 Envío a Domicilio":
                cp_cli = st.text_input("Código Postal (5 dígitos) *", max_chars=5)
                direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *")
                
                # Validar el CP en tiempo real
                if cp_cli:
                    if cp_cli in MAPA_CODIGOS_POSTALES:
                        costo_envio = MAPA_CODIGOS_POSTALES[cp_cli]["costo"]
                        zona_detectada = MAPA_CODIGOS_POSTALES[cp_cli]["nombre"]
                        st.success(f"📍 Zona identificada: {zona_detectada} (Costo Envío: ${costo_envio:.2f})")
                    else:
                        st.error("⚠️ Lo sentimos, este Código Postal está fuera de nuestro radio de cobertura de entrega.")
                        costo_envio = None # Bloquear el envío
            
            elif tipo_entrega_opcion == "🛍️ Pasar a recoger al local":
                direccion_cli = "Cliente pasará a recoger al local"
                st.info("🛍️ Elegiste recoger en sucursal. No se aplicará costo de envío.")
                costo_envio = 0.0
            
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
                if tipo_entrega_opcion == "--- Selecciona método ---":
                    st.error("Por favor, selecciona si deseas envío a domicilio o recoger en local.")
                elif costo_envio is None:
                    st.error("No se puede enviar el pedido debido a que el Código Postal no tiene cobertura.")
                elif not nombre_cli or not telefono_cli or (tipo_entrega_opcion == "🛵 Envío a Domicilio" and (not cp_cli or not direccion_cli)):
                    st.error("Por favor, rellena todos los campos obligatorios (*).")
                else:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    total_final = total_productos + costo_envio + valor_propina
                    
                    # Guardado local
                    tipo_entrega_txt = f"Domicilio (CP {cp_cli})" if tipo_entrega_opcion == "🛵 Envío a Domicilio" else "Recoger Local"
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
                    
        # Resumen dinámico abajo de la pantalla
        if tipo_entrega_opcion != "--- Selecciona método ---" and costo_envio is not None:
            total_informativo = total_productos + costo_envio + valor_propina
            st.markdown(f"**Resumen de Cuenta:**")
            st.write(f"• Productos: ${total_productos:.2f}")
            st.write(f"• Envío: ${costo_envio:.2f}")
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
        st.write("Apaga los productos que no estés vendiendo en este momento o que se hayan terminado:")
        
        for categoria, productos in MENU.items():
            st.markdown(f"### {categoria}")
            for prod in productos.keys():
                estado_actual = st.session_state.inventario.get(prod, True)
                nuevo_estado = st.toggle(f"Disponible: {prod}", value=estado_actual, key=f"switch_{prod}")
                st.session_state.inventario[prod] = nuevo_estado
    elif password_input != "":
        st.error("Contraseña incorrecta.")
