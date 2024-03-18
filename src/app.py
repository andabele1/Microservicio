from flask import Flask, render_template, jsonify
from flask_mysqldb import MySQL
from config import config
import random
from datetime import datetime

app = Flask(__name__)
conexion = MySQL(app)


# Ruta para renderizar el archivo HTML
@app.route('/main')
def index():
    return render_template('main.html')


# Función para buscar una receta aleatoria y generar una orden
def buscar_receta():
    try:
        # Generar un número aleatorio del 1 al 6
        numero_aleatorio = random.randint(1, 6)

        # Conexión a la base de datos
        cursor = conexion.connection.cursor()

        # Consultar la receta con el ID generado
        cursor.execute("SELECT nombre, descripcion FROM recetas WHERE id = %s", (numero_aleatorio,))
        receta = cursor.fetchone()

        if receta:
            nombre_receta, descripcion_receta = receta

            # Consultar los ingredientes necesarios para esta receta
            cursor.execute("SELECT ingrediente, cantidad FROM ingrediente_receta INNER JOIN ingredientes ON ingrediente_receta.ingredientes_id = ingredientes.id WHERE recetas_id = %s", (numero_aleatorio,))
            ingredientes = cursor.fetchall()

            # Verificar la disponibilidad de los ingredientes en el inventario
            ingredientes_suficientes = True
            for ingrediente, cantidad in ingredientes:
                cursor.execute("SELECT inventario FROM ingredientes WHERE ingrediente = %s", (ingrediente,))
                inventario = cursor.fetchone()
                if inventario is None or inventario[0] < cantidad:
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
                # Si no hay suficientes ingredientes, establecer el estado de la orden en "en cola" (estado_id = 2)
                actualizacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("INSERT INTO orden (Actualizacion, recetas_id, estado_id) VALUES (%s, %s, %s)", (actualizacion, numero_aleatorio, 2))  # En cola (estado_id = 2)
                conexion.connection.commit()

                return jsonify({'error': 'No hay suficientes ingredientes para preparar la receta'}), 404
        else:
            return jsonify({'error': 'No se encontró ninguna receta con el ID generado'}), 404

    except Exception as e:
        return jsonify({'error': f'Error al buscar la receta: {e}'}), 500

    finally:
        if cursor:
            # Cerrar la conexión a la base de datos
            cursor.close()


@app.route('/buscar_receta')
def buscar_receta_endpoint():
    return buscar_receta()


if __name__ == '__main__':
    app.config.from_object(config['development'])
    app.run()
