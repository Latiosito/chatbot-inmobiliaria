from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

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
    print("❌ Error de conexión a la base de datos:")
    print(e)
    conn = None
    cursor = None

esperando_datos = {}
progreso_usuario = {}  # para manejar la paginación por usuario

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    from_number = request.values.get('From', '')
    resp = MessagingResponse()
    msg = resp.message()

    global esperando_datos, progreso_usuario

    # Registrar avance
    if from_number not in progreso_usuario:
        progreso_usuario[from_number] = {"casas": 0, "terrenos": 0}

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
                response = "✅ Gracias, en un momento lo contactará un asesor."
                esperando_datos[from_number] = None
            except Exception as e:
                response = f"⚠ Error al guardar tus datos: {e}"
        else:
            response = "⚠ Por favor, envía tus datos como:\nMi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado"
        msg.body(response)
        return str(resp)

    if 'hola' in incoming_msg_lower:
        esperando_datos[from_number] = None
        progreso_usuario[from_number] = {"casas": 0, "terrenos": 0}
        response = (
            "👋 ¡Hola! Bienvenido a nuestro asesor virtual inmobiliario.\n\n"
            "🏠 1. Ver casas\n"
            "🌳 2. Ver terrenos\n"
            "📞 3. Contactar a un asesor"
        )

    elif incoming_msg_lower in ['1', 'ver casas', 'más casas']:
        try:
            offset = progreso_usuario[from_number]["casas"]
            if offset >= 4:
                response = "🔁 Has llegado al límite de propiedades mostradas. Escribe 'hola' para reiniciar."
            else:
                cursor.execute(f"""
                    SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                           num_recamaras, num_banios, num_estacionamientos, superficie_terreno,
                           mtrs_construidos, pdf_url
                    FROM propiedades
                    ORDER BY id ASC
                    OFFSET {offset} LIMIT 1
                """)
                casa = cursor.fetchone()
                if casa:
                    progreso_usuario[from_number]["casas"] += 1
                    (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                     num_recamaras, num_banios, num_estacionamientos, superficie_terreno,
                     mtrs_construidos, pdf_url) = casa

                    response = (
                        f"🏠 {titulo}\n"
                        f"🖊 {descripcion}\n"
                        f"📍 Ubicación: {ubicacion}\n"
                        f"📄 Tipo: {tipo} | Estado: {estado}\n"
                        f"👫 Edad: {edad} años\n"
                        f"🛏 Recámaras: {num_recamaras} | 🚿 Baños: {num_banios} | 🚗 Estacionamientos: {num_estacionamientos}\n"
                        f"🌊 Terreno: {superficie_terreno or 'No especificado'} m²\n"
                        f"🏗 Construcción: {mtrs_construidos or 'No especificado'} m²\n"
                        f"💵 Precio: ${precio:,.2f} MXN\n"
                        f"🌐 Modalidad: {modalidad}\n"
                        f"📎 Más detalles: {pdf_url}"
                    )
                    response += "\n\n✅ Escribe 'más casas' para ver otra o 'comprar casa' para registrar tus datos."
                else:
                    response = "❌ No hay más propiedades registradas."
        except Exception as e:
            response = f"⚠ Error al consultar casas: {e}"

    elif incoming_msg_lower in ['2', 'ver terrenos', 'más terrenos']:
        try:
            offset = progreso_usuario[from_number]["terrenos"]
            if offset >= 4:
                response = "🔁 Has llegado al límite de terrenos mostrados. Escribe 'hola' para reiniciar."
            else:
                cursor.execute(f"""
                    SELECT ubicacion, descripcion, precio, superficie, documento, pdf_url
                    FROM terrenos
                    ORDER BY id ASC
                    OFFSET {offset} LIMIT 1
                """)
                terreno = cursor.fetchone()
                if terreno:
                    progreso_usuario[from_number]["terrenos"] += 1
                    ubicacion, descripcion, precio, superficie, documento, pdf_url = terreno
                    response = (
                        f"🌳 {ubicacion}\n"
                        f"🖊 {descripcion}\n"
                        f"📏 Superficie: {superficie} m²\n"
                        f"📄 Documento: {documento}\n"
                        f"💵 Precio: ${precio:,.2f} MXN\n"
                        f"📎 Más detalles: {pdf_url}"
                    )
                    response += "\n\n✅ Escribe 'más terrenos' para ver otro o 'comprar terreno' para registrar tus datos."
                else:
                    response = "❌ No hay más terrenos registrados."
        except Exception as e:
            response = f"⚠ Error al consultar terrenos: {e}"

    elif incoming_msg_lower == 'comprar casa':
        esperando_datos[from_number] = 'casa'
        response = (
            "📝 ¡Perfecto! Por favor envíanos tus datos así:\n\n"
            "Mi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado"
        )

    elif incoming_msg_lower == 'comprar terreno':
        esperando_datos[from_number] = 'terreno'
        response = (
            "📝 ¡Perfecto! Por favor envíanos tus datos así:\n\n"
            "Mi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado"
        )

    elif incoming_msg_lower in ['3', 'asesor', 'contactar asesor']:
        try:
            cursor.execute("SELECT nombre, telefono FROM asesores LIMIT 1")
            asesor = cursor.fetchone()
            if asesor:
                nombre, telefono = asesor
                response = (
                    f"📞 Asesor disponible:\n\n"
                    f"👤 Nombre: {nombre}\n"
                    f"📞 Teléfono: {telefono}\n"
                    "👇 Puedes llamarlo directamente o enviarle un WhatsApp."
                )
            else:
                response = "⚠ No hay asesores disponibles en este momento."
        except Exception as e:
            response = f"⚠ Error al buscar asesor: {e}"

    else:
        response = (
            "🤔 No entendí tu mensaje.\n"
            "✉ Por favor responde 'hola' para ver las opciones disponibles."
        )

    msg.body(response)
    return str(resp)

if __name__ == '__main__':
    app.run(port=5000)
