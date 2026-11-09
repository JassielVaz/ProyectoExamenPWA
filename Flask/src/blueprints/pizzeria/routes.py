
from flask import jsonify, request, flash, get_flashed_messages
from datetime import date
from . import pizzeria_bp
from database import mysql


# ==========================================
# CONVERTIR RESULTADOS DE MYSQL
# ==========================================

def convertir_filas(cursor, resultados):

    if not resultados:
        return []

    if isinstance(resultados[0], dict):
        return resultados

    columnas = [columna[0] for columna in cursor.description]

    return [
        dict(zip(columnas, fila))
        for fila in resultados
    ]


def convertir_fila(cursor, resultado):

    if resultado is None:
        return None

    if isinstance(resultado, dict):
        return resultado

    columnas = [columna[0] for columna in cursor.description]

    return dict(zip(columnas, resultado))


# ==========================================
# COMPROBAR API
# ==========================================

@pizzeria_bp.route('/', methods=['GET'])
def inicio():

    return jsonify({
        'mensaje': 'API de Pizzeria funcionando',
        'exito': True
    })


# ==========================================
# REGISTRAR CLIENTE
# ==========================================

@pizzeria_bp.route('/clientes', methods=['POST'])
def registrar_cliente():

    datos = request.get_json()

    if not datos:
        return jsonify({
            'exito': False,
            'mensaje': 'No se recibieron datos.'
        }), 400

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        cursor.execute("""
            INSERT INTO clientes
            (nombre, direccion, telefono)
            VALUES (%s, %s, %s)
        """, (
            datos['nombre'],
            datos['direccion'],
            datos['telefono']
        ))

        mysql.connection.commit()

        return jsonify({
            'exito': True,
            'mensaje': 'Cliente registrado correctamente.'
        }), 201

    except Exception as error:

        mysql.connection.rollback()

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()


# ==========================================
# REGISTRAR PEDIDO
# ==========================================

@pizzeria_bp.route('/pedidos', methods=['POST'])
def registrar_pedido():

    datos = request.get_json()

    if not datos:
        return jsonify({
            'exito': False,
            'mensaje': 'No se recibieron datos.'
        }), 400

    cliente = datos.get('cliente')
    pizzas = datos.get('pizzas')
    fecha = datos.get('fecha') or date.today().isoformat()

    if not cliente or not pizzas:
        return jsonify({
            'exito': False,
            'mensaje': 'Faltan los datos del cliente o las pizzas.'
        }), 400

    if (
        not cliente.get('nombre') or
        not cliente.get('direccion') or
        not cliente.get('telefono')
    ):
        return jsonify({
            'exito': False,
            'mensaje': 'Completa todos los datos del cliente.'
        }), 400

    if len(pizzas) == 0:
        return jsonify({
            'exito': False,
            'mensaje': 'Agrega al menos una pizza.'
        }), 400

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        # Registrar cliente
        cursor.execute("""
            INSERT INTO clientes
            (nombre, direccion, telefono)
            VALUES (%s, %s, %s)
        """, (
            cliente['nombre'],
            cliente['direccion'],
            cliente['telefono']
        ))

        id_cliente = cursor.lastrowid

        # Calcular total
        total = sum(
            float(pizza['subtotal'])
            for pizza in pizzas
        )

        # Registrar pedido
        cursor.execute("""
            INSERT INTO pedidos
            (id_cliente, fecha_pedido, total)
            VALUES (%s, %s, %s)
        """, (
            id_cliente,
            fecha,
            total
        ))

        id_pedido = cursor.lastrowid

        # Registrar detalle de las pizzas
        for pizza in pizzas:

            cantidad = int(pizza['cantidad'])
            subtotal = float(pizza['subtotal'])

            precio_unitario = subtotal / cantidad

            cursor.execute("""
                INSERT INTO detalle_pedido
                (id_pedido, tamano, ingredientes, cantidad,
                 precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                id_pedido,
                pizza['tamano'],
                pizza['ingredientes'],
                cantidad,
                precio_unitario,
                subtotal
            ))

        mysql.connection.commit()

        mensaje = (
            f'Pedido registrado correctamente. '
            f'Total a pagar: ${total:.2f}'
        )

        flash(mensaje, 'success')

        return jsonify({
            'exito': True,
            'mensaje': mensaje,
            'id_pedido': id_pedido,
            'total': total,
            'alertas': get_flashed_messages(with_categories=True)
        }), 201

    except Exception as error:

        mysql.connection.rollback()

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR TODOS LOS PEDIDOS
# ==========================================

@pizzeria_bp.route('/pedidos', methods=['GET'])
def obtener_pedidos():

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                p.id_pedido,
                c.nombre,
                c.direccion,
                c.telefono,
                p.fecha_pedido,
                p.total
            FROM pedidos p
            INNER JOIN clientes c
                ON p.id_cliente = c.id_cliente
            ORDER BY p.id_pedido DESC
        """)

        resultados = cursor.fetchall()

        pedidos = convertir_filas(cursor, resultados)

        return jsonify({
            'exito': True,
            'pedidos': pedidos
        })

    except Exception as error:

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR VENTAS POR DÍA
# ==========================================

