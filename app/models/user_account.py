class UserAccount():

    def __init__(self, username, password, livros_lidos=None):
        self.username= username
        self.password= password
        self.livros_lidos = livros_lidos if livros_lidos else []
        
    def isAdmin(self):
        return False


class SuperAccount(UserAccount):

    def __init__(self, username, password, permissions =None, livros_lidos=None):

        super().__init__(username, password,livros_lidos)
        self.permissions= permissions
        if not permissions:
            self.permissions= ['user']

    def isAdmin(self):
        return True
