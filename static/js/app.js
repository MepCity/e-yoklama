// Nav toggle (mobil)
function toggleNav() {
    var nav = document.getElementById('navLinks');
    nav.classList.toggle('nav-open');
}

// Flash mesajlarini 5 saniye sonra otomatik kapat
document.addEventListener('DOMContentLoaded', function () {
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.opacity = '0';
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });
});

(function () {
    var originalFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        var method = (init.method || 'GET').toUpperCase();
        if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
            var tokenMeta = document.querySelector('meta[name="csrf-token"]');
            if (tokenMeta) {
                init.headers = new Headers(init.headers || {});
                init.headers.set('X-CSRF-Token', tokenMeta.getAttribute('content'));
            }
        }
        return originalFetch(input, init);
    };
}());
