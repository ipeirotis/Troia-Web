USE %(db_name)s;

DROP TABLE IF EXISTS
   projects;

CREATE TABLE projects ( id VARCHAr(100) NOT NULL PRIMARY KEY, data LONGTEXT NOT NULL);
CREATE INDEX idIndex ON projects (id);
