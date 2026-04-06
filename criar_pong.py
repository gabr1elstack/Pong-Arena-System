#!/usr/bin/env python3
import sqlite3
import pandas as pd
from datetime import datetime, timedelta


conn = sqlite3.connect('pong_game.db')
cursor = conn.cursor()

# Tabela de jogadores
cursor.execute('''
CREATE TABLE IF NOT EXISTS jogadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    nivel INTEGER DEFAULT 1,
    pontos_totais INTEGER DEFAULT 0,
    partidas_jogadas INTEGER DEFAULT 0,
    partidas_vencidas INTEGER DEFAULT 0,
    ativo BOOLEAN DEFAULT 1
)
''')

# Tabela de partidas
cursor.execute('''
CREATE TABLE IF NOT EXISTS partidas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jogador1_id INTEGER NOT NULL,
    jogador2_id INTEGER NOT NULL,
    placar1 INTEGER,
    placar2 INTEGER,
    vencedor_id INTEGER,
    data_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_fim DATETIME,
    duracao_segundos INTEGER,
    status TEXT DEFAULT 'completa',
    FOREIGN KEY (jogador1_id) REFERENCES jogadores(id),
    FOREIGN KEY (jogador2_id) REFERENCES jogadores(id),
    FOREIGN KEY (vencedor_id) REFERENCES jogadores(id)
)
''')

# Tabela de sessões online
cursor.execute('''
CREATE TABLE IF NOT EXISTS sessoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jogador_id INTEGER NOT NULL,
    conectado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    desconectado_em DATETIME,
    status TEXT DEFAULT 'online',
    FOREIGN KEY (jogador_id) REFERENCES jogadores(id)
)
''')

# Tabela de conquistas/badges
cursor.execute('''
CREATE TABLE IF NOT EXISTS conquistas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jogador_id INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT,
    data_obtencao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jogador_id) REFERENCES jogadores(id)
)
''')

# Limpar dados antigos
cursor.execute('DELETE FROM conquistas')
cursor.execute('DELETE FROM sessoes')
cursor.execute('DELETE FROM partidas')
cursor.execute('DELETE FROM jogadores')

# Inserir jogadores de teste
jogadores = [
    ('ProPlayer', 'pro@pong.com'),
    ('NovaMão', 'novamao@pong.com'),
    ('Champion', 'champion@pong.com'),
    ('Casual', 'casual@pong.com'),
    ('Speedster', 'speed@pong.com'),
]

cursor.executemany(
    'INSERT INTO jogadores (username, email) VALUES (?, ?)',
    jogadores
)

# Inserir partidas (simuladas)
partidas = [
    (1, 2, 11, 8, 1, datetime.now() - timedelta(hours=2), (datetime.now() - timedelta(hours=2)) + timedelta(minutes=5), 300),
    (2, 3, 7, 11, 3, datetime.now() - timedelta(hours=1, minutes=30), (datetime.now() - timedelta(hours=1, minutes=30)) + timedelta(minutes=4), 240),
    (1, 3, 11, 9, 1, datetime.now() - timedelta(hours=1), (datetime.now() - timedelta(hours=1)) + timedelta(minutes=6), 360),
    (4, 5, 5, 11, 5, datetime.now() - timedelta(minutes=45), (datetime.now() - timedelta(minutes=45)) + timedelta(minutes=3), 180),
    (2, 4, 9, 11, 4, datetime.now() - timedelta(minutes=30), (datetime.now() - timedelta(minutes=30)) + timedelta(minutes=4), 240),
    (1, 4, 11, 6, 1, datetime.now() - timedelta(minutes=15), (datetime.now() - timedelta(minutes=15)) + timedelta(minutes=5), 300),
]

