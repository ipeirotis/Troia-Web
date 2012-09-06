exec mysql --user="%(db_user)s" --password="%(db_password)s" %(db_name)s < %(sql_root)s/db_clear.sql
