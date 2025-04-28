from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2

# Crear la aplicación Flask
app = Flask(__name__)

# Conexión a la base de datos PostgreSQL
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

    elif incoming_msg_lower in ['1', '1.', 'uno', 'ver casas']:
        if cursor:
            cursor.execute("""
                SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                       num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos
                FROM propiedades
                ORDER BY id ASC
            """)
            propiedades = cursor.fetchall()
            response = "🏡 Casas disponibles:\n"
            for prop in propiedades:
                (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad,
                 num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos) = prop

                response += (
                    f"\n🏠 {titulo}\n"
                    f"🖋 {descripcion}\n"
                    f"📍 Ubicación: {ubicacion}\n"
                    f"📄 Tipo: {tipo} | Estado: {estado}\n"
                    f"👫‍👩 Edad de la propiedad: {edad} años\n"
                    f"🛏️ Recámaras: {num_recamaras} | 🚿 Baños: {num_banios} | 🚗 Estacionamientos: {num_estacionamientos}\n"
                    f"🌊 Superficie de terreno: {superficie_terreno if superficie_terreno else 'No especificado'} m²\n"
                    f"🛏️ M² Construidos: {mtrs_construidos if mtrs_construidos else 'No especificado'} m²\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                    f"🌐 Modalidad: {modalidad}\n"
                )
            response += "\n✅ Si te interesa alguna, responde 'comprar casa'"
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower in ['2', '2.', 'dos', 'ver terrenos']:
        if cursor:
            cursor.execute("""
                SELECT ubicacion, descripcion, precio, superficie, documento
                FROM terrenos
                ORDER BY id ASC
            """)
            terrenos = cursor.fetchall()
            response = "🌳 Terrenos disponibles:\n"
            for terreno in terrenos:
                ubicacion, descripcion, precio, superficie, documento = terreno
                response += (
                    f"\n🌳 {ubicacion}\n"
                    f"🖋 {descripcion}\n"
                    f"📈 Superficie: {superficie} m²\n"
                    f"📄 Documento: {documento}\n"
                    f"💵 Precio: ${precio:,.2f} MXN\n"
                )
            response += "\n✅ Si te interesa alguno, responde 'comprar terreno'"
        else:
            response = "⚠️ Error de conexión a la base de datos."

    elif incoming_msg_lower in ['comprar casa', 'comprar terreno']:
        response = (
            "📝 ¡Excelente! Para ponernos en contacto contigo, por favor envíanos:\n\n"
            "1. Tu nombre completo\n"
            "2. Tu número de teléfono\n"
            "3. Tu correo electrónico\n"
            "4. Forma de pago: ¿Infonavit o Contado? 💼"
        )

    elif incoming_msg_lower.startswith('mi nombre es'):
        if cursor:
            nombre = incoming_msg.replace('mi nombre es', '').strip().title()
            cursor.execute("INSERT INTO clientes (nombre, fecha_registro) VALUES (%s, NOW())", (nombre,))
            conn.commit()
            response = "👏 Datos recibidos correctamente. Un asesor se pondrá en contacto contigo pronto. 📞"
        else:
            response = "⚠️ Error de conexión para guardar tus datos."

    elif incoming_msg_lower in ['3', '3.', 'tres', 'contactar asesor', 'contactar a un asesor']:
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
