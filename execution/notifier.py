"""
Módulo de Alerta Automático (Disparador de Crise)
Envia notificações imediatas aos gestores para feedbacks classificados como 'Crítico'.
Suporta SMTP real com contingência resiliente para gravação estruturada em .tmp/alerts.log.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

TMP_DIR = os.path.join(BASE_DIR, ".tmp")
ALERTS_LOG_FILE = os.path.join(TMP_DIR, "alerts.log")


def _ensure_tmp_dir():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR, exist_ok=True)


def dispatch_crisis_alert(feedback_item):
    """
    Dispara o alerta de crise.
    Verifica se credenciais SMTP estão presentes; caso contrário ou em falha de conexão,
    grava imediatamente em .tmp/alerts.log e emite aviso no terminal.
    """
    _ensure_tmp_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Consolidação segura dos dados do cliente (evita campos vazios ou nulos)
    nome = feedback_item.get("nome") or "Cliente não identificado"
    contato = feedback_item.get("contato") or "Não informado"
    pedido_id = feedback_item.get("pedido_id") or "S/N"
    nota = feedback_item.get("nota") or "N/A"
    comentario = feedback_item.get("comentario") or ""
    tags = ", ".join(feedback_item.get("tags", []))
    resumo = feedback_item.get("resumo") or "Feedback Crítico registrado"

    # Preparação da mensagem de alerta estruturada
    alert_entry = (
        f"================================================================================\n"
        f"[ALERTA DE CRISE - BURGERSYNC OURINHOS]\n"
        f"Data/Hora: {timestamp}\n"
        f"ID Registro: {feedback_item.get('id', 'N/A')}\n"
        f"Pedido: #{pedido_id} | Nota: {nota}/5\n"
        f"Cliente: {nome} | Contato: {contato}\n"
        f"Tags Detectadas: [{tags}]\n"
        f"Resumo da IA: {resumo}\n"
        f"Comentário do Cliente:\n\"{comentario}\"\n"
        f"================================================================================\n\n"
    )

    # 1. Registro determinístico garantido no log de auditoria
    with open(ALERTS_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(alert_entry)

    # Emissão no terminal com sanitização de caracteres para Windows CP1252
    print(f"\n[ALERTA CRÍTICO DETECTADO] Pedido: #{pedido_id} | Cliente: {nome} | Contato: {contato}")
    print(f"[ALERTA CRÍTICO] Motivo: {resumo}")

    # 2. Tentativa de despacho SMTP se configurado no ambiente
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT", "587")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_RECIPIENT", "gerencia@burgersync.com.br")

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 [CRISE URGENTE] Feedback Crítico - Pedido #{pedido_id} ({nome})"
            msg["From"] = smtp_user
            msg["To"] = recipient

            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #fff4f2; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 2px solid #e74c3c; padding: 25px;">
                  <h2 style="color: #c0392b; margin-top: 0;">🚨 Alerta de Crise de Cliente</h2>
                  <p>Um feedback com sentimento <strong>Crítico</strong> foi recebido pela BurgerSync Ourinhos:</p>
                  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr><td style="padding: 8px; font-weight: bold; width: 120px;">Pedido:</td><td style="padding: 8px;">#{pedido_id}</td></tr>
                    <tr style="background: #fdf2f2;"><td style="padding: 8px; font-weight: bold;">Cliente:</td><td style="padding: 8px;">{nome}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Contato:</td><td style="padding: 8px;">{contato}</td></tr>
                    <tr style="background: #fdf2f2;"><td style="padding: 8px; font-weight: bold;">Nota:</td><td style="padding: 8px;">⭐ {nota}/5</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Tags:</td><td style="padding: 8px;">{tags}</td></tr>
                    <tr style="background: #fdf2f2;"><td style="padding: 8px; font-weight: bold;">Diagnóstico IA:</td><td style="padding: 8px; color: #c0392b; font-weight: bold;">{resumo}</td></tr>
                  </table>
                  <div style="background: #f9f9f9; padding: 15px; border-left: 4px solid #e74c3c; margin-bottom: 20px;">
                    <strong>Depoimento do Cliente:</strong>
                    <p style="font-style: italic; margin-top: 8px;">"{comentario}"</p>
                  </div>
                  <p style="font-size: 13px; color: #7f8c8d;">Acesse o Painel Administrativo BurgerSync para registrar o contato e marcar como tratado.</p>
                </div>
              </body>
            </html>
            """
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            print(f"[SUCESSO] Alerta enviado via SMTP para {recipient}")
            return {"success": True, "method": "smtp", "recipient": recipient}
        except Exception as e:
            print(f"[AVISO] Falha no disparo SMTP ({e}). Alerta preservado em .tmp/alerts.log.")
            return {"success": True, "method": "log_fallback", "error": str(e)}
    else:
        # Fallback padrão quando SMTP não estiver explicitado no .env
        print(f"[INFO] SMTP não configurado no .env. Alerta registrado com sucesso em .tmp/alerts.log.")
        return {"success": True, "method": "log_fallback", "recipient": recipient}
