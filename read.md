# 🌐 Gerenciador de Active Directory Web

Uma aplicação web interna desenvolvida em **Flask** para simplificar e agilizar o gerenciamento de usuários no **Active Directory** da sua organização.

---

## ✨ Funcionalidades

A ferramenta permite que administradores realizem tarefas de forma rápida e intuitiva:

| Funcionalidade | Descrição | Status | Demonstração |
|----------------|-----------|--------|--------------|
| 🔍 **Buscar Usuários** | Encontre usuários rapidamente por nome ou login | ✅ Ativo | ![Buscar Usuários](https://media.giphy.com/media/3o7TKtnuHOHHUjR38Y/giphy.gif) |
| 🔒 **Habilitar / Desabilitar Contas** | Alterar o status de uma conta de usuário com um clique | ✅ Ativo | ![Habilitar/Desabilitar](https://media.giphy.com/media/l0HlD6p3XCE8rDsRi/giphy.gif) |
| 🔑 **Resetar Senhas** | Defina novas senhas temporárias para os usuários | ✅ Ativo | ![Resetar Senha](https://media.giphy.com/media/xT9IgG50Fb7Mi0prBC/giphy.gif) |
| ➕ **Criar Usuário** | Adicionar novos usuários ao AD | ⚠️ Em manutenção | N/A |

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


2️⃣ Instalar as Bibliotecas
bash
Copiar código
pip install -r requirements.txt

3️⃣ Configurar a Conexão com o Active Directory
Execute o script descobrir_ad.py em um servidor AD ou máquina com RSAT:

bash
Copiar código
python descobrir_ad.py
Copie as informações exibidas no terminal:

plaintext
Copiar código
✅ Configuração do Active Directory descoberta com sucesso!

# --- Configurações de Conexão ---
AD_SERVER = '0000000'
AD_PORT = 0000
AD_DOMAIN_NETBIOS = 'nome'
AD_DOMAIN_UPN = 'nome'
SEARCH_BASE = 'DC=nome,DC=nome,DC=nome'

# --- Configuração de Segurança ---
AD_REQUIRED_GROUP_DN = 'CN=Domain Admins,CN=Users,DC=nome,DC=nome,DC=nome'

4️⃣ Atualizar o app.py
python
Copiar código
# app.py

AD_SERVER = '0000000'
AD_PORT = 0000
AD_DOMAIN_NETBIOS = 'nome'
AD_DOMAIN_UPN = 'nome'
SEARCH_BASE = 'OU=HRMJ,DC=hrmj,DC=pa,DC=org'
# IMPORTANTE: Ajuste para sua OU principal

AD_REQUIRED_GROUP_DN = 'CN=TI,OU=TI,OU=ADM,OU=Users,OU=nome,DC=nome,DC=nome,DC=nome'
# IMPORTANTE: Use o DN do seu grupo de TI se for o setor ADM do servidor
🔐 Controle de Acesso
Somente membros do grupo TI podem acessar a aplicação.

O login valida automaticamente se o usuário pertence ao grupo definido na variável AD_REQUIRED_GROUP_DN dentro do app.py.


▶️ Executando a Aplicação
bash
Copiar código
python app.py
Abra o navegador e acesse:

cpp
Copiar código
http://127.0.0.1:5000

