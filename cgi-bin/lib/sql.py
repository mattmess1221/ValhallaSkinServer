import mysql.connector
from configparser import ConfigParser

config = ConfigParser()
config.read("hdskins.ini")
host = config.get("mysql", "host")
user = config.get("mysql", "user")
password = config.get("mysql", "password")
database = config.get("mysql", "database")

class Database(object):
    """An instance of a mysql database"""
    def __init__(self):
        self.cnx = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
    def __enter__(self):
        self.cursor = self.cnx.cursor()
        return self
    def __exit__(self, type, value, traceback):
        self.close()
    def close(self):
       # self.cursor.close()
        self.cnx.close()

    def get_textures(self, uuid, get_meta = True):
        """Gets a dict of textures from the database if it exists
        :param uuid: the id of the player
        :type uuid: str
        :param get_meta: True to get any metadata information. False to skip.
        :rtype: dict
        """
        self.cursor.execute("""SELECT t.type,t.url
        FROM users u
        JOIN textures t
        ON u.id = t.user_id
        WHERE u.uuid = %s;""", (uuid,))
        obj = {}
        for (type,url) in self.cursor.fetchall():
            texture = {"url": url}
            if get_meta:
                metadata = self.get_metadata(uuid, type)
                if metadata:
                    texture.update({"metadata": metadata})
            obj.update({type:texture})
        return obj

    def get_name(self, uuid):
        """Gets the known name from the database."""
        self.cursor.execute("SELECT name FROM users WHERE uuid = %s;", (uuid,))

        return self.cursor.fetchone()

    def get_metadata(self, uuid, type):
        """Gets all texture metadata for this uuid"""
        self.cursor.execute("""SELECT m.key,m.val
        FROM users u
        JOIN textures t
        ON u.id = t.user_id
        JOIN metadata m
        ON t.id = m.texture_id
        WHERE u.uuid = %(id)s AND t.type = %(type)s;
        """, {"id":uuid, "type":type})
        obj = {}
        for (key, val) in self.cursor:
            obj.update({key:val})
        return obj
