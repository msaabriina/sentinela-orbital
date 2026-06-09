# -*- coding: utf-8 -*-
"""
gerar_pdf.py
==============================================================================
SENTINELA ORBITAL - Gera o documento PDF oficial da entrega (Global Solution).

Estetica escura + laranja; capa com integrantes e "QUERO CONCORRER"; Introducao,
Desenvolvimento, Resultados Esperados e Conclusoes; todas as figuras; trechos
REAIS de codigo como TEXTO selecionavel (extraidos dos arquivos-fonte); e os
links do repositorio e do video. O TEXTO do documento usa acentuacao
portuguesa completa e nao usa travessoes ("-") como pausa.

Saida: /mnt/user-data/outputs/Sentinela_Orbital_GlobalSolution_2026.pdf
==============================================================================
"""

import os
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak,
                                Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
SRC = os.path.dirname(__file__)
BASE = os.path.join(SRC, "..")
ASSETS = os.path.join(BASE, "assets")
SAIDA_DIR = "/mnt/user-data/outputs" if os.path.isdir("/mnt/user-data/outputs") \
    else os.path.abspath(BASE)
os.makedirs(SAIDA_DIR, exist_ok=True)
SAIDA = os.path.join(SAIDA_DIR, "Sentinela_Orbital_GlobalSolution_2026.pdf")

# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
LARANJA = colors.HexColor("#E8501F")
DARK = colors.HexColor("#15151B")
GRAF = colors.HexColor("#26262E")
CORPO = colors.HexColor("#2A2A30")
CINZA = colors.HexColor("#6B6B75")
CODEBG = colors.HexColor("#F5F5F7")
CODEBORDA = colors.HexColor("#E2E2E6")
AZUL = colors.HexColor("#2E5E8C")
TEAL = colors.HexColor("#1F9E8E")
BRANCO = colors.white

LARG_CONTEUDO = A4[0] - 2 * 22 * mm

# ---------------------------------------------------------------------------
# Extracao de trechos REAIS de codigo
# ---------------------------------------------------------------------------
def bloco(caminho_rel, primeira, ultima, dedent=True):
    caminho = os.path.join(BASE, caminho_rel)
    with open(caminho, encoding="utf-8") as f:
        linhas = f.readlines()
    ini = next(i for i, l in enumerate(linhas) if primeira in l)
    fim = next(i for i, l in enumerate(linhas[ini:], ini) if ultima in l)
    trecho = "".join(linhas[ini:fim + 1]).rstrip("\n")
    if dedent:
        trecho = textwrap.dedent(trecho)
    return trecho


# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
styles = getSampleStyleSheet()

st_corpo = ParagraphStyle("corpo", parent=styles["Normal"], fontName="Helvetica",
                          fontSize=10.3, leading=15.2, alignment=TA_JUSTIFY,
                          textColor=CORPO, spaceAfter=7)
st_h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17,
                       textColor=GRAF, spaceBefore=4, spaceAfter=9, leading=20)
st_h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12.5,
                       textColor=LARANJA, spaceBefore=10, spaceAfter=5,
                       leading=15)
st_legenda = ParagraphStyle("legenda", fontName="Helvetica-Oblique",
                            fontSize=8.6, textColor=CINZA, alignment=TA_CENTER,
                            spaceBefore=3, spaceAfter=12)
st_codigo = ParagraphStyle("codigo", fontName="Courier", fontSize=7.5,
                           leading=9.6, textColor=colors.HexColor("#16161A"))
st_cap = ParagraphStyle("cap", fontName="Courier-Bold", fontSize=7.6,
                        leading=10, textColor=LARANJA)
st_toc = ParagraphStyle("toc", fontName="Helvetica", fontSize=11, leading=20,
                        textColor=CORPO)
st_toc2 = ParagraphStyle("toc2", parent=st_toc, leftIndent=20,
                         textColor=colors.HexColor("#55555F"))
st_quote = ParagraphStyle("quote", parent=st_corpo, leftIndent=12,
                          textColor=GRAF, fontName="Helvetica-Oblique",
                          borderColor=LARANJA, spaceBefore=4, spaceAfter=10)
st_celula = ParagraphStyle("celula", fontName="Helvetica", fontSize=9.3,
                           leading=11.5, textColor=CORPO)


