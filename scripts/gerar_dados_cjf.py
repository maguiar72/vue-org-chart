#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera os arquivos de dados do organograma do Conselho da Justiça Federal (CJF)
para o vue-org-chart, a partir da estrutura vigente (Organograma CJF de
24/08/2026 e tabela de siglas 02/26).

Saída (sobrescreve):
  public/data.js       -> var INPUT_DATA = {...}; var UPDATED_ON = "..."
  public/config.js     -> var CONFIG = {...}
  public/translate.js  -> var UINAMES = {...}

Uso:
  python3 scripts/gerar_dados_cjf.py

Convenções da árvore abaixo (tupla por unidade):
  (sigla_ou_id, nome_completo, staff, filhos)
  staff = True  -> unidade de assessoramento/apoio (exibida ao lado, "staff")
  staff = False -> unidade de linha (exibida abaixo, na hierarquia)
Um asterisco (*) na sigla marca atividade compartilhada com o STJ.
"""
import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ATUALIZACAO = "24-08-2026"

# ---------------------------------------------------------------------------
# Estrutura organizacional (transcrita do Organograma CJF de 24/08/2026)
# ---------------------------------------------------------------------------
ARVORE = (
    "CJF", "Conselho da Justiça Federal", False, [
        ("PLENARIO", "Plenário", True, []),
        ("PRESIDENCIA", "Ministro Presidente", False, [
            ("OUVE*", "Núcleo de Ouvidoria", True, []),
            ("SA", "Secretaria de Auditoria", False, [
                ("GAB-SA", "Gabinete da Secretaria de Auditoria", True, []),
                ("COALP", "Coordenadoria de Auditoria de Licitações, Contratos e de Pessoal", False, [
                    ("SEATIC", "Seção de Auditoria de Licitações e de Contratos de Tecnologia da Informação e Comunicação", False, []),
                    ("SEALCO", "Seção de Auditoria de Licitações e de Contratos", False, []),
                    ("SEAPES", "Seção de Auditoria de Pessoal", False, []),
                ]),
                ("COAGO", "Coordenadoria de Auditoria de Governança e de Gestão", False, [
                    ("SEAUGE", "Seção de Auditoria de Gestão e Prestação de Contas", False, []),
                    ("SEAOGO", "Seção de Auditoria Operacional e de Governança", False, []),
                    ("SEACON", "Seção de Auditoria Contábil", False, []),
                ]),
            ]),
            ("DG", "Diretoria-Geral", False, [
                ("GAB-DG", "Gabinete da Diretoria-Geral", True, []),
                ("ASJUR", "Assessoria Jurídica", True, []),
                ("CESEGI*", "Centro de Segurança Institucional e Transporte", True, [
                    ("SETRAN*", "Seção de Transporte", True, []),
                ]),
                ("CEGDOC", "Centro de Gestão Documental", True, []),
                ("CEREVI", "Centro de Revisão de Documentos e Publicações", True, []),
                ("SGP", "Secretaria de Gestão de Pessoas", False, [
                    ("GAB-SGP", "Gabinete da Secretaria de Gestão de Pessoas", True, []),
                    ("DIAME", "Divisão de Saúde", True, [
                        ("NUBEM", "Núcleo de Saúde e Bem-Estar", True, []),
                    ]),
                    ("DIAPE", "Divisão de Aposentadorias, Pensões, Direitos e Deveres", True, [
                        ("SEDIRD", "Seção de Direitos e Deveres", True, []),
                    ]),
                    ("DIRED", "Divisão de Redistribuição", True, []),
                    ("COPAG", "Coordenadoria de Pagamento", False, [
                        ("SEFPAG", "Seção de Folha de Pagamento", False, [
                            ("NURUB", "Núcleo de Rubrica de Pagamento", False, []),
                        ]),
                    ]),
                    ("CODEP", "Coordenadoria de Desenvolvimento de Pessoas", False, [
                        ("SEEDUC", "Seção de Educação Corporativa", False, []),
                        ("SEDESC", "Seção de Gestão de Desempenho e Carreira", False, []),
                        ("SEQUAV", "Seção de Qualidade de Vida", False, [
                            ("NUCAF", "Núcleo de Acolhimento Funcional", False, []),
                        ]),
                    ]),
                    ("COPIF", "Coordenadoria de Provimento e Informações Funcionais", False, [
                        ("SEPROV", "Seção de Provimento e Vacância", False, []),
                        ("SERINF", "Seção de Registros e Informações Funcionais", False, []),
                    ]),
                ]),
                ("SAD", "Secretaria de Administração", False, [
                    ("GAB-SAD", "Gabinete da Secretaria de Administração", True, []),
                    ("DICOB", "Divisão de Contabilidade", True, []),
                    ("DIPAS", "Divisão de Diárias e Passagens", True, []),
                    ("DIGOC", "Divisão de Governança das Contratações", True, []),
                    ("DIPLA", "Divisão de Apoio ao Planejamento e à Fiscalização", True, [
                        ("SEAPOC", "Seção de Apoio ao Planejamento das Contratações", True, []),
                    ]),
                    ("COMPR", "Coordenadoria de Compras, Licitações e Contratos", False, [
                        ("SECOMP", "Seção de Compras", False, []),
                        ("SELITA", "Seção de Licitações", False, []),
                        ("SECCON", "Seção de Contratos", False, []),
                    ]),
                    ("COMAG", "Coordenadoria de Manutenção Predial, Material e Patrimônio e de Serviços Gerais e Gráficos", False, [
                        ("SEMANP", "Seção de Manutenção Predial", False, []),
                        ("SEMAPA", "Seção de Material e Patrimônio", False, []),
                        ("SEGRAF", "Seção de Serviços Gráficos", False, []),
                        ("SESERV", "Seção de Serviços Gerais", False, []),
                    ]),
                    ("COOFI", "Coordenadoria de Execução Orçamentária e Financeira", False, [
                        ("SEPROG", "Seção de Programação e Planejamento Orçamentário", False, []),
                        ("SEALDE", "Seção de Análise e de Liquidação de Despesas", False, []),
                        ("SEORCA", "Seção de Execução Orçamentária", False, []),
                        ("SEFINE", "Seção de Execução Financeira", False, []),
                    ]),
                ]),
            ]),
            ("SE", "Secretaria de Estratégia e Projetos", False, [
                ("GAB-SE", "Gabinete da Secretaria de Estratégia e Projetos", True, []),
                ("DPJ", "Departamento de Pesquisas Judiciárias", False, [
                    ("SEEJUD", "Seção de Estudos Judiciários", False, [
                        ("NUPEA", "Núcleo de Pesquisa e Aplicação", False, []),
                    ]),
                ]),
                ("SGI", "Secretaria de Governança e Inteligência Analítica", False, [
                    ("CORIA", "Coordenadoria de Processos, Riscos e Inteligência Analítica", False, [
                        ("SEDATA", "Seção de Engenharia Analítica", False, []),
                        ("SEOPRI", "Seção de Arquitetura Organizacional, Processos e Riscos", False, []),
                    ]),
                ]),
                ("SPI", "Secretaria de Projetos e Inovação", False, [
                    ("IPÊ LAB", "Divisão Laboratório de Inovação", True, []),
                    ("COGEP", "Coordenadoria de Gestão de Projetos", False, [
                        ("SEBENE", "Seção de Planejamento e Monitoramento de Benefícios", False, []),
                        ("SEPORT", "Seção de Portfólio e Suporte a Projetos", False, []),
                    ]),
                    ("COPES", "Coordenadoria de Planejamento Estratégico", False, [
                        ("SESUST", "Seção de Sustentabilidade", False, []),
                        ("SEMEST", "Seção de Formulação e Monitoramento da Estratégia", False, []),
                    ]),
                ]),
            ]),
            ("SG", "Secretaria-Geral", False, [
                ("GAB-SG", "Gabinete da Secretaria-Geral", True, []),
                ("ASESG", "Assessoria Especial", True, []),
                ("ASSES", "Assessoria de Apoio às Sessões", True, []),
                ("ASINT", "Assessoria de Assuntos Institucionais", True, []),
                ("ASIJF", "Assessoria de Segurança Institucional da Justiça Federal", True, []),
                ("CECINT*", "Centro de Cooperação Jurídica Internacional", True, []),
                ("NUCER*", "Núcleo de Cerimonial", True, []),
                ("NUCOM*", "Núcleo de Comunicação", True, []),
                ("NUBIB*", "Núcleo de Biblioteca", True, []),
                ("STI", "Secretaria de Tecnologia da Informação", False, [
                    ("GAB-STI", "Gabinete da Secretaria de Tecnologia da Informação", True, []),
                    ("DIDIA", "Divisão de Tratamento de Dados, Inovação e Inteligência Artificial", True, [
                        ("SESSER", "Seção de Suporte a Serviços", True, []),
                    ]),
                    ("DIRAC", "Divisão de Relacionamento e da AC-JUS", True, [
                        ("SEATEN", "Seção de Atendimento e Suporte ao Usuário", True, []),
                    ]),
                    ("CEGOVE", "Centro de Governança de Tecnologia da Informação", True, []),
                    ("COSOF", "Coordenadoria de Engenharia de Software", False, [
                        ("SESUSO", "Seção de Sustentação de Software", False, []),
                        ("SESUPE", "Seção de Suporte à Engenharia de Software", False, []),
                        ("SECORP", "Seção de Projetos de Softwares Corporativos", False, [
                            ("NUPRO", "Núcleo de Apoio aos Projetos da Corregedoria-Geral", False, []),
                        ]),
                    ]),
                    ("COSTI", "Coordenadoria de Segurança da Tecnologia da Informação", False, [
                        ("SESERE", "Seção de Segurança de Rede", False, []),
                    ]),
                    ("COSNA", "Coordenadoria de Planejamento e Gestão de Sistemas Nacionais", False, [
                        ("SESINA", "Seção de Sistemas Nacionais", False, []),
                    ]),
                    ("COTEC", "Coordenadoria de Infraestrutura e de Suporte Técnico", False, [
                        ("SESINF", "Seção de Suporte à Infraestrutura", False, []),
                    ]),
                ]),
                ("SPO", "Secretaria de Planejamento, Orçamento e Finanças da Justiça Federal", False, [
                    ("GAB-SPO", "Gabinete da Secretaria de Planejamento, Orçamento e Finanças", True, []),
                    ("DICOS", "Divisão de Contabilidade e Custos", True, [
                        ("SECONT", "Seção de Orientação Contábil", True, []),
                    ]),
                    ("COPLA", "Coordenadoria de Planejamento Orçamentário", False, [
                        ("SEPLAN", "Seção de Planejamento", False, []),
                        ("SEANOR", "Seção de Análise e de Acompanhamento da Execução Orçamentária", False, []),
                    ]),
                    ("COPRE", "Coordenadoria de Precatórios", False, [
                        ("SEPREF", "Seção de Programação Financeira de Precatórios", False, []),
                        ("SEPREC", "Seção de Programação Orçamentária de Precatórios", False, [
                            ("NUABI", "Núcleo de Avaliação de Banco de Dados e de Indicadores Orçamentários", False, []),
                        ]),
                    ]),
                    ("COFIN", "Coordenadoria de Programação Orçamentária e Financeira", False, [
                        ("SEPROR", "Seção de Programação Orçamentária", False, []),
                        ("SEPROF", "Seção de Programação Financeira", False, []),
                    ]),
                ]),
                ("SGO", "Secretaria de Gestão de Obras da Justiça Federal", False, [
                    ("GAB-SGO", "Gabinete da Secretaria de Gestão de Obras", True, []),
                    ("COPOB", "Coordenadoria de Planejamento de Obras", False, [
                        ("SEPLAO", "Seção de Planejamento de Obras", False, []),
                    ]),
                    ("COPRA", "Coordenadoria de Projetos e Acompanhamento de Obras", False, [
                        ("SEACOB", "Seção de Projetos e Acompanhamento Técnico de Obras", False, []),
                    ]),
                ]),
            ]),
        ]),
        ("CORREGEDOR", "Ministro Corregedor-Geral", False, [
            ("JUIZ-AUX", "Juiz Auxiliar", True, [
                ("CEAJUA", "Centro de Apoio aos Juízes Auxiliares", True, []),
            ]),
            ("CGJF", "Corregedoria-Geral da Justiça Federal", False, [
                ("FPC-JF", "Fórum Permanente de Corregedores da Justiça Federal", True, []),
                ("SCG", "Secretaria da Corregedoria-Geral da Justiça Federal", False, [
                    ("GAB-SCG", "Gabinete da Secretaria da Corregedoria-Geral da Justiça Federal", True, []),
                    ("CEINSP", "Centro de Inspeções e Correições", True, [
                        ("SEAINS", "Seção de Apoio às Inspeções", True, []),
                    ]),
                    ("DISCI", "Divisão de Procedimentos Disciplinares", False, [
                        ("SEADIS", "Seção de Apoio aos Procedimentos Disciplinares", False, []),
                    ]),
                    ("DIAIN", "Divisão de Assuntos Institucionais", False, [
                        ("SEPROT", "Seção de Procedimentos Técnicos", False, []),
                    ]),
                    ("DIEST", "Divisão de Estatística", False, []),
                ]),
            ]),
            ("TNU", "Turma Nacional de Uniformização dos Juizados Especiais Federais", False, [
                ("CPC-JEF", "Comissão Permanente dos Coordenadores dos JEFs", True, []),
                ("STU", "Secretaria da Turma Nacional de Uniformização", False, [
                    ("DIANP", "Divisão de Análise Processual e Gestão de Precedentes", False, [
                        ("SESFET", "Seção de Sobrestamento de Feitos", False, []),
                    ]),
                    ("DIAPU", "Divisão de Admissibilidade de Pedidos de Uniformização", False, [
                        ("SEAPRE", "Seção de Adequação de Precedentes", False, []),
                    ]),
                    ("DIDIP", "Divisão de Distribuição e de Processamento de Feitos", False, [
                        ("SEAJUR", "Seção de Apoio a Julgamento e Publicação de Jurisprudência", False, []),
                        ("SEFEIT", "Seção de Processamento de Feitos", False, []),
                        ("SEAPRA", "Seção de Análise de Pressupostos Recursais", False, []),
                    ]),
                ]),
            ]),
            ("CEJ", "Centro de Estudos Judiciários", False, [
                ("CEMAF", "Conselho das Escolas da Magistratura Federal", True, []),
                ("SCE", "Secretaria do Centro de Estudos Judiciários", False, [
                    ("GAB-SCE", "Gabinete da Secretaria do Centro de Estudos Judiciários", True, []),
                    ("DIEVE", "Divisão de Eventos Especiais", False, [
                        ("SEEDIT", "Seção de Editoração", False, []),
                    ]),
                    ("DINPE", "Divisão de Inteligência e Pesquisa", False, []),
                    ("DIPRO", "Divisão de Programas Educacionais", False, [
                        ("SEPRED", "Seção de Programas Educacionais a Distância", False, []),
                        ("SEPREP", "Seção de Programas Educacionais Presenciais", False, []),
                    ]),
                ]),
            ]),
        ]),
    ]
)

# Unidades sem sigla oficial (o id é um identificador interno): não exibir o id no box
SEM_SIGLA = {"CJF", "PLENARIO", "PRESIDENCIA", "CORREGEDOR", "JUIZ-AUX", "CGJF", "FPC-JF", "CPC-JEF"}

NOTA_COMPARTILHADA = (
    "Atividade compartilhada, executada sob a coordenação de unidades do STJ "
    "com fundamento em Acordo de Cooperação e, em hipóteses específicas, também "
    "nos respectivos Termos de Execução Descentralizada de Recursos Orçamentários."
)

# Pessoas conhecidas quando não há importação da Agenda Funcional.
# Campos: id, name, photo, functionName, fields, gerencia (sigla da unidade da qual é titular)
# e lotacoes (lista de {"sigla", "role"}). Se dados/pessoas.json existir (gerado por
# scripts/importar_agenda.py), ele substitui esta lista.
PESSOAS_PADRAO = [
    {
        "id": "P0001",
        "name": "Marcos Aguiar",
        "photo": "",
        "functionName": "Diretor da Secretaria de Tecnologia da Informação",
        "fields": {"E-mail": "", "Ramal": "", "Matrícula": "", "Afastamento": ""},
        "gerencia": "STI",
        "lotacoes": [{"sigla": "STI", "role": "Diretor da Secretaria de Tecnologia da Informação"}],
    },
]
ARQUIVO_PESSOAS = os.path.join(RAIZ, "dados", "pessoas.json")


def carregar_pessoas():
    if os.path.exists(ARQUIVO_PESSOAS):
        with open(ARQUIVO_PESSOAS, encoding="utf-8") as f:
            pessoas = json.load(f)
        print("Pessoas carregadas de dados/pessoas.json: %d" % len(pessoas))
        return pessoas
    return PESSOAS_PADRAO


def tipo_unidade(nome):
    """Deduz a natureza da unidade pelo prefixo do nome completo."""
    prefixos = [
        ("Conselho da Justiça Federal", "Órgão"),
        ("Plenário", "Colegiado"),
        ("Ministro", "Autoridade"),
        ("Juiz", "Autoridade"),
        ("Fórum", "Colegiado"),
        ("Comissão", "Colegiado"),
        ("Conselho", "Colegiado"),
        ("Turma", "Órgão julgador"),
        ("Corregedoria", "Órgão"),
        ("Diretoria", "Diretoria"),
        ("Secretaria", "Secretaria"),
        ("Departamento", "Departamento"),
        ("Gabinete", "Gabinete"),
        ("Assessoria", "Assessoria"),
        ("Centro", "Centro"),
        ("Coordenadoria", "Coordenadoria"),
        ("Divisão", "Divisão"),
        ("Seção", "Seção"),
        ("Núcleo", "Núcleo"),
    ]
    for p, t in prefixos:
        if nome.startswith(p):
            return t
    return ""


def slug(texto):
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()


def rotulo(sigla, nome):
    """Texto principal do box: a sigla (ou o nome, para unidades sem sigla)."""
    if sigla in SEM_SIGLA:
        return nome
    return sigla


# Unidades cuja subárvore inicia totalmente expandida (além dos níveis superiores)
EXPANDIR_SUBARVORE = {"STI"}


def montar(no, parent_id="", nivel=0, gerentes=None, expandir=False):
    sigla, nome, staff, filhos = no
    expandir = expandir or sigla in EXPANDIR_SUBARVORE
    compartilhada = sigla.endswith("*")
    # A denominação completa fica em "description" (exibida como subtítulo no box e na barra lateral)
    descricao = "" if sigla in SEM_SIGLA else nome
    dept = {
        "id": slug(sigla),
        "name": rotulo(sigla, nome),
        "description": descricao,
        "parent_id": parent_id,
        "staff_department": "Y" if staff else "N",
        "manager_id": gerentes.get(sigla, "") if gerentes else "",
        "dataFields": [
            {"name": "Sigla", "value": "" if sigla in SEM_SIGLA else sigla.rstrip("*"), "type": "text"},
            {"name": "Natureza", "value": tipo_unidade(nome), "type": "text"},
            {"name": "Compartilhada com o STJ", "value": "Sim (*)" if compartilhada else "Não", "type": "text"},
            {"name": "Observação", "value": NOTA_COMPARTILHADA if compartilhada else "", "type": "text"},
        ],
        "children": [montar(f, slug(sigla), nivel + 1, gerentes, expandir) for f in filhos],
        # Abre a árvore até o nível das Secretarias (CJF > Ministros > Secretarias/DG > unidades);
        # níveis inferiores ficam recolhidos, exceto as subárvores listadas em EXPANDIR_SUBARVORE
        "showChildren": nivel < 3 or expandir,
    }
    return dept


def contar(dept):
    return 1 + sum(contar(c) for c in dept["children"])


def main():
    pessoas = carregar_pessoas()
    siglas_validas = set()

    def coletar(no):
        siglas_validas.add(no[0])
        for f in no[3]:
            coletar(f)

    coletar(ARVORE)

    gerentes = {p["gerencia"]: p["id"] for p in pessoas if p.get("gerencia") in siglas_validas}
    chart = montar(ARVORE, gerentes=gerentes)

    people = []
    assignments = []
    for p in pessoas:
        pessoa = {k: v for k, v in p.items() if k not in ("gerencia", "lotacoes")}
        people.append(pessoa)
        lotacoes = p.get("lotacoes") or ([{"sigla": p["gerencia"], "role": p.get("functionName", "")}] if p.get("gerencia") else [])
        for lot in lotacoes:
            if lot.get("sigla") not in siglas_validas:
                print("  aviso: unidade %r de %s não existe no organograma" % (lot.get("sigla"), p["name"]))
                continue
            assignments.append({
                "department_id": slug(lot["sigla"]),
                "id": len(assignments),
                "person_id": p["id"],
                "role": lot.get("role", ""),
            })

    input_data = {
        "api_version": "2.0",
        "chart": chart,
        "people": people,
        "assignments": assignments,
    }

    config = {
        "enableUserSettings": True,
        "showUserManual": False,
        "title": {"color": "#1F4E79", "text": "Conselho da Justiça Federal - Organograma"},
        "information": (
            "Organograma do Conselho da Justiça Federal (CJF), conforme estrutura de 24/08/2026 "
            "e tabela de siglas 02/26.<br><br>"
            "Unidades marcadas com <b>*</b> são de atividade compartilhada, executada sob a "
            "coordenação de unidades do STJ (OUVE, CESEGI, SETRAN, CECINT, NUBIB, NUCER e NUCOM).<br><br>"
            "Encontrou algum erro? Envie um e-mail para a "
            "<a href=\"mailto:sti@cjf.jus.br?Subject=Organograma%20CJF\" target=\"_top\">STI</a>."
        ),
        "photoUrl": {"prefix": "photos/", "suffix": ".jpg"},
        "startView": {
            "photos": True,
            "names": True,
            "columnview": True,
            "staffColumnview": False,
            "showNrDepartments": True,
            "showNrPeople": False,
            "darkMode": False,
        },
        "enableScreenCapture": True,
        "boxWidth": 175,
        "boxHeight": 68,
        # Exibe a denominação completa (description) como subtítulo no box
        "showDescriptionInBox": True,
        # Cores por nível, inspiradas no organograma oficial
        # 1 CJF | 2 Ministros/Plenário | 3 Secretarias/DG | 4 Secretarias vinculadas | 5 Coordenadorias/Divisões | 6 Seções | 7 Núcleos
        "levelColors": ["#1F4E79", "#ED7D31", "#FFC000", "#5B9BD5", "#70AD47", "#A9D18E", "#C5E0B4"],
        "editCommand": "_edit",
        "dataFields": [
            {"name": "Sigla", "type": "text"},
            {"name": "Natureza", "type": "text"},
            {"name": "Compartilhada com o STJ", "type": "text"},
            {"name": "Observação", "type": "text"},
        ],
        "personProperties": [
            {"name": "Ramal", "type": "text", "order": 0},
            {"name": "E-mail", "type": "email", "order": 1},
            {"name": "Matrícula", "type": "text", "order": 2},
            {"name": "Afastamento", "type": "text", "order": 3},
        ],
    }

    uinames = {
        "person": {
            "name": "Nome",
            "function": "Função",
            "id": "Matrícula",
            "departments": "Unidades",
        },
        "sidebar": {
            "detailTabName": "Detalhes",
            "peopleTabName": "Pessoas",
            "departmentName": "Unidade",
            "departmentManager": "Titular",
            "departmentDescription": "Denominação",
            "departmentType": "Tipo de unidade",
            "departmentHierarchy": "Hierarquia",
            "departmentTypeStaff": "Unidade de assessoramento/apoio",
            "departmentTypeNormal": "Unidade de linha",
            "managerOfDepartment": "Titular da unidade",
        },
    }

    dumps = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    pub = os.path.join(RAIZ, "public")
    with open(os.path.join(pub, "data.js"), "w", encoding="utf-8") as f:
        f.write("var INPUT_DATA=%s;var UPDATED_ON=%s\n" % (dumps(input_data), dumps(DATA_ATUALIZACAO)))
    with open(os.path.join(pub, "config.js"), "w", encoding="utf-8") as f:
        f.write("var CONFIG = %s\n" % json.dumps(config, ensure_ascii=False, indent=2))
    with open(os.path.join(pub, "translate.js"), "w", encoding="utf-8") as f:
        f.write("var UINAMES = %s\n" % json.dumps(uinames, ensure_ascii=False, indent=2))

    print("Unidades geradas: %d" % contar(chart))
    print("Pessoas: %d | Lotações: %d" % (len(people), len(assignments)))


if __name__ == "__main__":
    main()
