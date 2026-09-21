# vueOrgChart

> Organization chart:
> A complete solution to generate and publish an orgchart without the need of a webserver and database
> (c) Michael Hoogkamer

Here is the online [Demo](https://hoogkamer.github.io/vue-org-chart/)

For more information see the [Website](https://freeorgchart.netlify.app/)

**Do you want to show your (Agile) teams instead of an orgchart? Try: [Teamviewer](https://github.com/Hoogkamer/TeamViewer) open source.**

## Build Setup

This is only needed if you want to build/change your own version. If you want to use it without modification, open \doc\index.html. See also \doc\config.js. For more info see the [Website](https://freeorgchart.netlify.app/)

_The config.js, data.js and photos folder used for development are in the \static folder_

```bash
# install dependencies
$ npm install

# serve with hot reload at localhost:3000
$ npm run dev


# build for production and launch server
$ npm run build
$ npm start

# generate static project
$ npm run generate
static output will be place in \dist folder, copy this to any location
```

Use Node 16

---

## Instância CJF (Conselho da Justiça Federal)

Esta versão do projeto está configurada com o organograma do **Conselho da Justiça Federal**,
conforme o Organograma CJF de 24/08/2026 e a tabela de novas siglas (02/26). São 160 unidades,
da Presidência e Corregedoria-Geral até o nível de Seções e Núcleos, incluindo a estrutura
completa da Secretaria de Tecnologia da Informação (STI).

### Como executar localmente

Sem servidor (instância pronta): abra `docs/index.html` diretamente no navegador.

Com servidor de desenvolvimento (Node 18+):

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # gera docs/index.html (arquivo único) e copia public/*.js para docs/
```

### Onde estão os dados

| Arquivo | Conteúdo |
|---|---|
| `scripts/gerar_dados_cjf.py` | Fonte única da estrutura (árvore de unidades, siglas, denominações, pessoas). Edite aqui. |
| `public/data.js` | Gerado: `INPUT_DATA` (unidades, pessoas, lotações) e `UPDATED_ON`. |
| `public/config.js` | Gerado: título, cores por nível, campos extras (Sigla, Natureza, Compartilhada com o STJ, Observação), propriedades de pessoas. |
| `public/translate.js` | Gerado: rótulos da interface em português. |

Para alterar a estrutura, edite a árvore `ARVORE` no script e execute:

```bash
python3 scripts/gerar_dados_cjf.py
npm run build
```

Convenções do script: cada unidade é uma tupla `(sigla, denominação, staff, filhos)`.
`staff=True` marca unidades de assessoramento/apoio (Gabinetes, Assessorias, Divisões vinculadas
diretamente a Secretarias), exibidas ao lado da linha hierárquica, como no organograma oficial.
Siglas com `*` indicam atividade compartilhada com o STJ (OUVE, CESEGI, SETRAN, CECINT, NUBIB,
NUCER e NUCOM).

### Ajustes feitos no aplicativo

- `store/index.js`: passa a respeitar `showChildren: true` do arquivo de dados, permitindo definir
  a expansão inicial da árvore (abre até as Secretarias e toda a subárvore da STI).
- `components/DeptBox.vue`: nova opção `config.showDescriptionInBox` exibe a denominação completa
  (campo `description`) como subtítulo abaixo da sigla.
- `components/SearchBox.vue`: a busca passa a considerar também a denominação da unidade.
