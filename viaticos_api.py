from flask import Blueprint, request, jsonify
import xml.etree.ElementTree as ET
import requests
from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables desde el archivo .env

db_name = os.getenv('DB_NAME')
db_userSAP = os.getenv('DB_USER_SAP')
db_passwordSAP = os.getenv('DB_PASSWORD_SAP')
db_host = os.getenv('DB_HOST')
# Crear el Blueprint
viaticos_bp = Blueprint('viaticos', __name__)

@viaticos_bp.route('/procesar_xml', methods=['POST'])
def procesar_xml_route():
    if 'archivo_xml' not in request.files:
        return jsonify({"error": "No se encontró ningún archivo"}), 400

    archivo_xml = request.files['archivo_xml']
    viatico_data, detalles = procesar_xml_helper(archivo_xml)

    if not viatico_data:
        return jsonify({"error": "Error procesando el archivo XML"}), 500

    # Obtener el código del cliente basado en el RUC
    ruc = viatico_data.get('ruc')
    if ruc:
        card_code = obtener_codigo_cliente(ruc)
        if card_code:
            viatico_data['codigo_cliente'] = card_code
        else:
            return jsonify({"error": "No se encontró el cliente con el RUC proporcionado"}), 404

    return jsonify({
        "viatico_data": viatico_data,
        "detalles": detalles
    })

def procesar_xml_helper(archivo_xml):
    detalles = []
    viatico_data = {}
    try:
        tree = ET.parse(archivo_xml)
        root = tree.getroot()
        viatico_data['numero_factura'] = root.find(".//secuencial").text
        viatico_data['ruc'] = root.find(".//ruc").text
        viatico_data['clave_acceso'] = root.find(".//claveAcceso").text
        viatico_data['establecimiento'] = root.find(".//estab").text
        viatico_data['punto_emision'] = root.find(".//ptoEmi").text
        viatico_data['fecha_emision'] = root.find(".//fechaEmision").text
        viatico_data['valor'] = root.find(".//importeTotal").text

        detalle_nodes = root.findall(".//detalles/detalle")
        for detalle in detalle_nodes:
            detalles.append({
                'codigo_principal': detalle.find(".//codigoPrincipal").text,
                'cantidad': detalle.find(".//cantidad").text,
                'precio_unitario': detalle.find(".//precioUnitario").text,
                'precio_total_sin_impuesto': detalle.find(".//precioTotalSinImpuesto").text,
                'codigo_porcentaje': detalle.find(".//impuestos/impuesto/codigoPorcentaje").text,
            })
        
        return viatico_data, detalles
    except Exception as e:
        print(f"Error procesando el XML: {e}")
        return {}, []

def obtener_codigo_cliente(ruc):
    session_id = validar_conexionSL()
    if session_id is None:
        return None

    headers = {
        "Cookie": f"B1SESSION={session_id}; ROUTEID=.node0"
    }

    url = f"https://{db_host}:50000/b1s/v1/BusinessPartners?$filter=FederalTaxID eq '{ruc}'"

    try:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            response_data = response.json()
            if response_data["value"]:
                return response_data["value"][0]["CardCode"]
            else:
                return None
        else:
            print(f"Error al consultar SAP Business One: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error al conectarse con SAP Business One: {str(e)}")
        return None

def validar_conexionSL():
    cuerpo = {
        "CompanyDB": db_name,
        "Password": db_passwordSAP,
        "UserName": db_userSAP
    }

    url = f"https://{db_host}:50000/b1s/v1/Login"
    try:
        response = requests.post(url, json=cuerpo, verify=False)
        if response.status_code == 200:
            session_id = response.json().get('SessionId')
            return session_id
        else:
            print(f"Error en la conexión al servicio web. Código de estado: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error al realizar la conexión: {str(e)}")
        return None

@viaticos_bp.route('/registrar_factura', methods=['POST'])
def registrar_factura():
    data = request.json
    session_id = validar_conexionSL()
    
    if session_id is None:
        return jsonify({"error": "Error al conectar con SAP"}), 500

    # Crear el cuerpo de la solicitud para el Service Layer
    invoice_data = {
        "DocDate": data.get('DocDate'),
        "CardCode": data.get('CardCode'),
        "NumAtCard": data.get('NumAtCard'),
        "U_HBT_SER_EST": data.get('U_HBT_SER_EST'),
        "U_HBT_PTO_EST": data.get('U_HBT_PTO_EST'),
        "U_HBT_AUT_FAC": data.get('U_HBT_AUT_FAC'),
        "DocumentLines": []
    }

    for detalle in data.get('DocumentLines', []):
        invoice_data["DocumentLines"].append({
            "Quantity": detalle.get('Quantity'),
            "AccountCode": "1105050100",  # Valor quemado
            "SupplierCatNum": detalle.get('SupplierCatNum'),
            "VatGroup": "IVAIM00",  # Valor quemado
            "LineTotal": detalle.get('LineTotal')
        })

    url = f"https://{db_host}:50000/b1s/v1/PurchaseInvoices"
    headers = {
        "Cookie": f"B1SESSION={session_id}; ROUTEID=.node0",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=invoice_data, headers=headers, verify=False)
        if response.status_code == 201:
            return jsonify({"message": "Factura registrada exitosamente"}), 201
        else:
            print(f"Error al registrar la factura: {invoice_data}")
        
            return jsonify({"error": "Error al registrar la factura en SAP"}), response.status_code
    except Exception as e:
        print(f"Error al conectar con SAP: {str(e)}")
        return jsonify({"error": "Error al conectar con SAP"}), 500
