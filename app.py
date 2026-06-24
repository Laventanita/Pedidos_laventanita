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

# --- DICIONARIO DE COLONIAS Y COSTOS DE ENVÍO ---
COLONIAS_ENVIO = {
    "--- Selecciona tu Colonia o Fraccionamiento ---": None,
    "🛍️ Pasar a recoger al local ($0)": 0.0,
    
    # ZONA 1: Cercana (0 a 3 km) - $25
    "Ampliación Ozumbilla ($25)": 25.0,
    "Santa Maria Ozumbilla ($25)": 25.0,
    "Los Héroes Tecámac Secc. Ozumbilla ($25)": 25.0,
    "Los Héroes Tecámac II ($25)": 25.0,
    "Los Héroes Tecámac III ($25)": 25.0,
    "Los Héroes (Secc. Bosques, Jardines o Flores) ($25)": 25.0,
    "San Pedro Atzompa Pueblo ($25)": 25.0,
    "Ampliación San Pedro Atzompa ($25)": 25.0,
    "Ojo de Agua (Zona Residencial) ($25)": 25.0,
    "Colinas de Ojo de Agua ($25)": 25.0,
    "Fraccionamientos aledaños a Ojo de Agua ($25)": 25.0,
    "Conjunto Urbano Real Verona ($25)": 25.0,
    "Real del Cid ($25)": 25.0,
    "Hacienda del Bosque ($25)": 25.0,
    "Margarito F. Ayala ($25)": 25.0,
    
    # ZONA 2: Media (3 a 7 km) - $40
    "San Martín Azcatepec ($40)": 40.0,
    "San Francisco Cuautliquixca ($40)": 40.0,
    "Tecámac de Felipe Villanueva Centro ($40)": 40.0,
    "Sierra Hermosa Pueblo ($40)": 40.0,
    "Conjunto Urbano Sierra Hermosa ($40)": 40.0,
    "Villa del Real ($40)": 40.0,
    "Real del Sol ($40)": 40.0,
    "Real Castell ($40)": 40.0,
    "Real Alcalá ($40)": 40.0,
    "San Antonio Hueyotenco ($40)": 40.0,
    
    # ZONA 3: Lejana (7 a 10 km) - $55
    "San Pablo Tecalco ($55)": 55.0,
    "Los Héroes San Pablo ($55)": 55.0,
    "Real Toscana ($55)": 55.0,
    "Real Vizcaya ($55)": 55.0,
    "Santa Cruz Tecámac (Rancho la Capilla) ($55)": 55.0,
    "Urbi Villa del Campo (Valle San Pedro) ($55)": 55.0,
    "Paseos de Tecámac ($55)": 55.0,
    "Paseos del Bosque ($55)": 55.0,
    "Santo Tomás Chiconautla ($55)": 55.0
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

# --- BASE DE DATOS LOCAL ---
def init_db():
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, nombre TEXT, 
                  telefono TEXT, direccion TEXT, pedido TEXT, total REAL, estado TEXT)''')
    conn.commit()
    conn.close()

def enviar_pedido_telegram(nombre, telefono, direccion, colonia, costo_envio, propina_txt, detalle, total):
    tipo_entrega = "🛍️ Pasar a recoger al local" if costo_envio == 0 else f"🛵 Servicio a Domicilio ({colonia})"
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO CONFIRMADO!*\n"
        f"----------------------------------------\n"
        f"👤 *Cliente:* {nombre}\n"
        f"📞 *Teléfono:* {telefono}\n"
        f"🛵 *Entrega:* {tipo_entrega}\n"
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

# --- PESTAÑAS ---
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
        
        # Formulario unificado
        with st.form("formulario_envio", clear_on_submit=True):
            nombre_cli = st.text_input("Nombre Completo *")
            telefono_cli = st.text_input("Teléfono de Contacto (WhatsApp) *")
            
            # El selector de Colonia ahora va integrado adentro del formulario del cliente
            colonia_seleccionada = st.selectbox("Selecciona tu Colonia o Fraccionamiento *", list(COLONIAS_ENVIO.keys()))
            costo_envio = COLONIAS_ENVIO[colonia_seleccionada]
            
            # Dirección dinámica según la colonia
            if costo_envio == 0:
                direccion_cli = "Pasará a recoger al local"
                st.info("🛍️ Elegiste pasar a recoger. No necesitas poner dirección.")
            else:
                direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *")
                
            st.markdown("---")
            st.markdown("🚴‍♂️ **Propina para el Repartidor** (Opcional - Apoya a quien te lleva tu comida)")
            opcion_propina = st.radio(
                "¿Deseas agregar propina?",
                ["No agregar por ahora", "$10.00", "$15.00", "$20.00", "Dar en efectivo al recibir"],
                horizontal=True
            )
            
            # Calcular valor monetario de la propina
            valor_propina = 0.0
            propina_mensaje_telegram = "No asignada"
            if "10" in opcion_propina: valor_propina = 10.0; propina_mensaje_telegram = "$10.00"
            elif "15" in opcion_propina: valor_propina = 15.0; propina_mensaje_telegram = "$15.00"
            elif "20" in opcion_propina: valor_propina = 20.0; propina_mensaje_telegram = "$20.00"
            elif "efectivo" in opcion_propina: propina_mensaje_telegram = "Se entregará en efectivo"

            enviar_pedido = st.form_submit_button("🚀 Confirmar y Enviar Pedido")
            
            if enviar_pedido:
                # Candado de validaciones: obliga a que se seleccione una colonia real
                if costo_envio is None:
                    st.error("Por favor, selecciona una Colonia o Fraccionamiento válido de la lista.")
                elif not nombre_cli or not telefono_cli or (costo_envio > 0 and not direccion_cli):
                    st.error("Por favor, rellena todos los campos obligatorios (*).")
                else:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    total_final = total_productos + costo_envio + valor_propina
                    
                    conn = sqlite3.connect('pedidos_negocio.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (fecha_actual, nombre_cli, telefono_cli, f"{colonia_seleccionada} - {direccion_cli}", detalle_ticket_telegram, total_final, "Pendiente"))
                    conn.commit()
                    conn.close()
                    
                    enviar_pedido_telegram(nombre_cli, telefono_cli, direccion_cli, colonia_seleccionada, costo_envio, propina_mensaje_telegram, detalle_ticket_telegram, total_final)
                    st.success("¡Tu pedido ha sido enviado a la cocina con éxito!")
                    st.session_state.carrito = {}
                    time.sleep(2)
                    st.rerun()
                    
        # Vista informativa de precios abajo del formulario
        if costo_envio is not None:
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
