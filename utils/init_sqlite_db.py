import sqlite3


def create_db():
    c = sqlite3.connect('avtoprom.db')
    cursor = c.cursor()

    cursor.execute('PRAGMA foreign_keys = ON;')
    ctine = 'create table if not exists'

    query = (f'{ctine} permissions('
             f'perm_id integer primary key autoincrement,'
             f'title text unique not null)')
    cursor.execute(query)

    query = (f'{ctine} roles('
             f'role_id integer primary key autoincrement,'
             f'title text unique not null)')
    cursor.execute(query)

    query = (f'{ctine} users ('
             f'user_id integer primary key autoincrement,'
             f'lastname text,'
             f'firstname text,'
             f'patronymic text,'
             f'emp_num text unique,'
             f'login text unique not null,'
             f'password text not null)')
    cursor.execute(query)

    query = (f'{ctine} roles_permission('
             f'role_id integer,'
             f'perm_id integer,'
             f'foreign key (role_id) references roles (role_id) on delete cascade,'
             f'foreign key (perm_id) references permissions (perm_id) on delete cascade)')
    cursor.execute(query)

    query = (f'{ctine} employees('
             f'user_id integer,'
             f'role_id integer,'
             f'foreign key (user_id) references users (user_id) on delete cascade,'
             f'foreign key (role_id) references roles (role_id) on delete cascade)')
    cursor.execute(query)

    c.commit()
    close()

