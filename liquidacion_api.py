from flask import request, jsonify, Blueprint
import pandas as pd
from werkzeug.utils import secure_filename
import os
import json
import requests
from datetime import datetime
from itertools import groupby
from pipes import quote
from operator import itemgetter

# Crear el Blueprint
liquidacion_bp = Blueprint('liquidacion', __name__)


db_DNS = os.getenv('DB_DNS')
db_user = os.getenv('DB_USER_HANA')
db_password = os.getenv('DB_PASSWORD_HANA')
db_host = os.getenv('DB_HOST')
database_name = os.getenv('DB_NAME')
db_vista = os.getenv('DB_VISTA')
db_userSAP = os.getenv('DB_USER_SAP')
db_passwordSAP = os.getenv('DB_PASSWORD_SAP')
port = os.getenv('PUERTO')

hoja1 = os.getenv('HOJA1')
series = int(os.getenv('SERIES'))
comentario_deposito = os.getenv('COMENTARIO_DEPOSITO')
cuenta_comision = os.getenv('CUENTA_COMISION')
cuenta_impuesto_iva = os.getenv('CUENTA_IMPUESTO_IVA')
cuenta_impuesto_fuente = os.getenv('CUENTA_IMPUESTO_FUENTE')
tarjetas = os.getenv('TARJETAS').split(',')
ws = os.getenv('WS')

plantilla_fecha = int(os.getenv('PLANTILLA_FECHA'))
plantilla_referencia = int(os.getenv('PLANTILLA_REFERENCIA'))
plantilla_referencia_bancaria = int(os.getenv('PLANTILLA_REFERENCIA_BANCARIA'))
plantilla_tc_marca = int(os.getenv('PLANTILLA_TC_MARCA'))
plantilla_valor_bruto = int(os.getenv('PLANTILLA_VALOR_BRUTO'))
plantilla_comision = int(os.getenv('PLANTILLA_COMISION'))
plantilla_iva = int(os.getenv('PLANTILLA_IVA'))
plantilla_fuente = int(os.getenv('PLANTILLA_FUENTE'))
plantilla_pago = int(os.getenv('PLANTILLA_PAGO'))
plantilla_banco = int(os.getenv('PLANTILLA_BANCO'))


class RegistroExcel:
    def __init__(self, Fecha, Referencia, ReferenciaBancaria, TC_MARCA, ValorBruto, Comision, IVA, FUENTE, Pago, Banco):
        self.Fecha = Fecha
        self.Referencia = Referencia
        self.ReferenciaBancaria = ReferenciaBancaria
        self.TC_MARCA = TC_MARCA
        self.ValorBruto = ValorBruto
        self.Comision = Comision
        self.IVA = IVA
        self.FUENTE = FUENTE
        self.Pago = Pago
        self.Banco = Banco
        
    def to_dict(self):
        return {
            'Fecha': self.Fecha,
            'Referencia': self.Referencia,
            'ReferenciaBancaria': self.ReferenciaBancaria,
            'TC_MARCA': self.TC_MARCA,
            'ValorBruto': self.ValorBruto,
            'Comision': self.Comision,
            'IVA': self.IVA,
            'FUENTE': self.FUENTE,
            'Pago': self.Pago,
            'Banco': self.Banco
        }
        
# Conversión de fechas
def convert_date(date):
    if isinstance(date, str):
        return pd.to_datetime(date, format='%d/%m/%Y').strftime('%Y-%m-%d')
    elif isinstance(date, datetime):
        return date.strftime('%Y-%m-%d')
    else:
        return date

# Validar conexión con el Service Layer
def validar_conexionSL():

    cuerpo = {
        "CompanyDB": database_name,
        "Password": db_passwordSAP,
        "UserName": db_userSAP
    }

    url = f"https://{db_host}:50000/b1s/v1/Login"
    try:
        response = requests.post(url, json=cuerpo, verify=False)
        if response.status_code == 200:
            session_id = response.json().get('SessionId')
            print("Conexión exitosa Service Layer. SessionId:", session_id)
            return session_id
        else:
            print("Error en la conexión al servicio web:", response.status_code)
            return None
    except Exception as e:
        print("Error al realizar la conexión:", str(e))
        return None

# Cerrar sesión en el Service Layer
def cerrar_session_SL():

    url = f"https://{db_host}:50000/b1s/v1/Logout"
    try:
        requests.post(url, verify=False)
    except Exception as e:
        print("Error al cerrar sesión:", str(e))

