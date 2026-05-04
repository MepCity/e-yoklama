"""
OpenAPI/Swagger Documentation for Verification API
"""

from flask import Blueprint
from flask_restx import Api, Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity

# API Blueprint ve Swagger setup
docs_bp = Blueprint('docs', __name__, url_prefix='/api/docs')
api = Api(docs_bp, version='1.0', title='E-Yoklama Verification API',
          description='Modern RESTful API for Location and Network Verification',
          doc='/docs/')

# --- Data Models for Swagger ---

verification_model = api.model('Verification', {
    'verification_id': fields.Integer(description='Doğrulama ID'),
    'status': fields.String(description='Doğrulama durumu'),
    'verification_type': fields.String(description='Doğrulama tipi'),
    'verified_at': fields.DateTime(description='Doğrulama zamanı'),
    'expires_at': fields.DateTime(description='Bitiş zamanı'),
    'is_suspicious': fields.Boolean(description='Şüpheli mi'),
    'details': fields.Raw(description='Detaylar')
})

location_request_model = api.model('LocationVerificationRequest', {
    'latitude': fields.Float(required=True, description='Enlem', example=40.7128),
    'longitude': fields.Float(required=True, description='Boylam', example=-74.0060),
    'accuracy': fields.Float(description='GPS hassasiyeti', example=10.5),
    'timestamp': fields.DateTime(description='Zaman damgası')
})

network_request_model = api.model('NetworkVerificationRequest', {
    'network_name': fields.String(description='Ağ adı', example='eduroam'),
    'network_type': fields.String(description='Ağ tipi', example='wifi'),
    'signal_strength': fields.Integer(description='Sinyal gücü', example=-65),
    'timestamp': fields.DateTime(description='Zaman damgası')
})

manual_request_model = api.model('ManualVerificationRequest', {
    'reason': fields.String(description='Manuel doğrulama sebebi'),
    'notes': fields.String(description='Notlar'),
    'timestamp': fields.DateTime(description='Zaman damgası')
})

standard_response_model = api.model('StandardResponse', {
    'success': fields.Boolean(description='İşlem başarılı mı'),
    'timestamp': fields.DateTime(description='Yanıt zamanı'),
    'status_code': fields.Integer(description='HTTP durum kodu'),
    'message': fields.String(description='Mesaj'),
    'data': fields.Raw(description='Veri'),
    'error': fields.String(description='Hata'),
    'details': fields.Raw(description='Detaylar')
})

# --- Namespaces ---

ns_location = api.namespace('location', description='Konum doğrulama işlemleri')
ns_network = api.namespace('network', description='Ağ doğrulama işlemleri')
ns_manual = api.namespace('manual', description='Manuel doğrulama işlemleri')
ns_status = api.namespace('status', description='Doğrulama durumu işlemleri')
ns_history = api.namespace('history', description='Doğrulama geçmişi işlemleri')

# --- API Endpoints Documentation ---

@ns_location.route('/')
class LocationVerificationResource(Resource):
    @ns_location.doc('create_location_verification')
    @ns_location.expect(location_request_model)
    @ns_location.marshal_with(standard_response_model)
    @ns_location.response(201, 'Doğrulama başarıyla oluşturuldu')
    @ns_location.response(400, 'Geçersiz istek')
    @ns_location.response(403, 'Cihaz eşleşmesi gerekli')
    @ns_location.response(500, 'Sunucu hatası')
    @jwt_required()
    def post(self):
        """Konum doğrulaması oluştur"""
        pass  # Implementasyonu ana API dosyasında

@ns_network.route('/')
class NetworkVerificationResource(Resource):
    @ns_network.doc('create_network_verification')
    @ns_network.expect(network_request_model)
    @ns_network.marshal_with(standard_response_model)
    @ns_network.response(201, 'Doğrulama başarıyla oluşturuldu')
    @ns_network.response(400, 'Geçersiz istek')
    @ns_network.response(403, 'Cihaz eşleşmesi gerekli')
    @ns_network.response(500, 'Sunucu hatası')
    @jwt_required()
    def post(self):
        """Ağ doğrulaması oluştur"""
        pass  # Implementasyonu ana API dosyasında

@ns_manual.route('/')
class ManualVerificationResource(Resource):
    @ns_manual.doc('create_manual_verification')
    @ns_manual.expect(manual_request_model)
    @ns_manual.marshal_with(standard_response_model)
    @ns_manual.response(201, 'Doğrulama başarıyla oluşturuldu')
    @ns_manual.response(400, 'Geçersiz istek')
    @ns_manual.response(403, 'Cihaz eşleşmesi gerekli')
    @ns_manual.response(500, 'Sunucu hatası')
    @jwt_required()
    def post(self):
        """Manuel doğrulama oluştur"""
        pass  # Implementasyonu ana API dosyasında

@ns_status.route('/')
class VerificationStatusResource(Resource):
    @ns_status.doc('get_verification_status')
    @ns_status.marshal_with(standard_response_model)
    @ns_status.response(200, 'Durum başarıyla alındı')
    @ns_status.response(401, 'Yetkilendirme gerekli')
    @ns_status.response(500, 'Sunucu hatası')
    @jwt_required()
    def get(self):
        """Aktif doğrulama durumunu kontrol et"""
        pass  # Implementasyonu ana API dosyasında

@ns_history.route('/')
class VerificationHistoryResource(Resource):
    @ns_history.doc('get_verification_history')
    @ns_history.marshal_with(standard_response_model)
    @ns_history.param('limit', 'Kayıt sayısı', type=int, default=10)
    @ns_history.param('offset', 'Başlangıç kaydı', type=int, default=0)
    @ns_history.param('type', 'Doğrulama tipi', type=str)
    @ns_history.response(200, 'Geçmiş başarıyla alındı')
    @ns_history.response(401, 'Yetkilendirme gerekli')
    @ns_history.response(500, 'Sunucu hatası')
    @jwt_required()
    def get(self):
        """Doğrulama geçmişini al"""
        pass  # Implementasyonu ana API dosyasında
