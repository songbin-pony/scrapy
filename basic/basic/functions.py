import pymysql


def mysql(sql):
    db = pymysql.connect("47.101.189.229","pony","1","pony",charset='utf8')
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
    except:
        db.rollback()
        return "failure"
    db.close()