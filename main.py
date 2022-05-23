import vk_api
import time
import datetime
import sys
import traceback
import requests

PEER_ID = 2000000402
SLEEP = 0.5
COUNT = 200
OKAY = False
TOKEN = ''
GET = 0
POST = 1

collected = False
photos = 0
videos = 0
ids = []
important_ids = []
last_formed_request = ''
last_formed_response = ''
api_version = '5.122'

def logfile(string):
    global last_formed_response
    now = datetime.datetime.now()
    print("\n==================\n" + string + "\ntime: " + str(now) + "\n==================")
    nn = now.strftime("%d-%m-%Y_%H.%M")
    f = open(str(nn) + '.txt', 'w')
    f.write(str(string))
    print('waiting 2 sec\n')
    time.sleep(2)
    #exit()


def auth_handler():
    key = input("Enter authentication code: ")
    remember_device = True
    return key, remember_device

def reqs(link, gp): # gp0 is get, gp1 is post
    done = False
    while not done:
        try:
            if gp == GET:
                answer = requests.get(link)
            elif gp == POST:
                answer = requests.post(link)
            done = True
            return answer
        except:
            now = datetime.datetime.now()
            s = str(sys.exc_info()[0])
            print("ERROR:", s)
            print('time is ' + str(now))
            nn = now.strftime("%d-%m-%Y_%H.%M")
            f = open(str(nn) + '.txt', 'w')
            f.write(str(s))
            time.sleep(1)


def callMethod(method, args, arg_count, gp):
    global last_formed_request
    link = 'https://api.vk.com/method/' + str(method) + '?' + str(args)
    if arg_count > 0:
        link = link + '&'
    link = link + '&access_token=' + str(TOKEN) + '&v=' + str(api_version)
    last_formed_request = link
    answer = reqs(link, gp)
    return answer


