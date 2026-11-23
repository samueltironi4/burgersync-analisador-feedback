"""
Módulo de Análise Inteligente de Feedbacks com Gemini e Fallback Determinístico.
Responsável pelo processamento de linguagem natural, classificação de sentimento e extração de tags.
"""

import json
import os
import re
import time
import uuid
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TMP_DIR = os.path.join(BASE_DIR, ".tmp")
REQUESTS_TMP_DIR = os.path.join(TMP_DIR, "requests")


def _ensure_tmp_dirs():
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(REQUESTS_TMP_DIR, exist_ok=True)


def heuristic_fallback_analysis(comentario, nota=None):
    """
    Classificador heurístico determinístico de contingência local.
    Garante resiliência completa mesmo se houver queda de rede, cota esgotada ou ausência de chave.
    """
    texto = (comentario or "").lower()
    
    # Palavras-chave de sentimentos
    palavras_criticas = [
        "horrivel", "horrível", "pessimo", "péssimo", "ruim", "frio", "atrasou", "demorou",
        "cru", "queimado", "estragado", "gosto ruim", "nojento", "cabelo", "falta", "errado",
        "decepcionado", "engano", "demorou demais", "sujo", "barata", "intoxicacao", "indigesto",
        "lixo", "vergonha", "nunca mais", "absurdo", "odiei"
    ]
    palavras_positivas = [
        "maravilhoso", "excelente", "otimo", "ótimo", "delicioso", "top", "perfeito", "rapido",
        "rápido", "quentinho", "melhor", "saboroso", "suculento", "adorei", "parabens", "parabéns",
        "incrivel", "incrível", "recomendo", "muito bom", "gostoso", "pontual", "nota 10"
    ]
    
    # Extração de tags por contexto
    tags = []
    if any(k in texto for k in ["sabor", "delicioso", "gostoso", "queimado", "cru", "salgado", "carne", "molho", "lanche", "hamburguer"]):
        tags.append("Sabor")
    if any(k in texto for k in ["entrega", "motoboy", "demorou", "atrasou", "chegou", "espera", "tempo", "pontual"]):
        tags.append("Entrega")
    if any(k in texto for k in ["atendimento", "garçom", "caixa", "educado", "grosseiro", "mal educado", "atendente"]):
        tags.append("Atendimento")
    if any(k in texto for k in ["frio", "quente", "quentinho", "gelado", "temperatura"]):
        tags.append("Temperatura")
    if any(k in texto for k in ["embalagem", "aberto", "amassado", "embrulho"]):
        tags.append("Embalagem")
    if any(k in texto for k in ["preço", "caro", "barato", "custo", "promoção"]):
        tags.append("Preço")
    if any(k in texto for k in ["sujo", "higiene", "cabelo", "limpeza"]):
        tags.append("Higiene")
        
    if not tags:
        tags.append("Geral")

    # Contagem de correspondências
    pontos_criticos = sum(1 for p in palavras_criticas if p in texto)
    pontos_positivos = sum(1 for p in palavras_positivas if p in texto)

    # Avaliação conjunta do texto e da nota numérica se fornecida
    if nota is not None:
        if nota <= 2:
            pontos_criticos += 3
        elif nota >= 4:
            pontos_positivos += 3

    if pontos_criticos > pontos_positivos or (nota is not None and nota <= 2):
        sentimento = "Crítico"
        urgencia = "Alta"
        resumo = "Feedback negativo demandando atenção imediata."
    elif pontos_positivos > pontos_criticos or (nota is not None and nota >= 4):
        sentimento = "Positivo"
        urgencia = "Baixa"
        resumo = "Cliente elogiou a experiência com a hamburgueria."
    else:
        sentimento = "Neutro"
        urgencia = "Média"
        resumo = "Avaliação neutra ou construtiva sobre o pedido."

    return {
        "sentimento": sentimento,
        "tags": list(set(tags)),
        "resumo": resumo,
        "urgencia": urgencia,
        "alerta_necessario": sentimento == "Crítico",
        "origem_analise": "heuristic_fallback"
    }