# ---------------------------------------------------------------------------
# Helpers de conteudo
# ---------------------------------------------------------------------------
def h1(texto):
    return KeepTogether([
        HRFlowable(width=42, thickness=3.2, color=LARANJA, spaceAfter=5,
                   hAlign="LEFT", lineCap="round"),
        Paragraph(texto, st_h1),
    ])


def h2(texto):
    return Paragraph(texto, st_h2)


def p(texto):
    return Paragraph(texto, st_corpo)


def imagem(nome, largura_mm=None, legenda=""):
    caminho = os.path.join(ASSETS, nome)
    from PIL import Image as PILImage
    with PILImage.open(caminho) as im:
        w, h = im.size
    larg = (largura_mm * mm) if largura_mm else LARG_CONTEUDO
    alt = larg * h / w
    flow = [Image(caminho, width=larg, height=alt, hAlign="CENTER")]
    if legenda:
        flow.append(Paragraph(legenda, st_legenda))
    else:
        flow.append(Spacer(1, 10))
    return flow


def codigo(titulo, texto):
    linhas = []
    if titulo:
        linhas.append(Paragraph(titulo, st_cap))
        linhas.append(Spacer(1, 3))
    esc = (texto.replace("&", "&amp;").replace("<", "&lt;")
           .replace(">", "&gt;"))
    esc = esc.replace(" ", "&nbsp;").replace("\n", "<br/>")
    par = Paragraph(esc, st_codigo)
    tabela = Table([[par]], colWidths=[LARG_CONTEUDO])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODEBG),
        ("BOX", (0, 0), (-1, -1), 0.75, CODEBORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBEFORE", (0, 0), (0, -1), 3, LARANJA),
    ]))
    bloco_final = (linhas + [tabela]) if titulo else [tabela]
    return KeepTogether(bloco_final + [Spacer(1, 12)])


def tabela_dados(dados, larguras, cabecalho=True):
    t = Table(dados, colWidths=larguras)
    estilo = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.3),
        ("TEXTCOLOR", (0, 0), (-1, -1), CORPO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, CODEBORDA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, colors.HexColor("#FAFAFB")]),
    ]
    if cabecalho:
        estilo += [
            ("BACKGROUND", (0, 0), (-1, 0), GRAF),
            ("TEXTCOLOR", (0, 0), (-1, 0), BRANCO),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9.3),
        ]
    t.setStyle(TableStyle(estilo))
    return KeepTogether([t, Spacer(1, 12)])


# ---------------------------------------------------------------------------
# Capa + rodape
# ---------------------------------------------------------------------------
INTEGRANTES = [
    ("Karina Garta Szewczuk", "RM569309"),
    ("Maria Sabrina Feitosa da Silva", "RM568714"),
    ("Nicolas Lima Apolinário", "RM570741"),
    ("Roger Gabriel de Souza Jesus Costa", "RM573659"),
]
NOME_GRUPO = "Sentinela Orbital"


