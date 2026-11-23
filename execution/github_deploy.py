"""
Script Determinístico de Integração e Publicação no GitHub
Cria o repositório remoto caso não exista e faz o push do código BurgerSync.
"""

import os
import subprocess
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_TOKEN")
REPO_NAME = "burgersync-analisador-feedback"
REPO_DESC = "Sistema Web Inteligente de Coleta, Análise de Sentimento (Gemini) e Alerta de Crise da BurgerSync Ourinhos"


def run_cmd(cmd, cwd=BASE_DIR):
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def deploy_to_github():
    print(f"\n[INFO] Iniciando integração com o GitHub para o repositório '{REPO_NAME}'...")
    if not GITHUB_TOKEN:
        print("[ERRO] GITHUB_PERSONAL_TOKEN não encontrado no arquivo .env.")
        return False

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Verifica identidade do usuário autenticado
    user_res = requests.get("https://api.github.com/user", headers=headers, timeout=10)
    if user_res.status_code != 200:
        print(f"[ERRO] Falha ao autenticar no GitHub com o token fornecido: {user_res.status_code}")
        return False

    username = user_res.json().get("login")
    print(f"[SUCESSO] Usuário GitHub autenticado: @{username}")

    # 2. Cria repositório remoto se não existir
    repo_res = requests.get(f"https://api.github.com/repos/{username}/{REPO_NAME}", headers=headers, timeout=10)
    if repo_res.status_code == 404:
        print(f"[INFO] Criando repositório '{REPO_NAME}' no GitHub...")
        create_payload = {
            "name": REPO_NAME,
            "description": REPO_DESC,
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False
        }
        create_res = requests.post("https://api.github.com/user/repos", headers=headers, json=create_payload, timeout=10)
        if create_res.status_code in [200, 201]:
            print(f"[SUCESSO] Repositório criado com sucesso no GitHub!")
        else:
            print(f"[AVISO] Resposta da criação de repositório: {create_res.status_code} - {create_res.text[:100]}")
    else:
        print(f"[INFO] Repositório '{REPO_NAME}' já existe no GitHub do usuário.")

    # 3. Cria arquivo .gitignore para proteger o .env e arquivos temporários
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    with open(gitignore_path, "w", encoding="utf-8") as f:
        f.write(".env\n__pycache__/\n*.pyc\n.tmp/requests/\n")
    print("[SUCESSO] .gitignore configurado.")

    # 4. Inicializa git e prepara commit/push
    remote_url = f"https://{username}:{GITHUB_TOKEN}@github.com/{username}/{REPO_NAME}.git"

    run_cmd("git init")
    run_cmd('git config user.name "BurgerSync Bot"')
    run_cmd('git config user.email "bot@burgersync.com.br"')
    run_cmd("git remote remove origin")
    run_cmd(f'git remote add origin "{remote_url}"')
    run_cmd("git add -A")
    run_cmd('git commit -m "feat: implementacao completa BurgerSync Analisador Feedback (Gemini AI + Dashboard + Alertas)"')
    run_cmd("git branch -M main")
    code, out, err = run_cmd("git push -u origin main --force")

    if code == 0:
        public_url = f"https://github.com/{username}/{REPO_NAME}"
        print(f"\n=======================================================")
        print(f" [SUCESSO] PROJETO PUBLICADO NO GITHUB!")
        print(f" URL do Repositório: {public_url}")
        print(f"=======================================================\n")
        return public_url
    else:
        print(f"[AVISO] Saída do Git Push: {out}\n{err}")
        return False


if __name__ == "__main__":
    deploy_to_github()
