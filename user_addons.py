from flask import request
from addons import mysql, responses_codes
from functions import get_following, get_followers, get_subscriptions
import json


def list_follow(arg1, arg2):
    cur = mysql.connection.cursor()
    user_email = request.args.get("user")
    if not user_email:
        return json.dumps(responses_codes[2])
    since = request.args.get("since_id")
    limit = request.args.get("limit")
    order = request.args.get("order")

    if arg1 == "follower" and arg2 == "followee" :
        query = '''SELECT about, email, u.id, isAnonymous, name, username FROM Follow AS f INNER JOIN User AS u ON email = follower WHERE followee = '%s' '''

    if arg1 == "followee" and arg2 == "follower" :
        query = '''SELECT about, email, u.id, isAnonymous, name, username FROM Follow AS f INNER JOIN User AS u ON email = followee WHERE follower = '%s' '''
    query_params = (user_email,)
    if since:
        query += "AND u.id >= '%s' "
        query_params += (since,)
    if order:
        query += "ORDER BY name " + order + " "
    else:
        query += "ORDER BY name DESC "
    if limit:
        query += "LIMIT %s "
        query_params += (int(limit),)
    cur.execute(query % query_params)
    array_entitys = []
    for x in cur.fetchall():
        entity = {
            "about": x[0],
            "email": x[1],
            "followers": [],
            "following": [],
            "id": x[2],
            "isAnonymous": bool(x[3]),
            "name": x[4],
            "subscriptions": [],
            "username": x[5]
        }
        array_entitys.append(entity)

    for x in array_entitys:
        followers = get_followers(x["email"])
        following = get_following(x["email"])
        subscriptions = get_subscriptions(x["email"])
        x.update({"followers": followers, "following": following, "subscriptions": subscriptions})
    results = {
        "code": 0,
        "response": array_entitys
    }
    return json.dumps(results, sort_keys=True)
