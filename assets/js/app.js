/* Armin Tesisat — app.js
   1) mobil menü  2) dock sayfa dibinde gizlenir (imzayı örtmesin)
   3) Google Ads dönüşümü: tel: ve wa.me tıklaması → window.W4_ADS.tel / .wa (send_to etiketi) */
(function () {
  var dg = document.querySelector('.menu-ac'), menu = document.getElementById('menu');
  if (dg && menu) {
    dg.addEventListener('click', function () {
      var acik = menu.classList.toggle('acik');
      dg.setAttribute('aria-expanded', acik ? 'true' : 'false');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) { menu.classList.remove('acik'); dg.setAttribute('aria-expanded', 'false'); }
    });
  }

  var dock = document.getElementById('dock');
  if (dock) {
    var bekle = false;
    var kontrol = function () {
      bekle = false;
      var kalan = document.documentElement.scrollHeight - (window.scrollY + window.innerHeight);
      dock.classList.toggle('gizli', kalan < 140);
    };
    window.addEventListener('scroll', function () { if (!bekle) { bekle = true; requestAnimationFrame(kontrol); } }, { passive: true });
    kontrol();
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    var ads = window.W4_ADS;
    if (!a || !ads || typeof window.gtag !== 'function') return;
    var href = a.getAttribute('href') || '';
    var tur = href.indexOf('tel:+90532') === 0 ? 'tel' : (href.indexOf('wa.me/') !== -1 ? 'wa' : '');
    if (!tur || !ads[tur]) return;
    window.gtag('event', 'conversion', { send_to: ads.etiket + '/' + ads[tur] });
  });
})();
