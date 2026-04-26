(function () {
    var DB_NAME = 'e-yoklama-offline';
    var DB_VERSION = 1;
    var STORE_NAME = 'pending_attendance';

    function openDb() {
        return new Promise(function (resolve, reject) {
            if (!('indexedDB' in window)) {
                reject(new Error('IndexedDB desteklenmiyor.'));
                return;
            }

            var request = indexedDB.open(DB_NAME, DB_VERSION);
            request.onupgradeneeded = function () {
                var db = request.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
                }
            };
            request.onsuccess = function () { resolve(request.result); };
            request.onerror = function () { reject(request.error); };
        });
    }

    function savePendingAttendance(payload) {
        return openDb().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(STORE_NAME, 'readwrite');
                tx.objectStore(STORE_NAME).add(payload);
                tx.oncomplete = resolve;
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }

    function getPendingAttendance() {
        return openDb().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(STORE_NAME, 'readonly');
                var request = tx.objectStore(STORE_NAME).getAll();
                request.onsuccess = function () { resolve(request.result || []); };
                request.onerror = function () { reject(request.error); };
            });
        });
    }

    function deletePendingAttendance(id) {
        return openDb().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(STORE_NAME, 'readwrite');
                tx.objectStore(STORE_NAME).delete(id);
                tx.oncomplete = resolve;
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }

    function formToPayload(form) {
        var formData = new FormData(form);
        var data = {};
        formData.forEach(function (value, key) {
            data[key] = value;
        });
        return {
            action: form.action,
            method: form.method || 'POST',
            data: data,
            created_at: new Date().toISOString()
        };
    }

    function payloadToFormData(payload) {
        var formData = new FormData();
        Object.keys(payload.data || {}).forEach(function (key) {
            formData.append(key, payload.data[key]);
        });
        return formData;
    }

    function updateOfflineBanner() {
        var banner = document.getElementById('offlineBanner');
        if (!banner) {
            return;
        }
        banner.hidden = navigator.onLine;
    }

    function syncPendingAttendance() {
        if (!navigator.onLine) {
            updateOfflineBanner();
            return Promise.resolve();
        }

        return getPendingAttendance().then(function (items) {
            return items.reduce(function (chain, item) {
                return chain.then(function () {
                    return fetch(item.action, {
                        method: item.method || 'POST',
                        body: payloadToFormData(item),
                        credentials: 'same-origin'
                    }).then(function (response) {
                        if (response.redirected && response.url.indexOf('/login') !== -1) {
                            return null;
                        }
                        if (response.ok || response.redirected || response.status < 500) {
                            return deletePendingAttendance(item.id);
                        }
                        return null;
                    });
                });
            }, Promise.resolve());
        }).catch(function (error) {
            console.warn('Offline yoklama senkronizasyonu başarısız:', error);
        });
    }

    function bindOfflineAttendanceForms() {
        var forms = document.querySelectorAll('form[data-offline-attendance="1"]');
        forms.forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (navigator.onLine) {
                    return;
                }
                event.preventDefault();
                savePendingAttendance(formToPayload(form)).then(function () {
                    var status = form.querySelector('.gps-status');
                    if (status) {
                        status.textContent = 'Çevrimdışı kaydedildi. Bağlantı gelince gönderilecek.';
                    }
                    form.reset();
                    updateOfflineBanner();
                }).catch(function () {
                    form.submit();
                });
            });
        });
    }

    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function () {
            navigator.serviceWorker.register('/sw.js').catch(function (error) {
                console.warn('Service Worker kaydı başarısız:', error);
            });
        });
    }

    window.addEventListener('online', function () {
        updateOfflineBanner();
        syncPendingAttendance();
    });
    window.addEventListener('offline', updateOfflineBanner);

    document.addEventListener('DOMContentLoaded', function () {
        updateOfflineBanner();
        bindOfflineAttendanceForms();
        syncPendingAttendance();
    });
}());
