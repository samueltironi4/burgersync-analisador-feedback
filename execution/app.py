"""
Servidor Web e API REST - BurgerSync Analisador de Feedback
Orquestra requisições de clientes, processamento com IA, banco de dados JSON e painel de gestão.
"""

import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv

import storage
import analyzer
import notifier

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


@app.route("/")
@app.route("/feedback")
def index():
    """Página web pública para envio de avaliações pelos clientes."""
    return render_template("index.html")


@app.route("/admin")
@app.route("/dashboard")
def admin():
    """Painel administrativo de gestão de feedbacks e análise de crises."""
    return render_template("admin.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Endpoint de verificação de integridade do serviço."""
    return jsonify({
        "status": "online",
        "service": "BurgerSync Feedback Analyzer",
        "version": "1.0.0"
    }), 200


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """
    Recebe uma avaliação do cliente, orquestra a análise com IA,
    armazena no banco JSON e aciona alerta imediato em caso de crise.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    nome = (data.get("nome") or "").strip()
    contato = (data.get("contato") or "").strip()
    pedido_id = (data.get("pedido_id") or "").strip()
    comentario = (data.get("comentario") or "").strip()
    
    # Tratamento da nota numérica
    nota_raw = data.get("nota")
    try:
        nota = int(nota_raw) if nota_raw is not None and str(nota_raw).isdigit() else None
    except Exception:
        nota = None

    if not comentario:
        return jsonify({
            "success": False,
            "error": "O campo de comentário ou feedback é obrigatório."
        }), 400

    # 1. Processamento da IA (Gemini com fallback determinístico)
    analysis = analyzer.analyze_feedback(
        comentario=comentario,
        nota=nota,
        cliente_nome=nome or "Cliente"
    )

    # 2. Montagem do registro estruturado completo
    feedback_record = {
        "nome": nome or "Anônimo",
        "contato": contato or "Não informado",
        "pedido_id": pedido_id or "S/N",
        "nota": nota if nota is not None else 5,
        "comentario": comentario,
        "sentimento": analysis.get("sentimento", "Neutro"),
        "tags": analysis.get("tags", ["Geral"]),
        "resumo": analysis.get("resumo", ""),
        "urgencia": analysis.get("urgencia", "Média"),
        "origem_analise": analysis.get("origem_analise", "local"),
        "alerta_disparado": False,
        "status": "Pendente"
    }

    # 3. Disparo de Alerta de Crise se 'Crítico'
    if analysis.get("sentimento") == "Crítico" or analysis.get("alerta_necessario"):
        alert_result = notifier.dispatch_crisis_alert(feedback_record)
        feedback_record["alerta_disparado"] = True
        feedback_record["alerta_info"] = alert_result

    # 4. Gravação no Banco Estruturado JSON
    saved_item = storage.save_feedback(feedback_record)

    return jsonify({
        "success": True,
        "message": "Feedback processado e registrado com sucesso!",
        "feedback": saved_item
    }), 201


@app.route("/api/feedbacks", methods=["GET"])
def list_feedbacks():
    """
    Lista feedbacks armazenados com suporte a filtros, busca e ordenação.
    """
    feedbacks = storage.get_all_feedbacks()

    # Filtros
    sentimento = request.args.get("sentimento")
    if sentimento and sentimento.lower() != "todos":
        feedbacks = [f for f in feedbacks if f.get("sentimento", "").lower() == sentimento.lower()]

    status_filter = request.args.get("status")
    if status_filter and status_filter.lower() != "todos":
        feedbacks = [f for f in feedbacks if f.get("status", "").lower() == status_filter.lower()]

    tag = request.args.get("tag")
    if tag and tag.lower() != "todos":
        feedbacks = [f for f in feedbacks if tag.lower() in [t.lower() for t in f.get("tags", [])]]

    search = request.args.get("search", "").strip().lower()
    if search:
        feedbacks = [
            f for f in feedbacks
            if search in (f.get("nome", "").lower())
            or search in (f.get("pedido_id", "").lower())
            or search in (f.get("comentario", "").lower())
            or search in (f.get("resumo", "").lower())
        ]

    # Ordenação
    sort_by = request.args.get("sort", "date_desc")
    if sort_by == "date_asc":
        feedbacks = sorted(feedbacks, key=lambda x: x.get("timestamp", ""))
    elif sort_by == "rating_desc":
        feedbacks = sorted(feedbacks, key=lambda x: x.get("nota", 0), reverse=True)
    elif sort_by == "rating_asc":
        feedbacks = sorted(feedbacks, key=lambda x: x.get("nota", 0))
    elif sort_by == "urgency":
        urgency_map = {"Alta": 3, "Média": 2, "Baixa": 1}
        feedbacks = sorted(feedbacks, key=lambda x: urgency_map.get(x.get("urgencia", "Média"), 0), reverse=True)
    else:  # date_desc
        feedbacks = sorted(feedbacks, key=lambda x: x.get("timestamp", ""), reverse=True)

    return jsonify({
        "success": True,
        "count": len(feedbacks),
        "feedbacks": feedbacks
    }), 200


@app.route("/api/feedback/<feedback_id>/status", methods=["PATCH"])
def update_status(feedback_id):
    """Alterna ou define o status de um feedback ('Pendente' <-> 'Tratado')."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if not new_status:
        # Se não fornecido, inverte o status atual
        all_f = storage.get_all_feedbacks()
        current = next((f for f in all_f if f.get("id") == feedback_id), None)
        if current:
            new_status = "Tratado" if current.get("status") == "Pendente" else "Pendente"
        else:
            new_status = "Tratado"

    if new_status not in ["Pendente", "Tratado"]:
        return jsonify({"success": False, "error": "Status inválido. Use 'Pendente' ou 'Tratado'."}), 400

    updated = storage.update_feedback_status(feedback_id, new_status)
    if not updated:
        return jsonify({"success": False, "error": "Feedback não encontrado."}), 404

    return jsonify({
        "success": True,
        "message": f"Status atualizado para {new_status}",
        "feedback": updated
    }), 200


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Retorna indicadores agregados (KPIs) para os gráficos e contadores do painel."""
    stats = storage.get_kpi_stats()
    return jsonify({
        "success": True,
        "stats": stats
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n=======================================================")
    print(f" BurgerSync Ourinhos - Servidor Web Ativo")
    print(f" Formulário do Cliente: http://localhost:{port}/")
    print(f" Painel Administrativo: http://localhost:{port}/admin")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
