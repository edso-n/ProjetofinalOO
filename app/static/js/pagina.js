// Inicializa a conexão WebSocket
const socket = io(); // Isso cria a conexão com o servidor WebSocket

// Função para atualizar o estado do botão
function atualizarBotao(titulo, lido) {
    const btn = document.querySelector(`[data-titulo="${titulo}"]`);
    if (btn) {
        btn.classList.toggle('lido', lido);
        btn.classList.toggle('nao-lido', !lido);
        btn.textContent = lido ? 'Lido ✓' : 'Não Lido';
    }
}

// Escuta o evento 'status_livro_atualizado' do servidor
socket.on('status_livro_atualizado', (data) => {
    atualizarBotao(data.titulo, data.lido);
});

// Evento de clique no botão
document.addEventListener('click', async (e) => {
    const btn = e.target.closest('.status-btn');
    if (btn) {
        e.preventDefault();
        const titulo = btn.dataset.titulo;
        const novoEstado = !btn.classList.contains('lido');
        
        console.log(`Título: ${titulo}, Novo Estado: ${novoEstado}`); // Log para depuração
        
        // Atualização otimista (não espera resposta do servidor)
        atualizarBotao(titulo, novoEstado);
        
        try {
            const response = await fetch(`/alugar/${titulo}`, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lido: novoEstado })
            });
            
            console.log('Resposta do servidor:', response); // Log para depuração
            
            if (!response.ok) {
                throw new Error('Erro ao atualizar o status do livro');
            }
        } catch (error) {
            // Reverte em caso de erro
            atualizarBotao(titulo, !novoEstado);
            console.error('Erro:', error);
        }
    }
});