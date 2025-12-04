import os
import random
import re
import sqlite3
import string
from transliterate import translit
import pandas as pd
import bcrypt

db_path = os.path.join(os.path.dirname(__file__), 'avtoprom.db')


def connect():
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    cursor = c.cursor()
    c.execute('pragma foreign_keys = on')
    return c, cursor


def signup_root():
    # c = sqlite3.connect(db_path)
    # c.row_factory = sqlite3.Row
    # cursor = c.cursor()
    c, cursor = connect()
    query = 'select * from users where login=?'
    cursor.execute(query, ('root',))
    res = cursor.fetchone()
    print(res)

    if res is None:
        root = {
            'login': 'root',
            'password': bcrypt.hashpw('root'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        }
        query = f'insert into users (login, password) values (?, ?)'
        cursor.execute(query, (root['login'], root['password']))

        query = f'insert into employees (user_id, role_id) values(?, ?)'
        cursor.execute(query, (1, 1))

        c.commit()
        print('root аккаунт восстановлен')
    c.close()


def get_user(login, password=None):
    c, cursor = connect()
    query = f'select * from users where login=?'
    cursor.execute(query, (login,))
    user = cursor.fetchone()
    print(user)
    c.close()

    if user is None:
        return None
    if password:
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return user
        raise Exception('Неверный логин и/или пароль')
    print(f"dict: {user}")
    return dict(user)


def get_permissions_list():
    c, cursor = connect()
    query = 'select * from permissions'
    cursor.execute(query)
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def get_broadcast_list(role_id=None):
    # c, cursor = connect()
    c = sqlite3.connect(db_path)
    if role_id:
        c.row_factory = sqlite3.Row
    cursor = c.cursor()
    query = 'select * from broadcast'
    if role_id:
        query += ' where role_id=?'
        cursor.execute(query, (role_id,))
    else:
        cursor.execute(query)
    data = cursor.fetchall()
    c.close()
    return data


def clear_broadcast(task_id: int):
    try:
        c, cursor = connect()
        query = 'delete from broadcast where task_id=?'
        cursor.execute(query, (task_id,))
        c.commit()
        c.close()
    except:
        raise Exception(f'Не удалось очистить рассылку по задаче {task_id}')


def broadcast_audience(task_id):
    c, cursor = connect()
    query = 'select * from broadcast where task_id=?'
    cursor.execute(query, (task_id,))

    c.close()


def get_all_tg():
    c, cursor = connect()
    query = 'select * from tg'
    cursor.execute(query)
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def get_emp_subscriptions(tg):
    c, cursor = connect()
    query = """
        select distinct(bc.task_id)
        from broadcast bc
        join roles r on r.role_id=bc.role_id
        join employees e on e.role_id=r.role_id
        join users u on u.user_id=e.user_id
        join tg on tg.chat_id=u.tg
        where tg.chat_id=?
    """
    cursor.execute(query, (tg,))
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def get_permissions(login):
    c, cursor = connect()
    query = (f'select p.* '
             f'from permissions p '
             f'join roles_permission rp on rp.perm_id=p.perm_id '
             f'join roles r on r.role_id=rp.role_id '
             f'join employees e on e.role_id=r.role_id '
             f'join users u on u.user_id=e.user_id '
             f'where u.login=?')
    cursor.execute(query, (login,))
    perms = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(perms, columns=columns)
    return table


def get_roles(with_reserved=False):
    c, cursor = connect()
    query = 'select * from roles'
    if not with_reserved:
        query += ' where reserved=0'
    cursor.execute(query)
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def get_role(role):
    c, cursor = connect()
    query = 'select * from roles where role_id=?'
    cursor.execute(query, (role,))
    data = cursor.fetchone()
    c.close()
    return dict(data) if not data is None else None


def get_role_permissions(role):
    c, cursor = connect()
    query = ('select p.* '
             'from permissions p '
             'join roles_permission rp on rp.perm_id=p.perm_id '
             'where rp.role_id=?')
    cursor.execute(query, (role,))
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def get_user_roles(user_id: int):
    c, cursor = connect()
    query = ('select r.* '
             'from roles r '
             'join employees e on e.role_id=r.role_id '
             'where e.user_id=?')
    cursor.execute(query, (user_id,))
    data = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(data, columns=columns)
    return table


def create_role(data: dict, columns: dict):
    c, cursor = connect()
    try:
        query = 'insert into roles (title) values (?)'
        cursor.execute(query, (data[columns['title']],))
        id = cursor.lastrowid

        query = 'insert into roles_permission (role_id, perm_id) values (?,?)'
        args = [(id, p) for p in data[columns['permission']]]
        cursor.executemany(query, args)

        query = 'insert into broadcast (role_id, task_id) values(?,?)'
        args = [(id, bc) for bc in data[columns['broadcast']]]
        cursor.executemany(query, args)

        c.commit()
        return
    except Exception as e:
        c.rollback()
        raise Exception(f'Не удалось создать роль: {e}')
    finally:
        c.close()


def update_role(role_id: int, data: dict, perms: list, bc: list, columns: dict):
    c, cursor = connect()
    try:
        query = 'update roles set title=? where role_id=?'
        cursor.execute(query, (data[columns['title']], role_id))

        query = 'delete from roles_permission where role_id=?'
        cursor.execute(query, (role_id,))

        query = 'insert into roles_permission (role_id, perm_id) values (?,?)'
        args = [(role_id, p) for p in perms]
        cursor.executemany(query, args)

        query = 'delete from broadcast where role_id=?'
        cursor.execute(query, (role_id,))

        query = 'insert into broadcast (role_id, task_id) values(?,?)'
        args = [(role_id, p) for p in bc]
        cursor.executemany(query, args)

        c.commit()
        return True
    except Exception as e:
        c.rollback()
        raise Exception(f'Не удалось обновить роль: {e}')
    finally:
        c.close()


def delete_role(role_id: int):
    try:
        c, cursor = connect()
        query = 'delete from roles where role_id=?'
        cursor.execute(query, (role_id,))
        c.commit()

        query = "delete from sqlite_sequence where name='roles';"
        cursor.execute(query)
        c.commit()

        c.close()
        return True
    except Exception as e:
        raise Exception(f'Не удалось удалить роль: {e}')


def permissions_parents(role: str):
    c, cursor = connect()
    query = ("with recursive tree as ("
             "select p1.perm_id, p1.title, p1.child from permissions p1 "
             "inner join roles_permission rp1 on rp1.perm_id=p1.perm_id "
             "inner join roles r1 on r1.role_id=rp1.role_id "
             "where r1.title=? "
             "union all "
             "select p.perm_id, p.title, p.child from permissions p "
             "inner join tree t on p.child=t.perm_id"
             ") "
             "select distinct title "
             "from tree "
             "order by title;")
    cursor.execute(query, (role,))
    perms = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(perms, columns=columns)
    return table


def permissions_children(role: str):
    c, cursor = connect()
    query = ("with recursive tree as ("
             "select p1.perm_id, p1.title, p1.child from permissions p1 "
             "inner join roles_permission rp1 on rp1.perm_id=p1.perm_id "
             "inner join roles r1 on r1.role_id=rp1.role_id "
             "where r1.title=? "
             "union all "
             "select p.perm_id, p.title, p.child from permissions p "
             "inner join tree t on p.perm_id=t.child"
             ") "
             "select distinct title "
             "from tree "
             "order by title;")
    cursor.execute(query, (role,))
    perms = cursor.fetchall()
    c.close()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(perms, columns=columns)
    return table


def do_signup(user: dict):
    c, cursor = connect()
    try:
        print(user)
        cursor.execute('begin')
        login = f"{user['lastname']}{user['firstname'][0]}{user['patronymic'][0]}{random.randint(1000, 9999)}".lower().replace(
            ' ', '')
        # login = Tools.transliterate_ru_to_en()
        login = translit(login, 'ru', reversed=True)
        login = re.sub(r'[^a-zA-Z0-9]', '', login).lower()
        query = ('insert into users (lastname, firstname, patronymic, emp_num, login, password)'
                 'values (?,?,?,?,?,?)')
        password = generate_password(12)
        hashed = bcrypt.hashpw(password.encode('utf-8'),
                               bcrypt.gensalt()).decode('utf-8')
        cursor.execute(query, (user['lastname'], user['firstname'], user['patronymic'], user['emp_num'], login, hashed))
        cursor.execute('commit')

        user['login'] = login
        user['password'] = password
        print(user)
        return user
    except Exception as e:
        cursor.execute('rollback')
        raise e
    finally:
        c.close()


def do_signup_many(credentials: pd.DataFrame, columns: dict):
    c, cursor = connect()
    try:
        cursor.execute('begin')
        for i, row in credentials.iterrows():
            login = f"{row[columns['lastname']]}{row[columns['firstname']][0]}{row[columns['patronymic']][0]}{random.randint(1000, 99999)}".lower()
            # print(login)
            login = translit(login, 'ru', reversed=True)
            login = re.sub(r'[^a-zA-Z0-9]', '', login).lower()
            credentials.at[i, 'login'] = login
            password = generate_password(12)
            hashed = bcrypt.hashpw(password.encode('utf-8'),
                                   bcrypt.gensalt()).decode('utf-8')
            credentials.at[i, 'password'] = password
            query = ('insert into users (lastname, firstname, patronymic, emp_num, login, password)'
                     'values (?,?,?,?,?,?)')
            # print(row.to_dict())
            cursor.execute(query, (
                row[columns['lastname']], row[columns['firstname']], row[columns['patronymic']],
                row[columns['emp_num']], login, hashed
            ))
            cursor.execute('commit')
        return credentials
    except Exception as e:
        print(f'Не удалось записать пользователей: {e}')
        cursor.execute('rollback')
        return None
    finally:
        c.close()


def get_users(exclude_me=None):
    c, cursor = connect()
    query = 'select * from users'
    if exclude_me:
        query += ' where login != ?'
        cursor.execute(query, (exclude_me,))
    else:
        cursor.execute(query)
    users = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    table = pd.DataFrame(users, columns=columns)
    c.close()
    return table


def update_user(data: dict, assoc: dict, roles: list | None, user_id):
    c, cursor = connect()
    try:
        query = 'update users set '
        args = []
        for k, v in assoc.items():
            if v in data:
                query += f'{k}=?, '
                args.append(data[v])
        query = query[:-2]
        query += ' where user_id=?'
        args.append(user_id)
        # print(f'query: {query}, args: {args}')
        cursor.execute(query, tuple(args))

        if roles:
            query = 'delete from employees where user_id=?'
            cursor.execute(query, (user_id,))

            query = 'insert into employees (user_id, role_id) values (?,?)'
            args = [(user_id, r) for r in roles]
            cursor.executemany(query, args)

        c.commit()
        return True
    except Exception as e:
        c.rollback()
        raise Exception(e)
    finally:
        c.close()


def delete_user(user_id: int):
    try:
        c, cursor = connect()
        query = 'delete from users where user_id=?'
        cursor.execute(query, (user_id,))
        c.commit()
        c.close()
    except Exception as e:
        raise Exception(f'Не удалось удалить пользователя: {str(e)}')


def generate_password(length, hard=False):
    characters = string.ascii_letters + string.digits
    if hard:
        characters += string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password
