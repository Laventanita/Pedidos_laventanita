import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Carnicería La Ventanita", page_icon="🥩", layout="centered")

# Inyección de diseño CSS limpio
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}
h1, h2, h3 {
    color: #ffffff !important;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
/* Estilo personalizado para las tarjetas de resumen */
.resumen-box {
    background-color: #1f2937;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #4b5563;
    margin-top: 15px;
    margin-bottom: 15px;
}
div.stButton > button:first-child {
    background-color: #25D366;
    color: white;
    border: none;
    font-weight: bold;
    width: 100%;
    padding: 10px;
}
div.stButton > button:first-child:hover {
    background-color: #128C7E;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Encabezado de la aplicación
st.title("🥩 Carnicería La Ventanita")
st.subheader("Haz tu pedido de forma fácil y rápida")
st.markdown("---")

# Función para conectar a Google Sheets
def conectar_base_datos():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = {
            "type": st.secrets["gspread"]["type"],
            "project_id": st.secrets["gspread"]["project_id"],
            "private_key_id": st.secrets["gspread"]["private_key_id"],
            "private_key": st.secrets["gspread"]["private_key"],
            "client_email": st.secrets["gspread"]["client_email"],
            "client_id": st.secrets["gspread"]["client_id"],
            "auth_uri": st.secrets["gspread"]["auth_uri"],
            "token_uri": st.secrets["gspread"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gspread"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gspread"]["client_x509_cert_url"],
            "universe_domain": st.secrets["gspread"]["universe_domain"]
        }
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open("Carniceria").sheet1
        return sheet
    except Exception as e:
        return None

# Intentar obtener los datos
sheet = conectar_base_datos()

if sheet is None:
    st.error("Error al conectar con la base de datos. Verifica la configuración de Secrets.")
else:
    try:
        # Leer todas las filas de la hoja de cálculo
        datos = sheet.get_all_records()
        
        # Filtrar los productos aceptando "SI" o "TRUE"
        productos_disponibles = []
        for p in datos:
            val_disponible = p.get("Disponible", "")
            texto_disponible = str(val_disponible).strip().upper()
            if texto_disponible in ["SI", "TRUE"] or val_disponible is True:
                productos_disponibles.append(p)
        
        if not productos_disponibles:
            st.info("No hay productos disponibles por el momento o se está actualizando el inventario.")
        else:
            # --- SECCIÓN DEL FORMULARIO DE PEDIDO ---
            st.write("### 📝 Configura tu Pedido")
            st.caption("Haz clic en cualquier producto para desplegar sus opciones de cantidad")
            
            # Diccionario para almacenar lo que seleccione el usuario
            pedido_usuario = {}
            
            # Opciones de kilos
            opciones_kilos = {
                "1/4 kg (250g)": 0.25,
                "1/2 kg (500g)": 0.50,
                "3/4 kg (750g)": 0.75,
                "1 kg": 1.0,
                "1.5 kg": 1.5,
                "2 kg": 2.0,
                "2.5 kg": 2.5,
                "3 kg": 3.0,
                "4 kg": 4.0,
                "5 kg": 5.0
            }
            
            # Mostrar cada producto dentro de un menú desplegable (Acordeón)
            for prod in productos_disponibles:
                nombre = prod.get("Producto", "Sin nombre")
                
                # Limpiar el precio
                precio_raw = str(prod.get("Precio", 0)).replace("$", "").replace(",", "").strip()
                try:
                    precio = float(precio_raw)
                except ValueError:
                    precio = 0.0
                
                # Crear el menú desplegable (Expander) para cada producto
                with st.expander(f"➕ {nombre} — (Precio por Kg: ${precio:,.2f})"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        tipo_pedido = st.selectbox(
                            "¿Cómo quieres pedir?", 
                            ["No pedir", "Por Kilos", "Por Dinero ($)"], 
                            key=f"tipo_{nombre}"
                        )
                    with col2:
                        if tipo_pedido == "Por Kilos":
                            medida_kilos = st.selectbox(
                                "Selecciona el peso:",
                                list(opciones_kilos.keys()),
                                index=3,  # 1 kg por defecto
                                key=f"cant_kilos_{nombre}"
                            )
                            factor = opciones_kilos[medida_kilos]
                            costo_estimado = precio * factor
                            pedido_usuario[nombre] = {"tipo": "Kilos", "texto_cant": medida_kilos, "subtotal": costo_estimado}
                            
                        elif tipo_pedido == "Por Dinero ($)":
                            monto = st.number_input(
                                "Monto ($ MXN):", 
                                min_value=10, 
                                max_value=5000, 
                                value=100, 
                                step=10, 
                                key=f"cant_dinero_{nombre}"
                            )
                            pedido_usuario[nombre] = {"tipo": "Dinero", "texto_cant": f"${monto} pesos", "subtotal": float(monto)}

            st.markdown("---")
            
            # --- SECCIÓN: RESUMEN DEL PEDIDO EN PANTALLA ---
            st.write("### 🛒 Resumen de tu Compra")
            
            if not pedido_usuario:
                st.info("Aún no has agregado ningún producto a tu carrito.")
            else:
                html_resumen = '<div class="resumen-box">'
                total_pedido = 0.0
                
                for prod_nombre, detalle in pedido_usuario.items():
                    html_resumen += f"<p style='margin:5px 0; color:white;'>• <b>{prod_nombre}</b>: {detalle['texto_cant']} — <span style='color:#25D366;'>${detalle['subtotal']:,.2f}</span></p>"
                    total_pedido += detalle['subtotal']
                
                html_resumen += "<hr style='border-color:#4b5563;'>"
                html_resumen += f"<h4 style='margin:0; color:white; text-align:right;'>Total Estimado: <span style='color:#ff4b4b; font-size:22px;'>${total_pedido:,.2f}</span></h4>"
                html_resumen += '</div>'
                
                st.markdown(html_resumen, unsafe_allow_html=True)

            st.markdown("---")
            
            # --- SECCIÓN DE DATOS DEL CLIENTE Y MÉTODO DE PAGO ---
            st.write("### 👤 Datos de Entrega y Pago")
            nombre_cliente = st.text_input("Nombre completo:")
            direccion_cliente = st.text_area("Dirección completa (Calle, Número, Colonia):")
            
            # NUEVO: Selección de Método de Pago
            metodo_pago = st.selectbox(
                "Selecciona tu método de pago:",
                ["Efectivo", "Transferencia", "Tarjeta de Débito/Crédito"]
            )
            
            notas_adicionales = st.text_input("Notas del pedido (Ej: término de carne, empaque, etc.):")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- BOTÓN PARA ENVIAR POR WHATSAPP ---
            if st.button("📱 Enviar Pedido por WhatsApp"):
                if not nombre_cliente.strip() or not direccion_cliente.strip():
                    st.warning("Por favor, ingresa tu nombre y dirección antes de enviar.")
                elif not pedido_usuario:
                    st.warning("No has seleccionado ningún producto para tu pedido.")
                else:
                    # Construir el mensaje de WhatsApp
                    texto_mensaje = f"🥩 *NUEVO PEDIDO - CARNICERÍA LA VENTANITA*\n\n"
                    texto_mensaje += f"👤 *Cliente:* {nombre_cliente.strip()}\n"
                    texto_mensaje += f"📍 *Dirección:* {direccion_cliente.strip()}\n"
                    texto_mensaje += f"💳 *Método de Pago:* {metodo_pago}\n"
                    if notas_adicionales.strip():
                        texto_mensaje += f"📝 *Notas:* {notas_adicionales.strip()}\n"
                    
                    texto_mensaje += f"\n🛒 *DETALLE DEL PEDIDO:*\n"
                    
                    total_pedido = 0.0
                    for prod_nombre, detalle in pedido_usuario.items():
                        texto_mensaje += f"• {prod_nombre}: *{detalle['texto_cant']}* (${detalle['subtotal']:,.2f})\n"
                        total_pedido += detalle['subtotal']
                    
                    texto_mensaje += f"\n💰 *TOTAL ESTIMADO:* *${total_pedido:,.2f}*\n"
                    texto_mensaje += f"\n¡Muchas gracias por su preferencia! 🙏"
                    
                    # Codificar el texto para la URL
                    mensaje_codificado = urllib.parse.quote(texto_mensaje)
                    
                    # Recuerda cambiar este número por el tuyo oficial (52 + 10 dígitos)
                    telefono_recibe = "525574977297" 
                    
                    url_whatsapp = f"https://api.whatsapp.com/send?phone={telefono_recibe}&text={mensaje_codificado}"
                    
                    st.success("¡Pedido listo para ser enviado!")
                    st.markdown(f'<a href="{url_whatsapp}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:12px; font-weight:bold; width:100%; border-radius:5px; cursor:pointer;">👉 CLICK AQUÍ PARA RECONFIRMAR EN WHATSAPP</button></a>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error("Error al leer los datos de la hoja de cálculo.")
