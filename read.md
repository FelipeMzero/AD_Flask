# 🌐 Gerenciador de Active Directory Web

Uma aplicação web interna desenvolvida em **Flask** para simplificar e agilizar o gerenciamento de usuários no **Active Directory** da sua organização.

---

## ✨ Funcionalidades

A ferramenta permite que administradores realizem tarefas de forma rápida e intuitiva:

| Funcionalidade | Descrição | Status |
|----------------|-----------|--------|
| 🔍 **Buscar Usuários** | Encontre usuários rapidamente por nome ou login | ✅ Ativo |
| 🔒 **Habilitar / Desabilitar Contas** | Alterar o status de uma conta de usuário com um clique | ✅ Ativo |
| 🔑 **Resetar Senhas** | Defina novas senhas temporárias para os usuários | ✅ Ativo |
| ➕ **Criar Usuário** | Adicionar novos usuários ao AD | ⚠️ Em manutenção |

![Dashboard](https://via.placeholder.com/800x300.png?text=Dashboard+AD+Web)  
*Exemplo da interface do Gerenciador de AD*

---

## 🚀 Guia de Instalação e Configuração

### 1️⃣ Preparar o Ambiente

- **Instale o Python 3**: [Download Python](https://www.python.org/downloads/)  
- **Editor de Código**: Recomendado usar Visual Studio Code ou outro de sua preferência.  
- **Clone o Repositório**:

```bash
git clone https://github.com/seu-usuario/gerenciador-ad-web.git
cd gerenciador-ad-web
```

---

### 2️⃣ Instalar as Bibliotecas

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Configurar a Conexão com o Active Directory

Execute o script `descobrir_ad.py` em um servidor AD ou máquina com RSAT:

```bash
python descobrir_ad.py
```

Copie as informações exibidas no terminal:

```python
# --- Configurações de Conexão ---
AD_SERVER = '0000000'           # Endereço ou IP do servidor AD
AD_PORT = 0000                   # Porta do serviço LDAP
AD_DOMAIN_NETBIOS = 'nome'       # Nome NETBIOS do domínio
AD_DOMAIN_UPN = 'nome'           # UPN do domínio
SEARCH_BASE = 'DC=nome,DC=nome,DC=nome'  # Base para busca no AD

# --- Configuração de Segurança ---
AD_REQUIRED_GROUP_DN = 'CN=Domain Admins,CN=Users,DC=nome,DC=nome,DC=nome'
```

> ⚠️ **Dicas importantes:**  
> - Ajuste o `SEARCH_BASE` para a **OU principal** que contém seus usuários.  
> - Ajuste o `AD_REQUIRED_GROUP_DN` para o grupo de TI ou ADM que terá acesso à aplicação.

---

### 4️⃣ Atualizar o `app.py`

```python
# app.py

AD_SERVER = '0000000'
AD_PORT = 0000
AD_DOMAIN_NETBIOS = 'nome'
AD_DOMAIN_UPN = 'nome'
SEARCH_BASE = 'OU=HRMJ,DC=hrmj,DC=pa,DC=org'  # Ajuste para sua OU principal

AD_REQUIRED_GROUP_DN = 'CN=TI,OU=TI,OU=ADM,OU=Users,OU=nome,DC=nome,DC=nome,DC=nome'
# IMPORTANTE: Use o DN do seu grupo de TI ou do setor ADM do servidor
```

---

### 🔐 Controle de Acesso

- Apenas membros do grupo definido em `AD_REQUIRED_GROUP_DN` podem acessar a aplicação.  
- O login valida automaticamente se o usuário pertence ao grupo.  
- Usuários não autorizados receberão uma mensagem de acesso negado.  
- Ao realizar o primeiro login, o usuário deve alterar a senha temporária para uma senha pessoal.

---

### ▶️ Executando a Aplicação

```bash
python app.py
```

Abra o navegador e acesse:

```
http://127.0.0.1:5000
```

---

### 📌 Observações Finais

- Certifique-se de que o servidor onde a aplicação será executada tem conectividade com o AD.  
- Funcionalidades ativas atualmente: busca de usuários, habilitar/desabilitar contas, reset de senhas.  
- Criação de novos usuários no AD ainda está em manutenção.  
- Para suporte ou solicitações novas, utilize o GLPI.  
- Todos os acessos ao TASY devem ser preenchidos no formulário de criação de acessos e validados via GLPI, garantindo que a solicitação seja protocolada corretamente.

