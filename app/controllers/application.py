from app.controllers.datarecord import UserRecord, MessageRecord, BookRecord, LivroFiccao, LivroNaoFiccao
from bottle import template, redirect, request, response, Bottle, static_file
import socketio

class Application:

    def __init__(self):

        self.pages = {
            'portal': self.portal,
            'pagina': self.pagina,
            'create': self.create,
            'delete': self.delete,
            'chat': self.chat,
            'edit': self.edit
        }
        self.__users = UserRecord()
        self.__messages = MessageRecord()

        self.edited = None
        self.removed = None
        self.created= None
        
        self.__books = BookRecord()
        self.__initialize_sample_books()

        # Initialize Bottle app
        self.app = Bottle()
        self.setup_routes()

        # Initialize Socket.IO server
        self.sio = socketio.Server(async_mode='eventlet')
        self.setup_websocket_events()

        # Create WSGI app
        self.wsgi_app = socketio.WSGIApp(self.sio, self.app)


    # estabelecimento das rotas
    def setup_routes(self):
        @self.app.route('/static/<filepath:path>')
        def serve_static(filepath):
            return static_file(filepath, root='./app/static')


        @self.app.route('/pagina', method='GET')
        def pagina_getter():
            return self.render('pagina')

        @self.app.route('/chat', method='GET')
        def chat_getter():
            return self.render('chat')

        @self.app.route('/')
        @self.app.route('/portal', method='GET')
        def portal_getter():
            return self.render('portal')

        @self.app.route('/edit', method='GET')
        def edit_getter():
            return self.render('edit')

        @self.app.route('/portal', method='POST')
        def portal_action():
            username = request.forms.get('username')
            password = request.forms.get('password')
            self.authenticate_user(username, password)

        @self.app.route('/edit', method='POST')
        def edit_action():
            username = request.forms.get('username')
            password = request.forms.get('password')
            print(username + ' sendo atualizado...')
            self.update_user(username, password)
            return self.render('edit')

        @self.app.route('/create', method='GET')
        def create_getter():
            return self.render('create')

        @self.app.route('/create', method='POST')
        def create_action():
            username = request.forms.get('username')
            password = request.forms.get('password')
            self.insert_user(username, password)
            return self.render('portal')

        @self.app.route('/logout', method='POST')
        def logout_action():
            self.logout_user()
            return self.render('portal')

        @self.app.route('/delete', method='GET')
        def delete_getter():
            return self.render('delete')

        @self.app.route('/delete', method='POST')
        def delete_action():
            self.delete_user()
            return self.render('portal')
        
        @self.app.route('/alugar/<titulo>', method='POST')
        def marcar_livro_como_lido(titulo):
            current_user = self.getCurrentUserBySessionId()
            if current_user:
                if self.__users.marcar_livro_como_lido(current_user.username, titulo):
                    self.sio.emit('status_livro_atualizado', {
                        'titulo': titulo,
                        'lido': True
                    })
                    return "Livro marcado como lido!"
                return "Livro já estava marcado como lido."
            return redirect('/portal')


    
    # método controlador de acesso às páginas:
    def render(self, page, parameter=None):
        content = self.pages.get(page, self.portal)
        if not parameter:
            return content()
        return content(parameter)

    # métodos controladores de páginas
    def getAuthenticatedUsers(self):
        return self.__users.getAuthenticatedUsers()

    def getCurrentUserBySessionId(self):
        session_id = request.get_cookie('session_id')
        return self.__users.getCurrentUser(session_id)

    def create(self):
        return template('app/views/html/create')

    def delete(self):
        current_user = self.getCurrentUserBySessionId()
        user_accounts= self.__users.getUserAccounts()
        return template('app/views/html/delete', user=current_user, accounts=user_accounts)

    def edit(self):
        current_user = self.getCurrentUserBySessionId()
        user_accounts= self.__users.getUserAccounts()
        return template('app/views/html/edit', user=current_user, accounts= user_accounts)

    def portal(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            portal_render = template('app/views/html/portal', \
            username=current_user.username, edited=self.edited, \
            removed=self.removed, created=self.created)
            self.edited = None
            self.removed= None
            self.created= None
            return portal_render
        portal_render = template('app/views/html/portal', username=None, \
        edited=self.edited, removed=self.removed, created=self.created)
        self.edited = None
        self.removed= None
        self.created= None
        return portal_render

    def pagina(self):
        self.update_users_list()
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            livros = self.__books.get_all_books()  
            return template('app/views/html/pagina', 
                        transfered=True, 
                        current_user=current_user,
                        livros=livros) 
        return template('app/views/html/pagina', transfered=False)

    def is_authenticated(self, username):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            return username == current_user.username
        return False

    def authenticate_user(self, username, password):
        session_id = self.__users.checkUser(username, password)
        if session_id:
            self.logout_user()
            response.set_cookie('session_id', session_id, httponly=True, secure=False, max_age=3600)
            redirect('/pagina')
        redirect('/portal')

    def delete_user(self):
        current_user = self.getCurrentUserBySessionId()
        self.logout_user()
        self.removed= self.__users.removeUser(current_user)
        self.update_account_list()
        print(f'Valor de retorno de self.removed: {self.removed}')
        redirect('/portal')

    def insert_user(self, username, password):
        self.created= self.__users.book(username, password,[])
        self.update_account_list()
        redirect('/portal')

    def update_user(self, username, password):
        self.edited = self.__users.setUser(username, password)
        redirect('/portal')

    def logout_user(self):
        session_id = request.get_cookie('session_id')
        self.__users.logout(session_id)
        response.delete_cookie('session_id')
        self.update_users_list()

    def chat(self):
        current_user = self.getCurrentUserBySessionId()
        if current_user:
            messages = self.__messages.getUsersMessages()
            auth_users= self.__users.getAuthenticatedUsers().values()
            return template('app/views/html/chat', current_user=current_user, \
            messages=messages, auth_users=auth_users)
        redirect('/portal')

    def newMessage(self, message):
        try:
            content = message
            current_user = self.getCurrentUserBySessionId()
            if current_user:
                print(f"Usuário autenticado: {current_user.username}")  # Log para depuração
                new_msg = self.__messages.book(current_user.username, content)
                print(f"Nova mensagem salva: {new_msg.content} | Usuário: {new_msg.username}")  # Log para depuração
                self.sio.emit('message', {'content': new_msg.content, 'username': new_msg.username}, broadcast=True)
                return new_msg
            else:
                print("Usuário não autenticado.")  # Log para depuração
                return None
        except Exception as e:
            print(f"Erro ao processar a mensagem: {e}")  # Log para depuração
            return None
        
    def __initialize_sample_books(self):
        self.__books.add_book(LivroFiccao(
            "1984", 
            "George Orwell", 
            "/static/img/1984.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Crime e Castigo", 
            "Fiodor Dostoyevisky", 
            "/static/img/crime.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Dom Quixote de La Mancha", 
            "Miguel cervantes", 
            "/static/img/domquixote.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Memórias Postumas de Brás Cubas", 
            "Machado de Assis", 
            "/static/img/memoria.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "A Odisseia", 
            "Homero", 
            "/static/img/odisseia.jpeg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Pequeno Príncipe", 
            "George Orwell", 
            "/static/img/pequenop.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Divina Comédia", 
            "Dante", 
            "/static/img/dante.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Meditações", 
            "Marcus Aurélio", 
            "/static/img/meditacoes.jpeg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "A morte de Ivan Ilith", 
            "Tolstoy", 
            "/static/img/ivan.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroFiccao(
            "Pequeno Príncipe", 
            "George Orwell", 
            "/static/img/pequenop.jpg", 
            "Distopia"
        ) )
        
        self.__books.add_book(LivroNaoFiccao(
            "O idiota", 
            "Fiodor Dostoievisky", 
            "/static/img/idiota.jpg", 
            "História"
        ))
        
        

    # Websocket:
    def setup_websocket_events(self):
        
        @self.sio.event
        def status_livro_atualizado(sid, data):
            self.sio.emit('status_livro_atualizado', data, broadcast=True)

        @self.sio.event
        async def connect(sid, environ):
            print(f'Client connected: {sid}')
            self.sio.emit('connected', {'data': 'Connected'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            print(f'Client disconnected: {sid}')

        # recebimento de solicitação de cliente para atualização das mensagens
        @self.sio.event
        def message(sid, data):
            new_msg = self.newMessage(data)
            self.sio.emit('message', {'content': new_msg.content, 'username': new_msg.username}, broadcast=True)
        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_users_list()
        @self.sio.event
        def update_users_event(sid, data):
            self.sio.emit('update_users_event', {'content': data})

        # solicitação para atualização da lista de usuários conectados. Quem faz
        # esta solicitação é o próprio controlador. Ver update_users_list()
        @self.sio.event
        def update_account_event(sid, data):
            self.sio.emit('update_account_event', {'content': data})

    # este método permite que o controller se comunique diretamente com todos
    # os clientes conectados. Sempre que algum usuários LOGAR ou DESLOGAR
    # este método vai forçar esta atualização em todos os CHATS ativos. Este
    # método é chamado sempre que a rota ''
    def update_users_list(self):
        print('Atualizando a lista de usuários conectados...')
        users = self.__users.getAuthenticatedUsers()
        users_list = [{'username': user.username} for user in users.values()]
        self.sio.emit('update_users_event', {'users': users_list})

    # este método permite que o controller se comunique diretamente com todos
    # os clientes conectados. Sempre que algum usuários se removerem
    # este método vai comunicar todos os Administradores ativos.
    def update_account_list(self):
        print('Atualizando a lista de usuários cadastrados...')
        users = self.__users.getUserAccounts()
        users_list = [{'username': user.username} for user in users]
        self.sio.emit('update_account_event', {'accounts': users_list})
