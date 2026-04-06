# 🎮 Pong Arena System

Um jogo de ping pong feito em Python, direto ao ponto. Sem firula. Aqui a ideia foi pegar algo simples e fazer bem feito: organizar código, cuidar dos detalhes e fazer tudo funcionar do jeito certo.

---

## 💡 Sobre o projeto

Esse projeto junta duas coisas:

* A parte visual, com interface rodando em tempo real
* A parte “por trás”, cuidando dos dados e da lógica

Enquanto o jogo roda, tem código trabalhando quieto: criando pasta, salvando jogador, registrando pontuação. Nada mágico, só código bem feito fazendo o serviço.

---

## ⚙️ O que rola no sistema

* Login para dois jogadores
* Criação automática da pasta de dados
* Conexão com banco SQLite
* Ranking salvo e atualizado
* Jogo rodando em tempo real com pontuação até 10

---

## 🛠️ Tecnologias

* Python
* Pygame
* SQLite

---

## 📂 Estrutura

```
pong-arena/
│
├── pingpong.py
├── criar_pong.py
│
├── dados/
│   └── jogadores.db
```
---

## ▶️ Como rodar

1. Clone:

```
git clone https://github.com/gabr1elstack/pong-arena-system.git
```

2. Entre na pasta:

```
cd pong-arena-system
```

3. Instale:

```
pip install pygame
```

4. Execute:

```
python main.py
```

---

## 🧠 Na prática

Tem coisa simples aqui que muita gente pula, mas faz diferença:

```python
if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

def conectar():
    conn = sqlite3.connect(CAMINHO_DB)
```

Isso aqui é o básico bem feito:

* garante que a pasta existe
* garante que o banco abre certo

Sem isso, o resto quebra.

---

## 📌 Próximos passos

* Modo contra IA
* Interface mais limpa
* Sons durante a partida
* Histórico de jogos

---

## 👨‍💻 Autor

Gabriel (gabr1elstack)

---

Projeto feito na prática, sem pular etapa. Testando, ajustando e repetindo até ficar redondo.
