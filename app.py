from flask import Flask, render_template, request, redirect, url_for, session, flash
from ldap3 import Server, Connection, ALL, Tls, core, SUBTREE, MODIFY_REPLACE
import ssl
import os

# --- Configurações da Aplicação ---
# Chave secreta para a sessão do Flask. Em produção, use uma variável de ambiente.
SECRET_KEY = os.urandom(24)

# --- Configurações do Active Directory ---
# ATENÇÃO: Preencha estas variáveis com os dados do seu ambiente
AD_SERVER = '10.172.0.31'          # IP ou nome do seu Domain Controller
AD_PORT = 636                     # Porta LDAPS (SSL/TLS)
AD_DOMAIN_NETBIOS = 'HRMJ'        # Nome NetBIOS do domínio
AD_DOMAIN_UPN = 'hrmj.org.pa'     # Sufixo UPN
SEARCH_BASE = 'OU=HRMJ,DC=hrmj,DC=pa,DC=org' # Base de busca principal

# --- Grupo autorizado a usar a ferramenta ---
# DN completo (Distinguished Name) do grupo. Somente membros deste grupo poderão fazer login.
# ATENÇÃO: ESTE VALOR PRECISA SER O CAMINHO EXATO DO SEU GRUPO DE TI NO AD.
AD_REQUIRED_GROUP_DN = 'CN=TI,OU=TI,OU=ADM,OU=Users,OU=HRMJ,DC=hrmj,DC=pa,DC=org'

# --- Constantes do Active Directory ---
# Flags do UserAccountControl (UAC)
UAC_ENABLED = 512                 # Conta normal habilitada
UAC_DISABLED = 2                  # Flag para desabilitar a conta
UAC_PASSWORD_NEVER_EXPIRES = 0x10000 # Flag para "senha nunca expira"

# --- Configuração de TLS ---
# AVISO DE SEGURANÇA: ssl.CERT_NONE desabilita a validação do certificado do servidor.
# Para máxima segurança em produção, use ssl.CERT_REQUIRED e aponte para o seu certificado de CA.
TLS_CONFIG = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

# --- Inicialização da aplicação Flask ---
app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- Funções de Conexão com o AD ---

def get_ad_connection(username, password):
    """
    Cria e retorna uma conexão segura com o Active Directory via LDAPS.
    Retorna None se a autenticação ou conexão falhar.
    """
    user_dn = f"{AD_DOMAIN_NETBIOS}\\{username}"
    server = Server(AD_SERVER, port=AD_PORT, get_info=ALL, use_ssl=True, tls=TLS_CONFIG)
    try:
        conn = Connection(server, user=user_dn, password=password, authentication="SIMPLE", auto_bind=True)
        return conn
    except (core.exceptions.LDAPBindError, core.exceptions.LDAPSocketOpenError) as e:
        print(f"Erro de conexão/bind: {e}")
        return None

def is_user_in_required_group(conn, username):
    """
    Verifica se um usuário é membro (direto ou aninhado) do grupo requerido.
    """
    try:
        conn.search(SEARCH_BASE, f'(sAMAccountName={username})', attributes=['distinguishedName'])
        if not conn.entries:
            return False
        
        user_dn = conn.entries[0].distinguishedName.value
        
        # Filtro especial para verificar membresia aninhada de forma eficiente
        search_filter = f'(&(distinguishedName={user_dn})(memberOf:1.2.840.113556.1.4.1941:={AD_REQUIRED_GROUP_DN}))'
        
        conn.search(SEARCH_BASE, search_filter, attributes=['cn'])
        return len(conn.entries) > 0
    except Exception as e:
        print(f"Erro ao verificar grupo: {e}")
        return False

# --- Rotas da Aplicação ---

@app.route("/login", methods=['GET', 'POST'])
def login():
    """Renderiza a página de login e processa a autenticação do usuário."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_ad_connection(username, password)
        
        if conn:
            # DEBUG: Adicionado para diagnóstico
            print(f"DEBUG: Conexão para '{username}' bem-sucedida. Verificando grupo...")
            try:
                # DEBUG: Adicionado para diagnóstico
                is_member = is_user_in_required_group(conn, username)
                print(f"DEBUG: Verificação de grupo para '{username}' retornou: {is_member}")

                if is_member:
                    session['logged_in'] = True
                    session['username'] = username
                    session['password'] = password
                    flash('Login bem-sucedido!', 'success')
                    return redirect(url_for('menu'))
                else:
                    flash('Acesso negado. Você não pertence ao grupo autorizado.', 'danger')
            finally:
                conn.unbind()
        else:
            flash('Usuário ou senha inválidos.', 'danger')
            
    return render_template('login.html')

@app.route("/logout")
def logout():
    """Limpa a sessão do usuário e o redireciona para a página de login."""
    session.clear()
    flash('Você foi desconectado com segurança.', 'info')
    return redirect(url_for('login'))

@app.route("/")
def menu():
    """Renderiza o menu principal da aplicação."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('menu.html')

