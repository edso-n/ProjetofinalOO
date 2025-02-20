from app.models.user_account import UserAccount, SuperAccount
from app.models.user_message import UserMessage
import json
import uuid


class MessageRecord():
    """Banco de dados JSON para o recurso: Mensagem"""

    def __init__(self):
        self.__user_messages= []
        self.read()


    def read(self):
        try:
            with open("app/controllers/db/user_messages.json", "r") as fjson:
                user_msg = json.load(fjson)
                self.__user_messages = [UserMessage(**msg) for msg in user_msg]
        except FileNotFoundError:
            print('Não existem mensagens registradas!')

    def __write(self):
        try:
            with open("app/controllers/db/user_messages.json", "w") as fjson:
                user_msg = [vars(user_msg) for user_msg in self.__user_messages]
                json.dump(user_msg, fjson, indent=4)  # Use indent=4 para facilitar a leitura do arquivo
                print(f'Arquivo gravado com sucesso (Mensagem)!')
        except Exception as e:
            print(f'Erro ao gravar o arquivo (Mensagem): {e}')

    def book(self,username,content):
        new_msg= UserMessage(username,content)
        self.__user_messages.append(new_msg)
        self.__write()
        return new_msg


    def getUsersMessages(self):
        return self.__user_messages


# ------------------------------------------------------------------------------

class UserRecord():
    """Banco de dados JSON para o recurso: Usuário"""

    def __init__(self):
        self.__allusers= {'user_accounts': [], 'super_accounts': []}
        self.__authenticated_users = {}
        self.read('user_accounts')
        self.read('super_accounts')

    def update_user(self, user):
        # Lógica para atualizar o usuário no banco de dados
        for u in self.users:
            if u.username == user.username:
                self.users[self.users.index(u)] = user
                break
    
    def read(self,database):
        account_class = SuperAccount if (database == 'super_accounts' ) else UserAccount
        try:
            with open(f"app/controllers/db/{database}.json", "r") as fjson:
                user_d = json.load(fjson)
                self.__allusers[database]= [account_class(**data) for data in user_d]
        except FileNotFoundError:
            self.__allusers[database].append(account_class('Guest', '000000'))


    def __write(self,database):
        try:
            with open(f"app/controllers/db/{database}.json", "w") as fjson:
                user_data = [vars(user_account) for user_account in \
                self.__allusers[database]]
                json.dump(user_data, fjson)
                print(f'Arquivo gravado com sucesso (Usuário)!')
        except FileNotFoundError:
            print('O sistema não conseguiu gravar o arquivo (Usuário)!')



    def setUser(self,username,password):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if username == user.username:
                    user.password= password
                    print(f'O usuário {username} foi editado com sucesso.')
                    self.__write(account_type)
                    return username
        print('O método setUser foi chamado, porém sem sucesso.')
        return None


    def removeUser(self, user):
        for account_type in ['user_accounts', 'super_accounts']:
            if user in self.__allusers[account_type]:
                print(f'O usuário {"(super) " if account_type == "super_accounts" else ""}{user.username} foi encontrado no cadastro.')
                self.__allusers[account_type].remove(user)
                print(f'O usuário {"(super) " if account_type == "super_accounts" else ""}{user.username} foi removido do cadastro.')
                self.__write(account_type)
                return user.username
        print(f'O usuário {user.username} não foi identificado!')
        return None


    def book(self, username, password, permissions):
        account_type = 'super_accounts' if permissions else 'user_accounts'
        account_class = SuperAccount if permissions else UserAccount
        new_user = account_class(username, password, permissions) if permissions else account_class(username, password)
        self.__allusers[account_type].append(new_user)
        self.__write(account_type)
        return new_user.username


    def getUserAccounts(self):
        return self.__allusers['user_accounts']


    def getCurrentUser(self,session_id):
        if session_id in self.__authenticated_users:
            return self.__authenticated_users[session_id]
        else:
            return None


    def getAuthenticatedUsers(self):
        return self.__authenticated_users


    def checkUser(self, username, password):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if user.username == username and user.password == password:
                    session_id = str(uuid.uuid4())
                    self.__authenticated_users[session_id] = user
                    return session_id
        return None


    def logout(self, session_id):
        if session_id in self.__authenticated_users:
            del self.__authenticated_users[session_id] # Remove o usuário logado

    def marcar_livro_como_lido(self, username, titulo_livro):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if user.username == username:
                    if titulo_livro in user.livros_lidos:
                        # Se o livro já está marcado como lido, desmarque
                        user.livros_lidos.remove(titulo_livro)
                        print(f"Livro '{titulo_livro}' desmarcado como lido para o usuário {username}.")
                    else:
                        # Se o livro não está marcado como lido, marque
                        user.livros_lidos.append(titulo_livro)
                        print(f"Livro '{titulo_livro}' marcado como lido para o usuário {username}.")
                    self.__write(account_type)  # Salva as alterações no arquivo JSON
                    return True
        return False

    def obter_livros_lidos(self, username):
        for account_type in ['user_accounts', 'super_accounts']:
            for user in self.__allusers[account_type]:
                if user.username == username:
                    return user.livros_lidos
        return []

class BookRecord:
    def __init__(self):
        self.books = []
        
    def add_book(self, book):
        self.books.append(book)
        
    def get_all_books(self):
        return self.books
        
    def get_book_by_title(self, title):
        for book in self.books:
            if book.titulo == title:
                return book
        return None
    
    def livro_foi_lido(self, username, titulo_livro):
        for user in self.__users.get_all_users():
            if user.username == username and titulo_livro in user.livros_lidos:
                return True
        return False

class Livro:
    def __init__(self, titulo: str, autor: str, capa: str):
        self.titulo = titulo
        self.autor = autor
        self.capa = capa
        self.lido = False

class LivroFiccao(Livro):
    def __init__(self, titulo: str, autor: str, capa: str, genero: str):
        super().__init__(titulo, autor, capa)
        self.genero = genero

class LivroNaoFiccao(Livro):
    def __init__(self, titulo: str, autor: str, capa: str, area: str):
        super().__init__(titulo, autor, capa)
        self.area = area