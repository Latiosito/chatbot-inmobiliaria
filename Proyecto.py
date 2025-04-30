from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2

app = Flask(__name__)

# Conexión a la base de datos
try:
    conn = psycopg2.connect(
        host="dpg-d07dj7s9c44c739strhg-a.oregon-postgres.render.com",
        database="db_inmobiliaria_59oj",
        user="db_inmobiliaria_59oj_user",
        password="BCLBs5e4e9SgG6tl3Ckkq7Lg7GHlU0sw",
        port="5432",
        sslmode='require'
    )
    cursor = conn.cursor()
except Exception as e:
    print(f"Error de conexión a la base de datos: {e}")
    conn = None
    cursor = None

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hola' in incoming_msg_lower:
        response = (
            "👋 ¡Hola! Bienvenido a nuestro asesor virtual inmobiliario.\n\n"
            "🏠 1. Ver casas\n"
            "🌳 2. Ver terrenos\n"
            "📞 3. Contactar a un asesor"
        )

    elif 'ver casas' in incoming_msg_lower or incoming_msg_lower in ['1', '1.', 'uno']:
        if cursor:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                       imagen_url
                FROM propiedades
                ORDER BY id ASC
                LIMIT 1
            """)
            propiedades = cursor.fetchall()
            response = "🏡 Casas disponibles:\n"
            for prop in propiedades:
                (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                 num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                 imagen_url) = prop

                detalle = (
                    f"\n🏠 {titulo}\n"
                    f"🖊️ {descripcion}\n"
                    f"📍 Ubicación: {ubicacion}\n"
                    f"📄 Tipo: {tipo} | Estado: {estado}\n"
                    f"👫 Edad: {edad} años\n"
                    f"🛌 Recámaras: {num_recamaras} | 🚿 Baños: {num_banios} | 🚗 Estacionamientos: {num_estacionamientos}\n"
                    f"🌊 Terreno: {superficie_terreno if superficie_terreno else 'No especificado'} m²\n"
                    f"🏗️ Construcción: {mtrs_construidos if mtrs_construidos else 'No especificado'} m²\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                    f"🌐 Modalidad: {modalidad}\n"
                )
                if imagen_url:
                    msg.media(imagen_url)
                response += detalle

            response += "\n📅 Para ver más casas, responde 'ver más casas'"
            response += "\n🏠 Para comprar esta casa, responde 'comprar casa'"
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower == 'ver más casas':
        if cursor:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                       imagen_url
                FROM propiedades
                ORDER BY id ASC OFFSET 1 LIMIT 3
            """)
            propiedades = cursor.fetchall()
            response = "🏠 Más casas disponibles:\n"
            for prop in propiedades:
                (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                 num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                 imagen_url) = prop

                detalle = (
                    f"\n🏠 {titulo}\n"
                    f"🖊️ {descripcion}\n"
                    f"📍 Ubicación: {ubicacion}\n"
                    f"📄 Tipo: {tipo} | Estado: {estado}\n"
                    f"👫 Edad: {edad} años\n"
                    f"🛌 Recámaras: {num_recamaras} | 🚿 Baños: {num_banios} | 🚗 Estacionamientos: {num_estacionamientos}\n"
                    f"🌊 Terreno: {superficie_terreno if superficie_terreno else 'No especificado'} m²\n"
                    f"🏗️ Construcción: {mtrs_construidos if mtrs_construidos else 'No especificado'} m²\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                    f"🌐 Modalidad: {modalidad}\n"
                )
                if imagen_url:
                    msg.media(imagen_url)
                response += detalle

            response += "\n📅 Para comprar una casa, responde 'comprar casa'"
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower == 'comprar casa' or incoming_msg_lower == 'comprar terreno':
        response = (
            "📝 ¡Perfecto! Para ayudarte mejor, envíanos los siguientes datos en un solo mensaje:\n\n"
            "Ejemplo: Mi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado"
        )

    elif incoming_msg_lower.startswith('mi nombre es'):
        try:
            datos = incoming_msg.replace('mi nombre es', '').strip()
            cursor.execute("INSERT INTO clientes (nombre, fecha_registro) VALUES (%s, NOW())", (datos,))
            conn.commit()
            response = "👏 Datos recibidos correctamente. Un asesor se pondrá en contacto contigo pronto. 📞"
        except:
            response = "⚠️ Ocurrió un error guardando tus datos. Inténtalo más tarde."

    elif 'ver terrenos' in incoming_msg_lower or incoming_msg_lower in ['2', '2.', 'dos']:
        if cursor:
            cursor.execute("""
                SELECT ubicacion, descripcion, precio, superficie, documento
                FROM terrenos
                ORDER BY id ASC
                LIMIT 4
            """)
            terrenos = cursor.fetchall()
            response = "🌳 Terrenos disponibles:\n"
            for terreno in terrenos:
                ubicacion, descripcion, precio, superficie, documento = terreno
                response += (
                    f"\n🌳 {ubicacion}\n"
                    f"🖊️ {descripcion}\n"
                    f"📊 Superficie: {superficie} m²\n"
                    f"📄 Documento: {documento}\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                )
            response += "\n📅 Para comprar un terreno, responde 'comprar terreno'"
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif 'asesor' in incoming_msg_lower or incoming_msg_lower in ['3', '3.', 'tres']:
        if cursor:
            cursor.execute("SELECT nombre, telefono FROM asesores LIMIT 1")
            asesor = cursor.fetchone()
            if asesor:
                nombre, telefono = asesor
                response = (
                    f"📞 Asesor disponible:\n\n"
                    f"👤 Nombre: {nombre}\n"
                    f"🔎 Teléfono: {telefono}\n\n"
                    "🔻 Puedes llamarlo directamente o enviarle un WhatsApp."
                )
            else:
                response = "⚠️ No hay asesores disponibles en este momento."
        else:
            response = "⚠️ Error de conexión a la base de datos."

    else:
        response = (
            "🤔 No entendí tu mensaje.\n"
            "✉️ Por favor responde 'hola' para ver las opciones disponibles."
        )

    msg.body(response)
    return str(resp)

if __name__ == '__main__':
    app.run(port=5000)
