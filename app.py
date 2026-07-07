import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import urllib.parse

# 1. Configuraci贸n de la p谩gina
st.set_page_config(page_title="La Ventanita - Pedidos", page_icon="馃ォ", layout="centered")

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stCheckbox { margin-bottom: 0px; }
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 2. Conexi贸n a Google Sheets
@st.cache_data(ttl=15)
def cargar_datos():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('Carniceria').worksheet('Hoja 1')
    return sheet.get_all_records()

try:
    data = cargar_datos()
except Exception as e:
    st.error("Error al conectar con la base de datos. Verifica tus credenciales.")
    data = []

# 3. Encabezado
st.title("馃ォ Carnicer铆a La Ventanita")
st.subheader("Haz tu pedido de forma f谩cil y r谩pida")
st.write("---")

if data:
    st.markdown("### 馃洅 Productos Disponibles:")
    st.caption("Selecciona lo que necesites, elige c贸mo pedirlo (Kilos o Pesos) y pon la cantidad:")
    
    pedido_activo = {}
    
    for row in data:
        if str(row.get('Disponible', '')).upper() == 'TRUE':
            producto = row.get('Producto', 'Producto sin nombre')
            precio_raw = str(row.get('Precio') or row.get('precio') or row.get('PRECIO') or '')
            
            # Limpiamos si viene con doble signo de pesos por error en el Excel
            precio = precio_raw.replace('$$', '$').strip()
            
            # Formato de texto para el producto y precio
            texto_producto = f"**{producto}**"
            if precio:
                # Si el precio no trae signo de pesos, se lo ponemos
                formato_precio = precio if precio.startswith('$') else f"${precio}"
                texto_producto += f"   *( {formato_precio} / kg )*"
            
            col_check, col_tipo, col_cant = st.columns([1.5, 1.2, 1.3])
            
            with col_check:
                seleccionado = st.checkbox(texto_producto, key=f"check_{producto}")
            
            if seleccionado:
                with col_tipo:
                    tipo_pedido = st.selectbox(
                        "驴C贸mo pides?",
                        ["Por Kilos", "Por Dinero ($)"],
                        key=f"tipo_{producto}",
                        label_visibility="collapsed"
                    )
                
                with col_cant:
                    if tipo_pedido == "Por Kilos":
                        cantidad = st.selectbox(
                            "Kilos:",
                            ["1/2 kg", "1 kg", "1.5 kg", "2 kg", "2.5 kg", "3 kg", "Otro"],
                            key=f"cant_kg_{producto}",
                            label_visibility="collapsed"
                        )
                        pedido_activo[producto] = f"{cantidad}"
                    else:
                        pesos = st.text_input(
                            "Pesos:",
                            placeholder="$ 驴Cu谩nto?",
                            key=f"cant_mxn_{producto}",
                            label_visibility="collapsed"
                        )
                        if pesos:
                            formato_pesos = pesos if pesos.startswith('$') else f"${pesos}"
                            pedido_activo[producto] = f"{formato_pesos} pesos"
                        else:
                            pedido_activo[producto] = "Cantidad por definir"
            
            st.write("") 
            
    st.write("---")
    
    # NUEVO: Secci贸n de Resumen en Tiempo Real
    if pedido_activo:
        st.markdown("### 馃摑 Resumen de tu Compra:")
        with st.container(border=True): # Hace un recuadro limpio para el resumen
            for prod, cant in pedido_activo.items():
                st.write(f"鈥?**{prod}**: {cant}")
        st.write("---")
    
    # 4. Datos del Cliente
    st.markdown("### 馃搵 Tus Datos:")
    nombre = st.text_input("Tu Nombre:", placeholder="Ej. Aurora")
    notas = st.text_area("Notas adicionales:", placeholder="Ej. El bisteck bien delgadito, el pastor con pi帽a...")
    
    if st.button("Enviar Pedido por WhatsApp 馃摬", type="primary"):
        if not nombre:
            st.warning("Por favor, ingresa tu nombre antes de enviar.")
        elif not pedido_activo:
            st.warning("Selecciona al menos un producto.")
        else:
            productos_texto = ""
            for prod, cant in pedido_activo.items():
                productos_texto += f"- {prod}: *{cant}*\n"
                
            mensaje_wa = f"隆Hola! Quiero hacer un pedido en La Ventanita:\n\n馃懁 *Cliente:* {nombre}\n\n馃ォ *Pedido:*\n{productos_texto}"
            
            if notes := notas.strip():
                mensaje_wa += f"\n馃摑 *Notas:* {notes}"
            
            mi_numero = "525574977297" 
            
            mensaje_codificado = urllib.parse.quote(mensaje_wa)
            url_whatsapp = f"https://wa.me/{mi_numero}?text={mensaje_codificado}"
            
            st.success("隆Pedido listo!")
            st.markdown(f'<a href="{url_whatsapp}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #25D366; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">馃摬 Enviar por WhatsApp</a>', unsafe_allow_html=True)
else:
    st.info("No hay productos disponibles por el momento o se est谩 actualizando el inventario.")