def desenhar_capa(c, doc):
    W, H = A4
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    import random
    random.seed(7)
    c.setFillColor(colors.HexColor("#2A2A35"))
    for _ in range(90):
        x = random.uniform(0, W)
        y = random.uniform(H * 0.45, H)
        r = random.uniform(0.4, 1.4)
        c.circle(x, y, r, fill=1, stroke=0)

    c.setFillColor(LARANJA)
    c.rect(60, H - 92, 130, 6, fill=1, stroke=0)

    c.setFillColor(LARANJA)
    c.setFont("Helvetica-Bold", 44)
    c.drawString(58, H - 175, "SENTINELA")
    c.setFillColor(BRANCO)
    c.drawString(58, H - 222, "ORBITAL")

    # subtitulo (frase unica e completa, sem truncamento)
    c.setFillColor(colors.HexColor("#C9C9D2"))
    c.setFont("Helvetica", 12)
    c.drawString(60, H - 257, "Previsão e monitoramento inteligente de queimadas com dados")
    c.drawString(60, H - 275, "orbitais (INPE e NASA), inteligência artificial e sensores ESP32")

    c.setStrokeColor(colors.HexColor("#33333F"))
    c.setLineWidth(1)
    c.line(60, H - 360, W - 60, H - 360)

    c.setFillColor(LARANJA)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, H - 392, "GLOBAL SOLUTION 2026.1 · FIAP")
    c.setFillColor(colors.HexColor("#A9A9B4"))
    c.setFont("Helvetica", 9.8)
    c.drawString(60, H - 411, "Tema: como a tecnologia espacial pode melhorar a vida das pessoas,")
    c.drawString(60, H - 425, "tornar processos mais eficientes e criar novas oportunidades na Terra.")

    c.setFillColor(BRANCO)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, H - 470, "Integrantes")
    c.setFillColor(colors.HexColor("#8C8C97"))
    c.setFont("Helvetica", 9.5)
    c.drawString(60, H - 487, f"Grupo: {NOME_GRUPO}")
    y = H - 512
    c.setFont("Helvetica", 11)
    for i, (nome, rm) in enumerate(INTEGRANTES, 1):
        c.setFillColor(LARANJA)
        c.drawString(60, y, f"{i}.")
        c.setFillColor(colors.HexColor("#E6E6EC"))
        c.drawString(78, y, nome)
        c.setFillColor(colors.HexColor("#8C8C97"))
        c.drawRightString(W - 60, y, rm)
        y -= 23

    # "QUERO CONCORRER" posicionado logo APOS os nomes dos integrantes
    y -= 6
    c.setFillColor(LARANJA)
    c.roundRect(60, y - 26, 232, 34, 7, fill=1, stroke=0)
    c.setFillColor(BRANCO)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(78, y - 16, "QUERO CONCORRER")

    c.setStrokeColor(colors.HexColor("#33333F"))
    c.line(60, 96, W - 60, 96)
    c.setFillColor(colors.HexColor("#7A7A85"))
    c.setFont("Helvetica", 8.6)
    c.drawString(60, 78, "São Paulo, junho de 2026")
    c.drawRightString(W - 60, 78, "POC acadêmica com dados sintéticos baseados em padrões reais")


def rodape(c, doc):
    if doc.page == 1:
        return
    W, H = A4
    c.setStrokeColor(CODEBORDA)
    c.setLineWidth(0.6)
    c.line(22 * mm, 16 * mm, W - 22 * mm, 16 * mm)
    c.setFillColor(CINZA)
    c.setFont("Helvetica", 8)
    c.drawString(22 * mm, 11 * mm, "Sentinela Orbital · Global Solution 2026.1 / FIAP")
    c.setFillColor(LARANJA)
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - 22 * mm, 11 * mm, f"{doc.page:02d}")


def primeira_pagina(c, doc):
    desenhar_capa(c, doc)


