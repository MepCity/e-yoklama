/**
 * Modern API Client for E-Yoklama Verification System
 * RESTful API istemcisi ile standartlaştırılmış istekler
 */

class VerificationAPIClient {
    constructor(baseURL = '/api/v1/verifications') {
        this.baseURL = baseURL;
        this.token = null;
        this.cache = new Map();
        this.cacheTimeout = 5 * 60 * 1000; // 5 dakika cache
    }

    /**
     * JWT token'ını ayarla
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('jwt_token', token);
    }

    /**
     * JWT token'ını al
     */
    getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('jwt_token');
        }
        return this.token;
    }

    /**
     * Standart HTTP isteği gönder
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            // API yanıtı standart format kontrolü
            if (!data.hasOwnProperty('success')) {
                throw new Error('Invalid API response format');
            }

            // HTTP durum kodunu kontrol et
            if (!response.ok) {
                throw new APIError(data.error || 'UNKNOWN_ERROR', data.message || 'İşlem başarısız', response.status, data.details);
            }

            return data;
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError('NETWORK_ERROR', 'Ağ hatası', 0, { originalError: error.message });
        }
    }

    /**
     * GET isteği
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST isteği
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT isteği
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE isteği
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Cache ile veri al
     */
    async getCached(endpoint, params = {}) {
        const cacheKey = `${endpoint}:${JSON.stringify(params)}`;
        const cached = this.cache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }

        const data = await this.get(endpoint, params);
        this.cache.set(cacheKey, {
            data,
            timestamp: Date.now()
        });
        
        return data;
    }

    /**
     * Cache'i temizle
     */
    clearCache() {
        this.cache.clear();
    }

    // --- Verification API Methods ---

    /**
     * Konum doğrulaması oluştur
     */
    async createLocationVerification(latitude, longitude, accuracy = null) {
        const data = {
            latitude,
            longitude,
            accuracy,
            timestamp: new Date().toISOString()
        };

        return this.post('/location', data);
    }

    /**
     * Ağ doğrulaması oluştur
     */
    async createNetworkVerification(networkName = 'Unknown', networkType = 'wifi', signalStrength = null) {
        const data = {
            network_name: networkName,
            network_type: networkType,
            signal_strength: signalStrength,
            timestamp: new Date().toISOString()
        };

        return this.post('/network', data);
    }

    /**
     * Manuel doğrulama oluştur
     */
    async createManualVerification(reason = 'Manual verification requested', notes = null) {
        const data = {
            reason,
            notes,
            timestamp: new Date().toISOString()
        };

        return this.post('/manual', data);
    }

    /**
     * Aktif doğrulama durumunu kontrol et (cached)
     */
    async getVerificationStatus() {
        return this.getCached('/status');
    }

    /**
     * Doğrulama geçmişini al
     */
    async getVerificationHistory(limit = 10, offset = 0, type = null) {
        const params = { limit, offset };
        if (type) params.type = type;
        
        return this.get('/history', params);
    }

    /**
     * Toplu doğrulama (konum + ağ)
     */
    async createBulkVerification(locationData, networkData) {
        const promises = [];
        
        if (locationData) {
            promises.push(this.createLocationVerification(
                locationData.latitude, 
                locationData.longitude, 
                locationData.accuracy
            ));
        }
        
        if (networkData) {
            promises.push(this.createNetworkVerification(
                networkData.networkName,
                networkData.networkType,
                networkData.signalStrength
            ));
        }

        return Promise.allSettled(promises);
    }

    /**
     * Doğrulama durumunu gerçek zamanlı olarak izle
     */
    async watchVerificationStatus(callback, interval = 5000) {
        let isActive = true;
        
        const checkStatus = async () => {
            if (!isActive) return;
            
            try {
                const status = await this.getVerificationStatus();
                callback(status);
            } catch (error) {
                console.error('Status check error:', error);
                callback({ success: false, error: error.message });
            }
            
            if (isActive) {
                setTimeout(checkStatus, interval);
            }
        };
        
        checkStatus();
        
        return () => {
            isActive = false;
        };
    }
}

/**
 * API Hata Sınıfı
 */