@pizzeria_bp.route('/ventas/dia/<dia>', methods=['GET'])
def ventas_por_dia(dia):

    dias = {
        'lunes': 0,
        'martes': 1,
        'miercoles': 2,
        'miércoles': 2,
        'jueves': 3,
        'viernes': 4,
        'sabado': 5,
        'sábado': 5,
        'domingo': 6
    }

    dia_numero = dias.get(dia.lower())

    if dia_numero is None:
        return jsonify({
            'exito': False,
            'mensaje': 'Día no válido.'
        }), 400

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                p.id_pedido,
                c.nombre,
                p.fecha_pedido,
                p.total
            FROM pedidos p
            INNER JOIN clientes c
                ON p.id_cliente = c.id_cliente
            WHERE WEEKDAY(p.fecha_pedido) = %s
            ORDER BY p.fecha_pedido DESC
        """, (dia_numero,))

        resultados = cursor.fetchall()

        ventas = convertir_filas(cursor, resultados)

        return jsonify({
            'exito': True,
            'dia': dia,
            'ventas': ventas
        })

    except Exception as error:

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR VENTAS POR MES
# ==========================================

@pizzeria_bp.route('/ventas/mes/<int:mes>', methods=['GET'])
def ventas_por_mes(mes):

    if mes < 1 or mes > 12:
        return jsonify({
            'exito': False,
            'mensaje': 'El mes debe estar entre 1 y 12.'
        }), 400

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT
                p.id_pedido,
                c.nombre,
                p.fecha_pedido,
                p.total
            FROM pedidos p
            INNER JOIN clientes c
                ON p.id_cliente = c.id_cliente
            WHERE MONTH(p.fecha_pedido) = %s
            ORDER BY p.fecha_pedido DESC
        """, (mes,))

        resultados = cursor.fetchall()

        ventas = convertir_filas(cursor, resultados)

        total_mes = sum(
            float(venta['total'])
            for venta in ventas
        )

        return jsonify({
            'exito': True,
            'mes': mes,
            'ventas': ventas,
            'total_mes': total_mes
        })

    except Exception as error:

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()


# ==========================================
# CONSULTAR DETALLE DE UNA VENTA
# ==========================================

@pizzeria_bp.route('/ventas/<int:id_pedido>', methods=['GET'])
def detalle_venta(id_pedido):

    cursor = None

    try:

        cursor = mysql.connection.cursor()

        # Consultar información del pedido
        cursor.execute("""
            SELECT
                p.id_pedido,
                c.nombre,
                c.direccion,
                c.telefono,
                p.fecha_pedido,
                p.total
            FROM pedidos p
            INNER JOIN clientes c
                ON p.id_cliente = c.id_cliente
            WHERE p.id_pedido = %s
        """, (id_pedido,))

        resultado = cursor.fetchone()

        pedido = convertir_fila(cursor, resultado)

        if not pedido:
            return jsonify({
                'exito': False,
                'mensaje': 'No se encontró el pedido.'
            }), 404

        # Consultar pizzas del pedido
        cursor.execute("""
            SELECT
                tamano,
                ingredientes,
                cantidad,
                precio_unitario,
                subtotal
            FROM detalle_pedido
            WHERE id_pedido = %s
        """, (id_pedido,))

        resultados = cursor.fetchall()

        detalle = convertir_filas(cursor, resultados)

        return jsonify({
            'exito': True,
            'pedido': pedido,
            'detalle': detalle
        })

    except Exception as error:

        return jsonify({
            'exito': False,
            'mensaje': str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()
