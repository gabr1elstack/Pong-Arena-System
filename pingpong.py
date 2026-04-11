import pygame
import sqlite3
import os
import math

# ==============
# BANCO DE DADOS
# ==============

DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(DIRETORIO_ATUAL, "dados")
CAMINHO_DB = os.path.join(PASTA_DADOS, "banco.db")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "minhasenha123")

if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

def conectar():
    conn = sqlite3.connect(CAMINHO_DB)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jogadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT,
        telefone TEXT,
        vitorias INTEGER DEFAULT 0,
        derrotas INTEGER DEFAULT 0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    con.commit()
    con.close()

def inserir_ou_encontrar(nome, email, telefone):
    if not nome or not nome.strip():
        return False
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("SELECT id FROM jogadores WHERE nome=?", (nome.strip(),))
        existe = cur.fetchone()
        if existe:
            cur.execute(
                "UPDATE jogadores SET email=?, telefone=? WHERE nome=?",
                (email.strip() if email else None,
                 telefone.strip() if telefone else None,
                 nome.strip())
            )
        else:
            cur.execute(
                "INSERT INTO jogadores (nome, email, telefone) VALUES (?, ?, ?)",
                (nome.strip(), email.strip() if email else None,
                 telefone.strip() if telefone else None)
            )
        con.commit()
        con.close()
        return True
    except sqlite3.Error:
        con.close()
        return False

def registrar_partida(vencedor, perdedor):
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("UPDATE jogadores SET vitorias = vitorias + 1 WHERE nome=?", (vencedor,))
        cur.execute("UPDATE jogadores SET derrotas = derrotas + 1 WHERE nome=?", (perdedor,))
        con.commit()
        return True
    except sqlite3.Error:
        con.rollback()
        return False
    finally:
        con.close()

