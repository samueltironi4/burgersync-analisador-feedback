"""
Bateria de Testes Automatizados de Ponta a Ponta
BurgerSync Ourinhos - Avaliador de Feedback
"""

import os
import sys
import json
import unittest

# Ajuste do PATH para importar da pasta execution
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXECUTION_DIR = os.path.join(PROJECT_DIR, "execution")
sys.path.insert(0, EXECUTION_DIR)

import storage
import analyzer
import notifier
from app import app


class TestBurgerSyncSystem(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.tmp_dir = os.path.join(PROJECT_DIR, ".tmp")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def test_01_health_check(self):
        """Testa se o serviço web está online e respondendo."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode("utf-8"))
        self.assertEqual(data.get("status"), "online")
        print("[TESTE 1 PASSOU] Healthcheck online.")

    def test_02_heuristic_analyzer(self):
        """Testa o classificador determinístico de contingência local."""
        # Teste com elogio
        pos = analyzer.heuristic_fallback_analysis("O hamburguer estava maravilhoso e saboroso, entrega rápida!", 5)
        self.assertEqual(pos["sentimento"], "Positivo")
        self.assertIn("Sabor", pos["tags"])
        self.assertFalse(pos["alerta_necessario"])

        # Teste com crítica
        crit = analyzer.heuristic_fallback_analysis("Péssimo! Atrasou 2 horas, comida veio fria e estragada!", 1)
        self.assertEqual(crit["sentimento"], "Crítico")
        self.assertTrue(crit["alerta_necessario"])
        self.assertEqual(crit["urgencia"], "Alta")
        print("[TESTE 2 PASSOU] Analisador heurístico determinístico validado com sucesso.")

    def test_03_crisis_notifier_log_fallback(self):
        """Testa se o disparador de alertas registra o evento em .tmp/alerts.log."""
        sample_feedback = {
            "id": "test-alert-123",
            "nome": "Marcos Testador",
            "contato": "(14) 99999-0000",
            "pedido_id": "TEST-99",
            "nota": 1,
            "comentario": "Carne crua e cabelo no lanche. Quero meu dinheiro de volta!",
            "tags": ["Sabor", "Higiene"],
            "resumo": "Problema grave de higiene e cozimento.",
            "sentimento": "Crítico"
        }
        res = notifier.dispatch_crisis_alert(sample_feedback)
        self.assertTrue(res.get("success"))

        alerts_file = os.path.join(self.tmp_dir, "alerts.log")
        self.assertTrue(os.path.exists(alerts_file))
        with open(alerts_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("Marcos Testador", content)
            self.assertIn("TEST-99", content)
        print("[TESTE 3 PASSOU] Notifier de crise e log estruturado validados.")

    def test_04_submit_positive_feedback_api(self):
        """Testa envio de feedback positivo pela API REST."""
        payload = {
            "nome": "Juliana Santos",
            "contato": "juliana@email.com",
            "pedido_id": "2050",
            "nota": 5,
            "comentario": "Parabéns BurgerSync! Hambúrguer artesanal divino e atendimento impecável!"
        }
        res = self.client.post("/api/feedback", json=payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data.decode("utf-8"))
        self.assertTrue(data.get("success"))
        fb = data.get("feedback")
        self.assertEqual(fb.get("nome"), "Juliana Santos")
        self.assertEqual(fb.get("status"), "Pendente")
        self.assertIn(fb.get("sentimento"), ["Positivo", "Neutro"])
        print("[TESTE 4 PASSOU] Submissão de feedback positivo registrada.")

    def test_05_submit_critical_feedback_api_with_alert(self):
        """Testa envio de feedback crítico acionando alerta imediato."""
        payload = {
            "nome": "Roberto Alencar",
            "contato": "(14) 98765-4321",
            "pedido_id": "3099",
            "nota": 1,
            "comentario": "Horrível! O motoboy demorou 1h40, foi super grosseiro e o lanche estava completamente frio e amassado!"
        }
        res = self.client.post("/api/feedback", json=payload)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data.decode("utf-8"))
        fb = data.get("feedback")
        self.assertEqual(fb.get("sentimento"), "Crítico")
        self.assertTrue(fb.get("alerta_disparado"))
        self.assertIn("Entrega", fb.get("tags"))
        print("[TESTE 5 PASSOU] Feedback crítico processado com disparo automático de alerta.")

    def test_06_toggle_status_and_kpis(self):
        """Testa alternância de status para 'Tratado' e atualização de KPIs."""
        # Pega a lista
        list_res = self.client.get("/api/feedbacks")
        items = json.loads(list_res.data.decode("utf-8")).get("feedbacks", [])
        self.assertTrue(len(items) > 0)
        target_id = items[0]["id"]

        # Alterna para Tratado
        patch_res = self.client.patch(f"/api/feedback/{target_id}/status", json={"status": "Tratado"})
        self.assertEqual(patch_res.status_code, 200)
        updated = json.loads(patch_res.data.decode("utf-8")).get("feedback")
        self.assertEqual(updated.get("status"), "Tratado")

        # Verifica estatísticas KPI
        stats_res = self.client.get("/api/stats")
        stats = json.loads(stats_res.data.decode("utf-8")).get("stats")
        self.assertTrue(stats.get("total") >= 1)
        self.assertTrue(stats.get("tratados") >= 1)
        print("[TESTE 6 PASSOU] Atualização de status e recálculo de KPIs operando perfeitamente.")

    def test_07_frontend_pages_render(self):
        """Testa se as páginas HTML pública e administrativa renderizam sem erro."""
        res_public = self.client.get("/")
        self.assertEqual(res_public.status_code, 200)
        self.assertIn("BurgerSync", res_public.data.decode("utf-8"))

        res_admin = self.client.get("/admin")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn("Monitoramento de Qualidade", res_admin.data.decode("utf-8"))
        print("[TESTE 7 PASSOU] Páginas web cliente e painel administrativo renderizadas com sucesso.")


if __name__ == "__main__":
    unittest.main()
