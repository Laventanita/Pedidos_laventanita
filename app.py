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

# --- INICIALIZAR INVENTARIO EN SESIÓN ---
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        # Desayunos
        "Chilaquiles chicos (80g)": True,
        "Chilaquiles medianos (170g)": True,
        "Chilaquiles para acompañar (250g)": True,
        "Cuernito sencillo": True,
        "Cuernito con fruta": True,
        # Licuados 1/2 L
        "Licuado de Fresa (1/2 L)": True,
        "Licuado de Chocolate (1/2 L)": True,
        "Licuado de Plátano (1/2 L)": True,
        # Licuados 1 L
        "Licuado de Fresa (1 L)": True,
        "Licuado de Chocolate (1 L)": True,
        "Licuado de Plátano (1 L)": True,
        # Aguas
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
        "Agua de Café (1 L)": 40.0,
        "Agua de Mazapán (1 L)": 40.0,
        "Agua de Fresa (1 L)": 40.0,
        "Agua de Limón (1 L)": 40.0,
        "Agua de Melón (1 L)": 40.0,
        "Agua de Piña (1 L)": 40.0,
        "Agua de Sandía (1 L)": 40.0,
        "Agua de Guayaba (1 L)": 40.0,
        "Agua de Avena (1 L)": 40.0
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

def enviar_pedido_telegram(nombre, telefono, direccion, detalle, total):
    mensaje = (
        f"🔔 *¡NUEVO PEDIDO A DOMICILIO!*\n"
        f"----------------------------------------\n"
        f"👤 *Cliente:* {nombre}\n"
        f"📞 *Teléfono:* {telefono}\n"
        f"📍 *Dirección:* {direccion}\n"
        f"----------------------------------------\n"
        f"📝 *Detalle del Pedido:*\n"
        f"{detalle}\n"
        f"----------------------------------------\n"
        f"💰 *Total a Cobrar:* ${total:.2f}\n"
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
                    
                    # Selector de salsa especial si es chilaquiles
                    salsa = ""
                    if "Chilaquiles" in prod:
                        salsa_elegida = col1.selectbox("Salsa:", ["Verdes", "Rojos"], key=f"salsa_{prod}")
                        salsa = f" ({salsa_elegida})"
                    
                    if col2.button("➕", key=f"add_{prod}"):
                        nombre_final = f"{prod}{salsa}"
                        st.session_state.carrito[nombre_final] = st.session_state.carrito.get(nombre_final, 0) + 1
                    
                    # Buscar cantidad considerando si lleva salsa o no
                    cant = 0
                    for k, v in st.session_state.carrito.items():
                        if k.startswith(prod):
                            cant += v
                    col3.write(f"Cant total: **{cant}**")

    # Procesar Carrito
    total_cuenta = 0.0
    detalle_ticket_telegram = ""
    productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

    if productos_seleccionados:
        st.markdown("---")
        st.subheader("🛒 Tu Pedido")
        
        for nombre_completo, cant in productos_seleccionados.items():
            # Encontrar el precio base mapeando el nombre original sin la salsa
            nombre_base = nombre_completo.split(" (Verdes)")[0].split(" (Rojos)")[0]
            precio_unitario = next(precio for cat in MENU.values() for p, precio in cat.items() if p == nombre_base)
            subtotal = precio_unitario * cant
            total_cuenta += subtotal
            
            st.write(f"• {cant}x {nombre_completo} — ${subtotal:.2f}")
            if st.button("❌ Quitar uno", key=f"del_{nombre_completo}"):
                st.session_state.carrito[nombre_completo] -= 1
                st.rerun()
                
            detalle_ticket_telegram += f"• {cant}x {nombre_completo}\n"
            
        st.markdown(f"### **Total a pagar: ${total_cuenta:.2f}**")
        st.markdown("---")
        st.subheader("📍 Datos para la Entrega")
        
        with st.form("formulario_envio", clear_on_submit=True):
            nombre_cli = st.text_input("Nombre Completo *")
            telefono_cli = st.text_input("Teléfono de Contacto *")
            direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *")
            
            enviar_pedido = st.form_submit_button("🚀 Confirmar y Enviar Pedido")
            
            if enviar_pedido:
                if nombre_cli and telefono_cli and direccion_cli:
                    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    conn = sqlite3.connect('pedidos_negocio.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                              (fecha_actual, nombre_cli, telefono_cli, direccion_cli, detalle_ticket_telegram, total_cuenta, "Pendiente"))
                    conn.commit()
                    conn.close()
                    
                    enviar_pedido_telegram(nombre_cli, telefono_cli, direccion_cli, detalle_ticket_telegram, total_cuenta)
                    st.success("¡Tu pedido ha sido enviado a la cocina con éxito!")
                    st.session_state.carrito = {}
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Por favor rellena todos los campos obligatorios (*)")
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
