def fetch(syntax: str, cur):
    return list(map(lambda x: x[0], cur.execute(syntax).fetchall()))
