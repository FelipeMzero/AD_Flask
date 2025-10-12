from flask import Flask, render_template, request, redirect, url_for, session, flash
from ldap3 import Server, Connection, ALL, Tls, core, SUBTREE, MODIFY_REPLACE
import ssl
import os

# --- Configurações ---
SECRET_KEY = os.urandom(24)

# --- Configurações do Active Directory ---
AD_SERVER = ''
AD_PORT = 000
AD_DOMAIN_NETBIOS = ''
AD_DOMAIN_UPN = ''
SEARCH_BASE = ''

# --- MODIFICAÇÃO 1: Adicione o Distinguished Name do seu grupo de administradores ---
# ATENÇÃO: Substitua o valor abaixo pelo caminho completo (DN) do seu grupo "TI".
# Este é apenas um exemplo. O caminho precisa ser exato.
AD_REQUIRED_GROUP_DN = ''

TLS_CONFIG = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)

# Inicialização da aplicação Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- Funções de Conexão com o AD ---

def get_ad_connection(username, password):
    """Cria e retorna uma conexão com o AD. Retorna None se falhar."""
    user_dn = f"{AD_DOMAIN_NETBIOS}\\{username}"
    server = Server(AD_SERVER, port=AD_PORT, get_info=ALL, tls=TLS_CONFIG)
    try:
        conn = Connection(server, user=user_dn, password=password, authentication="SIMPLE", auto_bind=True)
        conn.start_tls()
        return conn
    except (core.exceptions.LDAPBindError, core.exceptions.LDAPStartTLSError):
        return None

# --- MODIFICAÇÃO 2: Nova função para verificar a permissão de grupo ---
def is_user_in_required_group(conn, username):
    """
    Verifica se um usuário é membro (direto ou aninhado) do grupo de administradores.
    Retorna True se for membro, False caso contrário.
    """
    try:
        # Encontra o Distinguished Name (DN) do usuário que está tentando logar
        conn.search(SEARCH_BASE, f'(sAMAccountName={username})', attributes=['distinguishedName'])
        if not conn.entries:
            return False  # Usuário não encontrado
        
        user_dn = conn.entries[0].distinguishedName.value

        # Utiliza um filtro LDAP especial para verificar pertencimento a grupos aninhados
        # Este é o método mais eficiente e correto para essa verificação.
        search_filter = f'(&(distinguishedName={user_dn})(memberOf:1.2.840.113556.1.4.1941:={AD_REQUIRED_GROUP_DN}))'
        
        conn.search(SEARCH_BASE, search_filter, attributes=['cn'])
        
        # Se a busca retornar uma entrada, significa que o usuário é membro do grupo.
        return len(conn.entries) > 0
    except Exception:
        return False


# --- Rotas da Aplicação Web ---

# --- MODIFICAÇÃO 3: Lógica de login atualizada ---
@app.route("/login", methods=['GET', 'POST'])
def login():
    """Página de login com verificação de permissão de grupo."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Passo 1: Tenta autenticar o usuário
        conn = get_ad_connection(username, password)
        
        if conn:
            # Passo 2: Se a autenticação foi bem-sucedida, verifica a permissão do grupo
            if is_user_in_required_group(conn, username):
                # Sucesso! O usuário é válido E tem permissão.
                session['logged_in'] = True
                session['username'] = username
                session['password'] = password
                flash('Login bem-sucedido!', 'success')
                conn.unbind()
                return redirect(url_for('menu'))
            else:
                # Falha na permissão: usuário válido, mas não está no grupo correto
                flash('Acesso negado. Você não tem permissão para usar esta ferramenta.', 'danger')
                conn.unbind()
        else:
            # Falha na autenticação: usuário ou senha incorretos
            flash('Usuário ou senha inválidos.', 'danger')
            
    return render_template('login.html')

# (O resto do código permanece o mesmo)

@app.route("/logout")
def logout():
    """Faz o logout do usuário."""
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route("/")
def menu():
    """Menu principal da aplicação."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('menu.html')

