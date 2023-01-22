"""
Handles mariaDB database commands
"""
import sys
import mariadb
import logging


class MariaDbHandler:
    def __init__(self) -> None:
        self.log = logging.getLogger("main")
        self.cursor = None
        self.database = None

    def write_mariadb_data(self, dbtable: str, **sqlargs: str) -> None:
        """
        write data to n different columns, column names defined as names in sqlargs
        """
        # build argstring -> column names
        # build qmstring -> correct amount of questionmarks for query syntax
        first = True
        argstring = ""
        qmstring = ""
        valuelist = []
        for sqlname in sqlargs:
            # build weird strings
            # detect first iteration
            if first:
                first = False
                argstring += sqlname
                qmstring += '?'
            else:
                argstring += ", " + sqlname
                qmstring += ",?"
            # update valuelist
            valuelist.append(sqlargs[sqlname])

        self.log.debug(f"ArgString built: '{argstring}'; QuestionmarkString built: '{qmstring}'; ValueListString built: '{valuelist}';")

        try:
            self.cursor.execute("INSERT INTO " + self.database + "." + dbtable + "(" + argstring + ") VALUES (" + qmstring + ")",(valuelist))
        except mariadb.Error:
            self.log.exception(f"Error inserting data to MariaDB table '{dbtable}@{self.database}'!")
            sys.exit(501)
        else:
            self.log.debug(f"SQL command executed: [INSERT INTO {self.database}.{dbtable}({argstring}) VALUES ({valuelist})")


    def check_mariadb_data(self, dbtable: str, **conditions: str) -> bool:
        """
        check if a value exists for conditions in dbname.dbtable, return true/false
        """
        first = True
        argstring = ""
        valuelist = []
        for condname in conditions:
            # build weird strings
            # detect first iteration
            if first:
                first = False
                argstring += condname + " = ?"
            else:
                argstring += " and " + condname + " = ?"
            # update valuelist
            valuelist.append(conditions[condname])
        # add sorting and limiting arguments to argstring
        argstring += " LIMIT 1"
        self.log.debug(f"ArgString built: '{argstring}'; ValueListString built: '{valuelist}';")

        try:
            self.cursor.execute("SELECT * FROM " + self.database + "." + dbtable + " WHERE " + argstring,(valuelist))
        except mariadb.Error:
            self.log.exception(f"Error checking if data exists in MariaDB table '{dbtable}@{self.database}'!")
            # TODO: cannot exit because of database error, retry somehow later
            sys.exit(502)
        else:
            self.log.debug(f"SQL command executed: [SELECT * FROM {self.database}.{dbtable} WHERE ({argstring}) = ({valuelist})")

        # check if data was found
        if len(list(self.cursor)) == 0:
            # data not found in DB yet
            self.log.debug(f"Argstring ({argstring}) = ({valuelist}) not found in mariaDB table '{dbtable}@{self.database}' yet.")
            return False
        return True


    def get_mariadb_data(self, dbtable: str, searchcolumnname: str, searchcolumnvalue: str, getcolumnname: str) -> str:
        """
        return value from getcolumnname
        where value searchcolumnvalue occurs in column searchcolumnname
        """
        try:
            self.cursor.execute("SELECT " + getcolumnname + " FROM " + self.database + "." + dbtable + " WHERE " + searchcolumnname + " = ?",(searchcolumnvalue,))
        except mariadb.Error:
            self.log.exception(f"Error getting data from MariaDB table '{dbtable}@{self.database}'!")
            # TODO: cannot exit because of database error, retry somehow later
            sys.exit(502)
        else:
            self.log.debug(f"SQL command executed: [SELECT '{getcolumnname}' FROM {self.database}.{dbtable} WHERE '{searchcolumnname}' = '{searchcolumnvalue}'")

        cursorlist = list(self.cursor)
        # check if data was found
        if len(cursorlist) == 0:
            # No data found
            self.log.debug(f"SQL response: No data found!")
            return None
        # return first occurence of data
        # TODO: handle multiple tuples
        self.log.debug(f"SQL response: data found; Data: [{cursorlist[0][0]}]")
        return cursorlist[0][0]


    def update_mariadb_data(self, dbtable: str, searchcolumnname: str, searchcolumnvalue: str, **writeargs: str) -> None:
        """
        update value of column writecolumnname with writecolumnvalue
        where value searchcolumnvalue occcurs in column searchcolumnname
        """
        # Individual update statements for each key:value pair
        for colname in writeargs:
            writecolumnname = colname
            writecolumnvalue = writeargs[colname]
            try:
                self.cursor.execute("UPDATE " + self.database + "." + dbtable + " SET " + writecolumnname + " = ? WHERE " + searchcolumnname + " = ?",(writecolumnvalue, searchcolumnvalue,))
            except mariadb.Error:
                self.log.exception(f"Error updating data in MariaDB table '{dbtable}@{self.database}'!")
                # TODO: cannot exit because of database error, retry somehow later
                sys.exit(502)
            else:
                self.log.debug(f"SQL command executed: [UPDATE {self.database}.{dbtable} SET '{writecolumnname}' = '{writecolumnvalue}' WHERE '{searchcolumnname}' = '{searchcolumnvalue}'")

