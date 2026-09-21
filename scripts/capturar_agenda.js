/*
 * Captura dos dados da Agenda Funcional do CJF (https://agenda.cjf.local/#/)
 * ---------------------------------------------------------------------------
 * A agenda é uma aplicação de página única (SPA) que carrega as pessoas por
 * chamadas de API (fetch/XHR). Este trecho intercepta essas respostas JSON e
 * permite baixá-las em um único arquivo, já com as fotos exibidas na tela
 * embutidas em base64.
 *
 * COMO USAR (no Chrome já autenticado na agenda):
 *   1. Abra https://agenda.cjf.local/#/ e pressione F12 > aba "Console".
 *   2. Cole TODO este arquivo no console e pressione Enter.
 *   3. Navegue na agenda de modo a listar TODAS as pessoas (por unidade ou
 *      pela listagem geral; role a página até o fim para carregar tudo).
 *      A cada resposta capturada o console mostra "[agenda] +N registros".
 *   4. Digite  baixarAgenda()  e pressione Enter. O arquivo
 *      "agenda_capturada.json" será salvo na pasta Downloads.
 *   5. Copie-o para  dados/agenda_funcional.json  no repositório e execute:
 *        python3 scripts/importar_agenda.py
 *        python3 scripts/gerar_dados_cjf.py
 *        npm run build
 *
 * Se a agenda não usar API JSON (dados renderizados direto no HTML), use
 * capturarTabelaDOM() após listar as pessoas: ele extrai as linhas visíveis.
 *
 * Nada é enviado para fora do navegador: o arquivo é gerado localmente.
 */
(function () {
  if (window.__agendaCaptura) {
    console.log('[agenda] captura já ativa. Use baixarAgenda() para salvar.');
    return;
  }
  const captura = { respostas: [], fotos: {}, dom: [] };
  window.__agendaCaptura = captura;

  const pareceDados = (json) => {
    const arr = Array.isArray(json) ? json : (json && (json.data || json.items || json.content || json.result || json.registros || json.pessoas));
    return Array.isArray(arr) ? arr : null;
  };

  const registrar = (url, json) => {
    const arr = pareceDados(json);
    captura.respostas.push({ url, json });
    if (arr) console.log('[agenda] +' + arr.length + ' registros de ' + url);
    else console.log('[agenda] resposta capturada de ' + url);
  };

  // --- fetch ---------------------------------------------------------------
  const fetchOriginal = window.fetch;
  window.fetch = async function (input, init) {
    const resp = await fetchOriginal.apply(this, arguments);
    try {
      const ct = resp.headers.get('content-type') || '';
      if (ct.includes('json')) {
        const clone = resp.clone();
        clone.json().then((j) => registrar(typeof input === 'string' ? input : input.url, j)).catch(() => {});
      }
    } catch (e) {}
    return resp;
  };

  // --- XMLHttpRequest ------------------------------------------------------
  const openOriginal = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.addEventListener('load', function () {
      try {
        const ct = this.getResponseHeader('content-type') || '';
        if (ct.includes('json') || (this.responseText || '').trim().startsWith('{') || (this.responseText || '').trim().startsWith('[')) {
          registrar(url, JSON.parse(this.responseText));
        }
      } catch (e) {}
    });
    return openOriginal.apply(this, arguments);
  };

  // --- fotos exibidas na tela (convertidas para base64) --------------------
  const capturarFotos = () => {
    document.querySelectorAll('img').forEach((img) => {
      const src = img.currentSrc || img.src;
      if (!src || captura.fotos[src] || src.startsWith('data:')) return;
      if (img.naturalWidth < 40 || img.naturalHeight < 40) return; // ícones
      try {
        const c = document.createElement('canvas');
        c.width = img.naturalWidth; c.height = img.naturalHeight;
        c.getContext('2d').drawImage(img, 0, 0);
        captura.fotos[src] = c.toDataURL('image/png');
      } catch (e) {
        // imagem de outra origem sem CORS: guarda apenas a URL
        captura.fotos[src] = src;
      }
    });
  };
  setInterval(capturarFotos, 2000);

  // --- fallback: extrair tabela/listagem renderizada no DOM ----------------
  window.capturarTabelaDOM = function () {
    const linhas = [];
    document.querySelectorAll('table tr').forEach((tr) => {
      const cels = Array.from(tr.querySelectorAll('td,th')).map((td) => td.innerText.trim());
      const img = tr.querySelector('img');
      if (cels.length) linhas.push({ colunas: cels, foto: img ? (img.currentSrc || img.src) : '' });
    });
    if (!linhas.length) {
      // listas em cards: captura texto de cada card com foto
      document.querySelectorAll('[class*=card], [class*=item], li').forEach((el) => {
        const img = el.querySelector('img');
        const txt = el.innerText.trim();
        if (img && txt) linhas.push({ texto: txt, foto: img.currentSrc || img.src });
      });
    }
    captura.dom = linhas;
    console.log('[agenda] DOM: ' + linhas.length + ' linhas capturadas');
    return linhas.length;
  };

  window.baixarAgenda = function () {
    capturarFotos();
    const blob = new Blob([JSON.stringify(captura, null, 1)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'agenda_capturada.json';
    document.body.appendChild(a); a.click(); a.remove();
    console.log('[agenda] arquivo gerado: respostas=' + captura.respostas.length + ' fotos=' + Object.keys(captura.fotos).length + ' dom=' + captura.dom.length);
  };

  console.log('[agenda] captura ativa. Navegue pela agenda para listar todas as pessoas e depois execute baixarAgenda().');
})();