@app.route("/criar", methods=['GET', 'POST'])
def criar_usuario():
    """Página para criar um novo usuário no Active Directory."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_ad_connection(session['username'], session['password'])
    if not conn:
        flash('Sua sessão expirou. Por favor, faça login novamente.', 'warning')
        return redirect(url_for('logout'))

    try:
        conn.search(search_base=SEARCH_BASE, search_filter='(objectClass=organizationalUnit)', 
                    search_scope=SUBTREE, attributes=['name', 'distinguishedName'])
        ous_list = sorted([(entry.name.value, entry.distinguishedName.value) for entry in conn.entries])

        if request.method == 'POST':
            nome = request.form['nome'].strip()
            sobrenome = request.form['sobrenome'].strip()
            ou_dn = request.form['ou_dn']
            senha = request.form['senha']
            confirmar_senha = request.form['confirmar_senha']

            if senha != confirmar_senha:
                flash('As senhas não conferem!', 'danger')
                return render_template('criar_usuario.html', ous=ous_list)

            sAMAccountName = f"{nome.lower().replace(' ', '')}.{sobrenome.lower().replace(' ', '')}"
            userPrincipalName = f"{sAMAccountName}@{AD_DOMAIN_UPN}"
            nome_completo = f"{nome} {sobrenome}"
            user_dn = f"CN={nome_completo},{ou_dn}"

            conn.search(SEARCH_BASE, f'(sAMAccountName={sAMAccountName})', attributes=['cn'])
            if conn.entries:
                flash(f'O nome de usuário "{sAMAccountName}" já existe no Active Directory.', 'danger')
                return render_template('criar_usuario.html', ous=ous_list)

            conn.add(user_dn, 
                     ['top', 'person', 'organizationalPerson', 'user'],
                     {'givenName': nome, 'sn': sobrenome, 'sAMAccountName': sAMAccountName,
                      'userPrincipalName': userPrincipalName, 'userAccountControl': UAC_ENABLED})

            if conn.result['result'] == 0:
                conn.extend.microsoft.modify_password(user_dn, senha)
                conn.modify(user_dn, {'pwdLastSet': [(MODIFY_REPLACE, [0])]})
                
                flash(f'Usuário "{sAMAccountName}" criado com sucesso!', 'success')
                return render_template('criar_usuario_sucesso.html', username=sAMAccountName, password=senha)
            else:
                flash(f"Falha ao criar usuário: {conn.result['description']}", 'danger')
    
    except Exception as e:
        flash(f"Ocorreu um erro inesperado: {e}", 'danger')
    finally:
        conn.unbind()
        
    return render_template('criar_usuario.html', ous=ous_list)

@app.route("/buscar", methods=['GET', 'POST'])
def buscar_usuario():
    """Página para buscar e listar usuários do AD."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    usuarios = []
    termo = request.form.get('termo', '')

    if request.method == 'POST' and termo:
        conn = get_ad_connection(session['username'], session['password'])
        if not conn:
            flash('Sessão expirada. Por favor, faça login novamente.', 'warning')
            return redirect(url_for('logout'))
        
        try:
            filtro = f"(&(objectClass=user)(objectCategory=person)(|(sAMAccountName=*{termo}*)(cn=*{termo}*)))"
            conn.search(search_base=SEARCH_BASE, search_filter=filtro, 
                        attributes=['sAMAccountName', 'cn', 'userAccountControl', 'distinguishedName'])
            
            for entry in conn.entries:
                is_disabled = entry.userAccountControl.value & UAC_DISABLED
                status = "Desabilitado" if is_disabled else "Habilitado"
                usuarios.append({
                    'sam': entry.sAMAccountName.value, 
                    'cn': entry.cn.value, 
                    'status': status, 
                    'dn': entry.distinguishedName.value
                })
        except Exception as e:
            flash(f"Erro durante a busca: {e}", "danger")
        finally:
            conn.unbind()
            
    return render_template('buscar_usuario.html', usuarios=usuarios, termo=termo)

@app.route("/gerenciar", methods=['POST'])
def gerenciar_usuario():
    """Processa ações de gerenciamento como reset de senha e habilitação/desabilitação de conta."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_dn = request.form.get('user_dn')
    acao = request.form.get('acao')

    if not user_dn or not acao:
        flash('Ação ou usuário inválido.', 'danger')
        return redirect(url_for('buscar_usuario'))

    conn = get_ad_connection(session['username'], session['password'])
    if not conn:
        flash('Sessão expirada. Por favor, faça login novamente.', 'warning')
        return redirect(url_for('logout'))

    try:
        if acao == 'resetar_senha':
            nova_senha = request.form.get('nova_senha')
            if not nova_senha:
                flash('A nova senha não pode ser vazia.', 'danger')
            else:
                conn.extend.microsoft.modify_password(user_dn, nova_senha)
                conn.modify(user_dn, {'pwdLastSet': [(MODIFY_REPLACE, [0])]})
                
                conn.search(user_dn, '(objectClass=user)', attributes=['userAccountControl'])
                uac_atual = conn.entries[0].userAccountControl.value
                novo_uac = uac_atual & ~UAC_PASSWORD_NEVER_EXPIRES
                conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [novo_uac])]})
                
                flash(f'Senha resetada. O usuário deverá alterá-la no próximo logon.', 'success')

        elif acao in ['habilitar', 'desabilitar']:
            conn.search(user_dn, '(objectClass=user)', attributes=['userAccountControl'])
            uac_atual = conn.entries[0].userAccountControl.value
            
            if acao == 'habilitar':
                novo_uac = uac_atual & ~UAC_DISABLED
                msg = 'habilitada'
            else: # Desabilitar
                novo_uac = uac_atual | UAC_DISABLED
                msg = 'desabilitada'
            
            conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [novo_uac])]})
            flash(f'Conta de usuário {msg} com sucesso.', 'success')

    except core.exceptions.LDAPException as e:
        flash(f"Falha na operação LDAP: {e}", 'danger')
    except Exception as e:
        flash(f"Erro inesperado: {e}", "danger")
    finally:
        conn.unbind()

    return redirect(url_for('buscar_usuario'))

# --- Execução da Aplicação ---
if __name__ == "__main__":
    # O host '0.0.0.0' torna a aplicação acessível na sua rede local.
    # debug=True é ótimo para desenvolvimento, mas deve ser desativado em produção.
    app.run(debug=True, host='0.0.0.0', port=5000)