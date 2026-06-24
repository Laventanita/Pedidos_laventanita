import streamlit as st
import sqlite3
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA (ESTILO MÓVIL) ---
st.set_page_config(page_title="Menú Digital", page_icon="🌮", layout="centered")

# --- CREDENCIALES DE TELEGRAM (SEGURAS) ---
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

# --- FUNCIONES CORE ---

def init_db():
    """Inicializa la base de datos local para guardar los pedidos."""
    conn = sqlite3.connect('pedidos_negocio.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  fecha TEXT, 
                  nombre TEXT, 
                  telefono TEXT, 
                  direccion TEXT, 
                  pedido TEXT, 
                  total REAL, 
                  estado TEXT)''')
    conn.commit()
    conn.close()

def enviar_pedido_telegram(nombre, telefono, direccion, detalle, total):
    """Envía el formato del ticket a Telegram."""
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
    try:
        requests.post(url, json=payload)
    except Exception as e:
        st.error(f"Error al notificar a la cocina: {e}")

# Inicializar DB al arrancar
init_db()

# --- ESTRUCTURA DEL MENÚ (Precios actualizados) ---
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

# --- INTERFAZ DE USUARIO (FRONTEND) ---
st.title("La Ventanita & Tacos Mixi")
st.subheader("📱 Menú Digital")
st.write("Arma tu pedido aquí abajo y te lo llevamos hasta tu hogar.")

# Control del carrito mediante st.session_state
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}

# Renderizar el menú por categorías
for categoria, productos in MENU.items():
    with st.expander(f"{categoria}", expanded=True):
        for prod, precio in productos.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            col1.write(f"**{prod}**\n${precio:.2f}")
            
            # Botón añadir
            if col2.button("➕", key=f"add_{prod}"):
                st.session_state.carrito[prod] = st.session_state.carrito.get(prod, 0) + 1
            
            # Cantidad actual
            cant = st.session_state.carrito.get(prod, 0)
            col3.write(f"Cant: **{cant}**")

# --- SECCIÓN DEL CARRITO Y DATOS DE ENVÍO ---
total_cuenta = 0.0
detalle_ticket_telegram = ""

# Filtrar solo productos seleccionados
productos_seleccionados = {k: v for k, v in st.session_state.carrito.items() if v > 0}

if productos_selected := productos_seleccionados:
    st.markdown("---")
    st.subheader("🛒 Tu Pedido")
    
    for prod, cant in productos_selected.items():
        # Buscar el precio del producto en el diccionario MENU
        precio_unitario = next(precio for cat in MENU.values() for p, precio in cat.items() if p == prod)
        subtotal = precio_unitario * cant
        total_cuenta += subtotal
        
        st.write(f"• {cant}x {prod} — ${subtotal:.2f}")
        # Botón opcional para disminuir cantidad si se equivocan
        if st.button("❌ Quitar uno", key=f"del_{prod}"):
            st.session_state.carrito[prod] -= 1
            st.rerun()
            
        detalle_ticket_telegram += f"• {cant}x {prod}\n"
        
    st.markdown(f"### **Total a pagar: ${total_cuenta:.2f}**")
    
    st.markdown("---")
    st.subheader("📍 Datos para la Entrega")
    
    # Formulario final
    with st.form("formulario_envio", clear_on_submit=True):
        nombre_cli = st.text_input("Nombre Completo *")
        telefono_cli = st.text_input("Teléfono de Contacto *")
        direccion_cli = st.text_area("Dirección Completa (Calle, Número, Colonia, Referencias) *")
        
        enviar_pedido = st.form_submit_button("🚀 Confirmar y Enviar Pedido")
        
        if enviar_pedido:
            if nombre_cli and telefono_cli and direccion_cli:
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 1. Guardar en SQLite
                conn = sqlite3.connect('pedidos_negocio.db')
                c = conn.cursor()
                c.execute("""INSERT INTO pedidos (fecha, nombre, telefono, direccion, pedido, total, estado) 
                             VALUES (?, ?, ?, ?, ?, ?, ?)""",
                          (fecha_actual, nombre_cli, telefono_cli, direccion_cli, detalle_ticket_telegram, total_cuenta, "Pendiente"))
                conn.commit()
                conn.close()
                
                # 2. Desparar alerta a Telegram
                enviar_pedido_telegram(nombre_cli, telefono_cli, direccion_cli, detalle_ticket_telegram, total_cuenta)
                
                st.success("¡Tu pedido ha sido enviado a la cocina con éxito! Va en camino.")
                
                # Limpiar carrito
                st.session_state.carrito = {}
                st.rerun()
            else:
                st.error("Por favor rellena todos los campos obligatorios (*)")
else:
    st.info("El carrito está vacío. Agrega tus platillos usando el botón ➕ de arriba.")