# Obtener depósitos
def obtener_depositos_1a1(lista):
    sesion_Id = validar_conexionSL()
    if not sesion_Id:
        print("No se pudo validar la sesión.")
        return None

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0",
        "Content-Type": "application/json"
    }

    lista_general = []

    for reg in lista:
        encoded_referencia = quote(str(reg.Referencia))
        url = f"https://{db_host}:{port}/b1s/v1/SQLQueries('{ws}')/List?ref='{encoded_referencia}'"
        try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data.get("value", []):
                    lista_general.append(data["value"][0])
            else:
                print("No se obtuvieron pagos pendientes para depósito.")
        except Exception as e:
            print("Error al obtener depósitos:", str(e))

    cerrar_session_SL()
    return lista_general

# Crear asiento contable
def crearAsiento(estructura):

    url = f"https://{db_host}:50000/b1s/v1/JournalEntries"
    sesion_Id = validar_conexionSL()
    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0"
    }

    if sesion_Id:
        try:
            response = requests.post(url, json=estructura, headers=headers, verify=False)
            if response.status_code == 201:
                data = response.json()
                cerrar_session_SL()
                return data.get('JdtNum')
            else:
                print("Error al crear Asiento:", response.content)
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error al crear Asiento:", str(e))
            cerrar_session_SL()
            return False
    else:
        return False