def main():
    global collected
    global ids
    global important_ids
    global OKAY
    global photos
    global videos
    global last_formed_request
    global last_formed_response
    login, password = '', ''
    vk_session = vk_api.VkApi(login, password, auth_handler=auth_handler)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return

    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    count = 0
    count_important = 0
    done = 0
    offset = 0
    # ids = []
    # important_ids = []
    response = vk.messages.getHistory(offset=0, count=0, peer_id=PEER_ID)
    if response['count']:
        count = int(response['count'])
    else:
        print('error 1:')
        print(response)
        return
    response = vk.messages.getConversationsById(extended=0, peer_ids=PEER_ID)
    if response['items']:
        title = response['items'][0]['chat_settings']['title']
    else:
        print('error 1:')
        print(response)
        return

    part = count // 100
    parts = part
    percent = 1

    print('There are {0} messages in conversation "{1}"'.format(count, title))
    print('Collecting messages\' IDs per {0} by request sleeping {1} s between them:'.format(COUNT, SLEEP))
    print('\rCollecting IDs... 0% ', end="")
    lastresp = response

    if collected == False:
        while done < count:
            reqd = False
            ok = False
            while reqd == False:
                try:
                    response = vk.messages.getHistory(offset=offset, count=COUNT, peer_id=PEER_ID, extended=0, rev=1)
                    #response = callMethod('messages.getHistory', f'offset={offset}&count={COUNT}&peer_id={PEER_ID}&extended=0&rev=1', 1, POST)
                    reqd = True
                    ok = True
                    #print('ok = True, ', end="")
                    lastresp = response
                    last_formed_response = response
                except:
                    #print(f'lastresponse = {0}', last_formed_request)
                    #print('done = {0}, offset = {1}, peer_id = {2}'.format(done, offset, PEER_ID))
                    print('done = {0}, offset = {1}, peer_id = {2}'.format(done, offset, PEER_ID))
                    s = 'from collecting IDs:\n' + str(traceback.format_exc())
                    logfile(s)
                    #continue
                reqd = True
            time.sleep(SLEEP)
            offset = offset + COUNT
            if not ok:
                continue
            if response['items']:
                for msg in response['items']:
                    done = done + 1
                    if done > parts and percent < 100:
                        print('\rCollecting IDs... {0}% '.format(percent), end="")
                        parts = parts + part
                        percent = percent + 1
                    app = True
                    if msg['attachments']:
                        for attch in msg['attachments']:
                            if str(attch['type']) == 'photo':
                                photos = photos + 1
                                app = False
                                continue
                            if str(attch['type']) == 'video':
                                videos = videos + 1
                                app = False
                                continue
                    if app == True:
                        ids.append(msg['id'])
            else:
                print('not response["items"], continuing')
                continue
        print('\rCollecting IDs... 100%\nDone.')
        count = count - photos
        count = count - videos
        print('There are {0} messages with photos and {1} messages with videos, ignoring them.\nNow count is {2}\n'.format(photos, videos, count))

        response = vk.messages.getImportantMessages(offset=0, count=0)
        if response['messages']:
            count_important = int(response['messages']['count'])
        else:
            print('error 3:')
            print(response)
            return

        print('There are {0} important messages.'.format(count_important))
        print('Collecting IDs...', end="\r")
        part = count_important // 100
        parts = part
        percent = 1
        done = 0
        offset = 0
        while done < count_important:
            reqd = False
            while reqd == False:
                try:
                    response = vk.messages.getImportantMessages(offset=offset, count=200)
                    reqd = True
                except:
                    s = 'from collecting importants:\n' + str(traceback.format_exc())
                    logfile(s)
            time.sleep(SLEEP)
            if response['messages']:
                for msg in response['messages']['items']:
                    #print(str(msg['id']) + ': ' + str(msg['text']))
                    important_ids.append(msg['id'])
                    done = done + 1
                    if done > parts and percent < 100:
                        print('\rCollecting IDs... {0}% '.format(percent), end="")
                        parts = parts + part
                        percent = percent + 1
            else:
                #print('error 4:')
                #print(response)
                return
            offset = offset + 200
        print('\rCollecting IDs... 100%\nDone.\n')
        collected = True
    else: # if collected
        print('Messages IDs collected, importants collected.\n')


    print('Excluding importants from deletion queue...', end="\r")
    part = count // 100
    parts = part
    percent = 1
    done = 0
    found = 0
    found_ids = []
    for msg in ids:
        for imp in important_ids:
            if msg == imp:
                found = found + 1
                found_ids.append(msg)
        done = done + 1
        if done > parts and percent < 100:
            print('\rExcluding importants from deletion queue... {0}% '.format(percent), end="")
            parts = parts + part
            percent = percent + 1
    for msg in found_ids:
        ids.remove(msg)
    count = count - found
    print('\rExcluding importants from deletion queue... 100%\nDone.')
    print('Found and excluded {0} important messages from deletion queue.\n\n'.format(found))



    print('There are {0} messages in "{1}" conversation will be deleted\nARE YOU SURE? ("yes" to go): \n'.format(count, title), end="")
    key = 'yes' #input()
    print('sleeping 5 sec')
    time.sleep(5)
    print(key)
    if str(key) == 'yes':
        part = count // 100
        parts = part
        percent = 1
        done = 0
        every = 0
        message_ids = ''
        while done < count:
            message_ids = ''
            every = 0
            while every < 200 and done < count:
                message_ids = message_ids + str(ids[done]) + ','
                every = every + 1
                done = done + 1
                if done > parts and percent < 100:
                    print('\rWorking... {0}% '.format(percent), end="")
                    parts = parts + part
                    #print('parts: {0} / {1}'.format(parts, count))
                    percent = percent + 1
            message_ids = message_ids[0:-1]
            #print(message_ids)
            reqd = False
            while reqd == False:
                try:
                    response = vk.messages.delete(message_ids=message_ids)
                    reqd = True
                except:
                    s = 'from deleting:\n' + str(traceback.format_exc())
                    logfile(s)
            time.sleep(SLEEP)
            #print(response)

            #print('done: {0}, count: {1}'.format(done, count))
        print('\rWorking... 100%\nDone.')
        #print(message_ids)
        print('There were {0} messages deleted.'.format(done))
        OKAY = True
        return
    print('Okay')


if __name__ == '__main__':
    while OKAY == False:
        try:
            main()
        except:
            s = 'Exception from __main__: \n' + str(traceback.format_exc())
            logfile(s)

# haha
