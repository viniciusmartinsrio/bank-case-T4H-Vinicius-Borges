"""
Gerenciador de dados CSV para o sistema bancário.
Responsável por leitura e escrita de dados de clientes, scores e solicitações.
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).parent.parent / "data"


class DataManager:
    """Gerencia operações com arquivos CSV."""

    @staticmethod
    def _ensure_file_exists(filename: str) -> Path:
        """Garante que o arquivo existe."""
        filepath = DATA_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        return filepath

    @staticmethod
    def authenticate_client(cpf: str, data_nascimento: str) -> Optional[Dict]:
        """
        Autentica um cliente verificando CPF e data de nascimento.
        
        Args:
            cpf: CPF do cliente (formato: 11 dígitos)
            data_nascimento: Data de nascimento (formato: YYYY-MM-DD)
            
        Returns:
            Dict com dados do cliente se autenticado, None caso contrário
        """
        try:
            filepath = DataManager._ensure_file_exists("clientes.csv")
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["cpf"] == cpf and row["data_nascimento"] == data_nascimento:
                        return {
                            "cpf": row["cpf"],
                            "nome": row["nome"],
                            "limite_credito": float(row["limite_credito"]),
                            "score_credito": float(row["score_credito"]),
                            "data_nascimento": row["data_nascimento"],
                        }
            return None
        except Exception as e:
            print(f"Erro ao autenticar cliente: {e}")
            return None

    @staticmethod
    def get_client_by_cpf(cpf: str) -> Optional[Dict]:
        """Obtém dados do cliente pelo CPF."""
        try:
            filepath = DataManager._ensure_file_exists("clientes.csv")
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["cpf"] == cpf:
                        return {
                            "cpf": row["cpf"],
                            "nome": row["nome"],
                            "limite_credito": float(row["limite_credito"]),
                            "score_credito": float(row["score_credito"]),
                            "data_nascimento": row["data_nascimento"],
                        }
            return None
        except Exception as e:
            print(f"Erro ao obter cliente: {e}")
            return None

    @staticmethod
    def update_client_score(cpf: str, novo_score: float) -> bool:
        """
        Atualiza o score de crédito do cliente.
        
        Args:
            cpf: CPF do cliente
            novo_score: Novo score de crédito (0-1000)
            
        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            filepath = DataManager._ensure_file_exists("clientes.csv")
            
            # Lê todos os dados
            rows = []
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["cpf"] == cpf:
                        row["score_credito"] = str(novo_score)
                    rows.append(row)
            
            # Escreve os dados atualizados
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                fieldnames = ["cpf", "data_nascimento", "nome", "limite_credito", "score_credito"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar score: {e}")
            return False

    @staticmethod
    def get_limit_by_score(score: float) -> Optional[float]:
        """
        Obtém o limite de crédito máximo permitido para um score.
        
        Args:
            score: Score de crédito do cliente (0-1000)
            
        Returns:
            Limite máximo permitido ou None se score inválido
        """
        try:
            filepath = DataManager._ensure_file_exists("score_limite.csv")
            
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    score_min = float(row["score_minimo"])
                    score_max = float(row["score_maximo"])
                    if score_min <= score <= score_max:
                        return float(row["limite_maximo"])
            return None
        except Exception as e:
            print(f"Erro ao obter limite por score: {e}")
            return None

    @staticmethod
    def register_limit_request(
        cpf: str,
        limite_atual: float,
        novo_limite: float,
        status: str = "pendente"
    ) -> bool:
        """
        Registra uma solicitação de aumento de limite.
        
        Args:
            cpf: CPF do cliente
            limite_atual: Limite atual de crédito
            novo_limite: Novo limite solicitado
            status: Status da solicitação (pendente, aprovado, rejeitado)
            
        Returns:
            True se registrado com sucesso, False caso contrário
        """
        try:
            filepath = DataManager._ensure_file_exists("solicitacoes_aumento_limite.csv")
            
            # ISO 8601 timestamp
            timestamp = datetime.now().isoformat()
            
            # Verifica se o arquivo está vazio (apenas cabeçalho)
            file_empty = os.path.getsize(filepath) <= 50
            
            with open(filepath, "a", encoding="utf-8", newline="") as f:
                fieldnames = [
                    "cpf_cliente",
                    "data_hora_solicitacao",
                    "limite_atual",
                    "novo_limite_solicitado",
                    "status_pedido"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # Escreve cabeçalho se arquivo vazio
                if file_empty:
                    writer.writeheader()
                
                writer.writerow({
                    "cpf_cliente": cpf,
                    "data_hora_solicitacao": timestamp,
                    "limite_atual": limite_atual,
                    "novo_limite_solicitado": novo_limite,
                    "status_pedido": status
                })
            
            return True
        except Exception as e:
            print(f"Erro ao registrar solicitação: {e}")
            return False

    @staticmethod
    def get_all_requests() -> List[Dict]:
        """Obtém todas as solicitações de aumento de limite."""
        try:
            filepath = DataManager._ensure_file_exists("solicitacoes_aumento_limite.csv")
            
            requests = []
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("cpf_cliente"):  # Ignora linhas vazias
                        requests.append(row)
            return requests
        except Exception as e:
            print(f"Erro ao obter solicitações: {e}")
            return []
