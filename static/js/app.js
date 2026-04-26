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