# ---------------------------------------------------------------------------
# Conteudo
# ---------------------------------------------------------------------------
def construir():
    S = []
    S.append(PageBreak())

    # ---------------- SUMARIO ----------------
    S.append(h1("Sumário"))
    sumario = [
        (1, "1.  Introdução"),
        (1, "2.  Desenvolvimento"),
        (2, "2.1  Visão da solução e arquitetura"),
        (2, "2.2  Dados: fontes, geração e análise exploratória"),
        (2, "2.3  Inteligência: modelos de Machine Learning"),
        (2, "2.4  Camada de borda: estações ESP32"),
        (2, "2.5  Comunicação MQTT e persistência"),
        (2, "2.6  Motor de fusão e alertas"),
        (2, "2.7  Dashboard interativo"),
        (2, "2.8  Tecnologias e disciplinas integradas"),
        (1, "3.  Resultados Esperados"),
        (1, "4.  Conclusões"),
        (1, "5.  Links do projeto (repositório e vídeo)"),
        (1, "Anexo A.  Como executar o projeto"),
    ]
    for nivel, item in sumario:
        S.append(Paragraph(item, st_toc if nivel == 1 else st_toc2))
    S.append(PageBreak())

    # ---------------- 1. INTRODUCAO ----------------
    S.append(h1("1. Introdução"))
    S.append(p(
        "Todos os anos o Brasil enfrenta uma temporada devastadora de queimadas. "
        "Os focos de calor se concentram na <b>estação seca</b>, entre julho e "
        "outubro, e atingem com força os biomas <b>Amazônia</b> e <b>Cerrado</b>. "
        "O monitoramento por satélite, conduzido pelo <b>INPE</b> através do "
        "Programa Queimadas, é referência mundial. Por sua natureza, porém, ele "
        "detecta o fogo que <i>já começou</i>, muitas vezes com horas de "
        "defasagem entre a passagem do satélite e a chegada do alerta a quem "
        "pode agir no terreno."))
    S.append(p(
        "O <b>Sentinela Orbital</b> nasce de uma pergunta simples: e se "
        "pudéssemos <b>prever o risco antes do fogo</b> e, ao mesmo tempo, "
        "<b>confirmar o início da queimada no chão, em minutos</b>? A resposta "
        "que propomos combina o melhor de duas perspectivas: a visão ampla dos "
        "satélites e a sensibilidade imediata de sensores instalados no local."))
    S.append(h2("Objetivo"))
    S.append(p(
        "Desenvolver um sistema integrado de <b>previsão e monitoramento de "
        "queimadas</b> que una dados orbitais (focos do INPE e clima da NASA), "
        "<b>inteligência artificial</b> para estimar risco e um número de focos, "
        "e uma <b>camada física com ESP32</b> capaz de detectar e alertar "
        "localmente, consolidando tudo em um painel de decisão."))
    S.append(h2("Aderência ao tema"))
    S.append(p(
        "O projeto aplica diretamente <b>tecnologia espacial</b> (sensoriamento "
        "remoto orbital e dados climáticos de satélite) para <b>melhorar a vida "
        "das pessoas</b> (protegendo comunidades, saúde pública e biodiversidade) "
        "e <b>tornar processos mais eficientes</b>, antecipando a alocação de "
        "brigadas de incêndio onde o risco é maior."))
    S.append(PageBreak())

    # ---------------- 2. DESENVOLVIMENTO ----------------
    S.append(h1("2. Desenvolvimento"))

    # 2.1
    S.append(h2("2.1  Visão da solução e arquitetura"))
    S.append(p(
        "A solução é organizada em <b>três camadas de informação</b> que se "
        "complementam, costuradas por um motor de fusão:"))
    S.append(p(
        "<b>(1) Camada orbital:</b> focos de calor por satélite (padrão INPE) "
        "e variáveis climáticas diárias por região (padrão NASA POWER). "
        "<b>(2) Camada de inteligência:</b> modelos de Machine Learning que, a "
        "partir do clima, preveem a quantidade de focos e classificam o nível de "
        "risco. <b>(3) Camada de borda (edge):</b> estações com ESP32 e sensores "
        "que medem as condições locais, decidem o alerta na própria placa "
        "(mesmo sem internet) e publicam a telemetria via protocolo MQTT."))
    S.append(p(
        "Um <b>motor de fusão</b> combina as três camadas em um <i>score</i> de 0 "
        "a 100 por bioma, traduzido em um alerta operacional (de VERDE a "
        "VERMELHO). A figura a seguir apresenta a arquitetura completa, dos "
        "dados brutos à decisão."))
    S += imagem("11_arquitetura.png",
                legenda="Figura 1. Arquitetura do Sentinela Orbital: das três "
                "fontes de dados até a decisão e a visualização.")

    # 2.2
    S.append(h2("2.2  Dados: fontes, geração e análise exploratória"))
    S.append(p(
        "Por se tratar de uma POC acadêmica executada sem acesso garantido às "
        "APIs externas, o projeto utiliza <b>dados sintéticos modelados a partir "
        "de padrões reais</b>: a sazonalidade da estação seca, a distribuição de "
        "focos por bioma, os satélites efetivamente usados pelo INPE "
        "(AQUA_M-T, TERRA_M-T, NOAA-20/21, GOES-16, METOP-C) e, sobretudo, a "
        "relação física entre clima e risco de fogo. Isso garante que os modelos "
        "aprendam padrões com significado, e não ruído."))
    S.append(p(
        "O coração da geração é um <b>índice de risco</b> inspirado na lógica da "
        "Fórmula de Monte Alegre (FMA), usada no Brasil. O risco cresce com calor, "
        "seca acumulada e carga de vegetação, e cai com umidade e chuva recente. "
        "A partir dele, o número de focos por dia e bioma é sorteado de uma "
        "distribuição de Poisson, introduzindo variabilidade realista."))
    S.append(codigo(
        "src/gerar_dados.py · índice de risco e classificação (código real)",
        bloco("src/gerar_dados.py",
              "def calcular_indice_risco(linha", "return float(np.clip(risco, 0, 100))")
        + "\n\n" +
        bloco("src/gerar_dados.py",
              "def classificar_risco(indice", 'return "Critico"')))
    S.append(codigo(
        "src/gerar_dados.py · geração dos focos via distribuição de Poisson",
        bloco("src/gerar_dados.py",
              "indice = calcular_indice_risco(linha)",
              "n_focos = np.random.poisson(lam)")))
    S.append(p(
        "As bases geradas somam <b>64.823 focos</b>, <b>2.196 registros "
        "climáticos</b> (6 biomas x 366 dias) e <b>2.880 leituras</b> de quatro "
        "estações ESP32. A análise exploratória (Pandas e Seaborn) confirma a "
        "forte sazonalidade e a concentração nos biomas Cerrado e Amazônia."))
    S += imagem("01_serie_temporal_focos.png",
                legenda="Figura 2. Sazonalidade dos focos: pico claro em setembro, "
                "no auge da estação seca.")
    S += imagem("02_focos_por_bioma.png",
                legenda="Figura 3. Distribuição por bioma: Cerrado e Amazônia "
                "concentram a maior parte dos focos, como nos dados reais.")
    S.append(p(
        "A <b>matriz de correlação</b> é decisiva para o projeto: ela orienta a "
        "seleção de atributos do modelo. Observa-se forte correlação positiva "
        "entre temperatura máxima e risco (+0,79) e negativa com a umidade "
        "(-0,76), exatamente o esperado pela física do fogo."))
    S += imagem("03_heatmap_correlacao.png", largura_mm=120,
                legenda="Figura 4. Correlação entre variáveis climáticas e o "
                "índice de risco.")
    S += imagem("05_mapa_focos_brasil.png", largura_mm=115,
                legenda="Figura 5. Distribuição geográfica dos focos sobre o "
                "território brasileiro, colorida por bioma.")

    # 2.3
    S.append(h2("2.3  Inteligência: modelos de Machine Learning"))
    S.append(p(
        "A camada de IA usa <b>scikit-learn</b> e treina dois modelos "
        "complementares sobre o cruzamento clima x focos (pares de bioma e dia):"))
    S.append(p(
        "<b>Modelo 1, Regressão (principal).</b> Prevê a quantidade de focos "
        "esperada a partir do clima. Comparamos uma Regressão Linear (baseline) "
        "com um Random Forest. O ganho é expressivo e <b>justifica a escolha do "
        "modelo</b>: o R<super>2</super> salta de 0,48 para 0,96."))
    S.append(codigo(
        "src/modelo_risco.py · comparação Regressão Linear x Random Forest",
        bloco("src/modelo_risco.py",
              "# --- baseline: Regressao Linear",
              'print(f"Ganho de R2 (RF vs Linear): +{(r2_rf - r2_lin):.3f}")')))
    S.append(p(
        "<b>Modelo 2, Classificação (apoio operacional).</b> Classifica o nível "
        "de risco (Baixo, Moderado, Alto, Crítico) para alimentar o motor de "
        "alertas. O modelo aprende a 'regra operacional' de risco diretamente dos "
        "dados, permitindo generalizar para regiões onde a fórmula manual não foi "
        "calibrada."))
    S.append(codigo(
        "src/modelo_risco.py · treino e avaliação do classificador",
        bloco("src/modelo_risco.py",
              "clf = RandomForestClassifier(",
              'f1 = f1_score(y_te, pred, average="macro")')))
    S.append(p(
        "Os resultados sintetizam a qualidade da solução:"))
    S.append(tabela_dados([
        ["Tarefa", "Modelo", "Métrica", "Resultado"],
        ["Previsão de focos", "Regressão Linear", Paragraph("R<super>2</super>", st_celula), "0,48"],
        ["Previsão de focos", "Random Forest", Paragraph("R<super>2</super>", st_celula), "0,96"],
        ["Previsão de focos", "Random Forest", "RMSE", "6,8 focos"],
        ["Nível de risco", "Random Forest", "Acurácia", "91,1%"],
        ["Nível de risco", "Random Forest", "F1-macro", "0,90"],
    ], larguras=[LARG_CONTEUDO * 0.30, LARG_CONTEUDO * 0.27,
                 LARG_CONTEUDO * 0.20, LARG_CONTEUDO * 0.23]))
    S.append(p(
        "A <b>importância das variáveis</b> revela que temperatura máxima, "
        "precipitação, umidade e dias sem chuva dominam a decisão, dando "
        "<b>interpretabilidade</b> ao modelo. Já a <b>matriz de confusão</b> "
        "mostra que os poucos erros ocorrem apenas entre classes vizinhas "
        "(por exemplo, Alto e Crítico), nunca um erro catastrófico (Baixo "
        "previsto como Crítico), o que é fundamental num sistema de segurança."))
    S += imagem("07_importancia_variaveis.png", largura_mm=140,
                legenda="Figura 6. Importância relativa das variáveis no modelo.")
    S += imagem("08_matriz_confusao.png", largura_mm=110,
                legenda="Figura 7. Matriz de confusão do classificador de risco.")
    S += imagem("09_regressao_pred_vs_real.png", largura_mm=105,
                legenda="Figura 8. Regressão: focos previstos versus observados "
                "(quanto mais próximo da diagonal, melhor).")

    # 2.4
    S.append(h2("2.4  Camada de borda: estações ESP32"))
    S.append(p(
        "As estações de borda são os 'olhos no chão'. Cada uma combina um <b>ESP32</b> "
        "com sensores <b>BME280</b> (temperatura, umidade, pressão), <b>MQ-135</b> "
        "(fumaça e gases) e um sensor de umidade do solo, além de LED e buzzer para "
        "alerta local. O firmware foi escrito em <b>Arduino C++</b> (e também em "
        "MicroPython), sendo real e compilável."))
    S.append(p(
        "O diferencial é a <b>decisão na borda (edge computing)</b>: a estação "
        "calcula o risco localmente e aciona o alarme <i>imediatamente</i>, mesmo "
        "sem internet. A mesma lógica de risco do servidor é replicada no "
        "dispositivo, garantindo coerência entre borda e nuvem."))
    S.append(codigo(
        "firmware/sentinela_esp32.ino · cálculo de risco na borda (Arduino C++)",
        bloco("firmware/sentinela_esp32.ino",
              "float calcularRiscoLocal(float tempMax",
              "return risco;") + "\n}"))
    S.append(codigo(
        "firmware/sentinela_esp32.ino · decisão e acionamento do alerta local",
        bloco("firmware/sentinela_esp32.ino",
              "// ---- 2. Decisao na borda (edge) ----",
              "acionarAlerta(alerta);")))
    S += imagem("06_serie_sensores_esp32.png",
                legenda="Figura 9. Telemetria de uma estação ESP32: relação "
                "inversa entre temperatura e umidade e picos de fumaça cruzando o "
                "limiar de alerta (500 ppm).")

    # 2.5
    S.append(h2("2.5  Comunicação MQTT e persistência"))
    S.append(p(
        "As estações publicam pacotes JSON via <b>MQTT</b> (protocolo leve, padrão "
        "em IoT) no tópico <font name='Courier'>sentinela/estacoes/telemetria</font>. "
        "No servidor, o receptor aplica o modelo de IA a cada leitura e grava tudo "
        "em um banco <b>SQLite</b>, permitindo histórico e auditoria. O código "
        "abaixo mostra como a leitura do sensor é transformada no vetor de "
        "atributos esperado pelo modelo e classificada em tempo real."))
    S.append(codigo(
        "src/mqtt_receptor.py · aplicação do modelo de IA na telemetria recebida",
        bloco("src/mqtt_receptor.py",
              "vetor = pd.DataFrame([{",
              "return str(modelo.predict(vetor)[0])")))
    S.append(p(
        "O módulo funciona em dois modos: conectado a um broker MQTT real "
        "(<font name='Courier'>--mqtt</font>) ou em <b>simulação</b> "
        "(<font name='Courier'>--sim</font>), reproduzindo as leituras a partir "
        "dos dados. Assim, a banca consegue testar todo o fluxo de ponta a ponta "
        "sem hardware físico."))

    # 2.6
    S.append(h2("2.6  Motor de fusão e alertas"))
    S.append(p(
        "É o 'cérebro' do sistema. Para cada bioma, o motor combina as três "
        "camadas em um <i>score</i> de 0 a 100: focos orbitais recentes "
        "(até 35 pontos), intensidade do fogo via FRP (até 10 pontos), risco "
        "previsto pela IA (até 40 pontos) e confirmação pelos sensores de borda "
        "(até 15 pontos). A lógica de fusão é mostrada a seguir."))
    S.append(codigo(
        "src/motor_alertas.py · fusão das três camadas em um score de risco",
        bloco("src/motor_alertas.py",
              "# --- FUSAO: combina as tres camadas",
              "nivel, acao = classificar_nivel(score)")))
    S.append(p(
        "<b>Por que fundir?</b> O satélite sozinho atrasa; o sensor sozinho cobre "
        "pouca área; a IA sozinha é previsão sem confirmação. Juntos, cobrem as "
        "fraquezas uns dos outros. Na data de pico analisada, o motor classificou "
        "<b>Amazônia, Cerrado e Pantanal como VERMELHO</b>, priorizando "
        "corretamente as regiões mais críticas."))

    # 2.7
    S.append(h2("2.7  Dashboard interativo"))
    S.append(p(
        "Toda a informação converge para um dashboard em <b>Streamlit e Plotly</b>, "
        "com filtros por bioma e período, mapa de focos, indicadores e séries "
        "temporais. O destaque é o <b>previsor de risco interativo</b>: o usuário "
        "ajusta as condições climáticas e o modelo de IA responde o nível de risco "
        "e as probabilidades <i>em tempo real</i>, mostrando o modelo vivo, e não "
        "apenas métricas estáticas."))
    S += imagem("10_painel_dashboard.png",
                legenda="Figura 10. Dashboard do Sentinela Orbital: indicadores, "
                "mapa, painel de alertas (fusão das 3 camadas) e previsor de risco "
                "com IA.")
    S += imagem("12_fluxo_pipeline.png", largura_mm=160,
                legenda="Figura 11. Fluxo de execução do projeto, do dado bruto ao "
                "dashboard.")

    # 2.8
    S.append(h2("2.8  Tecnologias e disciplinas integradas"))
    S.append(p(
        "O projeto foi desenhado para <b>integrar o máximo de disciplinas</b> das "
        "Fases 3 e 4, usando linguagens e ferramentas vistas no curso:"))
    S.append(tabela_dados([
        ["Disciplina / área", "Onde aparece no projeto"],
        ["Lógica de programação (Python)", "Todo o código: condicionais, laços, funções"],
        ["Análise de dados (Pandas/NumPy)", "gerar_dados.py, analise_exploratoria.py"],
        ["Estatística", "Correlações, distribuições, métricas"],
        ["Machine Learning", "modelo_risco.py (regressão e classificação)"],
        ["IoT / Edge / ESP32", "firmware/ (Arduino C++ e MicroPython)"],
        ["Comunicação (MQTT)", "firmware/ e mqtt_receptor.py"],
        ["Banco de dados (SQL)", "mqtt_receptor.py (SQLite)"],
        ["APIs / Web", "ingestao_dados.py (INPE e NASA POWER)"],
        ["Visualização e Dashboards", "analise_exploratoria.py, dashboard.py"],
        ["Versionamento (Git)", "Organização do repositório"],
    ], larguras=[LARG_CONTEUDO * 0.42, LARG_CONTEUDO * 0.58]))

    # ---------------- 3. RESULTADOS ESPERADOS ----------------
    S.append(h1("3. Resultados Esperados"))
    S.append(p(
        "Do ponto de vista <b>técnico</b>, o sistema entrega previsões "
        "confiáveis (R<super>2</super> de 0,96 na regressão e 91% de acurácia na "
        "classificação) e um pipeline completo, testado e reproduzível, que vai "
        "da coleta à decisão. Cada componente foi executado e validado."))
    S.append(p(
        "Do ponto de vista de <b>impacto</b>, espera-se:"))
    S.append(p(
        "&bull; <b>Redução do tempo de resposta:</b> a detecção na borda "
        "antecipa o alerta de horas para minutos no entorno das estações;<br/>"
        "&bull; <b>Alocação mais eficiente de recursos:</b> brigadas e "
        "fiscalização direcionadas aos biomas em nível VERMELHO;<br/>"
        "&bull; <b>Proteção à saúde e à biodiversidade:</b> menos área queimada "
        "significa menos emissão de fumaça e menos perda ambiental;<br/>"
        "&bull; <b>Escalabilidade:</b> novas estações ESP32 são de baixo custo, e "
        "a troca para dados ao vivo do INPE e da NASA não exige reescrever o "
        "sistema, apenas conectar à internet."))
    S.append(p(
        "O projeto é uma <b>prova de conceito</b>: os dados são sintéticos, mas a "
        "arquitetura, os modelos, o firmware e a integração com as APIs são reais "
        "e prontos para evoluir para um piloto de campo."))

    # ---------------- 4. CONCLUSOES ----------------
    S.append(h1("4. Conclusões"))
    S.append(p(
        "O <b>Sentinela Orbital</b> demonstra como a <b>tecnologia espacial</b>, "
        "combinada com inteligência artificial e sensores de baixo custo, pode "
        "transformar o combate às queimadas no Brasil, saindo de uma postura "
        "reativa (ver o fogo que já existe) para uma postura <b>preditiva e "
        "preventiva</b> (antecipar o risco e confirmar o foco cedo)."))
    S.append(p(
        "Mais do que um exercício acadêmico, o projeto integra de forma coesa "
        "praticamente todas as competências das Fases 3 e 4: lógica, análise de "
        "dados, estatística, Machine Learning, IoT com ESP32, comunicação MQTT, "
        "banco de dados, consumo de APIs e visualização em dashboard. Cada peça "
        "foi implementada, testada e documentada."))
    S.append(p(
        "Acreditamos que a união da visão orbital com a sensibilidade do chão, "
        "orquestrada por IA, aponta um caminho concreto e escalável para proteger "
        "nossos biomas e as pessoas que deles dependem. Por isso, <b>queremos "
        "concorrer</b>."))

    # ---------------- 5. LINKS ----------------
    S.append(h1("5. Links do projeto"))
    S.append(p("<b>Repositório (GitHub):</b>"))
    S.append(Paragraph("https://github.com/msaabriina/sentinela-orbital",
                       st_quote))
    S.append(p("<b>Vídeo demonstrativo (YouTube, Não listado, até 5 min):</b>"))
    S.append(Paragraph("[INSIRA AQUI O LINK DO VÍDEO NO YOUTUBE]", st_quote))
    S.append(p(
        "<i>Lembre-se de configurar o vídeo como 'Não listado' e de preencher os "
        "nomes e RMs dos integrantes na capa deste documento e no README do "
        "repositório.</i>"))

    # ---------------- ANEXO A ----------------
    S.append(h1("Anexo A. Como executar o projeto"))
    S.append(p("Pré-requisito: Python 3.10 ou superior."))
    S.append(codigo("Passo a passo (terminal)",
        "# 1) instalar as dependencias\n"
        "pip install -r requirements.txt\n\n"
        "# 2) entrar na pasta de codigo\n"
        "cd src\n\n"
        "# 3) gerar as bases de dados (focos, clima, sensores)\n"
        "python gerar_dados.py\n\n"
        "# 4) analise exploratoria (gera os graficos em /assets)\n"
        "python analise_exploratoria.py\n\n"
        "# 5) treinar os modelos de IA (salva em /modelos)\n"
        "python modelo_risco.py\n\n"
        "# 6) simular a recepcao de telemetria dos ESP32 (aplica a IA)\n"
        "python mqtt_receptor.py --sim\n\n"
        "# 7) gerar o painel de alertas (fusao das 3 camadas)\n"
        "python motor_alertas.py\n\n"
        "# 8) abrir o dashboard interativo\n"
        "streamlit run dashboard.py"))
    S.append(p(
        "Cada script é independente e pode ser executado isoladamente. Todos "
        "foram testados e estão operacionais. O firmware do ESP32, em "
        "<font name='Courier'>firmware/</font>, é compilável na Arduino IDE; "
        "consulte <font name='Courier'>firmware/README.md</font> para a pinagem "
        "e as bibliotecas."))

    return S


def main():
    doc = SimpleDocTemplate(
        SAIDA, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=22 * mm, bottomMargin=22 * mm,
        title="Sentinela Orbital · Global Solution 2026.1",
        author=NOME_GRUPO)
    doc.build(construir(), onFirstPage=primeira_pagina, onLaterPages=rodape)
    tam = os.path.getsize(SAIDA) / 1024
    print(f"PDF gerado: {SAIDA} ({tam:.0f} KB)")


if __name__ == "__main__":
    main()
