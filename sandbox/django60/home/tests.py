from django.contrib.auth import get_user_model
from django.test import TestCase

from home.backends import SandboxSuapAuthBackend

User = get_user_model()


class SandboxSuapAuthBackendTest(TestCase):

    def test_create_user_and_sync_profile(self):
        backend = SandboxSuapAuthBackend()
        suap_user_info = {
            "id": 159574,
            "identificacao": "2080882",
            "nome_usual": "Kelson Medeiros",
            "cpf": "645.834.571-20",
            "rg": "1586368 - SSP/DF",
            "filiacao": ["Leonea", "Cicero"],
            "data_nascimento": "1978-10-30",
            "naturalidade": "GAMA/DF",
            "tipo_sanguineo": "A+",
            "email": "kelson.medeiros@ifrn.edu.br",
            "tipo_vinculo": "Servidor",
            "tipo_usuario": "Servidor (Técnico-Administrativo)",
            "campus": "ZL",
            "vinculo": {
                "telefones_institucionais": ["(84) 3092-8938"],
                "funcao": ["SUB-CHEFIA0001 - CME/ZL"],
                "setor_suap": "DEAD/ZL",
                "campus": "ZL",
            },
            "meus_vinculos": [
                {
                    "id": 1588,
                    "identificador": "2080882",
                    "tipo": "servidor",
                    "campus": "ZL",
                    "estrangeiro": False,
                    "detalhamento": {"cargo": "ANALISTA DE TEC DA INFORMACAO"},
                }
            ],
            "servidores_funcao_ativa": [
                {
                    "id": 159574,
                    "nome": "Kelson da Costa Medeiros",
                    "funcao": ["SUB-CHEFIA0001 - CME/ZL"],
                    "campus": "CAMPUS AVANÇADO NATAL-ZONA LESTE",
                    "setor": "Diretoria (DEAD/ZL)",
                    "telefones_institucionais": ["(84) 3092-8938"],
                    "telefone_campus": "(84) 3092-8907",
                }
            ],
            "meu_historico_funcional": [
                {
                    "data": "2014-01-03",
                    "css": "success",
                    "eventos": [{"descricao": "Entrada no PCA", "css": "success"}],
                }
            ],
        }

        user = backend.authenticate(None, suap_user_info=suap_user_info)

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "2080882")
        self.assertEqual(user.email, "kelson.medeiros@ifrn.edu.br")

        # Check Profile 1x1
        profile = user.profile
        self.assertEqual(profile.cpf, "645.834.571-20")
        self.assertEqual(profile.naturalidade, "GAMA/DF")

        # Check RawData 1x1
        self.assertIsNotNone(profile.raw_data)
        self.assertEqual(profile.raw_data.data["identificacao"], "2080882")

        # Check Vinculo
        self.assertEqual(profile.vinculos.count(), 1)
        v = profile.vinculos.first()
        self.assertEqual(v.identificador, "2080882")
        self.assertEqual(v.tipo, "servidor")

        # Check Telefone
        self.assertGreaterEqual(profile.telefones.count(), 1)

        # Check Funcao
        self.assertEqual(profile.funcoes.count(), 1)
        f = profile.funcoes.first()
        self.assertEqual(f.nome, "SUB-CHEFIA0001 - CME/ZL")

        # Check HistoricoFuncional
        self.assertEqual(profile.historicos_funcionais.count(), 1)
        hf = profile.historicos_funcionais.first()
        self.assertEqual(hf.data, "2014-01-03")
