// /static/js/script.js

document.addEventListener('DOMContentLoaded', function() {
    
    // Validação de confirmação de senha no formulário de criação
    const passwordInput = document.getElementById('senha');
    const confirmPasswordInput = document.getElementById('confirmar_senha');
    if (passwordInput && confirmPasswordInput) {
        const validatePasswords = () => {
            if (passwordInput.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity("As senhas não conferem.");
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        };
        passwordInput.addEventListener('input', validatePasswords);
        confirmPasswordInput.addEventListener('input', validatePasswords);
    }

    // Modal de confirmação para ações de gerenciamento de usuário
    $('#confirmModal').on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget); // Botão que acionou o modal
        const action = button.data('action');
        const userDn = button.data('user-dn');
        const userCn = button.data('user-cn');
        const novaSenha = button.closest('form').find('input[name="nova_senha"]').val();

        const modal = $(this);
        modal.find('.modal-title').text(`Confirmar Ação`);
        
        let modalBodyText = '';
        if (action === 'desabilitar') {
            modalBodyText = `Você tem certeza que deseja <strong>desabilitar</strong> o usuário ${userCn}?`;
        } else if (action === 'habilitar') {
            modalBodyText = `Você tem certeza que deseja <strong>habilitar</strong> o usuário ${userCn}?`;
        } else if (action === 'resetar_senha') {
             if (!novaSenha) {
                alert('Por favor, digite a nova senha antes de clicar em Resetar.');
                return event.preventDefault();
            }
            modalBodyText = `Você tem certeza que deseja <strong>resetar a senha</strong> do usuário ${userCn} para "${novaSenha}"?`;
        }
        
        modal.find('.modal-body-text').html(modalBodyText);
        
        // Configura o formulário dentro do modal para enviar a ação correta
        modal.find('#modal-confirm-form-user-dn').val(userDn);
        modal.find('#modal-confirm-form-action').val(action);
        modal.find('#modal-confirm-form-nova-senha').val(novaSenha);
    });
});