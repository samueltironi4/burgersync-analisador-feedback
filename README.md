# 🍔 BurgerSync Ourinhos - Avaliador de Feedback & Gestão de Crises

Sistema web completo e inteligente para coleta, categorização com IA (Google Gemini 3.6 Flash) e gestão operacional de avaliações dos clientes da hamburgueria artesanal BurgerSync em Ourinhos.

---

## 🚀 Funcionalidades Principais

1. **Página Pública de Feedback do Cliente (`/`):**
   - Interface moderna, responsiva e elegante com tema de hamburgueria artesanal.
   - Avaliação interativa por estrelas (1 a 5 estrelas).
   - Coleta de dados completos: Nome, WhatsApp/E-mail, Pedido/Cupom e Comentário.
   - Análise instantânea com retorno visual do diagnóstico de IA em modal.

2. **Inteligência Artificial (Google Gemini 3.6 Flash com Fallback Resiliente):**
   - Classificação em tempo real do sentimento: `Positivo`, `Neutro` ou `Crítico`.
   - Extração automática de tópicos/tags: `Sabor`, `Entrega`, `Atendimento`, `Temperatura`, `Embalagem`, `Preço`, `Higiene`, etc.
   - Diagnóstico resumido e cálculo de urgência.
   - Mecanismo determinístico de contingência local (*Self-Annealing*) que assume automaticamente se houver instabilidade de rede ou esgotamento de cotas.

3. **Disparador Automático de Alertas de Crise:**
   - Detecta feedbacks críticos imediatamente.
   - Suporte a envio de e-mails via SMTP com template HTML destacado para o gerente.
   - Fallback de auditoria determinístico: salva em `.tmp/alerts.log` e exibe aviso no terminal.

4. **Painel Administrativo Interativo (`/admin`):**
   - Contadores gerenciais em tempo real (Total, Positivos, Neutros, Críticos, Pendentes, Média de Estrelas).
   - Banner dinâmico de crise para atendimento prioritário de clientes insatisfeitos.
   - Filtros combinados por Sentimento, Status (`Pendente` / `Tratado`), Tags e Ordenação (Data, Urgência, Nota).
   - Checkboxes de ação rápida para marcar e desmarcar atendimentos como tratados.
   - Modal com histórico detalhado e depoimento completo.
   - Botão para exportação instantânea dos dados em formato JSON.

---

## 📂 Arquitetura de 3 Camadas

```
burguersync.analisadorFeedback/
├── directive/
│   └── projeto.md              # Camada 1: Diretiva, regras de negócio e self-annealing
├── execution/                  # Camada 3: Scripts determinísticos
│   ├── app.py                  # Servidor Web Flask e API REST
│   ├── analyzer.py             # Integração Gemini 3.6 Flash + Heurística
│   ├── notifier.py             # Disparador de Alertas SMTP + .tmp/alerts.log
│   ├── storage.py              # I/O seguro no banco JSON e cálculo de KPIs
│   └── github_deploy.py        # Publicação automatizada no GitHub
├── templates/                  # Frontend HTML5 (Jinja2)
│   ├── index.html              # Página do cliente
│   └── admin.html              # Painel administrativo
├── static/                     # Ativos visuais
│   ├── css/styles.css          # Design System artesanal escuro com acentos âmbar
│   └── js/
│       ├── app.js              # Lógica do formulário e estrelas
│       └── admin.js            # Lógica do dashboard, filtros e status
├── data/
│   └── feedbacks.json          # Banco de dados estruturado JSON
├── .tmp/
│   ├── alerts.log              # Log de auditoria de crises disparadas
│   └── requests/               # Rastreabilidade de requisições
├── tests/
│   └── test_flow.py            # Bateria completa de testes automatizados
├── run.bat                     # Inicializador rápido para Windows CMD
├── run.ps1                     # Inicializador PowerShell
├── requirements.txt            # Dependências Python
└── README.md                   # Documentação do projeto
```

---

## 🛠️ Como Executar

### 1. Pré-requisitos
- Python 3.10+ instalado
- Pacotes instalados:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Iniciar o Servidor
Dê um duplo-clique no arquivo `run.bat` ou execute no terminal:
```bash
python execution/app.py
```

### 3. Acessar as Interfaces
- **Página de Avaliação (Cliente):** [http://localhost:5000/](http://localhost:5000/)
- **Painel Administrativo:** [http://localhost:5000/admin](http://localhost:5000/admin)

### 4. Executar os Testes Automatizados
```bash
python -m unittest tests/test_flow.py
```

---

## 🔐 Configuração do `.env`
O arquivo `.env` na raiz aceita as seguintes variáveis:
```ini
GEMINI_API_KEY=sua_chave_gemini_aqui
GITHUB_PERSONAL_TOKEN=seu_token_github_aqui

# Opcional (para envio real de e-mails de crise via SMTP):
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@empresa.com
SMTP_PASSWORD=sua_senha_de_aplicativo
ALERT_RECIPIENT=gerencia@burgersync.com.br
```
