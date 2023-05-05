import sys

import mysql.connector

from settings import CONFIG


class Database:
    def get_conn(self):
        try:
            return mysql.connector.connect(
                user=CONFIG.user,
                password=CONFIG.password,
                host=CONFIG.host,
                port=CONFIG.port,
                database=CONFIG.database,
            )
        except Exception as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    def select_with(self, query: str) -> list:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()
        conn.close()

        return res

    def select_all_from(self, table: str, condition: str = "1=1", cols: str = "*"):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT {cols} FROM {table} WHERE {condition}")
        res = cur.fetchall()
        cur.close()
        conn.close()

        return res

    def insert_into(self, table: str, data: tuple = None, is_bulk: bool = False):
        conn = self.get_conn()
        cur = conn.cursor()
        id = 0

        columns = f"({', '.join(CONFIG.INSERT[table])})"
        values = f"({', '.join(['%s'] * len(CONFIG.INSERT[table]))})"
        query = f"INSERT INTO {table} {columns} VALUES {values}"
        if is_bulk:
            cur.executemany(query, data)
        else:
            cur.execute(query, data)
            id = cur.lastrowid

        conn.commit()
        cur.close()
        conn.close()
        return id

    def update_table(
        self, table: str, set_cond: str, where_cond: str, data: tuple = ()
    ):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE {table} set {set_cond} WHERE {where_cond}", data)
        conn.commit()
        cur.close()
        conn.close()

    def delete_from(self, table: str = "", condition: str = "1=1"):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table} WHERE {condition}")
        conn.commit()
        cur.close()
        conn.close()

    def select_or_insert(self, table: str, condition: str, data: tuple):
        res = self.select_all_from(table=table, condition=condition)
        if not res:
            self.insert_into(table, data)
            res = self.select_all_from(table, condition=condition)
        return res


database = Database()


if __name__ == "__main__":
    ID = 85
    condition = f'ID = "{ID}"'
    posts = database.select_all_from(
        table=f"{CONFIG.TABLE_PREFIX}posts", condition=condition
    )
    print(posts)
