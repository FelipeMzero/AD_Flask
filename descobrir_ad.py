import subprocess
import re
import socket
import os

def descobrir_config_ad():
    """
    Usa comandos do Windows para descobrir automaticamente as configurações
    do Active Directory, incluindo o grupo padrão de administradores do domínio.
    """
    if os.name != 'nt':
        print("❌ Este script foi projetado para ser executado em uma máquina Windows conectada a um domínio.")
        return

    print("🔍 Buscando informações do Active Directory...")

    try:
        # 1. Descobrir o Domínio UPN (DNS) e NetBIOS
        output = subprocess.check_output("set USER", shell=True, text=True, stderr=subprocess.DEVNULL)
        ad_domain_upn = re.search(r"USERDNSDOMAIN=(.+)", output, re.IGNORECASE).group(1).strip()
        ad_domain_netbios = re.search(r"USERDOMAIN=(.+)", output, re.IGNORECASE).group(1).strip()

        # 2. Construir o Search Base a partir do Domínio UPN
        search_base = "DC=" + ad_domain_upn.replace(".", ",DC=")

        # 3. Descobrir o nome do Controlador de Domínio (DC)
        dc_output = subprocess.check_output(f"nltest /dsgetdc:{ad_domain_netbios}", shell=True, text=True, stderr=subprocess.DEVNULL)
        dc_hostname = re.search(r"Dc:\s+\\\\([^\s]+)", dc_output, re.IGNORECASE).group(1).strip()

        # 4. Descobrir o IP do Controlador de Domínio
        ad_server_ip = socket.gethostbyname(dc_hostname)
        
        # 5. Descobrir o Distinguished Name (DN) do grupo de Administradores do Domínio
        # O nome do grupo pode ser "Domain Admins" (inglês) ou "Administradores do Domínio" (português).
        # O comando 'dsquery' encontra o grupo independentemente do idioma do sistema.
        print("🔍 Buscando o grupo de administradores do domínio...")
        # O comando dsquery retorna o DN entre aspas, que precisamos remover.
        admin_group_output = subprocess.check_output('dsquery group -name "Domain Admins"', shell=True, text=True, stderr=subprocess.DEVNULL)
        admin_group_dn = admin_group_output.strip().strip('"')

        # 6. Imprimir todos os resultados formatados
        print("\n✅ Configuração do Active Directory descoberta com sucesso!\n")
        
        print("# --- Configurações de Conexão (Copie para o seu app.py) ---")
        print(f"AD_SERVER = '{ad_server_ip}'")
        print("AD_PORT = 389")
        print(f"AD_DOMAIN_NETBIOS = '{ad_domain_netbios}'")
        print(f"AD_DOMAIN_UPN = '{ad_domain_upn}'")
        print(f"SEARCH_BASE = '{search_base}' # Verifique se esta é a OU principal desejada (ex: OU=HRMJ,...)\n")
        
        print("# --- Configuração de Segurança (Grupo de Administradores) ---")
        print("# O valor abaixo é o grupo padrão de Admins do Domínio. Você pode alterá-lo para um grupo mais específico, como 'TI'.")
        print(f"AD_REQUIRED_GROUP_DN = '{admin_group_dn}'\n")

        print("# --- Configurações Estáticas (para a biblioteca ldap3) ---")
        print("# Estas linhas geralmente não mudam.")
        print("import ssl")
        print("from ldap3 import Tls")
        print("TLS_CONFIG = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)")
        
    except (subprocess.CalledProcessError, AttributeError, socket.gaierror) as e:
        print("\n❌ Falha ao descobrir as informações.")
        print("   Certifique-se de que está executando este script em uma máquina Windows")
        print("   conectada ao domínio e que as Ferramentas de Administração de Servidor Remoto (RSAT)")
        print("   (que incluem 'dsquery' e 'nltest') estão instaladas.")
        print(f"   Erro: {e}")

if __name__ == "__main__":
    descobrir_config_ad()