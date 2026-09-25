/* 机悟·政企超脑 官网 v6 共用脚本（单一来源，全站引用）
   包含：自建访问统计 / 移动端菜单 / 首屏影片轮播 / 二维码放大 / 留资表单（弹窗 + 内联） / 资料下载列表渲染
   无任何外部依赖、无第三方埋点。 */
(function () {
  'use strict';
  var q = function (s, r) { return (r || document).querySelector(s); };

  /* ================= 自建访问统计（无第三方埋点，数据存自家 D1） ================= */
  (function () {
    try {
      var APIH = ['https://api.javis.org.cn', 'https://javis-api.wanyejiang2018.workers.dev'];
      var dev = /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ? 'mobile' : 'desktop';
      var ref = document.referrer ? new URL(document.referrer).host : '';
      var qs = '/api/ping?p=' + encodeURIComponent(location.pathname) + '&r=' + encodeURIComponent(ref) + '&d=' + dev + '&s=' + encodeURIComponent(location.hostname) + '&t=' + Date.now();
      var hi = 0, img = new Image(1, 1);
      img.onerror = function () { if (++hi < APIH.length) img.src = APIH[hi] + qs; };
      img.src = APIH[0] + qs;
    } catch (e) { }
  })();

  /* ================= 移动端菜单 ================= */
  (function () {
    var menu = q('#menu');
    if (!menu) return;
    var tog = q('.menu-toggle');
    function close() { menu.classList.remove('open'); document.body.classList.remove('menu-open'); }
    Array.prototype.forEach.call(document.querySelectorAll('#menu a'), function (a) { a.addEventListener('click', close); });
    document.addEventListener('click', function (e) {
      if (!menu.classList.contains('open')) return;
      if (menu.contains(e.target) || (tog && tog.contains(e.target))) return;
      close();
    });
    addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  })();

  /* ================= 二维码放大 ================= */
  (function () {
    var zoomer = q('#zoomer'), zimg = q('#zimg');
    if (!zoomer || !zimg) return;
    function openZoom(src) { zimg.src = src; zoomer.classList.add('open'); document.body.style.overflow = 'hidden'; }
    function closeZoom() {
      zoomer.classList.remove('open');
      document.body.style.overflow = (q('#mback.open')) ? 'hidden' : '';
    }
    Array.prototype.forEach.call(document.querySelectorAll('.cbox .qr, .mqr img, .qr2'), function (img) {
      img.addEventListener('click', function (e) { e.stopPropagation(); openZoom(img.src); });
    });
    zoomer.addEventListener('click', closeZoom);
    var zx = q('#zclose'); if (zx) zx.addEventListener('click', function (e) { e.stopPropagation(); closeZoom(); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && zoomer.classList.contains('open')) closeZoom(); });
  })();

  /* ================= 留资表单（唯一线索接口：POST /api/lead） ================= */
  var API_HOSTS = ['https://api.javis.org.cn', 'https://javis-api.wanyejiang2018.workers.dev'];
  function apiFetch(primary, fallback, opts) {
    var urls = [primary, fallback].filter(Boolean), lastErr, i = 0;
    function attempt() {
      var ctl = new AbortController();
      var to = setTimeout(function () { ctl.abort(); }, 8000);
      var o = {}; for (var k in opts) { o[k] = opts[k]; }
      o.signal = ctl.signal;
      return fetch(urls[i], o).then(function (r) { clearTimeout(to); return r; },
        function (e) { clearTimeout(to); lastErr = e; i++; if (i < urls.length) return attempt(); throw lastErr; });
    }
    return attempt();
  }
  var KINDS = {
    eval: { title: '申请 40 分钟免费部署评估', sub: '现有设备能跑什么、缺什么、多少钱、多久能用——提交后 1 个工作日内联系您；也可以直接加下方官方微信，对接更快。', submit: '提交申请' },
    demo: { title: '预约远程接入演示（脱敏数据）', sub: '约 30 分钟远程演示：在您的设备上真跑一遍断网大模型，使用脱敏样本数据，全程无需外部设备进场。提交后 1 个工作日内联系您安排时间。', submit: '预约演示' }
  };
  function initLead(wrap) {
    var form = q('form.lead-form', wrap);
    if (!form) return;
    var okcard = q('.m-okcard', wrap);
    var msg = q('.mmsg', form);
    var btn = q('.msubmit', form);
    var ck = q('input[name="consent"]', form);
    function showMsg(t, isErr) { if (!msg) return; msg.textContent = t; msg.className = isErr ? 'mmsg err' : 'mmsg ok'; }
    function setKind(kind) {
      var k = KINDS[kind] || KINDS.eval;
      var t = q('.lw-title', wrap), s = q('.lw-sub', wrap);
      if (t) t.textContent = k.title;
      if (s) s.textContent = k.sub;
      if (btn) btn.textContent = k.submit;
      form.setAttribute('data-kind', kind);
    }
    form.setAttribute('data-kind', form.getAttribute('data-kind') || 'eval');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (msg) { msg.className = 'mmsg'; msg.textContent = ''; }
      var val = function (n) { var el = q('[name="' + n + '"]', form); return el ? (el.value || '').trim() : ''; };
      var ccRaw = val('cc'), pw = val('pw'), need = val('need');
      var parts = ccRaw.split(/\s+/).filter(Boolean);
      var company = parts.length > 1 ? parts.slice(0, -1).join(' ') : ccRaw;
      var contact = parts.length > 1 ? parts[parts.length - 1] : '';
      if (!company) return showMsg('请填写公司 / 单位名称', true);
      if (!pw) return showMsg('请填写电话或微信号（至少一项），方便我们联系您', true);
      if (!need) return showMsg('请简单介绍一下需求', true);
      if (need.length < 4) return showMsg('需求介绍再详细一点会更高效（4 字以上即可）', true);
      if (!ck || !ck.checked) {
        var row = ck && ck.closest ? ck.closest('.chk') : null;
        if (row) row.classList.add('err');
        return showMsg('请先阅读并勾选同意《隐私政策》，我们才能联系您', true);
      }
      var row2 = ck.closest ? ck.closest('.chk') : null;
      if (row2) row2.classList.remove('err');
      if (btn) { btn.disabled = true; }
      var old = btn ? btn.textContent : '';
      if (btn) btn.textContent = '提交中…';
      var apiPath = form.getAttribute('data-api') || (API_HOSTS[0] + '/api/lead');
      var apiFallback = form.getAttribute('data-api-fallback') || (API_HOSTS[1] + '/api/lead');
      apiFetch(apiPath, apiFallback, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: form.getAttribute('data-kind') || 'eval', company: company, contact: contact,
          title: val('title'), phone: pw, wechat: '', need: need, consent: true
        })
      }).then(function (resp) {
        return resp.json().catch(function () { return {}; }).then(function (data) {
          if (resp.ok && data && data.ok) {
            if (form) form.style.display = 'none';
            if (okcard) okcard.classList.add('on');
            else showMsg('已收到您的申请，工作人员将在 1 个工作日内与您联系。', false);
          } else showMsg((data && data.error) || '提交失败，请稍后再试，或直接加官方微信', true);
        });
      }).catch(function () {
        showMsg('网络开小差了，请稍后再试，或直接加官方微信（二维码见右）', true);
      }).then(function () {
        if (btn) { btn.disabled = false; btn.textContent = old; }
      });
    });
    return { setKind: setKind, form: form };
  }
  var leadInstances = [];
  Array.prototype.forEach.call(document.querySelectorAll('.lead-wrap'), function (w) {
    var inst = initLead(w); if (inst) leadInstances.push(inst);
  });
  var mback = q('#mback');
  function closeModal() { if (mback) mback.classList.remove('open'); document.body.style.overflow = ''; }
  function openModal(kind) {
    if (!mback) return;
    var inst = null;
    for (var i = 0; i < leadInstances.length; i++) { if (mback.contains(leadInstances[i].form)) { inst = leadInstances[i]; } }
    if (inst) {
      inst.setKind(kind);
      var form = inst.form, ok = q('.m-okcard', mback);
      form.reset(); form.style.display = '';
      if (ok) ok.classList.remove('on');
      var m = q('.mmsg', form); if (m) { m.className = 'mmsg'; m.textContent = ''; }
      var err = q('.chk.err', form); if (err) err.classList.remove('err');
    }
    mback.classList.add('open');
    document.body.style.overflow = 'hidden';
    var f = q('input[name=cc]', mback); if (f) setTimeout(function () { f.focus(); }, 60);
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-open]'), function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); openModal(a.getAttribute('data-open')); });
  });
  if (mback) {
    var mc = q('#mclose'); if (mc) mc.addEventListener('click', closeModal);
    var mok = q('[data-close="ok"]'); if (mok) mok.addEventListener('click', closeModal);
    mback.addEventListener('click', function (e) { if (e.target === mback) closeModal(); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && mback.classList.contains('open')) closeModal(); });
  }

  /* ================= 资料下载列表 =================
     新增文件：把文件放进 assets/downloads/ 后，在下面 DL 数组加一行。 */
  /* DL-LIST-START */
  var DL = [
    { t: "机悟·政企超脑 宣传册 v1", d: "产品定位 · 能力清单 · 部署路径 · 常见顾虑", f: "机悟·政企超脑宣传册_v1.pdf", s: "1.6 MB", date: "2026-09" }
  ];
  /* DL-LIST-END */
  (function () {
    var box = q('#dlList');
    if (!box) return;
    if (!DL.length) {
      box.innerHTML = '<div class="dl-empty">资料整理中，即将上线。<br>着急可先来信索取：info@javis.org.cn</div>';
      return;
    }
    var ICON = { pdf: 'pdf', ppt: 'ppt', pptx: 'ppt', doc: 'doc', docx: 'doc', zip: 'zip', rar: 'zip', xls: 'doc', xlsx: 'doc' };
    box.innerHTML = DL.map(function (x) {
      var ext = (x.f.split('.').pop() || '').toLowerCase();
      var label = ext === 'pptx' ? 'PPT' : (ext === 'docx' ? 'DOC' : ext.toUpperCase());
      var cls = ICON[ext] || '';
      var sub = [x.d, x.s, x.date].filter(Boolean).join(' · ');
      return '<div class="dl-item">'
        + '<div class="dl-ico ' + cls + '">' + label + '</div>'
        + '<div class="dl-meta"><b>' + x.t + '</b><span>' + sub + '</span></div>'
        + '<a class="dl-btn" href="assets/downloads/' + encodeURIComponent(x.f) + '" download>下载</a>'
        + '</div>';
    }).join('');
  })();

  /* ================= 首屏影片轮播（仅首页有 .film） ================= */
  (function () {
    var film = q('.film');
    if (!film) return;
    var v = q('video', film), dots = q('#filmDots'), playBtn = q('.play', film);
    if (!v) return;
    var BASE = 'assets/videos/';
    var LAND = ['v6.mp4', 'v1.mp4', 'v2.mp4', 'v3.mp4', 'v4.mp4', 'v5.mp4'];
    var PORT = ['v6_p.mp4', 'v1_p.mp4', 'v2_p.mp4', 'v3_p.mp4', 'v4_p.mp4', 'v5_p.mp4'];
    var i = 0, mode = null, timer = null;
    var pre = document.createElement('video');
    pre.muted = true; pre.preload = 'auto'; pre.setAttribute('playsinline', '');
    pre.style.cssText = 'position:absolute;top:0;left:-9999px;width:1px;height:1px;opacity:0;pointer-events:none';
    function isPortrait() { return window.matchMedia('(max-width:767px) and (orientation: portrait)').matches; }
    function list() { return isPortrait() ? PORT : LAND; }
    function posterOf(n) { return BASE + n.replace(/\.mp4$/, '_poster.jpg'); }
    function saveData() {
      try { var c = navigator.connection; if (c && c.saveData) return true; if (c && /(^|-)2g$/.test(c.effectiveType || '')) return true; } catch (e) { }
      return false;
    }
    function calmMotion() { try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; } }
    function markDots() {
      if (!dots) return;
      var bs = dots.querySelectorAll('button');
      for (var k = 0; k < bs.length; k++) { bs[k].classList.toggle('on', k === i); bs[k].setAttribute('aria-selected', k === i ? 'true' : 'false'); }
    }
    function buildDots() {
      if (!dots) return;
      dots.innerHTML = '';
      for (var k = 0; k < LAND.length; k++) {
        var b = document.createElement('button');
        b.type = 'button'; b.setAttribute('role', 'tab');
        b.setAttribute('aria-label', '第 ' + (k + 1) + ' 套影片（共 ' + LAND.length + ' 套轮播）');
        (function (kk) { b.addEventListener('click', function () { play(kk); }); })(k);
        dots.appendChild(b);
      }
    }
    function primeNext() {
      var l = list(); pre.src = BASE + l[(i + 1) % l.length];
      try { pre.load(); } catch (e) { }
    }
    function play(idx, doPlay) {
      var l = list(), n = l.length;
      i = ((idx % n) + n) % n;
      var name = l[i];
      v.poster = posterOf(name);
      v.muted = true; v.setAttribute('playsinline', '');
      v.src = BASE + name;
      try { v.load(); } catch (e) { }
      if (doPlay !== false) { var p = v.play(); if (p && p.catch) p.catch(function () { film.classList.add('needs-tap'); }); }
      markDots();
      clearTimeout(timer);
      if (doPlay !== false) timer = setTimeout(primeNext, 3000);
    }
    v.addEventListener('ended', function () { play(i + 1); });
    if (playBtn) playBtn.addEventListener('click', function () {
      film.classList.remove('needs-tap'); v.muted = true;
      if (!film.dataset.started) { film.dataset.started = '1'; play(0, true); return; }
      var p = v.play(); if (p && p.catch) p.catch(function () { });
      primeNext();
    });
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting) { if (v.paused && !film.classList.contains('needs-tap')) v.play().catch(function () { }); }
          else { try { v.pause(); } catch (err) { } }
        });
      }, { threshold: .05 }).observe(film);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { try { v.pause(); } catch (e) { } }
      else if (v.paused && !film.classList.contains('needs-tap')) v.play().catch(function () { });
    });
    mode = isPortrait();
    window.addEventListener('resize', function () { var m = isPortrait(); if (m !== mode) { mode = m; play(0); } });
    document.body.appendChild(pre);
    buildDots();
    var autoPlay = !saveData() && !calmMotion();
    if (!autoPlay) film.classList.add('needs-tap');
    function startFilm() { if (film.dataset.started) return; film.dataset.started = '1'; play(0, autoPlay); }
    if (document.readyState === 'complete') startFilm();
    else {
      window.addEventListener('load', function () { setTimeout(startFilm, 120); }, { once: true });
      setTimeout(startFilm, 3500);
    }
  })();
})();