def top_jogadores(limite=5):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT nome, vitorias, derrotas
        FROM jogadores
        ORDER BY vitorias DESC
        LIMIT ?
    """, (limite,))
    ranking = cur.fetchall()
    con.close()
    return [dict(j) for j in ranking]

# ====================
# INICIALIZAÇÃO PYGAME
# ====================
pygame.init()
LARGURA, ALTURA = 900, 650
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("PING PONG PRO")
clock = pygame.time.Clock()

# ==============================
# PALETA DE CORES
# ==============================
COR_FUNDO       = (8, 8, 18)
COR_FUNDO2      = (12, 12, 28)
COR_NEON_CYAN   = (0, 240, 200)
COR_NEON_PINK   = (255, 30, 120)
COR_NEON_YELLOW = (255, 220, 0)
COR_BRANCO      = (255, 255, 255)
COR_CINZA_ESC   = (30, 30, 50)
COR_CINZA_MED   = (80, 80, 110)
COR_CINZA_CLR   = (160, 160, 190)
COR_ERRO        = (255, 60, 80)
COR_SUCESSO     = (0, 220, 120)
COR_P1          = COR_NEON_CYAN
COR_P2          = COR_NEON_PINK

# ==============================
# FONTES
# ==============================
fonte_titulo    = pygame.font.SysFont("Consolas", 38, bold=True)
fonte_subtitulo = pygame.font.SysFont("Consolas", 18)
fonte_label     = pygame.font.SysFont("Consolas", 18)
fonte_input     = pygame.font.SysFont("Consolas", 20)
fonte_placar    = pygame.font.SysFont("Consolas", 72, bold=True)
fonte_btn       = pygame.font.SysFont("Consolas", 20, bold=True)
fonte_resultado = pygame.font.SysFont("Consolas", 48, bold=True)
fonte_ranking   = pygame.font.SysFont("Consolas", 22)
fonte_header    = pygame.font.SysFont("Consolas", 26, bold=True)
fonte_small     = pygame.font.SysFont("Consolas", 16)
fonte_nomes     = pygame.font.SysFont("Consolas", 20, bold=True)

# ==============================
# UTILITÁRIOS DE DESENHO
# ==============================
def desenhar_grade(surface, tick):
    """Grade animada no fundo."""
    espaco = 50
    offset = int(tick * 0.3) % espaco
    cor_grade = (18, 18, 38)
    for x in range(-espaco + offset, LARGURA + espaco, espaco):
        pygame.draw.line(surface, cor_grade, (x, 0), (x, ALTURA))
    for y in range(0, ALTURA + espaco, espaco):
        pygame.draw.line(surface, cor_grade, (0, y), (LARGURA, y))

def desenhar_borda_neon(surface, rect, cor, espessura=2, raio=8, glow=True):
    """Borda com efeito neon/glow."""
    if glow:
        cor_glow = (*cor[:3], 40)
        s = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(s, cor_glow, s.get_rect(), border_radius=raio + 4)
        surface.blit(s, (rect.x - 10, rect.y - 10))
    pygame.draw.rect(surface, cor, rect, espessura, border_radius=raio)

def desenhar_texto_centralizado(surface, texto, fonte, cor, y):
    surf = fonte.render(texto, True, cor)
    surface.blit(surf, (LARGURA // 2 - surf.get_width() // 2, y))

def desenhar_linha_divisora(surface, y, cor=COR_CINZA_ESC):
    pygame.draw.line(surface, cor, (40, y), (LARGURA - 40, y), 1)

def pulsar(tick, velocidade=0.05, minimo=150, maximo=255):
    """Retorna valor pulsante para efeitos de brilho."""
    return int(minimo + (maximo - minimo) * (0.5 + 0.5 * math.sin(tick * velocidade)))

# ==============================
# CLASSE INPUT BOX MELHORADA
# ==============================
class InputBox:
    def __init__(self, x, y, w, h, label="", placeholder="", cor_ativa=COR_NEON_CYAN):
        self.rect        = pygame.Rect(x, y, w, h)
        self.label       = label
        self.placeholder = placeholder
        self.cor_ativa   = cor_ativa
        self.text        = ""
        self.active      = False
        self.tick        = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_UP:
                return "proximo"
            elif len(self.text) < 40:
                self.text += event.unicode

        return None

    def draw(self, surface):
        self.tick += 1

        # Fundo do input
        fundo = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        fundo.fill((20, 20, 40, 200))
        surface.blit(fundo, self.rect.topleft)

        # Borda
        if self.active:
            alpha = pulsar(self.tick, velocidade=0.08, minimo=180, maximo=255)
            cor_borda = (*self.cor_ativa[:3],)
            desenhar_borda_neon(surface, self.rect, cor_borda, espessura=2, raio=6)
            # Linha inferior highlight
            pygame.draw.line(surface, self.cor_ativa,
                             (self.rect.x + 6, self.rect.bottom - 2),
                             (self.rect.right - 6, self.rect.bottom - 2), 2)
        else:
            pygame.draw.rect(surface, COR_CINZA_ESC, self.rect, 1, border_radius=6)

        # Label
        lbl = fonte_label.render(self.label, True,
                                  self.cor_ativa if self.active else COR_CINZA_MED)
        surface.blit(lbl, (self.rect.x, self.rect.y - 22))

        # Texto ou placeholder
        if self.text:
            txt_surf = fonte_input.render(self.text, True, COR_BRANCO)
        else:
            txt_surf = fonte_input.render(self.placeholder, True, COR_CINZA_MED)
        surface.blit(txt_surf, (self.rect.x + 12, self.rect.y + self.rect.height // 2 - txt_surf.get_height() // 2))

        # Cursor piscante
        if self.active and (self.tick // 30) % 2 == 0:
            cursor_x = self.rect.x + 12 + fonte_input.size(self.text)[0] + 2
            cursor_y1 = self.rect.y + 8
            cursor_y2 = self.rect.bottom - 8
            pygame.draw.line(surface, self.cor_ativa, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

    def validar(self):
        return len(self.text.strip()) > 0

# ==============================
# BOTÃO
# ==============================
class Botao:
    def __init__(self, x, y, w, h, texto, cor=COR_NEON_CYAN):
        self.rect  = pygame.Rect(x, y, w, h)
        self.texto = texto
        self.cor   = cor
        self.tick  = 0

    def draw(self, surface):
        self.tick += 1
        mouse = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse)

        # Fundo
        alpha = 220 if hover else 160
        fundo = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        r, g, b = self.cor
        fundo.fill((r // 4, g // 4, b // 4, alpha))
        surface.blit(fundo, self.rect.topleft)

        # Borda
        desenhar_borda_neon(surface, self.rect, self.cor, espessura=2, raio=8, glow=hover)

        # Texto
        cor_txt = COR_BRANCO if hover else self.cor
        txt = fonte_btn.render(self.texto, True, cor_txt)
        surface.blit(txt, (self.rect.centerx - txt.get_width() // 2,
                           self.rect.centery - txt.get_height() // 2))

    def clicado(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                self.rect.collidepoint(event.pos))

# ==============================
# TELA DE LOGIN
# ==============================
def tela_login():
    margem_y   = 110
    espaco_y   = 75
    col1_x     = 60
    col2_x     = 480
    largura_in = 340

    # Jogador 1
    p1_n = InputBox(col1_x, margem_y,            largura_in, 44, "NOME",     "ex: João Silva",   COR_P1)
    p1_e = InputBox(col1_x, margem_y + espaco_y, largura_in, 44, "EMAIL",    "ex: joao@mail.com", COR_P1)
    p1_t = InputBox(col1_x, margem_y + espaco_y*2, largura_in, 44, "TELEFONE", "ex: 11999998888", COR_P1)

    # Jogador 2
    p2_n = InputBox(col2_x, margem_y,            largura_in, 44, "NOME",     "ex: Maria Silva",   COR_P2)
    p2_e = InputBox(col2_x, margem_y + espaco_y, largura_in, 44, "EMAIL",    "ex: maria@mail.com", COR_P2)
    p2_t = InputBox(col2_x, margem_y + espaco_y*2, largura_in, 44, "TELEFONE", "ex: 11988887777", COR_P2)

    inputs        = [p1_n, p1_e, p1_t, p2_n, p2_e, p2_t]
    btn           = Botao(LARGURA // 2 - 130, 555, 260, 52, "▶  INICIAR PARTIDA", COR_NEON_CYAN)
    mensagem_erro = ""
    tempo_erro    = 0
    tick_global   = 0

    while True:
        tick_global += 1
        tela.fill(COR_FUNDO)
        desenhar_grade(tela, tick_global)

        # ---- Header ----
        # Linha topo decorativa
        pygame.draw.line(tela, COR_NEON_CYAN, (0, 0), (LARGURA, 0), 3)

        # Título principal
        titulo1 = fonte_titulo.render("PING", True, COR_NEON_CYAN)
        titulo2 = fonte_titulo.render(" PONG ", True, COR_BRANCO)
        titulo3 = fonte_titulo.render("PRO", True, COR_NEON_PINK)
        total_w = titulo1.get_width() + titulo2.get_width() + titulo3.get_width()
        tx = LARGURA // 2 - total_w // 2
        tela.blit(titulo1, (tx, 14))
        tela.blit(titulo2, (tx + titulo1.get_width(), 14))
        tela.blit(titulo3, (tx + titulo1.get_width() + titulo2.get_width(), 14))

        sub = fonte_small.render("CADASTRO DE JOGADORES", True, COR_CINZA_MED)
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 58))

        desenhar_linha_divisora(tela, 80)

        # ---- Cards dos jogadores ----
        card1 = pygame.Rect(col1_x - 16, 90, largura_in + 32, espaco_y * 3 + 14)
        card2 = pygame.Rect(col2_x - 16, 90, largura_in + 32, espaco_y * 3 + 14)
        pygame.draw.rect(tela, (14, 14, 30), card1, border_radius=10)
        pygame.draw.rect(tela, (14, 14, 30), card2, border_radius=10)
        desenhar_borda_neon(tela, card1, COR_P1, espessura=1, raio=10, glow=False)
        desenhar_borda_neon(tela, card2, COR_P2, espessura=1, raio=10, glow=False)

        # Tags P1 / P2
        tag1 = fonte_nomes.render("● JOGADOR 1", True, COR_P1)
        tag2 = fonte_nomes.render("● JOGADOR 2", True, COR_P2)
        tela.blit(tag1, (col1_x, 68))
        tela.blit(tag2, (col2_x, 68))

        # Tecla dica
        dica = fonte_small.render("↑  para avançar campo", True, COR_CINZA_MED)
        tela.blit(dica, (LARGURA // 2 - dica.get_width() // 2, 510))

        # Inputs
        for inp in inputs:
            inp.draw(tela)

        # Botão
        btn.draw(tela)

        # Erro
        if tempo_erro > 0:
            alpha = min(255, tempo_erro * 4)
            txt_erro = fonte_label.render(f"⚠  {mensagem_erro}", True, COR_ERRO)
            tela.blit(txt_erro, (LARGURA // 2 - txt_erro.get_width() // 2, 526))
            tempo_erro -= 1

        # Linha rodapé
        pygame.draw.line(tela, COR_NEON_PINK, (0, ALTURA - 3), (LARGURA, ALTURA - 3), 3)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            for idx, inp in enumerate(inputs):
                resultado = inp.handle_event(event)
                if resultado == "proximo":
                    inp.active = False
                    proximo = inputs[(idx + 1) % len(inputs)]
                    proximo.active = True
                    break

            if btn.clicado(event):
                if not p1_n.validar():
                    mensagem_erro = "Nome do Jogador 1 é obrigatório"
                    tempo_erro = 150
                elif not p1_e.validar():
                    mensagem_erro = "Email do Jogador 1 é obrigatório"
                    tempo_erro = 150
                elif not p2_n.validar():
                    mensagem_erro = "Nome do Jogador 2 é obrigatório"
                    tempo_erro = 150
                elif not p2_e.validar():
                    mensagem_erro = "Email do Jogador 2 é obrigatório"
                    tempo_erro = 150
                elif p1_n.text.strip() == p2_n.text.strip():
                    mensagem_erro = "Os jogadores devem ter nomes diferentes"
                    tempo_erro = 150
                else:
                    email1 = p1_e.text.strip() if "@" in p1_e.text else f"{p1_n.text.strip()}@game.local"
                    email2 = p2_e.text.strip() if "@" in p2_e.text else f"{p2_n.text.strip()}@game.local"
                    r1 = inserir_ou_encontrar(p1_n.text.strip(), email1, p1_t.text.strip())
                    r2 = inserir_ou_encontrar(p2_n.text.strip(), email2, p2_t.text.strip())
                    if not r1 or not r2:
                        mensagem_erro = "Erro ao registrar jogador no banco"
                        tempo_erro = 150
                    else:
                        return {
                            "p1_nome": p1_n.text.strip(), "p1_email": email1, "p1_tel": p1_t.text.strip(),
                            "p2_nome": p2_n.text.strip(), "p2_email": email2, "p2_tel": p2_t.text.strip()
                        }

        pygame.display.flip()
        clock.tick(60)

# ==============================
# TELA DO JOGO
# ==============================
def jogar(nome1, nome2):
    bola    = pygame.Rect(LARGURA // 2 - 10, ALTURA // 2 - 10, 18, 18)
    vel_x, vel_y = 5, 5
    vel_max = 13

    p1 = pygame.Rect(28, ALTURA // 2 - 55, 12, 110)
    p2 = pygame.Rect(LARGURA - 40, ALTURA // 2 - 55, 12, 110)
    pts1, pts2 = 0, 0
    tick = 0
    MAX_PONTOS = 10

    # Rastro da bola
    rastro = []

    while True:
        tick += 1
        tela.fill(COR_FUNDO)
        desenhar_grade(tela, tick)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_w] and p1.top > 0:       p1.y -= 7
        if teclas[pygame.K_s] and p1.bottom < ALTURA: p1.y += 7
        if teclas[pygame.K_UP] and p2.top > 0:       p2.y -= 7
        if teclas[pygame.K_DOWN] and p2.bottom < ALTURA: p2.y += 7

        # Movimento
        bola.x += vel_x
        bola.y += vel_y
        rastro.append(bola.center)
        if len(rastro) > 12:
            rastro.pop(0)

        if bola.top <= 0 or bola.bottom >= ALTURA:
            vel_y *= -1

        if bola.colliderect(p1) or bola.colliderect(p2):
            vel_x *= -1.05
            if abs(vel_x) > vel_max:
                vel_x = vel_max if vel_x > 0 else -vel_max

        if bola.left <= 0:
            pts2 += 1
            bola.center = (LARGURA // 2, ALTURA // 2)
            vel_x = 5
            rastro.clear()

        if bola.right >= LARGURA:
            pts1 += 1
            bola.center = (LARGURA // 2, ALTURA // 2)
            vel_x = -5
            rastro.clear()

        # ---- Desenho ----
        # Linha central tracejada
        for y in range(0, ALTURA, 28):
            pygame.draw.rect(tela, COR_CINZA_ESC, (LARGURA // 2 - 2, y, 4, 14))

        # Rastro da bola
        for i, pos in enumerate(rastro):
            alpha = int(200 * i / len(rastro))
            raio  = max(2, int(8 * i / len(rastro)))
            s = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*COR_BRANCO, alpha), (raio, raio), raio)
            tela.blit(s, (pos[0] - raio, pos[1] - raio))

        # Bola
        pygame.draw.ellipse(tela, COR_BRANCO, bola)
        glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (255, 255, 255, 50), (20, 20), 18)
        tela.blit(glow_s, (bola.centerx - 20, bola.centery - 20))

        # Raquetes com glow
        desenhar_borda_neon(tela, p1, COR_P1, espessura=0, raio=4, glow=True)
        pygame.draw.rect(tela, COR_P1, p1, border_radius=4)
        desenhar_borda_neon(tela, p2, COR_P2, espessura=0, raio=4, glow=True)
        pygame.draw.rect(tela, COR_P2, p2, border_radius=4)

        # Placar
        s1 = fonte_placar.render(str(pts1), True, COR_P1)
        s2 = fonte_placar.render(str(pts2), True, COR_P2)
        tela.blit(s1, (LARGURA // 4 - s1.get_width() // 2, 12))
        tela.blit(s2, (3 * LARGURA // 4 - s2.get_width() // 2, 12))

        # Nomes dos jogadores
        n1 = fonte_nomes.render(nome1.upper(), True, COR_P1)
        n2 = fonte_nomes.render(nome2.upper(), True, COR_P2)
        tela.blit(n1, (LARGURA // 4 - n1.get_width() // 2, ALTURA - 28))
        tela.blit(n2, (3 * LARGURA // 4 - n2.get_width() // 2, ALTURA - 28))

        # Barra de progresso dos pontos
        barra_w = 180
        for i in range(MAX_PONTOS):
            cor = COR_P1 if i < pts1 else COR_CINZA_ESC
            pygame.draw.rect(tela, cor, (40 + i * (barra_w // MAX_PONTOS + 2), ALTURA - 10, barra_w // MAX_PONTOS, 6), border_radius=3)
        for i in range(MAX_PONTOS):
            cor = COR_P2 if i < pts2 else COR_CINZA_ESC
            pygame.draw.rect(tela, cor, (LARGURA - 40 - barra_w + i * (barra_w // MAX_PONTOS + 2), ALTURA - 10, barra_w // MAX_PONTOS, 6), border_radius=3)

        # Bordas coloridas
        pygame.draw.line(tela, COR_P1, (0, 0), (0, ALTURA), 4)
        pygame.draw.line(tela, COR_P2, (LARGURA - 4, 0), (LARGURA - 4, ALTURA), 4)

        if pts1 >= MAX_PONTOS or pts2 >= MAX_PONTOS:
            vencedor = nome1 if pts1 >= MAX_PONTOS else nome2
            perdedor = nome2 if pts1 >= MAX_PONTOS else nome1
            return vencedor, perdedor

        pygame.display.flip()
        clock.tick(60)

# ==============================
# TELA DE RESULTADO
# ==============================
def tela_resultado(vencedor, perdedor):
    tick = 0
    ranking = top_jogadores(5)

    while True:
        tick += 1
        tela.fill(COR_FUNDO)
        desenhar_grade(tela, tick)

        # Bordas topo/rodapé
        pygame.draw.line(tela, COR_NEON_YELLOW, (0, 0), (LARGURA, 0), 3)
        pygame.draw.line(tela, COR_NEON_YELLOW, (0, ALTURA - 3), (LARGURA, ALTURA - 3), 3)

        # Troféu animado
        brilho = pulsar(tick, velocidade=0.06)
        cor_vitoria = (brilho, brilho, 0)

        titulo = fonte_resultado.render(f"🏆  {vencedor.upper()}  VENCEU!", True, COR_NEON_YELLOW)
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 28))

        sub = fonte_small.render(f"derrota de {perdedor}", True, COR_CINZA_MED)
        tela.blit(sub, (LARGURA // 2 - sub.get_width() // 2, 86))

        desenhar_linha_divisora(tela, 115, COR_NEON_YELLOW)

        # Ranking
        header = fonte_header.render("RANKING  GLOBAL", True, COR_NEON_CYAN)
        tela.blit(header, (LARGURA // 2 - header.get_width() // 2, 128))

        y = 172
        for i, j in enumerate(ranking, 1):
            # Fundo da linha
            linha_rect = pygame.Rect(LARGURA // 2 - 240, y - 4, 480, 36)
            if j['nome'] == vencedor:
                pygame.draw.rect(tela, (0, 50, 40), linha_rect, border_radius=6)
                desenhar_borda_neon(tela, linha_rect, COR_NEON_CYAN, espessura=1, raio=6, glow=False)

            # Medalhas
            medalha = ["🥇", "🥈", "🥉", "④", "⑤"][i - 1]
            cor_pos  = [COR_NEON_YELLOW, COR_CINZA_CLR, (210, 140, 70), COR_CINZA_MED, COR_CINZA_MED][i - 1]

            pos_surf = fonte_ranking.render(f"{i}.", True, cor_pos)
            nom_surf = fonte_ranking.render(j['nome'], True, COR_BRANCO if j['nome'] == vencedor else COR_CINZA_CLR)
            vit_surf = fonte_ranking.render(f"{j['vitorias']}V  {j['derrotas']}D", True, COR_NEON_CYAN)

            tela.blit(pos_surf, (LARGURA // 2 - 220, y))
            tela.blit(nom_surf, (LARGURA // 2 - 190, y))
            tela.blit(vit_surf, (LARGURA // 2 + 130, y))
            y += 46

        desenhar_linha_divisora(tela, y + 10)

        # Instruções
        inst = fonte_small.render("ENTER  →  nova partida        ESC  →  sair", True, COR_CINZA_MED)
        tela.blit(inst, (LARGURA // 2 - inst.get_width() // 2, ALTURA - 40))

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    return "novo"
                if ev.key == pygame.K_ESCAPE:
                    return "sair"

        clock.tick(60)

# ==============================
# LOOP PRINCIPAL
# ==============================
if __name__ == "__main__":
    criar_tabela()

    while True:
        try:
            dados = tela_login()
            if dados is None:
                break

            vencedor, perdedor = jogar(dados['p1_nome'], dados['p2_nome'])
            registrar_partida(vencedor, perdedor)

            if tela_resultado(vencedor, perdedor) == "sair":
                break

        except Exception as e:
            print(f"Erro: {e}")
            pygame.quit()
            exit()

    pygame.quit()
