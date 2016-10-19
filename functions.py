from addons import mysql, responses_codes


def is_none(s):
    return None if s == "None" or s == "" else s


def list_users(since_id, limit, order, entity_name, var):
    cur = mysql.connection.cursor()
    if entity_name == "forum":
        query = '''SELECT DISTINCT u.id, u.about, u.email, u.username, u.isAnonymous, u.name FROM User u,Post p WHERE u.email = p.user AND p.forum = '%s' '''
    query_params = (var,)
    if since_id:
        query += "AND u.id >= '%s' "
        query_params += (since_id,)
    if order:
        query += "ORDER BY u.name " + order + " "
    else:
        query += "ORDER BY u.name DESC "
    if limit:
        query += "LIMIT %s "
        query_params += (int(limit),)
    cur.execute(query % query_params)
    array_entitys = []
    for x in cur.fetchall():
        followers = get_followers(x[2])
        following = get_following(x[2])
        subscriptions = get_subscriptions(x[2])
        entity = {
            "id": x[0],
            "about": is_none(x[1]),
            "email": x[2],
            "username": is_none(x[3]),
            "isAnonymous": bool(x[4]),
            "name": is_none(x[5]),
            "followers": followers,
            "following": following,
            "subscriptions": subscriptions
        }
        array_entitys.append(entity)
    return array_entitys


def list_posts(related, since, limit, order, entity_name, var):
    cur = mysql.connection.cursor()
    if entity_name == "thread":
        query = '''SELECT * FROM Post WHERE thread = '%s' '''
    if entity_name == "forum":
        query = '''SELECT * FROM Post WHERE forum = '%s' '''
    if entity_name == "user":
        query = '''SELECT * FROM Post WHERE user = '%s' '''
    query_params = (var,)
    if since:
        query += "AND date >= '%s' "
        query_params += (since,)
    if order:
        query += "ORDER BY date " + order + " "
    else:
        query += "ORDER BY date DESC "
    if limit:
        query += "LIMIT %s "
        query_params += (int(limit),)
    cur.execute(query % query_params)
    array_entitys = []
    for x in cur.fetchall():
        entity = {
            "id": x[0],
            "forum": x[1],
            "thread": x[2],
            "user": x[3],
            "message": x[4],
            "date": str(x[5]),
            "likes": x[6],
            "dislikes": x[7],
            "points": x[8],
            "parent": x[9],
            "isHighlighted": bool(x[10]),
            "isApproved": bool(x[11]),
            "isEdited": bool(x[12]),
            "isSpam": bool(x[13]),
            "isDeleted": bool(x[14])
        }
        array_entitys.append(entity)
    for i in array_entitys:
        if "forum" in related:
            forum = get_forum_entity([], i["forum"])
            i.update({"forum": forum})
        if "user" in related:
            user = get_user_entity(i["user"])
            i.update({"user": user})
        if "thread" in related:
            thread = get_thread_entity([], i["thread"])
            i.update({"thread": thread})

    return array_entitys


def list_threads(related, since, limit, order, entity_name, var):
    cur = mysql.connection.cursor()
    if entity_name == "user":
        query = '''SELECT * FROM Thread WHERE user = '%s' '''
    if entity_name == "forum":
        query = '''SELECT * FROM Thread WHERE forum = '%s' '''
    query_params = (var,)
    if since:
        query += "AND date >= '%s' "
        query_params += (since,)
    if order:
        query += "ORDER BY date " + order + " "
    else:
        query += "ORDER BY date DESC "
    if limit:
        query += "LIMIT %s "
        query_params += (int(limit),)
    cur.execute(query % query_params)
    array_entitys = []
    for x in cur.fetchall():
        entity = {
            "id": x[0],
            "forum": x[1],
            "user": x[2],
            "title": x[3],
            "date": str(x[4]),
            "message": x[5],
            "slug": x[6],
            "isDeleted": bool(x[7]),
            "isClosed": bool(x[8]),
            "likes": x[9],
            "dislikes": x[10],
            "points": x[11],
            "posts": x[12]
        }
        array_entitys.append(entity)
    for i in array_entitys:
        if "forum" in related:
            forum = get_forum_entity([], i["forum"])
            i.update({"forum": forum})
        if "user" in related:
            user = get_user_entity(i["user"])
            i.update({"user": user})

    return array_entitys


