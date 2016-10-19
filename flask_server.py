from flask import Flask, jsonify, request
from addons import mysql, responses_codes
from functions import get_user_entity, list_posts, get_forum_entity, list_threads, list_users, get_post_entity, get_thread_entity
import user_addons
import json
import re


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'fro'
app.config['MYSQL_DB'] = 'forum_database'
app.config['MYSQL_CHARSET'] = 'utf8'
mysql.init_app(app)


@app.route('/')
def users():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM user''')
    result = cur.fetchall()
    for res in result:
        return str(result)


@app.route('/db/api/clear/', methods=['POST'])
def clear():
    cur = mysql.connection.cursor()
    tables = ['User', 'Forum', 'Thread', 'Post', 'Follow', 'Subscribe']
    for table in tables:
        cur.execute('''TRUNCATE TABLE %s''' % table)
    return jsonify(responses_codes[0])


@app.route('/db/api/status/', methods=['GET'])
def status():
    cur = mysql.connection.cursor()
    tables = ['User', 'Thread', 'Forum', 'Post']
    result = []
    for table in tables:
        cur.execute('''SELECT COUNT(*) FROM %s''' % table)
        result.append(cur.fetchone())

    return jsonify({"code": 0,
    	"response":{ "user": result[0][0], "thread": result[1][0], "forum": result[2][0], "post": result[3][0]}})


@app.route('/db/api/user/create/', methods=['POST'])
def create_user():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        username = json_obj["username"]
        about = json_obj["about"]
        name = json_obj["name"]
        email = json_obj["email"]
        isanon = 0
        if username == "None" or username is None:
            username = ""
        if about == "None" or about is None:
            about = ""
        if name == "None" or name is None:
            name = ""
        if "isAnonymous" in json_obj:
            isanon = int(json_obj["isAnonymous"])
    except Exception:
        return json.dumps(responses_codes[2])

    try:
        cur.execute('''INSERT INTO User (username,about,name,email,isAnonymous) VALUES ('%s','%s','%s','%s','%s')''' % (
            username, about, name, email, isanon,))
        cur.execute('''SELECT id FROM User WHERE email='%s' ''' % email)
        id = cur.fetchone()
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "id": id[0],
            "name": name,
            "username": username,
            "about": about,
            "email": email,
            "isAnonymous": bool(isanon)
        }
    })


@app.route('/db/api/user/details/', methods=['GET'])
def detail_forum_user():
    user_email = request.args.get("user")
    if not user_email:
        return json.dumps(responses_codes[2])
    response = get_user_entity(user_email)

    if response in responses_codes:
        return json.dumps(response)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result)


@app.route('/db/api/user/follow/', methods=['POST'])
def follow_user():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        follower = json_obj["follower"]
        followee = json_obj["followee"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not follower or not followee:
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM User WHERE email='%s' ''' % follower)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM User WHERE email='%s' ''' % followee)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM Follow WHERE follower = '%s' AND followee = '%s' ''' % (follower, followee,))
    if cur.fetchone():
        return json.dumps(responses_codes[5])

    try:
        cur.execute('''INSERT INTO Follow (follower, followee) VALUES ('%s','%s')''' % (follower, followee,))
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": get_user_entity(follower)
    }, sort_keys=True)


@app.route('/db/api/user/listFollowers/', methods=['GET'])
def list_followers():
    return user_addons.list_follow("follower", "followee")


@app.route('/db/api/user/listFollowing/', methods=['GET'])
def list_following():
    return user_addons.list_follow("followee", "follower")


