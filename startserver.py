from app.controllers.application import Application
import socketio
import eventlet

# Inicialize o servidor Socket.IO
sio = socketio.Server(cors_allowed_origins="http://0.0.0.0:8086")  # Use Server, não AsyncServer

# Inicialize a aplicação
app = Application()

# Anexe o Socket.IO à aplicação
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Configuração dos eventos do Socket.IO
@sio.event
def connect(sid, environ):
    print(f'Cliente conectado: {sid}')

@sio.event
def disconnect(sid):
    print(f'Cliente desconectado: {sid}')

# Executa a aplicação
if __name__ == '__main__':
    # Inicia o servidor com eventlet
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8086)), app.wsgi_app)