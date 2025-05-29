from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2
import re
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Conexión a la base de datos
try:
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        sslmode='require'
    )
    cursor = conn.cursor()
    print("✅ Conexión exitosa a la base de datos.")
except Exception as e:
    print("❌ Error de conexión a la base de datos:", e)
    conn = None
    cursor = None

esperando_datos = {}

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    global esperando_datos

    if from_number in esperando_datos and esperando_datos[from_number]:
        datos = incoming_msg.strip()
        match = re.match(r".*?nombre es (.*?),.*?tel.*?(\d{7,15}),.*?correo es (.*?@.*?),(.*)", datos, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip().title()
            telefono = match.group(2).strip()
            email = match.group(3).strip()
            interes = 'compra de propiedad' if esperando_datos[from_number] == 'casa' else 'compra de terreno'
            try:
                cursor.execute("""
                    INSERT INTO clientes (nombre, email, telefono, intereses, fecha_registro)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (nombre, email, telefono, interes))
                conn.commit()
                msg.body("✅ Gracias, en un momento lo contactará un asesor.")
                esperando_datos[from_number] = None
            except Exception as e:
                msg.body(f"⚠ Error al guardar tus datos: {e}")
        else:
            msg.body("⚠ Por favor, envía tus datos como:\nMi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado")
        return str(resp)

    if 'hola' in incoming_msg_lower:
        esperando_datos[from_number] = None
        msg.body(
            "👋 ¡Hola! Bienvenido a nuestro asesor virtual inmobiliario.\n\n"
            "🏠 1. Ver casas\n"
            "🌳 2. Ver terrenos\n"
            "📞 3. Contactar a un asesor"
        )

    elif incoming_msg_lower in ['1', '1.', 'uno', 'ver casas']:
        try:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno,
                       mtrs_construidos, pdf_url
                FROM propiedades
                ORDER BY id ASC
                LIMIT 2
            """)
            prop = cursor.fetchone()
            if prop:
                (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                 num_recamaras, num_banios, num_estacionamientos, superficie_terreno,
                 mtrs_construidos, pdf_url) = prop

                texto = (
                    f"🏠 {titulo}\n"
                    f"🖊 {descripcion}\n"
                    f"📍 Ubicación: {ubicacion}\n"
                    f"📄 Tipo: {tipo} | Estado: {estado}\n"
                    f"👫 Edad: {edad} años\n"
                    f"🛏 Recámaras: {num_recamaras} | 🚿 Baños: {num_banios} | 🚗 Estacionamientos: {num_estacionamientos}\n"
                    f"🌊 Terreno: {superficie_terreno} m² | 🏗 Construcción: {mtrs_construidos} m²\n"
                    f"💵 Precio: ${precio:,.2f} MXN | 🌐 Modalidad: {modalidad}\n"
                )
                if pdf_url:
                    texto += f"📎 Más detalles: {pdf_url}"
                msg.body(texto)
            else:
                msg.body("⚠ No hay casas registradas en este momento.")
        except Exception as e:
            msg.body("⚠ Error al consultar casas.")
            print("❌ Error:", e)

    elif incoming_msg_lower in ['2', '2.', 'dos', 'ver terrenos']:
        try:
            cursor.execute("""
                SELECT ubicacion, descripcion, precio, superficie, documento, pdf_url
                FROM terrenos
                ORDER BY id ASC
                LIMIT 2
            """)
            terreno = cursor.fetchone()
            if terreno:
                ubicacion, descripcion, precio, superficie, documento, pdf_url = terreno
                texto = (
                    f"🌳 {ubicacion}\n"
                    f"🖊 {descripcion}\n"
                    f"📏 Superficie: {superficie} m²\n"
                    f"📄 Documento: {documento}\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                )
                if pdf_url:
                    texto += f"📎 Más detalles: {pdf_url}"
                msg.body(texto)
            else:
                msg.body("⚠ No hay terrenos registrados en este momento.")
        except Exception as e:
            msg.body("⚠ Error al consultar terrenos.")
            print("❌ Error:", e)

    elif incoming_msg_lower in ['3', '3.', 'tres', 'asesor']:
        try:
            cursor.execute("SELECT nombre, telefono FROM asesores LIMIT 1")
            asesor = cursor.fetchone()
            if asesor:
                nombre, telefono = asesor
                msg.body(
                    f"📞 Asesor disponible:\n\n"
                    f"👤 Nombre: {nombre}\n"
                    f"📞 Teléfono: {telefono}\n\n"
                    "👇 Puedes llamarlo directamente o enviarle un WhatsApp."
                )
            else:
                msg.body("⚠ No hay asesores disponibles en este momento.")
        except Exception as e:
            msg.body("⚠ Error al consultar asesores.")
            print("❌ Error:", e)

    else:
        msg.body("🤔 No entendí tu mensaje.\n✉ Por favor responde 'hola' para ver las opciones disponibles.")

    return str(resp)

if __name__ == '__main__':
    app.run(port=5000)
