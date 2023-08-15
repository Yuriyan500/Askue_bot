import json


def get_users_id():

    user_list = []

    with open("middlewares/accounts.json", "r") as json_file:
        data_users = json.load(json_file)

        for item in data_users:
            user_list.extend([value for key, value in item.items() if key == 'user_id'])

    return user_list


def get_chat_id():

    chat_list = []

    with open("middlewares/accounts.json", "r") as json_file:
        data_users = json.load(json_file)

        for item in data_users:
            chat_list.extend([value for key, value in item.items() if key == 'chat_id'])

    return chat_list


def get_usernames():

    usernames_list = []

    with open("middlewares/accounts.json", "r") as json_file:
        data_users = json.load(json_file)

        for item in data_users:
            usernames_list.extend([value for key, value in item.items() if key == 'username'])

    return usernames_list
