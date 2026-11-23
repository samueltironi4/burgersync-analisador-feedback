"""
Módulo de Armazenamento Estruturado (JSON Database)
Gerencia a persistência de feedbacks e logs com segurança e integridade de dados.
"""

import json
import os
import uuid
from datetime import datetime
from threading import Lock

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FEEDBACKS_FILE = os.path.join(DATA_DIR, "feedbacks.json")

_file_lock = Lock()


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FEEDBACKS_FILE):
        with open(FEEDBACKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def get_all_feedbacks():
    """Retorna todos os feedbacks salvos no banco JSON."""
    _ensure_data_dir()
    with _file_lock:
        try:
            with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []


def save_feedback(feedback_data):
    """
    Salva um novo feedback completo (dados do cliente + análise de IA).
    Atribui id, timestamp e status inicial 'Pendente'.
    """
    _ensure_data_dir()
    with _file_lock:
        feedbacks = []
        try:
            with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            feedbacks = []

        # Garante identificador e carimbo de data/hora
        if "id" not in feedback_data or not feedback_data["id"]:
            feedback_data["id"] = str(uuid.uuid4())
        
        if "timestamp" not in feedback_data or not feedback_data["timestamp"]:
            feedback_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if "status" not in feedback_data:
            feedback_data["status"] = "Pendente"

        # Adiciona no início da lista (mais recentes primeiro)
        feedbacks.insert(0, feedback_data)

        with open(FEEDBACKS_FILE, "w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)

        return feedback_data


def update_feedback_status(feedback_id, new_status):
    """Atualiza o status de um feedback ('Pendente' ou 'Tratado')."""
    _ensure_data_dir()
    with _file_lock:
        try:
            with open(FEEDBACKS_FILE, "r", encoding="utf-8") as f:
                feedbacks = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

        updated_item = None
        for item in feedbacks:
            if item.get("id") == feedback_id:
                item["status"] = new_status
                item["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_item = item
                break

        if updated_item:
            with open(FEEDBACKS_FILE, "w", encoding="utf-8") as f:
                json.dump(feedbacks, f, ensure_ascii=False, indent=2)

        return updated_item


def get_kpi_stats():
    """Calcula estatísticas agregadas em tempo real para o dashboard."""
    feedbacks = get_all_feedbacks()
    total = len(feedbacks)
    positivos = sum(1 for f in feedbacks if f.get("sentimento") == "Positivo")
    neutros = sum(1 for f in feedbacks if f.get("sentimento") == "Neutro")
    criticos = sum(1 for f in feedbacks if f.get("sentimento") == "Crítico")
    pendentes = sum(1 for f in feedbacks if f.get("status") == "Pendente")
    tratados = sum(1 for f in feedbacks if f.get("status") == "Tratado")

    # Média de avaliações (estrelas)
    notas = [f.get("nota") for f in feedbacks if isinstance(f.get("nota"), (int, float))]
    media_nota = round(sum(notas) / len(notas), 1) if notas else 5.0

    # Contagem de tags
    tag_counts = {}
    for f in feedbacks:
        for tag in f.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "total": total,
        "positivos": positivos,
        "neutros": neutros,
        "criticos": criticos,
        "pendentes": pendentes,
        "tratados": tratados,
        "media_nota": media_nota,
        "tags": tag_counts
    }
