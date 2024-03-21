from flask import Flask, render_template, jsonify
from flask_mysqldb import MySQL
from config import config
import random
from datetime import datetime
import requests
import time
from threading import Thread

app = Flask(__name__)
conexion = MySQL(app)

def consumir_api(ingrediente):
    url = "https://microservices-utadeo-arq-fea471e6a9d4.herokuapp.com/api/v1/software-architecture/market-place"
    params = {"ingredient": ingrediente}

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if "data" in data and ingrediente in data["data"]:
                cantidad = data["data"][ingrediente]
                return cantidad
            else:
                return 0
        else:
            print("Error:", response.text)
            return None
    except Exception as e:
        print(f"Error al consumir la API: {e}")
        return None

def manejar_cola():
    while True:
        try:
            with app.app_context():
                with conexion.connection.cursor() as cursor:
                    cursor.execute("SELECT id, recetas_id FROM orden WHERE estado_id = 2")
                    ordenes = cursor.fetchall()

                    for orden_id, receta_id in ordenes:
                        cursor.execute("SELECT ingrediente, cantidad FROM ingrediente_receta INNER JOIN ingredientes ON ingrediente_receta.ingredientes_id = ingredientes.id WHERE recetas_id = %s", (receta_id,))
                        ingredientes_receta = cursor.fetchall()

                        ingredientes_suficientes = True
                        for ingrediente, cantidad in ingredientes_receta:
                            cantidad_disponible = consumir_api(ingrediente)
                            if cantidad_disponible is None or cantidad_disponible < cantidad:
                                ingredientes_suficientes = False
                                break

                        if ingredientes_suficientes:
                            actualizacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute("UPDATE orden SET estado_id = 1, actualizacion = %s WHERE id = %s", (actualizacion, orden_id))
                            conexion.connection.commit()
                            print(f"Orden {orden_id} preparada.")
                        else:
                            print(f"No hay suficientes ingredientes para la orden {orden_id}.")

            time.sleep(5)
        except Exception as e:
            print(f"Error al manejar la cola: {e}")
            # Si ocurre un error, continuamos con el ciclo después de una breve espera
            time.sleep(5)

# Ruta para renderizar el archivo HTML principal
@app.route('/main')
def index():
    # Iniciar el manejo de la cola en un hilo separado
    cola_thread = Thread(target=manejar_cola)
    cola_thread.start()
    return render_template('main.html')

# Resto del código de la aplicación...
@app.route('/buscar_receta')
def buscar_receta():
    try:
        with conexion.connection.cursor() as cursor:
            # Generar un número aleatorio del 1 al 6 para seleccionar una receta
            numero_aleatorio = random.randint(1, 6)
            cursor.execute("SELECT nombre, descripcion FROM recetas WHERE id = %s", (numero_aleatorio,))
            receta = cursor.fetchone()

            if receta:
                nombre_receta, descripcion_receta = receta
                cursor.execute("SELECT ingrediente, cantidad FROM ingrediente_receta INNER JOIN ingredientes ON ingrediente_receta.ingredientes_id = ingredientes.id WHERE recetas_id = %s", (numero_aleatorio,))
                ingredientes = cursor.fetchall()
                ingredientes_suficientes = True

                for ingrediente, cantidad in ingredientes:
                    cantidad_disponible = consumir_api(ingrediente)
                    if cantidad_disponible is None or cantidad_disponible < cantidad:
                        ingredientes_suficientes = False
                        break

                if ingredientes_suficientes:
                    # Generar una nueva orden
                    actualizacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("INSERT INTO orden (Actualizacion, recetas_id, estado_id) VALUES (%s, %s, %s)", (actualizacion, numero_aleatorio, 1))  # Plato preparado (estado_id = 1)
                    conexion.connection.commit()

                    # Reducir la cantidad de ingredientes en el inventario
                    for ingrediente, cantidad in ingredientes:
                        cursor.execute("UPDATE ingredientes SET inventario = inventario - %s WHERE ingrediente = %s", (cantidad, ingrediente))
                    conexion.connection.commit()

                    return jsonify({'nombre': nombre_receta, 'descripcion': descripcion_receta, 'ingredientes': ingredientes, 'mensaje': 'Plato preparado'})
                else:
                    # Si no hay suficientes ingredientes, encolar la orden
                    actualizacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("INSERT INTO orden (Actualizacion, recetas_id, estado_id) VALUES (%s, %s, %s)", (actualizacion, numero_aleatorio, 2))  # En cola (estado_id = 2)
                    conexion.connection.commit()

                    # Consumir la API para obtener los ingredientes faltantes
                    for ingrediente, cantidad in ingredientes:
                        cantidad_disponible = consumir_api(ingrediente)
                        if cantidad_disponible is not None and cantidad_disponible < cantidad:
                            print(f"Ingrediente {ingrediente} faltante. Consumiendo la API...")
                            # Aquí puedes manejar la lógica para consumir la API
                            # Por ejemplo:
                            # cantidad_faltante = cantidad - cantidad_disponible
                            # consumir_api(ingrediente, cantidad_faltante)
                            # También puedes encolar la orden aquí si la API no devuelve los ingredientes necesarios
                            # de inmediato, similar a cómo se hace con la lógica de encolado anteriormente
                            break

                    return jsonify({'error': 'No hay suficientes ingredientes para preparar la receta. Orden en cola.'}), 404
            else:
                return jsonify({'error': 'No se encontró ninguna receta con el ID generado'}), 404

    except Exception as e:
        return jsonify({'error': f'Error al buscar la receta: {e}'}), 500

# Ruta para visualizar órdenes anteriores
@app.route('/ordenes')
def mostrar_ordenes():
    try:
        with conexion.connection.cursor() as cursor:
            cursor.execute("SELECT id, recetas_id, estado_id FROM orden")
            ordenes = cursor.fetchall()
            ordenes_data = [{'id': orden[0], 'recetas_id': orden[1], 'estado_id': orden[2]} for orden in ordenes]
            return jsonify(ordenes_data)
    except Exception as e:
        return jsonify({'error': f'Error al obtener las órdenes: {e}'}), 500

# Ruta para visualizar las últimas 5 órdenes
@app.route('/ultimas_ordenes')
def mostrar_ultimas_ordenes():
    try:
        with conexion.connection.cursor() as cursor:
            cursor.execute("SELECT id, recetas_id, estado_id FROM orden ORDER BY id DESC LIMIT 5")
            ordenes = cursor.fetchall()
            ordenes_data = [{'id': orden[0], 'recetas_id': orden[1], 'estado_id': orden[2]} for orden in ordenes]
            return jsonify(ordenes_data)
    except Exception as e:
        return jsonify({'error': f'Error al obtener las últimas órdenes: {e}'}), 500

# Resto del código de la aplicación...

if __name__ == '__main__':
    app.config.from_object(config['development'])
    cola_thread = Thread(target=manejar_cola)
    cola_thread.start()
    app.run()