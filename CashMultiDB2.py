# cash2_api.py
from flask import Blueprint, request
from cash_logic import procesar_cash_common

cash2_bp = Blueprint('cash2', __name__)
BASE_KEY = 'DB2'

@cash2_bp.route('/procesar_cash/IDFNUEVA', methods=['POST'])
def procesar_cash():
    return procesar_cash_common(request, BASE_KEY)