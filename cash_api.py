from flask import Blueprint, request, jsonify, send_file
import os
from datetime import datetime
import pyodbc


# Crear el Blueprint
cash_bp = Blueprint('cash', __name__)
  # Carga las variables desde el archivo .env

import json

# Cargar configuración desde config.json
with open('config.json') as config_file:
    config = json.load(config_file)

# Acceder a los valores
db_DNS = config['db_DNS']
db_user = config['db_user']
db_password = config['db_password']
db_host = config['db_host']
database_name = config['database_name']
db_vista = config['db_vista']
frontend_path = os.path.abspath(config.get("frontend_path", "frontend/dist"))
cuenta12 = config['cuenta']

@cash_bp.route('/procesar_cash', methods=['POST'])
def procesar_cash():
    data = request.get_json()
    print(data)
    
    if not data:
        return jsonify({"error": "No se recibió JSON válido."}), 400

    pagos = data.get('pagos')
    cuenta = data.get('cuenta')  # NUEVO: obtenemos la cuenta

    if not pagos or len(pagos) != 1:
        return jsonify({"error": "Debes seleccionar exactamente un pago."}), 400

    if not cuenta:
        return jsonify({"error": "Debes seleccionar una cuenta bancaria."}), 400

    doc_entry = str(pagos[0])
    print(f"Procesando Cash documento: {doc_entry} - Cuenta: {cuenta}")

    try:
        #  LLAMADA CORREGIDA: enviamos doc_entry y cuenta
        ruta_archivo = procesarCash(doc_entry, cuenta)
        
        if not os.path.exists(ruta_archivo):
            return jsonify({"error": "No se pudo generar el archivo."}), 500

        print(f"Archivo generado: {ruta_archivo}")
        return send_file(
            ruta_archivo,
            as_attachment=True,
            download_name=os.path.basename(ruta_archivo),
            mimetype='text/plain'
        )

    except Exception as e:
        mensaje_error = str(e)
        print(f"Error en procesar_cash: {mensaje_error}")

        if "No hay registros para procesar" in mensaje_error:
            return jsonify({"error": "No hay registros para las fechas seleccionadas."}), 204

        return jsonify({"error": mensaje_error}), 500


def procesarCash(DocNum, cuenta):
    try:
        print("DocNum:", DocNum, "| Cuenta:", cuenta)
        connection_string = f"DSN={db_DNS};UID={db_user};PWD={db_password}"
        print(f"Conectando con la base de datos usando: {connection_string}")

        # Consulta para obtener JrnlMemo
        memo_query = f'''
            SELECT "JrnlMemo" FROM "{database_name}"."OVPM"
            WHERE "DocNum" = '{DocNum}' LIMIT 1;
        '''
        memo_resultado = conexionODBC(memo_query, connection_string)
        memo_texto = memo_resultado[0][0] if memo_resultado and memo_resultado[0][0] else 'SIN_MEMO'

        # Actualiza tu vista si acepta ambos parámetros
        consulta = f'''SELECT * FROM "{database_name}"."{db_vista}"('{DocNum}', '{cuenta}') ORDER BY 1;'''
        print(f"Consulta ejecutada: {consulta}")
        resultados = conexionODBC(consulta, connection_string)

        banco = "Pichincha"
        localDate = datetime.now()
        subfolder = 'CASH_PICHINCHA'
        if not os.path.exists(subfolder):
            os.makedirs(subfolder)
            print(f"Creado el subfolder: {subfolder}")

        ruta = os.path.abspath(os.path.join(
            subfolder,
            #f"{banco}_PAGOS_MULTICASH_{localDate.strftime('%d%m%Y-%H%M%S')}.txt"
            f"{memo_texto}_{localDate.strftime('%d%m%Y-%H%M%S')}.txt"

        ))

        if resultados:
            with open(ruta, 'w', encoding='utf-8') as archivo:
                for resultado in resultados:
                    linea = ' '.join(map(str, resultado))
                    archivo.write(linea + '\n')
            os.chmod(ruta, 0o444)

            update_query = f"""
            UPDATE "{database_name}"."OVPM"
            SET "U_HBT_ARCHI_PLANO" = 'SI'
            WHERE "DocNum" = '{DocNum}';
            """
            updated = ejecutarODBC(update_query, connection_string)
            print(f"{updated} filas actualizadas")

            return ruta
            # Luego de guardar el archivo en procesarCash
        else:
            raise Exception("No hay registros para procesar en el rango de fechas especificado.")

    except Exception as e:
        print(f"Error en procesarCash: {str(e)}")
        raise e


