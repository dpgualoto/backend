# cash_logic_multi.py
import os
import json
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import pyodbc
import traceback

# Cargar configuración desde config.json
with open('config.json') as config_file:
    config = json.load(config_file)

bases_config = config['bases']

# Función común para rutas multibase
def get_connection_params(base_key):
    if base_key not in bases_config:
        raise Exception("Base de datos inválida.")
    return bases_config[base_key]

def create_cash_blueprint(base_key, url_prefix):
    bp = Blueprint(f'cash_{base_key}', __name__)

    @bp.route(f'{url_prefix}/procesar_cash', methods=['POST'])
    def procesar_cash():
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió JSON válido."}), 400

        pagos = data.get('pagos')
        cuenta = data.get('cuenta')
        if not pagos or len(pagos) != 1:
            return jsonify({"error": "Debes seleccionar exactamente un pago."}), 400
        if not cuenta:
            return jsonify({"error": "Debes seleccionar una cuenta bancaria."}), 400

        doc_entry = str(pagos[0])
        base_cfg = get_connection_params(base_key)

        try:
            ruta_archivo = procesarCash(doc_entry, cuenta, base_cfg)
            if not os.path.exists(ruta_archivo):
                return jsonify({"error": "No se pudo generar el archivo."}), 500

            return send_file(
                ruta_archivo,
                as_attachment=True,
                download_name=os.path.basename(ruta_archivo),
                mimetype='text/plain'
            )
        except Exception as e:
            print("❌ Error interno:", str(e))
            traceback.print_exc()
            mensaje_error = str(e)
            if "No hay registros para procesar" in mensaje_error:
                return jsonify({"error": "No hay registros para las fechas seleccionadas."}), 204
            return jsonify({"error": mensaje_error}), 500

    @bp.route(f'{url_prefix}/proveedores', methods=['GET'])
    def obtener_proveedores():
        try:
            base_cfg = get_connection_params(base_key)
            print(base_cfg)
            connection_string = build_conn_string(base_cfg)
            consulta = f'SELECT "CardCode", "CardName" FROM "{base_cfg["database_name"]}"."OCRD" WHERE "CardType" = \'S\' ORDER BY "CardName"'
            print(consulta)
            resultados = conexionODBC(consulta, connection_string)
            return jsonify([{"codigo": r[0], "nombre": r[1]} for r in resultados])
        except Exception as e:
            return jsonify({"error": "No se pudo obtener la lista de proveedores."}), 500

    @bp.route(f'{url_prefix}/pagos', methods=['POST'])
    def obtener_pagos():
        data = request.get_json()
        inicio = data.get('inicio')
        fin = data.get('fin')
        proveedor = data.get('proveedor')

        if not inicio or not fin or not proveedor:
            return jsonify({"error": "Fechas y proveedor requeridos"}), 400

        try:
            base_cfg = get_connection_params(base_key)
            connection_string = build_conn_string(base_cfg)
            consulta = f"""
            SELECT "DocNum", "DocEntry", "CardCode", "DocDate", "DocTotal"
            FROM "{base_cfg['database_name']}"."OVPM"
            WHERE "CardCode" = '{proveedor}' AND "DocDate" BETWEEN '{inicio}' AND '{fin}'
            AND "TrsfrAcct"='{base_cfg['cuenta']}'
            AND "U_U_HBT_ARCHI_PLANO" = 'NO'
            ORDER BY "DocDate"
            """
            print(consulta)
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
            print(pagos)
            return jsonify(pagos)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route(f'{url_prefix}/cuentas_bancarias', methods=['POST'])
    def obtener_cuentas_bancarias():
        data = request.get_json()
        proveedor = data.get('proveedor')
        if not proveedor:
            return jsonify({"error": "Se requiere el proveedor (CardCode)."}), 400

        try:
            base_cfg = get_connection_params(base_key)
            connection_string = build_conn_string(base_cfg)
            consulta = f'''
            SELECT "Account" FROM "{base_cfg["database_name"]}"."OCRB"
            WHERE "CardCode" = '{proveedor}'
            ORDER BY "Account"
            '''
            resultados = conexionODBC(consulta, connection_string)
            cuentas = [r[0] for r in resultados]
            return jsonify(cuentas)
        except Exception as e:
            return jsonify({"error": "No se pudo obtener cuentas bancarias."}), 500

    return bp

# Función para generar archivo
def procesarCash(DocNum, cuenta, base_cfg):
    try:
        connection_string = build_conn_string(base_cfg)

        memo_query = f'''
            SELECT "JrnlMemo" FROM "{base_cfg["database_name"]}"."OVPM"
            WHERE "DocNum" = '{DocNum}' LIMIT 1;
        '''
        memo_resultado = conexionODBC(memo_query, connection_string)
        memo_texto = memo_resultado[0][0] if memo_resultado and memo_resultado[0][0] else 'SIN_MEMO'

        consulta = f'''SELECT * FROM "{base_cfg["database_name"]}"."{base_cfg["db_vista"]}"('{DocNum}', '{cuenta}') ORDER BY 1;'''
        resultados = conexionODBC(consulta, connection_string)

        subfolder = base_cfg.get('ruta_archivos', 'CASH_PICHINCHA')
        os.makedirs(subfolder, exist_ok=True)

        localDate = datetime.now()
        ruta = os.path.abspath(os.path.join(subfolder, f"{memo_texto}_{localDate.strftime('%d%m%Y-%H%M%S')}.txt"))

        if resultados:
            with open(ruta, 'w', encoding='utf-8') as archivo:
                for resultado in resultados:
                    linea = ' '.join(map(str, resultado))
                    archivo.write(linea + '\n')
            os.chmod(ruta, 0o444)

            update_query = f"""
            UPDATE "{base_cfg["database_name"]}"."OVPM"
            SET "U_U_HBT_ARCHI_PLANO" = 'SI'
            WHERE "DocNum" = '{DocNum}';
            """
            ejecutarODBC(update_query, connection_string)
            return ruta
        else:
            raise Exception("No hay registros para procesar en el rango de fechas especificado.")

    except Exception as e:
        raise Exception(f"Error en procesarCash: {str(e)}")

def build_conn_string(cfg):
    return f"DSN={cfg['db_DNS']};UID={cfg['db_user']};PWD={cfg['db_password']}"

def conexionODBC(consulta, connection_string):
    try:
        conexion = pyodbc.connect(connection_string)
        cursor = conexion.cursor()
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        return resultados
    except Exception as e:
        raise Exception(f"Error al ejecutar la consulta ODBC: {e}")

def ejecutarODBC(query, connection_string):
    conexion = pyodbc.connect(connection_string)
    cursor = conexion.cursor()
    cursor.execute(query)
    conexion.commit()
    rows = cursor.rowcount
    cursor.close()
    conexion.close()
    return rows
