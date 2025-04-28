from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import psycopg2

# Conexión a la base de datos PostgreSQL
conn = psycopg2.connect(
    host="dpg-d07dj7s9c44c739strhg-a",
    database="db_inmobiliaria_59oj",
    user="db_inmobiliaria_59oj_user",
    password="BCLBs5e4e9SgG6tl3Ckkq7Lg7GHlU0sw",
    port="5432",
    sslmode='require'
)
cursor = conn.cursor()

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hola' in incoming_msg:
        response = ("\ud83d\udc4b \u00a1Hola! Bienvenido a nuestro asesor virtual inmobiliario.\n\n"
                    "\ud83c\udfe0 1. Ver casas\n"
                    "\ud83c\udf33 2. Ver terrenos\n"
                    "\ud83d\udcde 3. Contactar a un asesor")

    elif incoming_msg == '1':
        cursor.execute("SELECT titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad, num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos FROM propiedades ORDER BY id ASC")
        propiedades = cursor.fetchall()
        response = "\ud83c\udfe1 Casas disponibles:\n"
        for prop in propiedades:
            (titulo, descripcion, precio, modalidad, ubicacion, tipo, estado, edad, num_recamaras, num_banios, num_estacionamientos, superficie_terreno, mtrs_construidos) = prop
            response += (f"\n\ud83c\udfe0 {titulo}\n"
                         f"\ud83d\udd8a\ufe0f {descripcion}\n"
                         f"\ud83d\udccd Ubicaci\u00f3n: {ubicacion}\n"
                         f"\ud83d\udcc4 Tipo: {tipo} | Estado: {estado}\n"
                         f"\ud83d\udc6b\u200d\ud83d\udc69 Edad de la propiedad: {edad} a\u00f1os\n"
                         f"\ud83d\udecf\ufe0f Rec\u00e1maras: {num_recamaras} | \ud83d\udebf Ba\u00f1os: {num_banios} | \ud83d\ude97 Estacionamientos: {num_estacionamientos}\n"
                         f"\ud83c\udf0a Superficie de terreno: {superficie_terreno if superficie_terreno else 'No especificado'} m\u00b2\n"
                         f"\ud83d\udecf\ufe0f M\u00b2 Construidos: {mtrs_construidos if mtrs_construidos else 'No especificado'} m\u00b2\n"
                         f"\ud83d\udcb5 Precio: ${precio:,.2f} MXN\n"
                         f"\ud83c\udf10 Modalidad: {modalidad}\n")
        response += "\n\u2705 Si te interesa alguna, responde 'comprar casa'"

    elif incoming_msg == '2':
        cursor.execute("SELECT ubicacion, descripcion, precio, superficie, documento FROM terrenos ORDER BY id ASC")
        terrenos = cursor.fetchall()
        response = "\ud83c\udf33 Terrenos disponibles:\n"
        for terreno in terrenos:
            ubicacion, descripcion, precio, superficie, documento = terreno
            response += (f"\n\ud83c\udf33 {ubicacion}\n"
                         f"\ud83d\udd8a\ufe0f {descripcion}\n"
                         f"\ud83d\udcc8 Superficie: {superficie} m\u00b2\n"
                         f"\ud83d\udcc4 Documento: {documento}\n"
                         f"\ud83d\udcb5 Precio: ${precio:,.2f} MXN\n")
        response += "\n\u2705 Si te interesa alguno, responde 'comprar terreno'"

    elif incoming_msg == 'comprar casa' or incoming_msg == 'comprar terreno':
        response = ("\ud83d\udcdd \u00a1Excelente! Para ponernos en contacto contigo, por favor env\u00edanos:\n\n"
                    "1. Tu nombre completo\n"
                    "2. Tu n\u00famero de tel\u00e9fono\n"
                    "3. Tu correo electr\u00f3nico\n"
                    "4. Forma de pago: \u00bfInfonavit o Contado? \ud83d\udcbc")

    elif incoming_msg.startswith('mi nombre es'):
        nombre = incoming_msg.replace('mi nombre es ', '').strip().title()
        cursor.execute("INSERT INTO clientes (nombre, fecha_registro) VALUES (%s, NOW())", (nombre,))
        conn.commit()
        response = "\ud83d\udc4f Datos recibidos correctamente. Un asesor se pondr\u00e1 en contacto contigo pronto. \ud83d\udcde"

    elif incoming_msg == '3':
        cursor.execute("SELECT nombre, telefono FROM asesores LIMIT 1")
        asesor = cursor.fetchone()
        nombre, telefono = asesor
        response = (f"\ud83d\udcde Asesor disponible:\n\n"
                    f"\ud83d\udc64 Nombre: {nombre}\n"
                    f"\ud83d\udcde Tel\u00e9fono: {telefono}\n\n"
                    "\ud83d\udc47 Puedes llamarlo directamente o enviarle un WhatsApp.")

    else:
        response = ("\ud83e\udd14 No entend\u00ed tu mensaje.\n"
                    "\u2709\ufe0f Por favor responde 'hola' para ver las opciones disponibles.")

    msg.body(response)
    return str(resp)

if __name__ == '__main__':
    app.run(port=5000)
