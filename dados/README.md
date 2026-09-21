# dados/

Pasta de entrada para a importação da Agenda Funcional (pessoas, cargos, ramais e fotos).

| Arquivo | Descrição |
|---|---|
| `agenda_funcional.json` / `.csv` / `.xlsx` | Exportação da agenda (não versionada; contém dados pessoais). |
| `agenda_funcional.exemplo.csv` | Modelo de colunas aceitas pelo importador. |
| `fotos/` | Fotos avulsas referenciadas pela coluna `foto` (opcional; não versionada). |
| `pessoas.json` | Gerado por `scripts/importar_agenda.py`; lido por `scripts/gerar_dados_cjf.py`. |
| `nao_localizados.csv` | Gerado: pessoas cuja unidade não foi encontrada no organograma. |

Fluxo completo:

```bash
# 1. no Chrome autenticado em https://agenda.cjf.local/#/  ->  colar scripts/capturar_agenda.js no console,
#    listar todas as pessoas e executar baixarAgenda(); copiar o arquivo para dados/agenda_funcional.json
python3 scripts/importar_agenda.py      # 2. gera dados/pessoas.json e public/photos/*.jpg
python3 scripts/gerar_dados_cjf.py      # 3. gera public/data.js com pessoas e lotações
npm run build                           # 4. atualiza docs/index.html
```