def get_forum_entity(related, forum_short_name):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT id, name, short_name, user FROM Forum WHERE short_name = '%s' ''' % forum_short_name)
    forum = cur.fetchone()
    if not forum:
        return responses_codes[1]
    result = {
        "id": forum[0],
        "name": is_none(forum[1]),
        "short_name": is_none(forum[2]),
        "user": is_none(forum[3])
    }
    if "user" in related:
        user = get_user_entity(forum[3])
        result.update({"user": user})
    return result


def get_user_entity(user_email):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT id, about, email, username, isAnonymous, name FROM User WHERE email = '%s' ''' % user_email)
    user = cur.fetchone()
    if not user:
        return responses_codes[1]
    followers = get_followers(user[2])
    following = get_following(user[2])
    subscriptions = get_subscriptions(user[2])
    result = {
        "about": is_none(user[1]),
        "email": user[2],
        "followers": followers,
        "following": following,
        "id": user[0],
        "isAnonymous": bool(user[4]),
        "name": is_none(user[5]),
        "subscriptions": subscriptions,
        "username": is_none(user[3])
    }
    return result


def get_thread_entity(related, thread_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute('''SELECT date,dislikes,forum,isClosed,isDeleted,likes,message,points,posts,slug,title,user FROM Thread WHERE id = '%s' ''' % thread_id)
    except Exception:
        return responses_codes[1]
    thread = cur.fetchone()
    if not thread:
        return responses_codes[1]
    result = {
        "date": str(thread[0]),
        "dislikes": thread[1],
        "forum": is_none(thread[2]),
        "id": thread_id,
        "isClosed": bool(thread[3]),
        "isDeleted": bool(thread[4]),
        "likes": thread[5],
        "message": is_none(thread[6]),
        "points": thread[7],
        "posts": thread[8],
        "slug": is_none(thread[9]),
        "title": is_none(thread[10]),
        "user": is_none(thread[11])
    }
    if "user" in related:
        user = get_user_entity(thread[11])
        result.update({"user": user})
    if "forum" in related:
        forum = get_forum_entity([], thread[2])
        result.update({"forum": forum})
    if result["isDeleted"]:
        result["posts"] = 0
    return result


def get_post_entity(related, post_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT date,dislikes,forum,id,isApproved,isDeleted,isEdited,isHighlighted,isSpam,likes,message,parent,points,thread,user,path FROM Post WHERE id = '%s' ''' % post_id)
    post = cur.fetchone()
    if not post:
        return responses_codes[1]
    result = {
        "date": str(post[0]),
        "dislikes": post[1],
        "forum": is_none(post[2]),
        "id": post_id,
        "isApproved": bool(post[4]),
        "isDeleted": bool(post[5]),
        "isEdited": bool(post[6]),
        "isHighlighted": bool(post[7]),
        "isSpam": bool(post[8]),
        "likes": post[9],
        "message": post[10],
        "parent": post[11],
        "points": post[12],
        "thread": post[13],
        "user": post[14],#
        "path": post[15]#####
    }
    if "user" in related:
        user = get_user_entity(post[14])
        result.update({"user": user})
    if "forum" in related:
        forum = get_forum_entity([], post[2])
        result.update({"forum": forum})
    if "thread" in related:
        thread = get_thread_entity([], post[13])
        result.update({"thread": thread})
    return result


def get_followers(user_email):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT follower FROM Follow WHERE followee = '%s' ''' % user_email)
    followers = []
    for x in cur.fetchall():
        followers.append(x[0])
    return followers


def get_following(user_email):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT followee FROM Follow WHERE follower = '%s' ''' % user_email)
    following = []
    for x in cur.fetchall():
        following.append(x[0])
    return following


def get_subscriptions(user_email):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT thread FROM Subscribe WHERE user = '%s' ''' % user_email)
    subscriptions = []
    for x in cur.fetchall():
        subscriptions.append(x[0])
    return subscriptions
