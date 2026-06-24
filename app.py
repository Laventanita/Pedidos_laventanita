import streamlit as st
import sqlite3
import requests
from datetime import datetime
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Menú Digital", page_icon="🌮", layout="centered")

# --- CREDENCIALES DESDE SECRETOS ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- CONTRASEÑA DEL ADMINISTRADOR ---
# Puedes cambiar "admin123" por la contraseña que tú quieras
PASSWORD_ADMIN = "admin123" 

# --- INICIALIZAR INVENTARIO EN SESIÓN ---
# Esto mantiene el estado de qué productos están prendidos o apagados
if 'inventario' not in st.session_state:
    st.session_state.inventario = {
        # Desayunos
        "Chilaquiles sencillos": True,
        "Chilaquiles con Huevo/Pollo": True,
        "Huevos al gusto": True,
        "Molletes": True,
        # Jugos
        "Jugo Verde": True,
        "Jugo de Naranja": True,
        "Jugo de Zanahoria": True,
        "Jugo Combinado": True,
        # Tacos y Quesadillas
        "Taco de Mixiote": True,
        "Taco de Bistec": True,
        "Taco de Longaniza": True,
        "Quesadilla sencilla": True,
        "Quesadilla con carne": True
    }

# --- ESTRUCTURA DEL MENÚ (Precios y Categorías fijas) ---
MENU = {
    "☕ Desayunos": {
        "Chilaquiles sencillos": 75.0,
        "Chilaquiles con Huevo/Pollo": 95.0,
        "Huevos al gusto": 70.0,
        "Molletes": 65.0
    },
    "🧃 Jugos de Fruta": {
        "Jugo Verde": 45.0,
        "Jugo de Naranja": 40.0,
        "Jugo de Zanahoria": 40.0,
        "Jugo Combinado": 45.0
    },
    "🌮 Tacos y Quesadillas": {
        "Taco de Mixiote": 18.0,
        "Taco de Bistec": 18.0,
        "Taco de Longaniza": 18.0,
        "Quesadilla sencilla": 25.0,
        "Quesadilla con carne": 35.0
    }
}

# --- UNIDAD BASE DE DATOS ---
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

# --- PESTAÑAS: MENÚ CLIENTE O PANEL ADMIN ---
# Usamos las pestañas nativas de Streamlit para separar las vistas
tab_cliente, tab_admin = st.tabs(["📋 Menú para Clientes", "🔐 Panel Administrador"])

# =====================================================================
# 📋 VISTA DEL CLIENTE
# =====================================================================
with tab_cliente:
    st.title("La Ventanita & Tacos Mixi")
    st.write("Arma tu pedido aquí abajo y te lo llevamos hasta tu hogar.")

    if 'carrito' not in st.session_state:
        st.session_state.carrito = {}

    # Mostrar categorías
    for categoria, productos in MENU.items():
        # Verificar si al menos un producto de la categoría está disponible para mostrarla
        al_menos_uno_disponible = any(st.session_state.inventario.get(p, True) for p in productos)
        
        if al_menos_uno_disponible:
            with st.expander(f"{categoria}", expanded=True):
                for prod, precio in productos.items():
                    # Si tú apagaste el producto en el panel, el cliente no lo ve
                    if not st.session_state.inventario.get(prod, True):
                        continue
                        
                    col1, col2, col3 = st.columns([2, 1, 1])
                    col1.write(f"**{prod}**\n${precio:.2f}")
                    
                    if col2.button("➕", key=f"add_{prod}"):
                        st.session_state.carrito[prod] = st.session_state.carrito.get(prod, 0) + 1
                    
                    cant = st.session_state.carrito.get(prod, 0)
                    col3.write(f"Cant: **{cant}**")

    # Procesar Carrito de Compras
    total_cuenta = 0.0
    detalle_ticket_telegram = ""
    productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

    if productos_seleccionados:
        st.markdown("---")
        st.subheader("🛒 Tu Pedido")
        
        for prod, cant in productos_seleccionados.items():
            precio_unitario = next(precio for cat in MENU.values() for p, precio in cat.items() if p == prod)
            subtotal = precio_unitario * cant
            total_cuenta += subtotal
            
            st.write(f"• {cant}x {prod} — ${subtotal:.2f}")
            if st.button("❌ Quitar uno", key=f"del_{prod}"):
                st.session_state.carrito[prod] -= 1
                st.rerun()
                
            detalle_ticket_telegram += f"• {cant}x {prod}\n"
            
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
# 🔐 PANEL ADMINISTRADOR (OCULTO)
# =====================================================================
with tab_admin:
    st.title("⚙️ Control de Inventario")
    
    # Input de seguridad para la contraseña
    password_input = st.text_input("Introduce la contraseña de Administrador", type="password")
    
    if password_input == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        st.write("Apaga o prende los productos. Los cambios se aplican inmediatamente para los clientes.")
        
        # Mostrar los interruptores organizados por categorías
        for categoria, productos in MENU.items():
            st.markdown(f"### {categoria}")
            for prod in productos.keys():
                # Crear un interruptor (toggle) por cada producto
                estado_actual = st.session_state.inventario.get(prod, True)
                
                # El switch cambia el estado directamente en st.session_state
                nuevo_estado = st.toggle(f"Disponible: {prod}", value=estado_actual, key=f"switch_{prod}")
                st.session_state.inventario[prod] = nuevo_estado
                
        st.info("💡 Consejo: Si apagas todos los productos de una categoría (ej. todos los desayunos), la sección completa desaparecerá para el cliente.")
    
    elif password_input != "":
        st.error("Contraseña incorrecta. Acceso denegado.")