@app.route('/db/api/user/listPosts/', methods=['GET'])
def listPosts_forum_user():
    email = request.args.get("user")
    if email:
        entity = "user"
        var = email
    else:
        return json.dumps(responses_codes[2], sort_keys=True)
    related = request.args.getlist("related")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_posts(related, since, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


@app.route('/db/api/user/unfollow/', methods=['POST'])
def unfollow_user():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        follower = json_obj["follower"]
        followee = json_obj["followee"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not follower or not followee:
        return json.dumps(responses_codes[2])

    try:
        cur.execute('''DELETE FROM Follow WHERE follower = '%s' AND followee = '%s' ''' % (follower, followee,))
    except Exception:
        return json.dumps(responses_codes[1])

    return json.dumps({
        "code": 0,
        "response": get_user_entity(follower)
    }, sort_keys=True)


@app.route('/db/api/user/updateProfile/', methods=['POST'])
def user_updateProfile():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        about = json_obj["about"]
        email = json_obj["user"]
        name = json_obj["name"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not about or not email or not name:
        return json.dumps(responses_codes[2])
    try:
        cur.execute('''UPDATE User SET about='%s',name='%s' WHERE email = '%s' ''' % (about, name, email,))
    except Exception:
        return json.dumps(responses_codes[1])
    return json.dumps({
        "code": 0,
        "response": get_user_entity(email)
    }, sort_keys=True)


@app.route('/db/api/forum/create/', methods=['POST'])
def create_forum():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        name = json_obj["name"]
        short_name = json_obj["short_name"]
        user = json_obj["user"]
    except Exception:
        return json.dumps(responses_codes[2], sort_keys=True)
    try:
        cur.execute('''SELECT * FROM User WHERE email = '%s' ''' % user)
        check_user = cur.fetchone()
        if not check_user:
            return json.dumps(responses_codes[1], sort_keys=True)
    except Exception:
        return json.dumps(responses_codes[1], sort_keys=True)

    try:
        cur.execute('''INSERT INTO Forum (name,short_name,user) VALUES ('%s','%s','%s')''' % (name, short_name, user,))
        cur.execute('''SELECT id FROM Forum WHERE name='%s' ''' % name)
        id = cur.fetchone()
    except Exception:
        return json.dumps(responses_codes[5], sort_keys=True)

    return json.dumps({
        "code": 0,
        "response": {
            "id": id[0],
            "name": name,
            "short_name": short_name,
            "user": user
        }
    }, sort_keys=True)


@app.route('/db/api/forum/details/', methods=['GET'])
def detail_forum():
    related = request.args.getlist("related")
    forum_short_name = request.args.get("forum")
    if not forum_short_name:
        return json.dumps(responses_codes[2], sort_keys=True)
    response = get_forum_entity(related, forum_short_name)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/forum/listPosts/', methods=['GET'])
def listPosts_forum():
    forum_short_name = request.args.get("forum")
    if forum_short_name:
        entity = "forum"
        var = forum_short_name
    else:
        return json.dumps(responses_codes[2], sort_keys=True)
    related = request.args.getlist("related")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_posts(related, since, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


@app.route('/db/api/forum/listThreads/', methods=['GET'])
def listThreads_forum():
    forum_short_name = request.args.get("forum")
    if forum_short_name:
        entity = "forum"
        var = forum_short_name
    else:
        return json.dumps(responses_codes[2], sort_keys=True)
    related = request.args.getlist("related")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_threads(related, since, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


@app.route('/db/api/forum/listUsers/', methods=['GET'])
def listUsers_forum():
    forum_short_name = request.args.get("forum")
    if forum_short_name:
        entity = "forum"
        var = forum_short_name
    else:
        return json.dumps(responses_codes[2], sort_keys=True)
    since_id = request.args.get("since_id")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_users(since_id, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


@app.route('/db/api/post/create/', methods=['POST'])
def create_post():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        date = json_obj["date"]
        thread_id = json_obj["thread"]
        message = json_obj["message"]
        email = json_obj["user"]
        forum_short_name = json_obj["forum"]
    except Exception:
        return json.dumps(responses_codes[2])
    isDeleted = 0
    if "isDeleted" in json_obj:
        isDeleted = int(json_obj["isDeleted"])

    isSpam = 0
    if "isSpam" in json_obj:
        isSpam = int(json_obj["isSpam"])

    isEdited = 0
    if "isEdited" in json_obj:
        isEdited = int(json_obj["isEdited"])

    isHighlighted = 0
    if "isHighlighted" in json_obj:
        isHighlighted = int(json_obj["isHighlighted"])

    isApproved = 0
    if "isApproved" in json_obj:
        isApproved = int(json_obj["isApproved"])

    parent = None
    try:
        if "parent" in json_obj:
            parent = int(json_obj["parent"])
    except Exception:
        parent = None

    if parent is None:
        query = ''' INSERT INTO Post (date,thread,message,user,forum,isDeleted,isSpam,isEdited,isHighlighted,isApproved,parent) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',NULL) '''
        query_params = (date,thread_id,message,email,forum_short_name,isDeleted,isSpam,isEdited,isHighlighted,isApproved,)

    else:
        query = ''' INSERT INTO Post (date,thread,message,user,forum,isDeleted,isSpam,isEdited,isHighlighted,isApproved,parent) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s') '''
        query_params = (date,thread_id,message,email,forum_short_name,isDeleted,isSpam,isEdited,isHighlighted,isApproved,parent,)

    cur.execute(query % query_params)
    cur.execute('''SELECT id FROM Post WHERE forum='%s' AND thread='%s' AND user='%s' AND message='%s' ''' % (forum_short_name, thread_id, email, message))
    post_id = cur.fetchone()
    cur.execute('''UPDATE Thread SET posts = posts + 1 WHERE id = '%s' ''' % thread_id)
    if parent:
        cur.execute('''SELECT path FROM Post WHERE id = '%s' ''' % parent)
        path = cur.fetchone()[0]
        path += '.' + str(post_id[0])
        cur.execute('''UPDATE Post SET path = '%s' WHERE id = '%s' ''' % (path, post_id[0],))
    else:
        path = str(post_id[0])
        cur.execute('''UPDATE Post SET path = '%s' WHERE id = '%s' ''' % (path, post_id[0],))

    return json.dumps({
        "code": 0,
        "response": {
            "date": date,
            "forum": forum_short_name,
            "id": post_id[0],
            "isApproved": bool(isApproved),
            "isDeleted": bool(isDeleted),
            "isEdited": bool(isEdited),
            "isHighlighted": bool(isHighlighted),
            "isSpam": bool(isSpam),
            "message": message,
            "parent": parent,
            "thread": thread_id,
            "user": email
        }
    }, sort_keys=True)


@app.route('/db/api/post/details/', methods=['GET'])
def detail_post():
    related = request.args.getlist("related")
    post_id = int(request.args.get("post"))
    if not post_id:
        return json.dumps(responses_codes[2], sort_keys=True)
    response = get_post_entity(related, post_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/post/list/', methods=['GET'])
def list_post():
    forum_short_name = request.args.get("forum")
    thread_id = request.args.get("thread")
    if forum_short_name:
        entity = "forum"
        var = forum_short_name
    else:
        if thread_id:
            entity = "thread"
            var = thread_id
        else:
            return json.dumps(responses_codes[2], sort_keys=True)
    related = request.args.getlist("related")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_posts(related, since, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


@app.route('/db/api/post/remove/', methods=['POST'])
def remove_post():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        post_id = json_obj["post"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not post_id:
        return json.dumps(responses_codes[1])

    try:
        cur.execute('''UPDATE Post SET isDeleted=true WHERE id = '%s' ''' % post_id)
        cur.execute('''SELECT thread FROM Post WHERE id = '%s' ''' % post_id)
        thread_id = cur.fetchone()
        cur.execute('''UPDATE Thread SET posts = posts - 1 WHERE id = '%s' ''' % thread_id[0])
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "post": post_id
        }
    }, sort_keys=True)


@app.route('/db/api/post/restore/', methods=['POST'])
def restore_post():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        post_id = json_obj["post"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not post_id:
        return json.dumps(responses_codes[1])

    try:
        cur.execute('''UPDATE Post SET isDeleted=false WHERE id = '%s' ''' %  post_id)
        cur.execute('''SELECT thread FROM Post WHERE id = '%s' ''' % post_id)
        thread_id = cur.fetchone()
        cur.execute('''UPDATE Thread SET posts = posts + 1 WHERE id = '%s' ''' % thread_id[0])
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "post": post_id
        }
    }, sort_keys=True)


@app.route('/db/api/post/update/', methods=['POST'])
def update_post():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        post_id = json_obj["post"]
        message = json_obj["message"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not post_id or not message:
        return json.dumps(responses_codes[1])
    try:
        cur.execute('''SELECT message, isEdited FROM Post WHERE id = '%s' ''' % post_id)
        res = cur.fetchone()
        isEdited = int(res[1])
        if res[0] != message:
            isEdited = 1

        cur.execute('''UPDATE Post SET message='%s', isEdited='%s' WHERE id = '%s' ''' % (message, isEdited, post_id,))
    except Exception:
        return json.dumps(responses_codes[5])
    response = get_post_entity([], post_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/post/vote/', methods=['POST'])
def vote_post():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        post_id = json_obj["post"]
        vote = str(json_obj["vote"])
    except Exception:
        return json.dumps(responses_codes[2])
    if not post_id or not vote:
        return json.dumps(responses_codes[1])
    if vote not in {'1', '-1'}:
        return json.dumps(responses_codes[2])
    try:
        if vote == '1':
            cur.execute('''UPDATE Post SET points = points + 1, likes = likes + 1 WHERE id = '%s' ''' % post_id)
        else:
            cur.execute('''UPDATE Post SET points = points - 1, dislikes = dislikes + 1 WHERE id = '%s' ''' % post_id)
    except Exception:
        return json.dumps(responses_codes[5])
    response = get_post_entity([], post_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/thread/open/', methods=['POST'])
def open_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread_id:
        return json.dumps(responses_codes[2])
    try:
        cur.execute('''UPDATE Thread SET isClosed=false WHERE id = '%s' ''' % (thread_id,))
    except Exception:
        return json.dumps(responses_codes[1])
    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread_id
        }
    })


@app.route('/db/api/thread/close/', methods=['POST'])
def close_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread_id:
        return json.dumps(responses_codes[2])
    try:
        cur.execute('''UPDATE Thread SET isClosed=true WHERE id = '%s' ''' % (thread_id,))
    except Exception:
        return json.dumps(responses_codes[1])
    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread_id
        }
    })

@app.route('/db/api/thread/create/', methods=['POST'])
def create_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        forum_short_name = json_obj["forum"]
        title = json_obj["title"]
        isClosed = int(json_obj["isClosed"])
        email = json_obj["user"]
        date = json_obj["date"]
        message = json_obj["message"]
        slug = json_obj["slug"]
    except Exception:
        return json.dumps(responses_codes[2])
    isDeleted = 0
    if "isDeleted" in json_obj:
        isDeleted = int(json_obj["isDeleted"])

    query = ''' INSERT INTO Thread (forum,title,isClosed,user,date,message,slug,isDeleted) VALUES ('%s','%s','%s','%s','%s','%s','%s','%s') '''
    try:
        cur.execute(query % (forum_short_name, title, isClosed, email, date, message, slug, isDeleted,))
        cur.execute('''SELECT id FROM Thread WHERE forum='%s' AND title='%s' AND user='%s' AND slug='%s' ''' % (
            forum_short_name, title, email, slug,))
        id = cur.fetchone()
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "date": date,
            "forum": forum_short_name,
            "id": id[0],
            "isClosed": bool(isClosed),
            "isDeleted": bool(isDeleted),
            "message": message,
            "slug": slug,
            "title": title,
            "user": email,
        }
    }, sort_keys=True)