def conexionODBC(consulta, connection_string):
    try:
        conexion = pyodbc.connect(connection_string)
        cursor = conexion.cursor()
        print("Conexión establecida exitosamente.")
        cursor.execute(consulta)
        print("Consulta ejecutada exitosamente.")
        resultados = cursor.fetchall()
        print(f"Resultados obtenidos: {len(resultados)} filas")
        cursor.close()
        conexion.close()
        return resultados
    except Exception as e:
        raise Exception(f"Error al ejecutar la consulta ODBC: {e}")

@cash_bp.route('/proveedores', methods=['GET'])
def obtener_proveedores():
    try:
        connection_string = f"DSN={db_DNS};UID={db_user};PWD={db_password}"
        consulta = f'SELECT "CardCode", "CardName" FROM "{database_name}"."OCRD" WHERE "CardType" = \'S\' ORDER BY "CardName"'
        resultados = conexionODBC(consulta, connection_string)
        return jsonify([{"codigo": r[0], "nombre": r[1]} for r in resultados])
    except Exception as e:
        print(f"Error al obtener proveedores: {str(e)}")
        return jsonify({"error": "No se pudo obtener la lista de proveedores."}), 500

@cash_bp.route('/pagos', methods=['POST'])
def obtener_pagos():
    data = request.get_json()
    inicio = data.get('inicio')
    fin = data.get('fin')
    proveedor = data.get('proveedor')

    if not inicio or not fin or not proveedor:
        return jsonify({"error": "Fechas y proveedor requeridos"}), 400

    try:
        connection_string = f"DSN={db_DNS};UID={db_user};PWD={db_password}"
        consulta = f"""
        SELECT "DocNum", "DocEntry", "CardCode", "DocDate", "DocTotal"
        FROM "{database_name}"."OVPM"
        WHERE "CardCode" = '{proveedor}' AND "DocDate" BETWEEN '{inicio}' AND '{fin}'
        AND "TrsfrAcct"='{cuenta12}'
        AND "U_HBT_ARCHI_PLANO" = 'NO'
        ORDER BY "DocDate"
        """
        resultados = conexionODBC(consulta, connection_string)
        pagos = [
            {
                "DocNum": row[0],
                "DocEntry": row[1],
                "CardCode": row[2],
                "DocDate": row[3].strftime('%Y-%m-%d'),
                "DocTotal": float(row[4])
            }
            for row in resultados
        ]
        return jsonify(pagos)
    except Exception as e:
        print(f"Error al obtener pagos: {e}")
        return jsonify({"error": str(e)}), 500
    
@cash_bp.route('/cuentas_bancarias', methods=['POST'])
def obtener_cuentas_bancarias():
    data = request.get_json()
    proveedor = data.get('proveedor')

    if not proveedor:
        return jsonify({"error": "Se requiere el proveedor (CardCode)."}), 400

    try:
        connection_string = f"DSN={db_DNS};UID={db_user};PWD={db_password}"
        consulta = f'''
        SELECT "Account" FROM "{database_name}"."OCRB"
        WHERE "CardCode" = '{proveedor}'
        ORDER BY "Account"
        '''
        resultados = conexionODBC(consulta, connection_string)
        cuentas = [r[0] for r in resultados]
        return jsonify(cuentas)
    except Exception as e:
        print(f"Error al obtener cuentas bancarias: {str(e)}")
        return jsonify({"error": "No se pudo obtener cuentas bancarias."}), 500
    
def ejecutarODBC(query, connection_string):
    conexion = pyodbc.connect(connection_string)
    cursor = conexion.cursor()
    cursor.execute(query)
    conexion.commit()
    rows = cursor.rowcount
    cursor.close()
    conexion.close()
    return rows