cursor.executemany(
    '''INSERT INTO partidas 
    (jogador1_id, jogador2_id, placar1, placar2, vencedor_id, data_inicio, data_fim, duracao_segundos) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
    partidas
)

# Inserir sessões online
sessoes = [
    (1, datetime.now() - timedelta(minutes=5), None, 'online'),
    (3, datetime.now() - timedelta(minutes=15), datetime.now() - timedelta(minutes=10), 'offline'),
    (5, datetime.now() - timedelta(minutes=2), None, 'online'),
]

cursor.executemany(
    'INSERT INTO sessoes (jogador_id, conectado_em, desconectado_em, status) VALUES (?, ?, ?, ?)',
    sessoes
)

# Inserir conquistas
conquistas = [
    (1, 'PRIMEIRA_VITORIA', 'Venceu a primeira partida'),
    (1, 'CINCO_VITORIAS', 'Conquistou 5 vitórias'),
    (3, 'PRIMEIRA_VITORIA', 'Venceu a primeira partida'),
    (5, 'PRIMEIRA_VITORIA', 'Venceu a primeira partida'),
]

cursor.executemany(
    'INSERT INTO conquistas (jogador_id, tipo, descricao) VALUES (?, ?, ?)',
    conquistas
)

# Atualizar estatísticas dos jogadores
cursor.execute('''
UPDATE jogadores SET
    partidas_jogadas = (
        SELECT COUNT(*) FROM partidas 
        WHERE jogador1_id = jogadores.id OR jogador2_id = jogadores.id
    ),
    partidas_vencidas = (
        SELECT COUNT(*) FROM partidas 
        WHERE vencedor_id = jogadores.id
    )
''')

conn.commit()

# Exibir resultados
print("=" * 70)
print("RANKING DE JOGADORES")
print("=" * 70)
df_jogadores = pd.read_sql_query('''
    SELECT id, username, nivel, partidas_jogadas, partidas_vencidas,
           ROUND(CAST(partidas_vencidas AS FLOAT) / NULLIF(partidas_jogadas, 0) * 100, 1) as taxa_vitoria
    FROM jogadores
    ORDER BY partidas_vencidas DESC
''', conn)
print(df_jogadores.to_string(index=False))

print("\n" + "=" * 70)
print("ÚLTIMAS PARTIDAS")
print("=" * 70)
df_partidas = pd.read_sql_query('''
    SELECT 
        p.id,
        j1.username as jogador1,
        j2.username as jogador2,
        p.placar1,
        p.placar2,
        jv.username as vencedor,
        ROUND(p.duracao_segundos / 60.0, 1) as duracao_min,
        strftime('%d/%m %H:%M', p.data_inicio) as data
    FROM partidas p
    JOIN jogadores j1 ON p.jogador1_id = j1.id
    JOIN jogadores j2 ON p.jogador2_id = j2.id
    LEFT JOIN jogadores jv ON p.vencedor_id = jv.id
    ORDER BY p.data_inicio DESC
''', conn)
print(df_partidas.to_string(index=False))

print("\n" + "=" * 70)
print("JOGADORES ONLINE AGORA")
print("=" * 70)
df_online = pd.read_sql_query('''
    SELECT j.username, s.status, strftime('%H:%M', s.conectado_em) as conectado_em
    FROM sessoes s
    JOIN jogadores j ON s.jogador_id = j.id
    WHERE s.status = 'online'
''', conn)
print(df_online.to_string(index=False) if len(df_online) > 0 else "Ninguém online agora")

print("\n" + "=" * 70)
print("CONQUISTAS DESBLOQUEADAS")
print("=" * 70)
df_conquistas = pd.read_sql_query('''
    SELECT j.username, c.tipo, c.descricao, strftime('%d/%m %H:%M', c.data_obtencao) as data
    FROM conquistas c
    JOIN jogadores j ON c.jogador_id = j.id
    ORDER BY c.data_obtencao DESC
''', conn)
print(df_conquistas.to_string(index=False))

conn.close()
print("\n✓ Banco 'pong_game.db' criado para Ping Pong multiplayer!")
