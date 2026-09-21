var CONFIG = {
  "enableUserSettings": true,
  "showUserManual": false,
  "title": {
    "color": "#1F4E79",
    "text": "Conselho da Justiça Federal - Organograma"
  },
  "information": "Organograma do Conselho da Justiça Federal (CJF), conforme estrutura de 24/08/2026 e tabela de siglas 02/26.<br><br>Unidades marcadas com <b>*</b> são de atividade compartilhada, executada sob a coordenação de unidades do STJ (OUVE, CESEGI, SETRAN, CECINT, NUBIB, NUCER e NUCOM).<br><br>Encontrou algum erro? Envie um e-mail para a <a href=\"mailto:sti@cjf.jus.br?Subject=Organograma%20CJF\" target=\"_top\">STI</a>.",
  "photoUrl": {
    "prefix": "photos/",
    "suffix": ".jpg"
  },
  "startView": {
    "photos": true,
    "names": true,
    "columnview": true,
    "staffColumnview": false,
    "showNrDepartments": true,
    "showNrPeople": false,
    "darkMode": false
  },
  "enableScreenCapture": true,
  "boxWidth": 175,
  "boxHeight": 68,
  "showDescriptionInBox": true,
  "levelColors": [
    "#1F4E79",
    "#ED7D31",
    "#FFC000",
    "#5B9BD5",
    "#70AD47",
    "#A9D18E",
    "#C5E0B4"
  ],
  "editCommand": "_edit",
  "dataFields": [
    {
      "name": "Sigla",
      "type": "text"
    },
    {
      "name": "Natureza",
      "type": "text"
    },
    {
      "name": "Compartilhada com o STJ",
      "type": "text"
    },
    {
      "name": "Observação",
      "type": "text"
    }
  ],
  "personProperties": [
    {
      "name": "Ramal",
      "type": "text",
      "order": 0
    },
    {
      "name": "E-mail",
      "type": "email",
      "order": 1
    },
    {
      "name": "Matrícula",
      "type": "text",
      "order": 2
    },
    {
      "name": "Afastamento",
      "type": "text",
      "order": 3
    }
  ]
}
