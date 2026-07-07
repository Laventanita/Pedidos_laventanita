import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Carnicería La Ventanita", page_icon="🥩", layout="centered")

# Estilos CSS personalizados para modo oscuro elegante
st.markdown("""
    <style>
    .reportview-container { background: #111216; }
    .stHeader { color: #FFFFFF; }
    h1 { color: #FFFFFF; font-family: 'Arial'; font-weight: 700; }
    h3 { color: #EEEEEE; }
    .stCheckbox label { color: #FFFFFF !important; font-size: 18px !important; }
    div.stButton > button:first-child {
        background-color: #25D366;
        color: white;
        font-size: 20px;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        padding: 0.5rem 2rem;
        width: 100%;
    }
    div.stButton > button:first-child:hover {
        background-color: #128C7E;
        color: white;
    }
    .resumen-box {
        background-color: #1E1E24;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado de la app
st.title("🥩 Carnicería La Ventanita")
st.subheader("Haz tu pedido de forma fácil y rápida")
st.markdown("---")

# Función para conectar a Google Sheets usando los Secrets de Streamlit
def conectar_base_datos():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Mapeo directo de los secretos cargados en formato TOML
        prod_secrets = st.secrets["gspread"]
        
        info_claves = {
            "type": prod_secrets["type"],
            "project_id": prod_secrets["project_id"],
            "private_key_id": prod_secrets["private_key_id"],
            "private_key": prod_secrets["private_key"].replace('\\n', '\n'),
            "client_email": prod_secrets["client_email"],
            "client_id": prod_secrets["client_id"],
            "auth_uri": prod_secrets["auth_uri"],
            "token_uri": prod_secrets["token_uri"],
            "auth_provider_x509_cert_url": prod_secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": prod_secrets["client_x509_cert_url"],
            "universe_domain": prod_secrets["universe_domain"]
        }
        
        creds = Credentials.from_service_account_info(info_claves, scopes=scope)
        cliente = gspread.authorize(creds)
        # Abre tu documento de Excel en Drive En la nube
        sheet = cliente.open("La Ventanita").sheet1
        return sheet
    except Exception as e:
        return None

# Intentar conectar
sheet = conectar_base_datos()

if sheet is None:
    st.error("Error al conectar con la base de datos. Verifica la configuración de Secrets.")
    st.info("No hay productos disponibles por el momento o se está actualizando el inventario.")
else:
    # Leer los datos del inventario (omitimos la fila de títulos)
    data = sheet.get_all_records()
    
    st.write("### 🛒 Productos Disponibles:")
    st.write("Selecciona lo que necesites, elige cómo pedirlo (Kilos o Pesos) y pon la cantidad:")
    
    pedido = {}
    
    # Recorrer productos del Excel dinámicamente
    for index, row in enumerate(data):
        producto = row.get("Producto", f"Producto {index+1}")
        precio = row.get("Precio", 0)
        disponible = str(row.get("Disponible", "SI")).strip().upper()
        
        if disponible == "SI":
            col1, col2, col3 = st.columns([2, 1.5, 1])
            
            with col1:
                # Checkbox para seleccionar el producto
                seleccionado = st.checkbox(f"{producto} ( ${precio:,.2f} / kg )", key=f"check_{index}")
            
            if seleccionado:
                with col2:
                    # Selectbox para decidir el tipo de medida
                    tipo_medida = st.selectbox("Pedir por:", ["Por Kilos (kg)", "Por Dinero ($)"], key=f"tipo_{index}")
                with col3:
                    # Entrada de texto para la cantidad o pesos
                    if tipo_medida == "Por Kilos (kg)":
                        cantidad = st.text_input("Cantidad:", value="1/2", key=f"cant_{index}")
                    else:
                        cantidad = st.text_input("¿Cuánto ($)?:", value="100", key=f"cant_{index}")
                
                pedido[producto] = {"tipo": tipo_medida, "valor": cantidad}

    st.markdown("---")
    
    # Mostrar el resumen de compra si hay algo seleccionado
    if pedido:
        st.write("### 📝 Resumen de tu Compra:")
        texto_resumen = "<div class='resumen-box'>"
        mensaje_whatsapp = "*¡Hola! Quiero hacer un pedido en La Ventanita:* \n\n"
        
        for prod, info in pedido.items():
            if "Kilos" in info["tipo"]:
                texto_resumen += f"• **{prod}:** {info['valor']} kg<br>"
                mensaje_whatsapp += f"• *{prod}:* {info['valor']} kg\n"
            else:
                texto_resumen += f"• **{prod}:** ${info['valor']} pesos<br>"
                mensaje_whatsapp += f"• *{prod}:* ${info['valor']} pesos\n"
                
        texto_resumen += "</div>"
        st.markdown(texto_resumen, unsafe_allow_html=True)
        
        # Datos del cliente
        st.write("### 📋 Tus Datos:")
        nombre_cliente = st.text_input("Tu Nombre:", value="")
        notas = st.text_input("Notas adicionales / dirección (si es a domicilio):", value="")
        
        if nombre_cliente:
            mensaje_whatsapp += f"\n*Cliente:* {nombre_cliente}"
        if notas:
            mensaje_whatsapp += f"\n*Notas:* {notas}"
            
        # Generar botón con enlace directo a WhatsApp
        texto_url = urllib.parse.quote(mensaje_whatsapp)
        # Tu número de WhatsApp de la carnicería listo
        numero_telefono = "525521404116" 
        url_whatsapp = f"https://wa.me/{numero_telefono}?text={texto_url}"
        
        st.write("")
        if st.button("🚀 Enviar Pedido por WhatsApp"):
            if not nombre_cliente:
                st.warning("Por favor ingresa tu nombre antes de enviar el pedido.")
            else:
                st.markdown(f"""
                    <meta http-equiv="refresh" content="0; url={url_whatsapp}">
                """, unsafe_allow_html=True)