class APIError extends Error {
    constructor(code, message, statusCode, details = null) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.statusCode = statusCode;
        this.details = details;
    }

    /**
     * Hata mesajını kullanıcı dostu formata dönüştür
     */
    getUserFriendlyMessage() {
        const errorMessages = {
            'VALIDATION_ERROR': 'Girdiğiniz bilgiler geçersiz. Lütfen kontrol edin.',
            'DEVICE_PAIRING_REQUIRED': 'Cihaz eşleşmesi gerekli. Lütfen cihazınızı eşleştirin.',
            'NETWORK_ERROR': 'İnternet bağlantınızı kontrol edin.',
            'INTERNAL_ERROR': 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.',
            'NOT_FOUND': 'İstenen kaynak bulunamadı.',
            'METHOD_NOT_ALLOWED': 'Bu işlem desteklenmiyor.',
            'UNAUTHORIZED': 'Oturumunuz sonlandı. Lütfen tekrar giriş yapın.',
            'FORBIDDEN': 'Bu işlem için yetkiniz yok.'
        };

        return errorMessages[this.code] || this.message;
    }

    /**
     * Hata detaylarını log için formatla
     */
    toLogFormat() {
        return {
            code: this.code,
            message: this.message,
            statusCode: this.statusCode,
            details: this.details,
            timestamp: new Date().toISOString(),
            stack: this.stack
        };
    }
}

/**
 * API İstemcisi Singleton
 */
const apiClient = new VerificationAPIClient();

/**
 * Yardımcı Fonksiyonlar
 */
const VerificationAPI = {
    /**
     * Konum doğrulaması yap
     */
    async verifyLocation() {
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    timeout: 10000,
                    enableHighAccuracy: true
                });
            });

            return await apiClient.createLocationVerification(
                position.coords.latitude,
                position.coords.longitude,
                position.coords.accuracy
            );
        } catch (error) {
            if (error.code === 1) {
                throw new APIError('PERMISSION_DENIED', 'Konum izni reddedildi', 403);
            } else if (error.code === 2) {
                throw new APIError('POSITION_UNAVAILABLE', 'Konum alınamadı', 503);
            } else if (error.code === 3) {
                throw new APIError('TIMEOUT', 'Konum alma zaman aşımı', 408);
            }
            throw error;
        }
    },

    /**
     * Ağ doğrulaması yap
     */
    async verifyNetwork() {
        try {
            const networkName = this.getNetworkName();
            return await apiClient.createNetworkVerification(networkName);
        } catch (error) {
            throw new APIError('NETWORK_VERIFICATION_FAILED', 'Ağ doğrulanamadı', 500, { originalError: error.message });
        }
    },

    /**
     * Ağ adını al
     */
    getNetworkName() {
        // Network Information API
        if ('connection' in navigator) {
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            if (connection) {
                return connection.type === 'wifi' ? 'Wi-Fi' : connection.type;
            }
        }
        
        // Tarayıcıdan Wi-Fi adını almayı dene
        if (navigator.getNetworkInformation) {
            try {
                const info = navigator.getNetworkInformation();
                return info.networkName || 'Unknown';
            } catch (e) {
                console.log('Network info not available');
            }
        }
        
        return 'Unknown';
    },

    /**
     * Tam doğrulama süreci
     */
    async performFullVerification() {
        try {
            // Önce durum kontrol et
            const status = await apiClient.getVerificationStatus();
            
            if (status.data.has_active_verification) {
                return {
                    success: true,
                    hasActiveVerification: true,
                    verification: status.data
                };
            }

            // Konum ve ağ doğrulamasını paralel yap
            const [locationResult, networkResult] = await Promise.allSettled([
                this.verifyLocation(),
                this.verifyNetwork()
            ]);

            return {
                success: true,
                hasActiveVerification: false,
                location: locationResult,
                network: networkResult
            };
        } catch (error) {
            throw new APIError('VERIFICATION_FAILED', 'Doğrulama başarısız', 500, { originalError: error.message });
        }
    },

    /**
     * Manuel doğrulama yap
     */
    async manualVerification(reason, notes) {
        return await apiClient.createManualVerification(reason, notes);
    },

    /**
     * Doğrulama durumunu izle
     */
    watchStatus(callback, interval = 5000) {
        return apiClient.watchVerificationStatus(callback, interval);
    }
};

// Global olarak erişilebilir yap
window.VerificationAPI = VerificationAPI;
window.apiClient = apiClient;
window.APIError = APIError;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VerificationAPI, apiClient, APIError };
}
