from flask import Flask, render_template, jsonify
from flask_mysqldb import MySQL
from config import config
import random

app = Flask(__name__)
conexion = MySQL(app)


# Ruta para renderizar el archivo HTML
@app.route('/main')
def index():
    return render_template('main.html')


# Función para buscar una receta aleatoria
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
                return jsonify({'nombre': nombre_receta, 'descripcion': descripcion_receta, 'ingredientes': ingredientes, 'mensaje': 'Plato preparado'})
            else:
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