def analyze_feedback(comentario, nota=None, cliente_nome="Cliente"):
    """
    Executa a análise de IA via Google Gemini REST API com retries e fallback local.
    """
    _ensure_tmp_dirs()
    req_id = str(uuid.uuid4())[:8]
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Registro de entrada temporária na pasta .tmp/requests/
    payload_in = {
        "req_id": req_id,
        "timestamp": timestamp,
        "cliente_nome": cliente_nome,
        "nota": nota,
        "comentario": comentario
    }
    tmp_file = os.path.join(REQUESTS_TMP_DIR, f"req_{req_id}.json")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(payload_in, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[AVISO] GEMINI_API_KEY não configurada. Usando fallback heurístico.")
        fallback = heuristic_fallback_analysis(comentario, nota)
        _save_tmp_result(tmp_file, payload_in, fallback)
        return fallback

    prompt = f"""
Você é o especialista de qualidade da BurgerSync Ourinhos (hamburgueria artesanal).
Analise o feedback abaixo e responda RIGOROSAMENTE apenas em formato JSON válido:

Cliente: {cliente_nome}
Nota atribuída (1 a 5): {nota if nota else 'Não informada'}
Comentário: "{comentario}"

Regras:
1. "sentimento": Deve ser EXATAMENTE um destes 3: "Positivo", "Neutro", ou "Crítico".
   - Use "Crítico" se o cliente teve problemas com atraso grave, comida fria/crua/estragada, atendimento ruim, higiene ou expressou grande insatisfação.
   - Use "Positivo" se o cliente elogiou sabor, entrega, pontualidade, atendimento ou custo-benefício.
   - Use "Neutro" se o comentário for meramente informativo, misto sem tom ofensivo ou sem fortes opiniões.
2. "tags": Lista de tags relevantes encontradas (Ex: ["Sabor", "Entrega", "Atendimento", "Temperatura", "Embalagem", "Preço", "Higiene", "Geral"]).
3. "resumo": Uma frase curta resumindo o ponto principal do cliente.
4. "urgencia": "Alta" (se Crítico), "Média" (se Neutro com ressalvas), "Baixa" (se Positivo).
5. "alerta_necessario": true se "sentimento" for "Crítico", senão false.

Exemplo de formato esperado:
{{
  "sentimento": "Crítico",
  "tags": ["Entrega", "Temperatura"],
  "resumo": "Lanche chegou frio após 1 hora de atraso.",
  "urgencia": "Alta",
  "alerta_necessario": true
}}
"""

    model_names = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    # Tentativas com backoff exponencial
    max_retries = 3
    for attempt in range(max_retries):
        for model in model_names:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = requests.post(url, headers=headers, json=body, timeout=12)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        # Limpa possíveis blocos markdown ```json
                        clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                        clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE).strip()
                        parsed = json.loads(clean_json)

                        result = {
                            "sentimento": parsed.get("sentimento", "Neutro"),
                            "tags": parsed.get("tags", ["Geral"]),
                            "resumo": parsed.get("resumo", "Feedback avaliado por IA."),
                            "urgencia": parsed.get("urgencia", "Média"),
                            "alerta_necessario": parsed.get("alerta_necessario", parsed.get("sentimento") == "Crítico"),
                            "origem_analise": model
                        }
                        _save_tmp_result(tmp_file, payload_in, result)
                        return result
                elif response.status_code == 429:
                    # Rate limit, aguarda backoff
                    time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                # Falha de conexão ou timeout, tenta próximo modelo / tentativa
                pass

        time.sleep(1.0 * (attempt + 1))

    # Caso a API esteja inacessível ou sem resposta, ativa fallback determinístico
    print(f"[INFO] API Gemini inacessível no momento para req {req_id}. Ativando fallback determinístico.")
    fallback = heuristic_fallback_analysis(comentario, nota)
    _save_tmp_result(tmp_file, payload_in, fallback)
    return fallback


def _save_tmp_result(tmp_file, payload_in, result):
    try:
        combined = {
            "input": payload_in,
            "analysis": result
        }
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
