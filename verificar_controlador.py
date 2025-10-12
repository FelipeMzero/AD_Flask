import socket
import subprocess

def servidor_ad_conectado():
    try:
        # Tenta descobrir o nome do domínio
        dominio = subprocess.check_output("echo %USERDOMAIN%", shell=True).decode().strip()
        
        # Tenta descobrir o servidor do AD com o comando nltest
        resultado = subprocess.check_output("nltest /dsgetdc:%USERDOMAIN%", shell=True).decode(errors="ignore")

        print("✅ Informações do Active Directory detectadas:\n")
        print(resultado)

        # Extrai apenas o nome do servidor do AD
        for linha in resultado.splitlines():
            if "DC:" in linha:
                servidor = linha.split(":")[1].strip()
                print(f"🖥️ Controlador de domínio conectado: {servidor}")
                break

        print(f"🏢 Domínio atual: {dominio}")
    except Exception as e:
        print(f"⚠️ Erro ao obter informações do AD: {e}")


if __name__ == "__main__":
    servidor_ad_conectado()
