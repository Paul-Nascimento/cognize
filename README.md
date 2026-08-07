# Cognize — Sistema de gestão contábil

Monólito em **Django + HTML/CSS/JavaScript** (sem framework de frontend) para uma
contabilidade. Reúne login por cargo, cadastro de empresas com enriquecimento
automático pela **ReceitaWS** e gestão mensal de tarefas.

---

## O que o sistema faz

### 1. Login e cargos
Autenticação com quatro cargos, em ordem crescente de permissão:

| Cargo | Visualiza | Cria/edita | Exclui | Importa em massa | Gerencia usuários |
|---|:-:|:-:|:-:|:-:|:-:|
| **Visualizador** | ✓ | | | | |
| **Colaborador** | ✓ | ✓ | | | |
| **Gestor** | ✓ | ✓ | ✓ | ✓ | |
| **Administrador** | ✓ | ✓ | ✓ | ✓ | ✓ |

As regras são aplicadas por decorators (`accounts/decorators.py`) nas views e
refletidas na navegação.

### 2. Cadastro de empresas
No cadastro **unitário** o usuário informa apenas:
`ID no sistema`, `CNPJ`, `Regime Tributário`, `Inscrição ISS`,
`Inscrição ICMS` e `Observações`.

O restante (razão social, nome fantasia, situação cadastral, natureza jurídica,
endereço, contato, CNAE principal/secundários, quadro societário, Simples/MEI, etc.)
é puxado da **ReceitaWS** pelo CNPJ.

> A ReceitaWS precisa do CNPJ para consultar — por isso ele é um campo informado
> pelo usuário, ao lado dos demais dados manuais.

**Limite de 3 consultas/minuto (plano gratuito):** tratado por uma **janela
deslizante** (`empresas/services.py`) baseada na tabela de log de consultas.
- No cadastro unitário, se houver saldo, a empresa já nasce enriquecida; se o
  limite estiver esgotado, ela é salva mesmo assim com status **Pendente**.
- As pendentes entram numa **fila de enriquecimento** processada na lista de
  empresas: o JavaScript chama o backend em rodadas, respeitando o limite e
  aguardando automaticamente entre elas, sem travar o navegador nem exigir
  Celery/broker.

### 3. Tarefas e gestão mensal
- **Tarefas avulsas** (modelo do *Relatório*): departamento, frequência, ação/meta
  em dias, dia de vencimento, fato gerador (competência) e órgão.
- **Vínculo empresa ↔ tarefa** sem regras automáticas: o usuário liga as tarefas
  às empresas manualmente — várias × várias.
- **Gestão mensal**: para uma competência (mês/ano), gera-se uma execução por
  vínculo ativo. Cada execução tem status (Pendente, Em andamento, Concluída,
  Atrasada, Dispensada), atualizável inline (AJAX). A geração é **idempotente**.

### 4. Importações automatizadas (planilha)
- **Empresas** — colunas: `ID Sistema`, `CNPJ`, `Regime Tributário`,
  `Inscrição ISS`, `Inscrição ICMS`, `Observações`.
- **Tarefas** — aceita direto o formato do *Relatório* (limpa marcadores como
  `-->` e `*`).
- **Vínculos** — `ID Empresa` + `Tarefa` (uma linha por vínculo).
- **Vincular pela interface** — tela com dois seletores múltiplos (empresas ×
  tarefas) e filtro rápido.

Cada tela de importação tem um botão **Baixar modelo** (.xlsx gerado na hora).

---

## Como rodar

Requer **Python 3.10+**.

```bash
# 1. Ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Dependências
pip install -r requirements.txt

# 3. (opcional) variáveis de ambiente
cp .env.example .env

# 4. Banco de dados
python manage.py migrate

# 5. Dados iniciais (usuários + empresas + tarefas do relatório)
python manage.py seed \
  --empresas "CADASTRO_EMPRESAS-COGNIZE_-_OFFICE_.xlsx" \
  --tarefas "Relatório.xlsx"
# (sem os arquivos, cria só os 4 usuários de demonstração)

# 6. Rodar
python manage.py runserver
```

Acesse **http://127.0.0.1:8000**.

### Usuários de demonstração (senha `cognize123`)
`admin` (Administrador) · `gestor` (Gestor) · `colab` (Colaborador) · `visual` (Visualizador)

Para criar um superusuário próprio: `python manage.py createsuperuser`.
O Django admin fica em `/django-admin/`.

---

## Observações técnicas

- **Banco**: SQLite por padrão (troque em `cognize/settings.py` para Postgres em produção).
- **Consultas reais à ReceitaWS** dependem de acesso à internet a
  `receitaws.com.br`. O limite/janela é configurável no `.env`
  (`RECEITAWS_MAX_POR_MINUTO`, `RECEITAWS_JANELA_SEGUNDOS`).
- O rate limiter usa a tabela `ConsultaReceitaLog` (funciona entre processos e
  serve de auditoria). Em produção com múltiplos workers, isso já é seguro.
- **Sem framework de frontend** — HTML via templates Django, CSS próprio
  (`static/css/app.css`) na identidade visual Cognize (navy `#16294C` + teal
  `#2AA9C4`) e JavaScript puro (`static/js/`).
- `runtests.py` é um teste de fumaça dos fluxos principais
  (`python runtests.py` com o venv ativo).

## Estrutura

```
cognize/
├── accounts/     # usuário customizado, cargos, permissões, login
├── empresas/     # modelo Empresa, ReceitaWS (services), rate limit, import
├── tarefas/      # Tarefa, VinculoTarefa, ExecucaoMensal, gestão mensal, import
├── core/         # dashboard, navegação, comando `seed`
├── templates/    # base + telas (login, empresas, tarefas, contas)
├── static/       # css, js, logos
└── cognize/      # settings, urls
```

## Próximos passos sugeridos
- Regras automáticas de vínculo (ex.: "empresas do Simples recebem tais tarefas").
- Geração de execuções sensível à frequência (gerar mensal só nos meses aplicáveis).
- Notificações de vencimento e quadro Kanban por competência.
