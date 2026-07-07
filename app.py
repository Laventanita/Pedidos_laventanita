import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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
.producto-card {
    background-color: #161b22;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
    border: 1px solid #30363d;
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

# Función para conectar a Google Sheets usando los Secrets de Streamlit
def conectar_base_datos():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
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
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Abre la hoja de cálculo por su nombre exacto
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
        
        # Filtrar los productos aceptando "SI", "TRUE" o el valor lógico True
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
            
            # Diccionario para almacenar lo que seleccione el usuario
            pedido_usuario = {}
            
            # Mostrar cada producto con sus opciones de pedido
            for prod in productos_disponibles:
                nombre = prod.get("Producto", "Sin nombre")
                precio = prod.get("Precio", 0)
                
                with st.container():
                    st.markdown(f"""
                    <div class="producto-card">
                        <h4 style='margin:0; color:#ff4b4b;'>{nombre}</h4>
                        <p style='margin:5px 0 5px 0; color:#8b949e;'>Precio: {precio}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Columnas para tipo de medida (Kilos o Dinero) y la cantidad
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        tipo_pedido = st.selectbox(
                            f"Pedir por:", 
                            ["No pedir", "Por Kilos", "Por Dinero ($)"], 
                            key=f"tipo_{nombre}"
                        )
                    with col2:
                        if tipo_pedido == "Por Kilos":
                            cantidad = st.number_input(
                                "Cantidad (Kilos):", 
                                min_value=0.1, 
                                max_value=20.0, 
                                value=1.0, 
                                step=0.05, 
                                key=f"cant_{nombre}"
                            )
                            pedido_usuario[nombre] = {"tipo": "Kilos", "cantidad": cantidad}
                        elif tipo_pedido == "Por Dinero ($)":
                            cantidad = st.number_input(
                                "Monto ($ MXN):", 
                                min_value=10, 
                                max_value=5000, 
                                value=100, 
                                step=10, 
                                key=f"cant_{nombre}"
                            )
                            pedido_usuario[nombre] = {"tipo": "Dinero", "cantidad": cantidad}
                st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("---")
            
            # --- SECCIÓN DE DATOS DEL CLIENTE ---
            st.write("### 👤 Datos de Entrega")
            nombre_cliente = st.text_input("Nombre completo:")
            direccion_cliente = st.text_area("Dirección completa (Calle, Número, Colonia):")
            notas_adicionales = st.text_input("Notas del pedido (Ej: término de carne, etc.):")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- BOTÓN PARA ENVIAR POR WHATSAPP ---
            if st.button("📱 Enviar Pedido por WhatsApp"):
                # Validar que se hayan agregado productos y datos mínimos
                if not nombre_cliente.strip() or not direccion_cliente.strip():
                    st.warning("Por favor, ingresa tu nombre y dirección antes de enviar.")
                elif not pedido_usuario:
                    st.warning("No has seleccionado una cantidad válida para ningún producto.")
                else:
                    # Construir el mensaje de texto para WhatsApp
                    texto_mensaje = f"🥩 *NUEVO PEDIDO - CARNICERÍA LA VENTANITA*\n\n"
                    texto_mensaje += f"👤 *Cliente:* {nombre_cliente.strip()}\n"
                    texto_mensaje += f"📍 *Dirección:* {direccion_cliente.strip()}\n"
                    if notas_adicionales.strip():
                        texto_mensaje += f"📝 *Notas:* {notas_adicionales.strip()}\n"
                    
                    texto_mensaje += f"\n🛒 *DETALLE DEL PEDIDO:*\n"
                    
                    for prod_nombre, detalle in pedido_usuario.items():
                        if detalle["tipo"] == "Kilos":
                            texto_mensaje += f"• {prod_nombre}: *{detalle['cantidad']} Kilos*\n"
                        elif detalle["tipo"] == "Dinero":
                            texto_mensaje += f"• {prod_nombre}: *${detalle['cantidad']} pesos*\n"
                    
                    texto_mensaje += f"\n¡Muchas gracias por su preferencia! 🙏"
                    
                    # Codificar el texto para la URL de WhatsApp
                    mensaje_codificado = urllib.parse.quote(texto_mensaje)
                    
                    # Tu número de teléfono para recibir los pedidos (ejemplo: 52 + 10 dígitos)
                    # REEMPLAZA ESTE NÚMERO POR EL TUYO:
                    telefono_recibe = "5574977297" 
                    
                    url_whatsapp = f"https://api.whatsapp.com/send?phone={telefono_recibe}&text={mensaje_codificado}"
                    
                    # Mostrar enlace de redirección seguro
                    st.success("¡Pedido listo para ser enviado!")
                    st.markdown(f'<a href="{url_whatsapp}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:12px; font-weight:bold; width:100%; border-radius:5px; cursor:pointer;">👉 CLICK AQUÍ PARA RECONFIRMAR EN WHATSAPP</button></a>', unsafe_allow_html=True)
                
    except Exception as e:
        st.error("Error al leer los datos de la hoja de cálculo.")
