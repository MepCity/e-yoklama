"""
Modern RESTful API for Location Verification System
Resource-based endpoints with standardized responses
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime, timedelta
import logging

from models.location_verification import LocationVerification
from database import db
from utils.auth import role_required

# Blueprint oluştur
verification_bp = Blueprint('verification', __name__, url_prefix='/api/v1/verifications')

# Logging setup
logger = logging.getLogger(__name__)

# --- Schemas for Request/Response Validation ---

class LocationVerificationRequestSchema(Schema):
    """Konum doğrulama isteği şeması"""
    latitude = fields.Float(required=True, validate=validate.Range(-90, 90))
    longitude = fields.Float(required=True, validate=validate.Range(-180, 180))
    accuracy = fields.Float(missing=None, validate=validate.Range(0, 1000))
    timestamp = fields.DateTime(missing=datetime.utcnow)

class NetworkVerificationRequestSchema(Schema):
    """Ağ doğrulama isteği şeması"""
    network_name = fields.String(required=False, missing="Unknown")
    network_type = fields.String(missing="wifi")
    signal_strength = fields.Integer(missing=None)
    timestamp = fields.DateTime(missing=datetime.utcnow)

class ManualVerificationRequestSchema(Schema):
    """Manuel doğrulama isteği şeması"""
    reason = fields.String(missing="Manual verification requested")
    notes = fields.String(missing=None)
    timestamp = fields.DateTime(missing=datetime.utcnow)

class VerificationResponseSchema(Schema):
    """Standart doğrulama yanıtı şeması"""
    verification_id = fields.Integer()
    user_id = fields.Integer()
    verification_type = fields.String()
    status = fields.String()
    verified_at = fields.DateTime()
    expires_at = fields.DateTime()
    is_suspicious = fields.Boolean()
    details = fields.Dict()

class ErrorResponseSchema(Schema):
    """Standart hata yanıtı şeması"""
    error = fields.String()
    message = fields.String()
    code = fields.Integer()
    timestamp = fields.DateTime()
    details = fields.Dict()

# --- Utility Functions ---

def create_standard_response(success=True, data=None, error=None, message=None, status_code=200):
    """Standart API yanıtı oluştur"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        'status_code': status_code
    }
    
    if success and data:
        response['data'] = data
        if message:
            response['message'] = message
    elif not success and error:
        response['error'] = error
        if message:
            response['message'] = message
    
    return jsonify(response), status_code

def validate_device_pairing(user_id):
    """Cihaz eşleşmesini kontrol et"""
    # Bu fonksiyon mevcut device pairing kontrolünü kullanır
    # TODO: Implement actual device pairing validation
    return True

def calculate_expiry_time(verification_type="normal"):
    """Doğrulama bitiş zamanını hesapla"""
    if verification_type == "suspicious":
        return datetime.utcnow() + timedelta(minutes=30)
    return datetime.utcnow() + timedelta(hours=1)

# --- API Endpoints ---