@app.route('/db/api/thread/remove/', methods=['POST'])
def remove_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread_id:
        return json.dumps(responses_codes[1])

    try:
        cur.execute('''UPDATE Thread SET isDeleted=true WHERE id = '%s' ''' % thread_id)
        cur.execute('''UPDATE Post SET isDeleted=true WHERE thread = '%s' ''' % thread_id)
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread_id
        }
    }, sort_keys=True)


@app.route('/db/api/thread/restore/', methods=['POST'])
def restore_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread_id:
        return json.dumps(responses_codes[1])

    try:
        cur.execute('''UPDATE Thread SET isDeleted=false WHERE id = '%s' ''' % thread_id)
        cur.execute('''UPDATE Post SET isDeleted=false WHERE thread = '%s' ''' % thread_id)
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread_id
        }
    }, sort_keys=True)


@app.route('/db/api/thread/details/', methods=['GET'])
def detail_thread():
    related = request.args.getlist("related")
    thread_id = int(request.args.get("thread"))
    if not thread_id:
        return json.dumps(responses_codes[2], sort_keys=True)
    for x in related:
        if x not in ["forum", "user"]:
            return json.dumps(responses_codes[3], sort_keys=True)

    response = get_thread_entity(related, thread_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/thread/list/', methods=['GET'])
def list_thread():
    forum_short_name = request.args.get("forum")
    user_email = request.args.get("user")
    if forum_short_name:
        entity = "forum"
        var = forum_short_name
    else:
        if user_email:
            entity = "user"
            var = user_email
        else:
            return json.dumps(responses_codes[2], sort_keys=True)
    related = request.args.getlist("related")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")
    results = {
        "code": 0,
        "response": list_threads(related, since, limit, order, entity, var)
    }
    return json.dumps(results, sort_keys=True)


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


@app.route('/db/api/thread/listPosts/', methods=['GET'])
def listPosts_thread():
    tree_posts_list = []
    cur = mysql.connection.cursor()

    thread_id = request.args.get("thread")
    if not thread_id:
        return json.dumps(responses_codes[2], sort_keys=True)
    sort = request.args.get("sort")
    since = request.args.get("since")
    limit = request.args.get("limit")
    order = request.args.get("order")

    if sort is None or sort == 'flat':
        results = {
            "code": 0,
            "response": list_posts([], since, limit, order, "thread", thread_id)
        }
        return json.dumps(results, sort_keys=True)

    if sort not in ['flat', 'tree', 'parent_tree']:
        return json.dumps(responses_codes[2], sort_keys=True)

    query = '''SELECT path FROM Post WHERE thread = '%s' '''
    query_params = (thread_id,)
    if since:
        query += "AND date >= '%s' "
        query_params += (since,)

    cur.execute(query % query_params)
    for x in cur.fetchall():
        tree_posts_list.append(x[0])

    tree_posts_list = natural_sort(tree_posts_list)

    if order is None or order == 'desc':
        tree_posts_list = sorted(tree_posts_list, key=lambda k: int(k.split('.')[0]), reverse=True)

    if limit and int(limit) <= len(tree_posts_list):
        n = int(limit)
    else:
        n = len(tree_posts_list)

    x = 0
    result_set = []
    if sort == 'tree':
        while x < n:
            split_list = tree_posts_list[x].split('.')
            result_set.append(get_post_entity([], int(split_list[len(split_list)-1])))
            x+=1
    else:
        i = 0
        prev_firs_id = tree_posts_list[0].split('.')[0]
        while x < n and i < len(tree_posts_list):
            split_list = tree_posts_list[i].split('.')
            if split_list[0] != prev_firs_id:
                x += 1
            if x < n:
                result_set.append(get_post_entity([], int(split_list[len(split_list)-1])))
            prev_firs_id = tree_posts_list[i].split('.')[0]
            i+=1

    results = {
        "code": 0,
        "response": result_set
    }
    return json.dumps(results, sort_keys=True)



@app.route('/db/api/thread/subscribe/', methods=['POST'])
def subscribe_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread = json_obj["thread"]
        email = json_obj["user"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread or not email:
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT title FROM Thread WHERE id='%s' ''' % thread)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM User WHERE email='%s' ''' % email)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM Subscribe WHERE user = '%s' AND thread = '%s' ''' % (email, thread,))
    if cur.fetchone():
        return json.dumps(responses_codes[5])

    try:
        cur.execute('''INSERT INTO Subscribe (user, thread) VALUES ('%s','%s')''' % (email, thread,))
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread,
            "user": email
        }
    }, sort_keys=True)


@app.route('/db/api/thread/unsubscribe/', methods=['POST'])
def unsubscribe_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread = json_obj["thread"]
        email = json_obj["user"]
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread or not email:
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT title FROM Thread WHERE id='%s' ''' % thread)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM User WHERE email='%s' ''' % email)
    if not cur.fetchone():
        return json.dumps(responses_codes[1])
    cur.execute('''SELECT id FROM Subscribe WHERE user = '%s' AND thread = '%s' ''' % (email, thread,))
    if not cur.fetchone():
        return json.dumps(responses_codes[5])

    try:
        cur.execute('''DELETE FROM Subscribe WHERE user='%s' AND thread='%s' ''' % (email, thread,))
    except Exception:
        return json.dumps(responses_codes[5])

    return json.dumps({
        "code": 0,
        "response": {
            "thread": thread,
            "user": email
        }
    }, sort_keys=True)


@app.route('/db/api/thread/update/', methods=['POST'])
def update_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
        message = json_obj["message"]
        slug = json_obj["slug"]
    except Exception:
        return json.dumps(responses_codes[2])

    if not thread_id or not message or not slug:
        return json.dumps(responses_codes[1])

    try:
        cur.execute('''UPDATE Thread SET message='%s', slug='%s' WHERE id = '%s' ''' % (message, slug, thread_id,))
    except Exception:
        return json.dumps(responses_codes[5])
    response = get_thread_entity([], thread_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


@app.route('/db/api/thread/vote/', methods=['POST'])
def vote_thread():
    cur = mysql.connection.cursor()
    try:
        json_obj = json.loads(json.dumps(request.json))
        thread_id = json_obj["thread"]
        vote = str(json_obj["vote"])
    except Exception:
        return json.dumps(responses_codes[2])
    if not thread_id or not vote:
        return json.dumps(responses_codes[1])
    if vote not in {'1', '-1'}:
        return json.dumps(responses_codes[2])
    try:
        if vote == '1':
            cur.execute('''UPDATE Thread SET points = points + 1, likes = likes + 1 WHERE id = '%s' ''' % thread_id)
        else:
            cur.execute('''UPDATE Thread SET points = points - 1, dislikes = dislikes + 1 WHERE id = '%s' ''' % thread_id)
    except Exception:
        return json.dumps(responses_codes[5])
    response = get_thread_entity([], thread_id)
    if response in responses_codes:
        return json.dumps(response, sort_keys=True)
    result = {
        "code": 0,
        "response": response
    }
    return json.dumps(result, sort_keys=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int('7777'), debug=True)
