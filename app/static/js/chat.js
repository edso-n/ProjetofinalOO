const socket = io();

// Escuta o evento 'message' do servidor
socket.on('message', (data) => {
    console.log('Nova mensagem recebida:', data); // Log para depuração

    // Encontra o elemento onde as mensagens serão exibidas
    const messageDisplay = document.getElementById('messageDisplay');

    if (messageDisplay) {
        // Cria um novo elemento <li> para a mensagem
        const newMessage = document.createElement('li');
        newMessage.textContent = `${data.content} | escrita por: ${data.username}`;

        // Adiciona a nova mensagem ao final da lista
        messageDisplay.appendChild(newMessage);

        // Rola a página para exibir a nova mensagem
        messageDisplay.scrollTop = messageDisplay.scrollHeight;
    } else {
        console.error('Elemento messageDisplay não encontrado!');
    }
});

// Envia uma nova mensagem
document.getElementById('sendButton').addEventListener('click', () => {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (message) {
        console.log('Enviando mensagem:', message); // Log para depuração
        socket.emit('message', message); // Envia a mensagem para o servidor
        messageInput.value = ''; // Limpa o campo de entrada
    }
});