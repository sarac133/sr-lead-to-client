/* Local stand-in for the Claude Design runtime that the .dc.html files expect.
   Implements just what these files use: <x-dc>, <helmet>, <sc-if>, <sc-for>, <dc-import>,
   {{path}} bindings, on* handlers and a DCLogic base class with setState + lifecycle hooks. */
(function () {
  'use strict';
  var defs = {}, loading = {}, cache = new Map(), nodeIds = new WeakMap(), nextId = 1, pending = false, mount = null;

  function DCLogic(props) { this.props = props || {}; this.state = {}; }
  DCLogic.prototype.setState = function (p, cb) {
    var patch = typeof p === 'function' ? p(this.state || {}, this.props) : p;
    if (patch) this.state = Object.assign({}, this.state, patch);
    schedule();
    if (cb) setTimeout(cb, 0);
  };
  DCLogic.prototype.renderVals = function () { return {}; };
  window.DCLogic = DCLogic;

  function schedule() {
    if (pending) return;
    pending = true;
    setTimeout(function () { pending = false; flush(); }, 0);
  }

  // ---------- expressions ----------
  function evalExpr(e, scope) {
    e = e.trim();
    if (e === 'true') return true;
    if (e === 'false') return false;
    if (e === 'null') return null;
    if (e === 'undefined') return undefined;
    if (/^-?\d+(\.\d+)?$/.test(e)) return Number(e);
    var q = e.match(/^(['"])(.*)\1$/);
    if (q) return q[2];
    var cur = scope, parts = e.split('.');
    for (var i = 0; i < parts.length; i++) {
      if (cur == null) return undefined;
      cur = cur[parts[i]];
    }
    return cur;
  }
  var WHOLE = /^\s*\{\{([^{}]*)\}\}\s*$/;
  function evalAttr(v, scope) {
    var m = v.match(WHOLE);
    if (m) return evalExpr(m[1], scope);
    return v.replace(/\{\{([^{}]*)\}\}/g, function (_, e) {
      var r = evalExpr(e, scope);
      return r == null || r === false ? '' : String(r);
    });
  }
  function nid(n) { if (!nodeIds.has(n)) nodeIds.set(n, nextId++); return nodeIds.get(n); }

  // ---------- build ----------
  var EVENTS = { onclick: 'click', onchange: 'change', onfocus: 'focusin', onkeydown: 'keydown',
    onmouseenter: 'mouseenter', onmouseleave: 'mouseleave', onmousemove: 'mousemove', oninput: 'input' };

  function setAttr(el, name, val) {
    if (/^aria-/.test(name) || name === 'draggable') { if (val != null) el.setAttribute(name, String(val)); return; }
    if (val === false || val == null) return;
    el.setAttribute(name, val === true ? '' : String(val));
  }
  function addHandlers(el) {
    el.__l = el.__l || {};
    Object.keys(el.__h || {}).forEach(function (evt) {
      if (el.__l[evt]) return;
      el.__l[evt] = 1;
      el.addEventListener(evt, function (e) { var f = el.__h && el.__h[evt]; if (f) f(e); });
    });
  }

  function buildList(nodes, scope, key, out) {
    for (var i = 0; i < nodes.length; i++) buildNode(nodes[i], scope, key, out);
    return out;
  }
  function buildNode(node, scope, key, out) {
    if (node.nodeType === 3) {
      out.push(document.createTextNode(node.data.indexOf('{{') >= 0 ? evalAttr(node.data, scope) : node.data));
      return;
    }
    if (node.nodeType !== 1) return;
    var tag = node.localName;
    if (tag === 'helmet') return;
    if (tag === 'sc-if') {
      var ok = evalAttr(node.getAttribute('value') || '', scope);
      if (ok) buildList(node.childNodes, scope, key, out);
      return;
    }
    if (tag === 'sc-for') {
      var list = evalAttr(node.getAttribute('list') || '', scope) || [], as = node.getAttribute('as');
      for (var i = 0; i < list.length; i++) {
        var s = Object.create(scope); s[as] = list[i];
        buildList(node.childNodes, s, key + '/' + nid(node) + ':' + i, out);
      }
      return;
    }
    if (tag === 'dc-import') {
      var name = node.getAttribute('name'), def = defs[name];
      if (!def || !def.Cls) { console.warn('dc-import: missing component', name); return; }
      var props = {};
      Array.prototype.forEach.call(node.attributes, function (a) {
        if (a.name === 'name' || /^hint-/.test(a.name)) return;
        props[a.name.replace(/-([a-z])/g, function (_, c) { return c.toUpperCase(); })] = a.value.indexOf('{{') >= 0 ? evalAttr(a.value, scope) : a.value;
      });
      var k = key + '#' + nid(node), rec = cache.get(k);
      if (!rec) { rec = { inst: new def.Cls(props), mounted: false, prevProps: {} }; cache.set(k, rec); }
      else { rec.prevProps = rec.inst.props; rec.inst.props = props; }
      rec.seen = true; rec.def = def;
      renderInst(rec, k, out);
      return;
    }
    var el = node.namespaceURI === 'http://www.w3.org/1999/xhtml'
      ? document.createElement(tag) : document.createElementNS(node.namespaceURI, tag);
    el.__h = {};
    Array.prototype.forEach.call(node.attributes, function (a) {
      var n = a.name, v = a.value;
      if (/^hint-/.test(n)) return;
      if (EVENTS[n]) {
        var fn = evalAttr(v, scope);
        if (typeof fn === 'function') {
          var evt = EVENTS[n];
          if (n === 'onchange' && /^(input|textarea)$/.test(tag)) evt = 'input';
          el.__h[evt] = fn;
        }
        return;
      }
      if (v.indexOf('{{') >= 0) {
        var val = evalAttr(v, scope);
        if (n === 'value' && /^(input|textarea|select)$/.test(tag)) { el.__val = val == null ? '' : String(val); el.value = el.__val; }
        setAttr(el, n, val);
      } else el.setAttribute(n, v);
    });
    addHandlers(el);
    var kids = buildList(node.childNodes, scope, key, []);
    for (var j = 0; j < kids.length; j++) el.appendChild(kids[j]);
    if (tag === 'textarea' && el.__val != null) el.value = el.__val;
    out.push(el);
  }
  function renderInst(rec, key, out) {
    var vals;
    try { vals = rec.inst.renderVals() || {}; } catch (e) { console.error('renderVals failed', e); vals = {}; }
    return buildList(rec.def.tpl, vals, key, out);
  }

  // ---------- patch ----------
  function syncAttrs(ok, nk) {
    var i, a;
    for (i = ok.attributes.length - 1; i >= 0; i--) {
      a = ok.attributes[i];
      if (!nk.hasAttribute(a.name) && !(ok.localName === 'details' && a.name === 'open')) ok.removeAttribute(a.name);
    }
    for (i = 0; i < nk.attributes.length; i++) {
      a = nk.attributes[i];
      if (ok.getAttribute(a.name) !== a.value) ok.setAttribute(a.name, a.value);
    }
  }
  function patchChildren(parent, kids) {
    var old = Array.prototype.slice.call(parent.childNodes), i;
    for (i = 0; i < kids.length; i++) {
      if (!old[i]) parent.appendChild(kids[i]);
      else patchNode(parent, old[i], kids[i]);
    }
    for (i = old.length - 1; i >= kids.length; i--) parent.removeChild(old[i]);
  }
  function patchNode(parent, ok, nk) {
    if (ok.nodeType !== nk.nodeType || ok.nodeName !== nk.nodeName || ok.namespaceURI !== nk.namespaceURI) { parent.replaceChild(nk, ok); return; }
    if (nk.nodeType === 3) { if (ok.data !== nk.data) ok.data = nk.data; return; }
    syncAttrs(ok, nk);
    ok.__h = nk.__h; addHandlers(ok);
    patchChildren(ok, Array.prototype.slice.call(nk.childNodes));
    if (nk.__val != null && ok.value !== nk.__val) ok.value = nk.__val;
  }

  // ---------- render loop ----------
  function flush() {
    var root = cache.get('root');
    if (!root) return;
    cache.forEach(function (r) { r.seen = false; });
    root.seen = true;
    var out = renderInst(root, 'root', []);
    patchChildren(mount, out);
    cache.forEach(function (r, k) {
      var i = r.inst;
      try {
        if (!r.seen) { if (i.componentWillUnmount) i.componentWillUnmount(); cache.delete(k); }
        else if (!r.mounted) { r.mounted = true; if (i.componentDidMount) i.componentDidMount(); }
        else if (i.componentDidUpdate) i.componentDidUpdate(r.prevProps, {});
      } catch (e) { console.error('lifecycle error', e); }
    });
  }

  // ---------- loading ----------
  function load(name) {
    if (loading[name]) return loading[name];
    return loading[name] = fetch('/' + name + '.dc.html').then(function (r) {
      if (!r.ok) throw new Error('Could not load ' + name);
      return r.text();
    }).then(function (txt) {
      var doc = new DOMParser().parseFromString(txt, 'text/html');
      var x = doc.querySelector('x-dc'), sc = doc.querySelector('script[data-dc-script]');
      var seen = {};
      Array.prototype.forEach.call(document.head.children, function (c) { seen[c.outerHTML] = 1; });
      Array.prototype.forEach.call(x.querySelectorAll('helmet > *'), function (c) {
        if (seen[c.outerHTML]) return;
        document.head.appendChild(document.importNode(c, true));
      });
      var def = defs[name] = { tpl: Array.prototype.slice.call(x.childNodes) };
      def.Cls = new Function('DCLogic', sc.textContent + '\n;return Component;')(DCLogic);
      var deps = [], re = /<dc-import\s+name="([^"]+)"/g, m;
      while ((m = re.exec(txt))) deps.push(m[1]);
      return Promise.all(deps.map(load));
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var name = decodeURIComponent(location.pathname.replace(/^\//, '').replace(/\.dc\.html$/, '')) || 'Main';
    load(name).then(function () {
      var x = document.querySelector('x-dc');
      mount = document.createElement('div'); mount.id = 'dc-root';
      if (x) x.parentNode.replaceChild(mount, x); else document.body.appendChild(mount);
      cache.set('root', { inst: new defs[name].Cls({}), def: defs[name], mounted: false, prevProps: {} });
      flush();
    }).catch(function (e) { console.error(e); document.body.textContent = 'Local runtime error: ' + e.message; });
  });
})();
