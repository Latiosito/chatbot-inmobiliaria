from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2

app = Flask(__name__)
offset_casas = 0

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
    global offset_casas
    incoming_msg = request.values.get('Body', '').strip()
    incoming_msg_lower = incoming_msg.lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hola' in incoming_msg_lower:
        offset_casas = 0
        response = (
            "👋 ¡Hola! Bienvenido a nuestro asesor virtual inmobiliario.\n\n"
            "🏠 1. Ver casas\n"
            "🌳 2. Ver terrenos\n"
            "📞 3. Contactar a un asesor"
        )

    elif 'ver casas' in incoming_msg_lower or incoming_msg_lower in ['1', '1.', 'uno']:
        offset_casas = 0
        if cursor:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                       imagen_url
                FROM propiedades
                ORDER BY id ASC
                OFFSET %s LIMIT 1
            """, (offset_casas,))
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
                    "\n📅 Para ver más casas, responde 'ver más casas'\n"
                    "🛒 Para comprar esta casa, responde 'comprar casa'"
                )
                if imagen_url:
                    msg.media(imagen_url)
                response += detalle
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower == 'ver más casas':
        offset_casas += 1
        if cursor:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos,
                       imagen_url
                FROM propiedades
                ORDER BY id ASC
                OFFSET %s LIMIT 1
            """, (offset_casas,))
            propiedades = cursor.fetchall()
            if not propiedades:
                response = "🏁 Ya no hay más casas disponibles."
            else:
                response = "🏡 Más casas disponibles:\n"
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
                        "\n📅 Para ver más casas, responde 'ver más casas'\n"
                        "🛒 Para comprar esta casa, responde 'comprar casa'"
                    )
                    if imagen_url:
                        msg.media(imagen_url)
                    response += detalle
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower in ['comprar casa', 'comprar terreno']:
        interes = 'casa' if 'casa' in incoming_msg_lower else 'terreno'
        msg.session = {'interes': interes}
        response = (
            "📝 ¡Perfecto! Para ayudarte mejor, envíanos los siguientes datos en un solo mensaje:\n\n"
            "Ejemplo:\nMi nombre es Juan Pérez, mi tel es 7441234567, mi correo es juan@mail.com, pago contado"
        )

    elif incoming_msg_lower.startswith('mi nombre es'):
        try:
            texto = incoming_msg.replace('Mi nombre es', '', 1).strip()
            partes = [p.strip() for p in texto.split(',')]
            nombre = partes[0]
            telefono = partes[1].replace('mi tel es', '').strip()
            email = partes[2].replace('mi correo es', '').strip()
            forma_pago = partes[3]

            cursor.execute("""
                INSERT INTO clientes (nombre, telefono, email, intereses, fecha_registro)
                VALUES (%s, %s, %s, %s, NOW())
            """, (nombre.title(), telefono, email.lower(), forma_pago.title()))
            conn.commit()
            response = "✅ Gracias, en un momento un asesor se contactará contigo. 📞"
        except Exception as e:
            print(f"Error insertando cliente: {e}")
            response = "⚠️ No se pudieron guardar tus datos. Asegúrate de seguir el formato del ejemplo."

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
                    f"📏 Superficie: {superficie} m²\n"
                    f"📄 Documento: {documento}\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                )
            response += "\n🛒 Para comprar un terreno, responde 'comprar terreno'"
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
                    f"📞 Teléfono: {telefono}\n\n"
                    "👇 Puedes llamarlo directamente o enviarle un WhatsApp."
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