@app.route("/criar", methods=['GET', 'POST'])
def criar_usuario():
    """Página para criar um novo usuário."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = get_ad_connection(session['username'], session['password'])
    if not conn:
        flash('Sua sessão expirou. Por favor, faça login novamente.', 'warning')
        return redirect(url_for('logout'))

    # Busca dinâmica das OUs
    conn.search(search_base=SEARCH_BASE, search_filter='(objectClass=organizationalUnit)', search_scope=SUBTREE, attributes=['name', 'distinguishedName'])
    ous_map = sorted([(entry.name.value, entry.distinguishedName.value) for entry in conn.entries])

    if request.method == 'POST':
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        ou_dn = request.form['ou_dn']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        if senha != confirmar_senha:
            flash('As senhas não conferem!', 'danger')
            return render_template('criar_usuario.html', ous=ous_map)

        sAMAccountName = f"{nome.lower().replace(' ', '')}.{sobrenome.lower().replace(' ', '')}"
        nome_completo = f"{nome} {sobrenome}"
        user_dn = f"CN={nome_completo},{ou_dn}"

        try:
            conn.add(user_dn, ['top', 'person', 'organizationalPerson', 'user'],
                     {'givenName': nome, 'sn': sobrenome, 'sAMAccountName': sAMAccountName,
                      'userPrincipalName': f"{sAMAccountName}@{AD_DOMAIN_UPN}", 'userAccountControl': 512})

            if conn.result['result'] == 0:
                conn.extend.microsoft.modify_password(user_dn, senha)
                conn.modify(user_dn, {'pwdLastSet': [(MODIFY_REPLACE, [0])]})
                conn.unbind()
                # Redireciona para uma página de sucesso mostrando os dados
                return render_template('criar_usuario_sucesso.html', username=sAMAccountName, password=senha)
            else:
                flash(f"Falha ao criar usuário: {conn.result['description']}", 'danger')
        except Exception as e:
            flash(f"Erro inesperado: {e}", 'danger')

    conn.unbind()
    return render_template('criar_usuario.html', ous=ous_map)

@app.route("/buscar", methods=['GET', 'POST'])
def buscar_usuario():
    """Página para buscar um usuário."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        termo = request.form['termo']
        conn = get_ad_connection(session['username'], session['password'])
        if not conn:
            flash('Sessão expirada.', 'warning')
            return redirect(url_for('logout'))
        
        filtro = f"(&(objectClass=user)(objectCategory=person)(|(sAMAccountName=*{termo}*)(cn=*{termo}*)))"
        conn.search(search_base=SEARCH_BASE, search_filter=filtro, attributes=['sAMAccountName', 'cn', 'userAccountControl', 'distinguishedName'])
        
        usuarios = []
        UAC_DISABLED = 2
        for entry in conn.entries:
            status = "Desabilitado" if entry.userAccountControl.value & UAC_DISABLED else "Habilitado"
            usuarios.append({'sam': entry.sAMAccountName.value, 'cn': entry.cn.value, 'status': status, 'dn': entry.distinguishedName.value})
        
        conn.unbind()
        return render_template('buscar_usuario.html', usuarios=usuarios, termo=termo)
        
    return render_template('buscar_usuario.html', usuarios=None)

@app.route("/gerenciar", methods=['POST'])
def gerenciar_usuario():
    """Processa ações para um usuário (resetar senha, habilitar, desabilitar)."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    user_dn = request.form.get('user_dn')
    acao = request.form.get('acao')

    conn = get_ad_connection(session['username'], session['password'])
    if not conn:
        flash('Sessão expirada.', 'warning')
        return redirect(url_for('logout'))

    try:
        if acao == 'resetar_senha':
            nova_senha = request.form.get('nova_senha')
            if not nova_senha:
                flash('A nova senha não pode ser vazia.', 'danger')
            else:
                conn.extend.microsoft.modify_password(user_dn, nova_senha)
                conn.modify(user_dn, {'pwdLastSet': [(MODIFY_REPLACE, [0])]})
                if conn.result['result'] == 0:
                    flash(f'Senha do usuário resetada com sucesso para "{nova_senha}".', 'success')
                else:
                     flash(f"Falha ao resetar senha: {conn.result['description']}", 'danger')

        elif acao in ['habilitar', 'desabilitar']:
            # Busca o valor atual do userAccountControl
            conn.search(user_dn, '(objectClass=user)', attributes=['userAccountControl'])
            uac_atual = conn.entries[0].userAccountControl.value
            UAC_DISABLED = 2
            
            if acao == 'habilitar':
                novo_uac = uac_atual & ~UAC_DISABLED
                msg = 'habilitada'
            else: # desabilitar
                novo_uac = uac_atual | UAC_DISABLED
                msg = 'desabilitada'
                
            conn.modify(user_dn, {'userAccountControl': [(MODIFY_REPLACE, [novo_uac])]})
            if conn.result['result'] == 0:
                flash(f'Conta de usuário {msg} com sucesso.', 'success')
            else:
                flash(f"Falha ao alterar status da conta: {conn.result['description']}", 'danger')

    except Exception as e:
        flash(f"Erro inesperado: {e}", "danger")
    
    finally:
        conn.unbind()

    return redirect(url_for('buscar_usuario'))


# --- Execução da Aplicação ---
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')