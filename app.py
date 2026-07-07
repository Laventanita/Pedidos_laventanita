import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
            # Convertimos a texto y a mayúsculas para comparar fácilmente
            texto_disponible = str(val_disponible).strip().upper()
            
            if texto_disponible in ["SI", "TRUE"] or val_disponible is True:
                productos_disponibles.append(p)
        
        if not productos_disponibles:
            st.info("No hay productos disponibles por el momento o se está actualizando el inventario.")
        else:
            # Mostrar la lista de productos en la interfaz
            for prod in productos_disponibles:
                nombre = prod.get("Producto", "Sin nombre")
                precio = prod.get("Precio", 0)
                
                st.markdown(f"""
                <div class="producto-card">
                    <h4 style='margin:0; color:#ff4b4b;'>{nombre}</h4>
                    <p style='margin:5px 0 0 0; color:#8b949e;'>Precio: {precio}</p>
                </div>
                """, unsafe_allow_html=True)
                
    except Exception as e:
        st.error("Error al leer los datos de la hoja de cálculo.")
