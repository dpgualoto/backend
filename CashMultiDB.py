# cash1_api.py
from flask import Blueprint, request
from cash_logic import procesar_cash_common

cash1_bp = Blueprint('cash1', __name__)
BASE_KEY = 'DB1'

@cash1_bp.route('/procesar_cash/IDF', methods=['POST'])
def procesar_cash():
    return procesar_cash_common(request, BASE_KEY)



