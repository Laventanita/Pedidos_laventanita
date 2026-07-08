import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import urllib.parse
import requests

# Configuración de la página
st.set_page_config(page_title="Carnicería La Ventanita", page_icon="🥩", layout="centered")

# Estilos CSS
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
}
h1, h2, h3 {
    color: #ffffff !important;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}
.resumen-box {
    background-color: #1f2937;
    padding: 20px;
    border-radius: 10px;
    border: 1px solid #4b5563;
    margin-top: 15px;
    margin-bottom: 15px;
}
div.stButton > button, div.stLinkButton > a {
    background-color: #25D366 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
    width: 100% !important;
    padding: 12px !important;
    border-radius: 5px !important;
    text-align: center !important;
    text-decoration: none !important;
    display: inline-block !important;
}
div.stButton > button:hover, div.stLinkButton > a:hover {
    background-color: #128C7E !important;
}
</style>
""", unsafe_allow_html=True)

# Encabezado
st.title("🥩 Carnicería La Ventanita")
st.subheader("Haz tu pedido de forma fácil y rápida")
st.markdown("---")

# Función para enviar notificación espejo a Telegram
def enviar_a_telegram(mensaje):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": mensaje
        }
        requests.post(url, json=payload)
    except Exception as e:
        pass

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
        client_sheet = client.open("Carniceria").sheet1
        return client_sheet
    except Exception as e:
        return None

sheet = conectar_base_datos()

if sheet is None:
    st.error("Error al conectar con la base de datos. Verifica la configuración de Secrets.")
else:
    try:
        datos = sheet.get_all_records()
        
        try:
            envio_raw = sheet.acell('E2').value
            envio_limpio = str(envio_raw).replace("$", "").replace(",", "").strip()
            costo_envio_base = float(envio_limpio)
        except Exception:
            costo_envio_base = 20.0
        
        productos_disponibles = []
        for p in datos:
            val_disponible = p.get("Disponible", "")
            texto_disponible = str(val_disponible).strip().upper()
            if texto_disponible in ["SI", "TRUE"] or val_disponible is True:
                productos_disponibles.append(p)
        
        if not productos_disponibles:
            st.info("No hay productos disponibles por el momento o se está actualizando el inventario.")
        else:
            st.write("### 📝 Configura tu Pedido")
            st.caption("Haz clic en cualquier producto para desplegar sus opciones de cantidad")
            
            pedido_usuario = {}
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
            
            for prod in productos_disponibles:
                nombre = prod.get("Producto", "Sin nombre")
                precio_raw = str(prod.get("Precio", 0)).replace("$", "").replace(",", "").strip()
                try:
                    precio = float(precio_raw)
                except ValueError:
                    precio = 0.0
                
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
                                index=3,
                                key=f"cant_kilos_{nombre}"
                            )
                            factor = opciones_kilos[medida_kilos]
                            costo_estimado = precio * factor
                            pedido_usuario[nombre] = {"tipo": "Kilos", "texto_cant": medida_kilos, "subtotal": costo_estimaged}
                            
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
            
            st.write("### 🛵 Tipo de Entrega y Pago")
            col_ent1, col_ent2 = st.columns([1, 1])
            with col_ent1:
                tipo_entrega = st.radio("Modalidad de entrega:", ["Entrega a domicilio", "Recoger en tienda"])
            
            COSTO_ENVIO = costo_envio_base if tipo_entrega == "Entrega a domicilio" else 0.0
            
            with col_ent2:
                metodo_pago = st.selectbox("Método de pago:", ["Efectivo", "Transferencia", "Tarjeta de Débito/Crédito"])

            st.write("### 🛒 Resumen de tu Compra")
            if not pedido_usuario:
                st.info("Aún no has agregado ningún producto a tu carrito.")
            else:
                html_resumen = '<div class="resumen-box">'
                subtotal_productos = 0.0
                for prod_nombre, detalle in pedido_usuario.items():
                    html_resumen += f"<p style='margin:5px 0; color:white;'>• <b>{prod_nombre}</b>: {detalle['texto_cant']} — <span style='color:#25D366;'>${detalle['subtotal']:,.2f}</span></p>"
                    subtotal_productos += detalle['subtotal']
                
                html_resumen += "<hr style='border-color:#4b5563;'>"
                html_resumen += f"<p style='margin:5px 0; color:#cbd5e1;'>Subtotal productos: <b>${subtotal_productos:,.2f}</b></p>"
                
                if tipo_entrega == "Entrega a domicilio":
                    html_resumen += f"<p style='margin:5px 0; color:#cbd5e1;'>Costo de envío a domicilio: <b>${COSTO_ENVIO:,.2f}</b></p>"
                else:
                    html_resumen += "<p style='margin:5px 0; color:#cbd5e1;'>Entrega: <b>Sin costo (Recoge en tienda)</b></p>"
                
                total_final = subtotal_productos + COSTO_ENVIO
                html_resumen += f"<h4 style='margin:10px 0 0 0; color:white; text-align:right;'>Total Estimado: <span style='color:#ff4b4b; font-size:22px;'>${total_final:,.2f}</span></h4>"
                html_resumen += '</div>'
                st.markdown(html_resumen, unsafe_allow_html=True)

            st.markdown("---")
            
            st.write("### 👤 Datos del Cliente")
            nombre_cliente = st.text_input("Nombre completo:")
            
            if tipo_entrega == "Entrega a domicilio":
                direccion_cliente = st.text_area("Dirección completa (Calle, Número, Colonia):")
            else:
                direccion_cliente = "N/A"
                
            notas_adicionales = st.text_input("Notas del pedido:")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.write("### 🤝 ¿Quién te recomendó?")
            
            lista_comisionistas = [
                "Ninguno (Venta Directa)", 
                "Ana", 
                "Aurora", 
                "Mary", 
                "Chayo"
            ]
            comisionista_seleccionado = st.selectbox(
                "Selecciona el nombre de la persona que te compartió la aplicación:",
                lista_comisionistas
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not nombre_cliente.strip():
                st.warning("Por favor, ingresa tu nombre completo.")
            elif tipo_entrega == "Entrega a domicilio" and not direccion_cliente.strip():
                st.warning("Por favor, ingresa tu dirección para el envío.")
            elif not pedido_usuario:
                st.info("Agrega productos para generar el botón de envío.")
            else:
                # Formato ultra compacto y plano para evitar errores de red en el móvil
                texto_mensaje = f"NUEVO PEDIDO LA VENTANITA\n"
                texto_mensaje += f"Recomendado por: {comisionista_seleccionado}\n"
                texto_mensaje += f"Cliente: {nombre_cliente.strip()}\n"
                texto_mensaje += f"Modalidad: {tipo_entrega}\n"
                if tipo_entrega == "Entrega a domicilio":
                    texto_mensaje += f"Direccion: {direccion_cliente.strip()}\n"
                texto_mensaje += f"Pago: {metodo_pago}\n"
                if notas_adicionales.strip():
                    texto_mensaje += f"Notas: {notas_adicionales.strip()}\n"
                
                texto_mensaje += f"\nPRODUCTOS:\n"
                subtotal_productos = 0.0
                for prod_nombre, detalle in pedido_usuario.items():
                    texto_mensaje += f"- {prod_nombre}: {detalle['texto_cant']}\n"
                    subtotal_productos += detalle['subtotal']
                
                total_final = subtotal_productos + COSTO_ENVIO
                texto_mensaje += f"\nTOTAL ESTIMADO: ${total_final:,.2f}"
                
                if st.session_state.get(f"enviado_{nombre_cliente}") is not True:
                    enviar_a_telegram(texto_mensaje)
                    st.session_state[f"enviado_{nombre_cliente}"] = True
                
                # quote_plus cambia espacios por '+' o '%20' de forma estricta, lo que digiere mejor WhatsApp Web
                mensaje_codificado = urllib.parse.quote_plus(texto_mensaje)
                
                telefono_recibe = "525574977297" 
                
                # Cambio al protocolo wa.me/ limpio
                url_whatsapp = f"https://wa.me/{telefono_recibe}?text={mensaje_codificado}"
                
                st.write("### 🎉 ¡Pedido Listo!")
                st.link_button("📱 ENVIAR PEDIDO POR WHATSAPP", url_whatsapp)
                
    except Exception as e:
        st.error("Error al leer los datos de la hoja de cálculo.")