@verification_bp.route('/location', methods=['POST'])
@jwt_required()
def create_location_verification():
    """
    Konum doğrulaması oluştur
    POST /api/v1/verifications/location
    """
    try:
        user_id = get_jwt_identity()
        
        # Device pairing kontrolü
        if not validate_device_pairing(user_id):
            return create_standard_response(
                success=False,
                error="DEVICE_PAIRING_REQUIRED",
                message="Cihaz eşleşmesi gerekli",
                status_code=403
            )
        
        # Request validation
        schema = LocationVerificationRequestSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return create_standard_response(
                success=False,
                error="VALIDATION_ERROR",
                message="Geçersiz istek verisi",
                details=err.messages,
                status_code=400
            )
        
        # Konum doğrulaması oluştur
        verification = LocationVerification(
            user_id=user_id,
            verification_type='location',
            latitude=data['latitude'],
            longitude=data['longitude'],
            accuracy=data.get('accuracy')
        )
        
        # Konum doğrulamasını yap
        verification.verify_location(data['latitude'], data['longitude'], data.get('accuracy'))
        verification.expires_at = calculate_expiry_time('suspicious' if verification.is_suspicious else 'normal')
        
        db.add(verification)
        db.commit()
        
        # Response data
        response_data = {
            'verification_id': verification.id,
            'status': 'verified' if verification.verified else 'failed',
            'in_campus': verification.in_campus,
            'campus_name': verification.campus_name,
            'distance_from_campus': verification.distance_from_campus,
            'is_suspicious': verification.is_suspicious,
            'expires_at': verification.expires_at.isoformat(),
            'coordinates': {
                'latitude': verification.latitude,
                'longitude': verification.longitude,
                'accuracy': verification.accuracy
            }
        }
        
        logger.info(f"Location verification created for user {user_id}: {verification.id}")
        
        return create_standard_response(
            success=True,
            data=response_data,
            message="Konum doğrulaması başarıyla oluşturuldu",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Location verification error: {str(e)}")
        return create_standard_response(
            success=False,
            error="INTERNAL_ERROR",
            message="Konum doğrulaması sırasında hata oluştu",
            details={'error': str(e)},
            status_code=500
        )

@verification_bp.route('/network', methods=['POST'])
@jwt_required()
def create_network_verification():
    """
    Ağ doğrulaması oluştur
    POST /api/v1/verifications/network
    """
    try:
        user_id = get_jwt_identity()
        
        # Device pairing kontrolü
        if not validate_device_pairing(user_id):
            return create_standard_response(
                success=False,
                error="DEVICE_PAIRING_REQUIRED",
                message="Cihaz eşleşmesi gerekli",
                status_code=403
            )
        
        # Request validation
        schema = NetworkVerificationRequestSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return create_standard_response(
                success=False,
                error="VALIDATION_ERROR",
                message="Geçersiz istek verisi",
                details=err.messages,
                status_code=400
            )
        
        # Ağ bilgilerini al
        remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
        network_name = data.get('network_name', 'Unknown')
        
        # Ağ doğrulaması oluştur
        verification = LocationVerification(
            user_id=user_id,
            verification_type='network',
            network_name=network_name,
            remote_address=remote_addr
        )
        
        # Ağ doğrulamasını yap
        verification.verify_network(remote_addr)
        verification.expires_at = calculate_expiry_time('suspicious' if verification.is_suspicious else 'normal')
        
        db.add(verification)
        db.commit()
        
        # Response data
        response_data = {
            'verification_id': verification.id,
            'status': 'verified' if verification.is_trusted_network else 'failed',
            'is_trusted_network': verification.is_trusted_network,
            'is_eduroam': verification.is_trusted_network and 'eduroam' in network_name.lower(),
            'network_name': network_name,
            'network_info': {
                'remote_address': remote_addr,
                'network_type': data.get('network_type', 'wifi'),
                'signal_strength': data.get('signal_strength')
            },
            'is_suspicious': verification.is_suspicious,
            'expires_at': verification.expires_at.isoformat()
        }
        
        logger.info(f"Network verification created for user {user_id}: {verification.id}")
        
        return create_standard_response(
            success=True,
            data=response_data,
            message="Ağ doğrulaması başarıyla oluşturuldu",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Network verification error: {str(e)}")
        return create_standard_response(
            success=False,
            error="INTERNAL_ERROR",
            message="Ağ doğrulaması sırasında hata oluştu",
            details={'error': str(e)},
            status_code=500
        )

@verification_bp.route('/manual', methods=['POST'])
@jwt_required()
def create_manual_verification():
    """
    Manuel doğrulama oluştur
    POST /api/v1/verifications/manual
    """
    try:
        user_id = get_jwt_identity()
        
        # Device pairing kontrolü
        if not validate_device_pairing(user_id):
            return create_standard_response(
                success=False,
                error="DEVICE_PAIRING_REQUIRED",
                message="Cihaz eşleşmesi gerekli",
                status_code=403
            )
        
        # Request validation
        schema = ManualVerificationRequestSchema()
        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return create_standard_response(
                success=False,
                error="VALIDATION_ERROR",
                message="Geçersiz istek verisi",
                details=err.messages,
                status_code=400
            )
        
        # Manuel doğrulama oluştur
        verification = LocationVerification(
            user_id=user_id,
            verification_type='manual',
            is_suspicious=True
        )
        
        verification.manual_verify()
        verification.expires_at = calculate_expiry_time('suspicious')
        
        db.add(verification)
        db.commit()
        
        # Response data
        response_data = {
            'verification_id': verification.id,
            'status': 'verified',
            'verification_type': 'manual',
            'is_suspicious': True,
            'reason': data.get('reason', 'Manual verification requested'),
            'notes': data.get('notes'),
            'expires_at': verification.expires_at.isoformat()
        }
        
        logger.info(f"Manual verification created for user {user_id}: {verification.id}")
        
        return create_standard_response(
            success=True,
            data=response_data,
            message="Manuel doğrulama başarıyla oluşturuldu",
            status_code=201
        )
        
    except Exception as e:
        logger.error(f"Manual verification error: {str(e)}")
        return create_standard_response(
            success=False,
            error="INTERNAL_ERROR",
            message="Manuel doğrulama sırasında hata oluştu",
            details={'error': str(e)},
            status_code=500
        )

@verification_bp.route('/status', methods=['GET'])
@jwt_required()
def get_verification_status():
    """
    Aktif doğrulama durumunu kontrol et
    GET /api/v1/verifications/status
    """
    try:
        user_id = get_jwt_identity()
        
        # Aktif doğrulamayı al
        active_verification = LocationVerification.get_active_verification(user_id, db.session)
        
        if not active_verification:
            return create_standard_response(
                success=True,
                data={
                    'has_active_verification': False,
                    'message': 'Aktif doğrulama bulunamadı'
                },
                message="Aktif doğrulama yok",
                status_code=200
            )
        
        # Response data
        response_data = {
            'has_active_verification': True,
            'verification_id': active_verification.id,
            'verification_type': active_verification.verification_type,
            'status': 'verified' if active_verification.verified else 'failed',
            'verified_at': active_verification.verified_at.isoformat(),
            'expires_at': active_verification.expires_at.isoformat(),
            'is_suspicious': active_verification.is_suspicious,
            'time_remaining': (active_verification.expires_at - datetime.utcnow()).total_seconds(),
            'details': {
                'in_campus': active_verification.in_campus,
                'is_trusted_network': active_verification.is_trusted_network,
                'network_name': active_verification.network_name
            }
        }
        
        return create_standard_response(
            success=True,
            data=response_data,
            message="Aktif doğrulama bulundu",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Verification status check error: {str(e)}")
        return create_standard_response(
            success=False,
            error="INTERNAL_ERROR",
            message="Doğrulama durumu kontrol edilirken hata oluştu",
            details={'error': str(e)},
            status_code=500
        )

@verification_bp.route('/history', methods=['GET'])
@jwt_required()
def get_verification_history():
    """
    Doğrulama geçmişini al
    GET /api/v1/verifications/history?limit=10&offset=0
    """
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        limit = min(request.args.get('limit', 10, type=int), 50)
        offset = request.args.get('offset', 0, type=int)
        verification_type = request.args.get('type', None)
        
        # Doğrulama geçmişini al
        query = LocationVerification.query.filter_by(user_id=user_id)
        
        if verification_type:
            query = query.filter_by(verification_type=verification_type)
        
        verifications = query.order_by(LocationVerification.verified_at.desc()).offset(offset).limit(limit).all()
        
        # Response data
        response_data = {
            'verifications': [
                {
                    'verification_id': v.id,
                    'verification_type': v.verification_type,
                    'status': 'verified' if v.verified else 'failed',
                    'verified_at': v.verified_at.isoformat(),
                    'expires_at': v.expires_at.isoformat() if v.expires_at else None,
                    'is_suspicious': v.is_suspicious,
                    'details': {
                        'in_campus': v.in_campus,
                        'is_trusted_network': v.is_trusted_network,
                        'network_name': v.network_name,
                        'campus_name': v.campus_name,
                        'distance_from_campus': v.distance_from_campus
                    }
                }
                for v in verifications
            ],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': query.count()
            }
        }
        
        return create_standard_response(
            success=True,
            data=response_data,
            message="Doğrulama geçmişi başarıyla alındı",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Verification history error: {str(e)}")
        return create_standard_response(
            success=False,
            error="INTERNAL_ERROR",
            message="Doğrulama geçmişi alınırken hata oluştu",
            details={'error': str(e)},
            status_code=500
        )

# --- Error Handlers ---

@verification_bp.errorhandler(404)
def not_found(error):
    return create_standard_response(
        success=False,
        error="NOT_FOUND",
        message="İstenen kaynak bulunamadı",
        status_code=404
    )

@verification_bp.errorhandler(405)
def method_not_allowed(error):
    return create_standard_response(
        success=False,
        error="METHOD_NOT_ALLOWED",
        message="Bu HTTP metodu desteklenmiyor",
        status_code=405
    )

@verification_bp.errorhandler(500)
def internal_error(error):
    return create_standard_response(
        success=False,
        error="INTERNAL_ERROR",
        message="Sunucu iç hatası",
        status_code=500
    )