# Crear depósito
def crearDeposito(estructura_json):

    url = f"https://{db_host}:50000/b1s/v1/Deposits"
    sesion_Id = validar_conexionSL()
    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0"
    }

    if sesion_Id:
        try:
            response = requests.post(url, json=estructura_json, headers=headers, verify=False)
            if response.status_code == 201:
                print("Depósito creado")
                cerrar_session_SL()
                return True
            else:
                print("Error al crear Depósito:", response.content)
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error al crear Depósito:", str(e))
            cerrar_session_SL()
            return False
    else:
        return False

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
@liquidacion_bp.route('/procesar_excel', methods=['POST'])
def validar_formato_PR():
    try:
        file = request.files['file']
        if file and file.filename.endswith(('.xls', '.xlsx')):
            filepath = os.path.join('uploads', secure_filename(file.filename))
            file.save(filepath)
            df = pd.read_excel(filepath)

            sesion_Id = validar_conexionSL()

            if not sesion_Id:
                cerrar_session_SL()
                return jsonify({"error": "Error en la configuración o en la conexión con el Service Layer"}), 500

            columns_mapping = {
                "Fecha": plantilla_fecha,
                "Referencia": plantilla_referencia,
                "Referencia Bancaria": plantilla_referencia_bancaria,
                "TC/MARCA": plantilla_tc_marca,
                "Valor Bruto": plantilla_valor_bruto,
                "Comision": plantilla_comision,
                "IVA": plantilla_iva,
                "Fuente": plantilla_fuente,
                "Pago": plantilla_pago,
                "Banco": plantilla_banco
            }

            df = pd.read_excel(filepath, sheet_name=os.getenv('HOJA1'), usecols=list(columns_mapping.values()))
            df.columns = list(columns_mapping.keys())

            df['Valor Bruto'] = pd.to_numeric(df['Valor Bruto'], errors='coerce').fillna(0)
            df['IVA'] = pd.to_numeric(df['IVA'], errors='coerce').fillna(0)
            df['Fuente'] = pd.to_numeric(df['Fuente'], errors='coerce').fillna(0)
            df['Comision'] = pd.to_numeric(df['Comision'], errors='coerce').fillna(0)
            df['Pago'] = pd.to_numeric(df['Pago'], errors='coerce').fillna(0)
            df['Fecha'] = df['Fecha'].apply(convert_date)

            registros = [
                RegistroExcel(
                    Fecha=row['Fecha'],
                    Referencia=row['Referencia'],
                    ReferenciaBancaria=row['Referencia Bancaria'],
                    TC_MARCA=row['TC/MARCA'],
                    ValorBruto=row['Valor Bruto'],
                    Comision=row['Comision'],
                    IVA=row['IVA'],
                    FUENTE=row['Fuente'],
                    Pago=row['Pago'],
                    Banco=row['Banco']
                ) for _, row in df.iterrows()
            ]

            registro_dict = {registro.Referencia: registro.to_dict() for registro in registros}
            registro_dict_ordenado = sorted(registro_dict.values(), key=itemgetter('TC_MARCA', 'ReferenciaBancaria'))

            fecha_actual = datetime.now()
            fecha_formateada = fecha_actual.strftime('%Y-%m-%d')
            
            grupos = {}
            for key, group in groupby(registro_dict_ordenado, key=lambda x: (x['TC_MARCA'], x['ReferenciaBancaria'])):
                tc_marca, ref_bancaria = key
                if tc_marca not in grupos:
                    grupos[tc_marca] = {}
                grupos[tc_marca][ref_bancaria] = list(group)

            for tc_marca, ref_grupos in grupos.items():
                for ref_bancaria, items in ref_grupos.items():
                    registros1 = [
                        RegistroExcel(
                            Fecha=item['Fecha'],
                            Referencia=item['Referencia'],
                            ReferenciaBancaria=item['ReferenciaBancaria'],
                            TC_MARCA=item['TC_MARCA'],
                            ValorBruto=item['ValorBruto'],
                            Comision=item['Comision'],
                            IVA=item['IVA'],
                            FUENTE=item['FUENTE'],
                            Pago=item['Pago'],
                            Banco=item['Banco']
                        )
                        for item in items
                    ]

                    resultados = obtener_depositos_1a1(registros1)

                    docnums_en_resultados = {str(resultado['VoucherNum']) for resultado in resultados}
                    docnums_en_resultados2 = {str(resultado['U_HBT_N_AUT']) for resultado in resultados}

                    pagos_no_en_resultados = [
                        reg for reg in registros1 if (str(reg.Referencia) not in docnums_en_resultados) and (str(reg.Referencia) not in docnums_en_resultados2)
                    ]

                    if pagos_no_en_resultados:
                        print(f"No se procesarán registros para TC_MARCA: {tc_marca}, Referencia Bancaria: {ref_bancaria}, debido a que hay registros sin depósito pendiente.")
                    else:
                        combinados = []
                        registro_dict = {str(k): v for k, v in registro_dict.items()}
                        for resultado in resultados:
                            conf_num = resultado.get('VoucherNum')
                            num_auto = resultado.get('U_HBT_N_AUT')

                            if conf_num or num_auto:
                                referenciaA = str(num_auto)
                                referenciaB = str(conf_num)

                                if referenciaB in registro_dict:
                                    combinado = {**resultado, **registro_dict[referenciaB]}
                                    combinados.append(combinado)
                                elif referenciaA in registro_dict:
                                    combinado = {**resultado, **registro_dict[referenciaA]}
                                    combinados.append(combinado)

                        if combinados:
                            primer_registro = combinados[0]
                            credit_acct = primer_registro['CreditAcct']

                            data = pd.DataFrame(combinados)
                            max_banco = data['Banco'].max()
                            max_credit = data['CreditAcct'].max()
                            max_fecha = data['Fecha'].astype(str).max()
                            max_ReferenciaBancaria = data['ReferenciaBancaria'].astype(str).max()

                            suma_total = round(data['ValorBruto'].sum(), 2)
                            suma_comision = round(data['Comision'].sum(), 2)
                            suma_valor_retencion_iva = round(data['IVA'].sum(), 2)
                            suma_valor_retencion_fuente = round(data['FUENTE'].sum(), 2)

                            journal_entry_lines = []
                            journal_entry_lines.append({
                                "AccountCode": str(max_banco),
                                "Debit": float(round(suma_total - suma_comision - suma_valor_retencion_iva - suma_valor_retencion_fuente, 2)),
                                "Reference2": max_ReferenciaBancaria
                            })

                            if suma_comision > 0:
                                journal_entry_lines.append({
                                    "AccountCode": str(cuenta_comision),
                                    "Debit": float(round(suma_comision, 2)),
                                    "Reference2": max_ReferenciaBancaria
                                })

                            if suma_valor_retencion_iva > 0:
                                journal_entry_lines.append({
                                    "AccountCode": str(cuenta_impuesto_iva),
                                    "Debit": float(round(suma_valor_retencion_iva, 2)),
                                    "Reference2": max_ReferenciaBancaria
                                })

                            if suma_valor_retencion_fuente > 0:
                                journal_entry_lines.append({
                                    "AccountCode": str(cuenta_impuesto_fuente),
                                    "Debit": float(round(suma_valor_retencion_fuente, 2)),
                                    "Reference2": max_ReferenciaBancaria
                                })

                            journal_entry_lines.append({
                                "AccountCode": str(max_credit),
                                "Credit": float(round(suma_total, 2)),
                                "Reference2": max_ReferenciaBancaria
                            })

                            estructura = {
                                "Reference2": max_ReferenciaBancaria,
                                "TaxDate": max_fecha,
                                "DueDate": max_fecha,
                                "ReferenceDate": max_fecha,
                                "TransactionCode": "LIQT",
                                "Memo": comentario_deposito,
                                "JournalEntryLines": journal_entry_lines
                            }

                            print("Asiento a crear:")
                            print(estructura)
                            crearAsiento(estructura)
                            
                            estructura_json = {
                                "DepositType": "dtCredit",
                                "DepositDate": fecha_formateada,
                                "DepositAccount": credit_acct,
                                "BankReference": max_ReferenciaBancaria,
                                "VoucherAccount": credit_acct,
                                "Series": series,
                                "CreditLines": [{"AbsId": item['AbsId']} for item in combinados]
                            }
                            print("Depósito a crear:")
                            print(estructura_json)
                            crearDeposito(estructura_json)

                           
            return jsonify({"message": "Processing completed successfully"}), 200 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
