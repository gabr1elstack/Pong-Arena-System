from debugpy import connect
import pygame
import sqlite3
import os


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

def inserir_jogador(nome, email, telefone):
    if not nome or not nome.strip():
        return False
    if "@" not in email or not email.strip():
        return False
    
    con = conectar()
    cur = con.cursor()
    try:
        cur.execute("""
        INSERT INTO jogadores (nome, email, telefone) 
        VALUES (?, ?, ?)""",
        (nome.strip(), email.strip(), telefone.strip() if telefone else None)
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error:
        return False
    finally:
        con.close()

def inserir_ou_encontrar(nome, email, telefone):
    """Se jogador existe, atualiza. Senão, cria novo."""
    if not nome or not nome.strip():
        return False
    
    con = conectar()
    cur = con.cursor()
    
    try:
        # Busca se existe
        cur.execute("SELECT id FROM jogadores WHERE nome=?", (nome.strip(),))
        existe = cur.fetchone()
        
        if existe:
            # Já existe, atualiza email se necessário
            cur.execute(
                "UPDATE jogadores SET email=?, telefone=? WHERE nome=?",
                (email.strip() if email else None, 
                 telefone.strip() if telefone else None,
                 nome.strip())
            )
            con.commit()
            con.close()
            return True
        
        # Não existe, cria novo
        cur.execute("""
        INSERT INTO jogadores (nome, email, telefone) 
        VALUES (?, ?, ?)""",
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
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Ping Pong Master Pro")
clock = pygame.time.Clock()

# Fontes (criadas UMA VEZ, não a cada frame)
fonte_titulo = pygame.font.SysFont("Arial", 40, bold=True)
fonte_label = pygame.font.SysFont("Arial", 24)
fonte_pequena = pygame.font.SysFont("Arial", 22)
fonte_placar = pygame.font.SysFont("Arial", 50)
fonte_btn = pygame.font.SysFont("Arial", 24, bold=True)
fonte_resultado = pygame.font.SysFont("Arial", 50, bold=True)
fonte_ranking = pygame.font.SysFont("Arial", 26)
fonte_header = pygame.font.SysFont("Arial", 30, bold=True)

# ====================
# UI: CLASSE CAIXA DE TEXTO
# ====================
class InputBox:
    def __init__(self, x, y, w, h, label=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (100, 100, 100)
        self.text = ""
        self.label = label
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.color = (100, 150, 255) if self.active else (100, 100, 100)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 40:
                self.text += event.unicode

    def draw(self, screen):
        lbl = fonte_label.render(self.label, True, (200, 200, 200))
        screen.blit(lbl, (self.rect.x, self.rect.y - 25))
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=5)
        txt_surface = fonte_label.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surface, (self.rect.x + 10, self.rect.y + 7))

    def validar(self):
        return len(self.text.strip()) > 0

# ====================
# TELA DE LOGIN
# ====================
def tela_login():
    col1_x = 50
    col2_x = 430
    y_start = 140
    espaco = 80

    p1_n = InputBox(col1_x, y_start, 300, 40, "Nome Jogador 1")
    p1_e = InputBox(col1_x, y_start + espaco, 300, 40, "Email P1")
    p1_t = InputBox(col1_x, y_start + espaco*2, 300, 40, "Telefone P1")

    p2_n = InputBox(col2_x, y_start, 300, 40, "Nome Jogador 2")
    p2_e = InputBox(col2_x, y_start + espaco, 300, 40, "Email P2")
    p2_t = InputBox(col2_x, y_start + espaco*2, 300, 40, "Telefone P2")

    inputs = [p1_n, p1_e, p1_t, p2_n, p2_e, p2_t]
    btn_rect = pygame.Rect(LARGURA//2 - 100, 500, 200, 50)
    mensagem_erro = ""
    tempo_erro = 0

    while True:
        tela.fill((20, 20, 30))
        
        txt_titulo = fonte_titulo.render("CADASTRO DE JOGADORES", True, (0, 255, 200))
        tela.blit(txt_titulo, (LARGURA//2 - txt_titulo.get_width()//2, 30))

        for i in inputs:
            i.draw(tela)

        # Botão
        mouse_pos = pygame.mouse.get_pos()
        cor_btn = (0, 200, 150) if btn_rect.collidepoint(mouse_pos) else (0, 150, 100)
        pygame.draw.rect(tela, cor_btn, btn_rect, border_radius=10)
        txt_btn = fonte_btn.render("INICIAR PARTIDA", True, (255, 255, 255))
        tela.blit(txt_btn, (btn_rect.centerx - txt_btn.get_width()//2, btn_rect.centery - txt_btn.get_height()//2))

        # Mensagem de erro
        if tempo_erro > 0:
            txt_erro = fonte_pequena.render(mensagem_erro, True, (255, 100, 100))
            tela.blit(txt_erro, (LARGURA//2 - txt_erro.get_width()//2, 460))
            tempo_erro -= 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            for i in inputs:
                i.handle_event(event)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect.collidepoint(event.pos):
                    # Validação
                    if not p1_n.validar():
                        mensagem_erro = "Nome do Jogador 1 inválido"
                        tempo_erro = 120
                    elif not p1_e.validar():
                        mensagem_erro = "Email P1 inválido"
                        tempo_erro = 120
                    elif not p2_n.validar():
                        mensagem_erro = "Nome do Jogador 2 inválido"
                        tempo_erro = 120
                    elif not p2_e.validar():
                        mensagem_erro = "Email P2 inválido"
                        tempo_erro = 120
                    elif p1_n.text.strip() == p2_n.text.strip():
                        mensagem_erro = "Jogadores não podem ter o mesmo nome"
                        tempo_erro = 120
                    else:
                        # Tenta salvar no banco
                        email1 = p1_e.text.strip() if p1_e.text.strip() and "@" in p1_e.text else f"{p1_n.text.strip()}@game.local"
                        email2 = p2_e.text.strip() if p2_e.text.strip() and "@" in p2_e.text else f"{p2_n.text.strip()}@game.local"
                        
                        r1 = inserir_ou_encontrar(p1_n.text.strip(), email1, p1_t.text.strip())
                        r2 = inserir_ou_encontrar(p2_n.text.strip(), email2, p2_t.text.strip())
                        
                        if not r1 or not r2:
                            mensagem_erro = "Erro ao registrar jogador"
                            tempo_erro = 120
                        else:
                            return {
                                "p1_nome": p1_n.text.strip(),
                                "p1_email": email1,
                                "p1_tel": p1_t.text.strip(),
                                "p2_nome": p2_n.text.strip(),
                                "p2_email": email2,
                                "p2_tel": p2_t.text.strip()
                            }

        pygame.display.flip()
        clock.tick(60)

# ====================
# TELA DO JOGO
# ====================
def jogar(nome1, nome2):
    bola = pygame.Rect(LARGURA // 2 - 10, ALTURA // 2 - 10, 20, 20)
    vel_bola_x, vel_bola_y = 5, 5
    vel_max = 12  # Limite de velocidade
    
    player1 = pygame.Rect(30, ALTURA // 2 - 50, 12, 100)
    player2 = pygame.Rect(LARGURA - 42, ALTURA // 2 - 50, 12, 100)
    pontos1, pontos2 = 0, 0

    while True:
        tela.fill((10, 10, 15))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # Controles
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_w] and player1.top > 0:
            player1.y -= 7
        if teclas[pygame.K_s] and player1.bottom < ALTURA:
            player1.y += 7
        if teclas[pygame.K_UP] and player2.top > 0:
            player2.y -= 7
        if teclas[pygame.K_DOWN] and player2.bottom < ALTURA:
            player2.y += 7

        # Movimento bola
        bola.x += vel_bola_x
        bola.y += vel_bola_y
        
        if bola.top <= 0 or bola.bottom >= ALTURA:
            vel_bola_y *= -1
        
        if bola.colliderect(player1) or bola.colliderect(player2):
            vel_bola_x *= -1.05
            # Limita velocidade máxima
            if abs(vel_bola_x) > vel_max:
                vel_bola_x = vel_max if vel_bola_x > 0 else -vel_max

        # Pontuação
        if bola.left <= 0:
            pontos2 += 1
            bola.center = (LARGURA // 2, ALTURA // 2)
            vel_bola_x = 5
        
        if bola.right >= LARGURA:
            pontos1 += 1
            bola.center = (LARGURA // 2, ALTURA // 2)
            vel_bola_x = -5

        # Desenho
        pygame.draw.rect(tela, (0, 255, 200), player1)
        pygame.draw.rect(tela, (255, 0, 100), player2)
        pygame.draw.ellipse(tela, (255, 255, 255), bola)
        pygame.draw.aaline(tela, (50, 50, 50), (LARGURA//2, 0), (LARGURA//2, ALTURA))
        
        # Placar
        s1 = fonte_placar.render(str(pontos1), True, (255, 255, 255))
        s2 = fonte_placar.render(str(pontos2), True, (255, 255, 255))
        tela.blit(s1, (LARGURA//4 - s1.get_width()//2, 20))
        tela.blit(s2, (3*LARGURA//4 - s2.get_width()//2, 20))

        # Verifica vitória
        if pontos1 >= 10 or pontos2 >= 10:
            vencedor = nome1 if pontos1 >= 10 else nome2
            perdedor = nome2 if pontos1 >= 10 else nome1
            return vencedor, perdedor

        pygame.display.flip()
        clock.tick(60)

# ====================
# TELA FINAL COM RANKING
# ====================
def tela_resultado(vencedor, perdedor):
    while True:
        tela.fill((20, 20, 30))
        
        # Título
        titulo = fonte_resultado.render(f"{vencedor} VENCEU!", True, (255, 255, 0))
        tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 30))

        # Ranking
        header = fonte_header.render("TOP 5 JOGADORES", True, (0, 255, 200))
        tela.blit(header, (LARGURA//2 - header.get_width()//2, 100))

        ranking = top_jogadores(5)
        y = 160
        for i, jogador in enumerate(ranking, 1):
            nome = jogador['nome']
            vitorias = jogador['vitorias']
            txt = fonte_ranking.render(f"{i}. {nome} --- {vitorias} Vitórias", True, (255, 255, 255))
            tela.blit(txt, (LARGURA // 2 - txt.get_width() // 2, y))
            y += 45

        # Instruções
        instrucao = fonte_pequena.render("ENTER = Nova Partida  |  ESC = Sair", True, (150, 150, 150))
        tela.blit(instrucao, (LARGURA // 2 - instrucao.get_width() // 2, 520))

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

# ====================
# LOOP PRINCIPAL
# ====================
if __name__ == "__main__":
    criar_tabela()
    
    while True:
        try:
            # Login
            dados = tela_login()
            if dados is None:
                break
            
            nome1 = dados['p1_nome']
            nome2 = dados['p2_nome']
            
            # Jogo
            vencedor, perdedor = jogar(nome1, nome2)
            
            # Registra resultado no banco
            registrar_partida(vencedor, perdedor)
            
            # Resultado
            acao = tela_resultado(vencedor, perdedor)
            if acao == "sair":
                break
        
        except Exception as e:
            print(f"Erro: {e}")
            pygame.quit()
            exit()
    
    pygame.quit()
