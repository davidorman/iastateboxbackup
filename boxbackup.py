from boxsdk import Client, OAuth2
from boxsdk.exception import *
import base64
import hashlib
from Crypto.Cipher import AES
import os
import codecs

class AESDecrypt(object):
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        # iv is the first block
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CFB, iv)
        # important to discard the iv here
        enc = enc[AES.block_size:]
        # decrypt
        data = cipher.decrypt(enc)
        # decode as utf-8
        return data.decode('utf-8')

class BoxBackupException(Exception):
    """
    I'll make my own damn exception class
    """
    def __init__(self, message):
        self.message = message
    def __unicode__(self):
        return "Exception: " + self.message

# Since I am lazy and there's not a great way to handle OAuth bs
# from the command line, we make the user do some of the steps
# manually. This means they need to go to the auth url and
# paste the access code that they get at the end of that
# back in here.
def get_authenticated_client():
    """Returns an authenticated box client"""
    CLIENT_ID = None
    CLIENT_SECRET = None
    ACCESS_TOKEN = None
    # client and secret are in a config file 
    with open('auth.cfg', 'r') as auth_cfg:
        # 100% guaranteed unhackable
        aes = AESDecrypt(base64.b64decode(codecs.decode('o2WzqKAwLKEco24u', 'rot_13')).decode('utf-8'))
        CLIENT_ID = aes.decrypt(auth_cfg.readline().strip())
        CLIENT_SECRET = aes.decrypt(auth_cfg.readline().strip())
    oauth = OAuth2(CLIENT_ID, CLIENT_SECRET)
    auth_url, csrf_token = oauth.get_authorization_url("https://iastateboxbackup")
    
    # ask user to go to the url and authorize our app
    print("Please go to "+auth_url+" in your web browser.\nYou will be asked to"
            +" authorize this app. Once you have done so you will be redirected to"
            +" an invalid webpage. Go to the address bar in your browser and copy"
            +" the string of random letters and numbers after 'code=' this is your"
            +" access token. You will need to paste this token here within 30 seconds.")
    ACCESS_TOKEN = input("Please paste your acccess token here:")
    access_token, refresh_token = oauth.authenticate(ACCESS_TOKEN)
    client = Client(oauth)
    return client

def logout_client(client):
    """Should invalidate our session. To be called when done."""
    client.auth.revoke()
def main():
    # TODO
    client = get_authenticated_client()
    try:
        print("Username: "+client.user(user_id='me').get()['login'])
        # for now let's assume that we always backup to the same folder and just create a subfolder within it that is this backup
        root = client.folder(folder_id='0')
        backup_root = None
        # check if a folder called 'iastateboxbackup' exists yet
        # I have no idea in what order things are returned, but let's get many in case
        search_results = client.search(query="iastateboxbackup", limit=100,offset=0,result_type='folder')
        if not search_results:
            #no results create folder sometimes folders take a while to show up so we may have to deal with that
            try:
                backup_root = root.create_subfolder(name="iastateboxbackup")
            except BoxAPIException as e:
                if e.code == "item_name_in_use":
                    #name collision. Assume we can use it
                    backup_root = client.folder(folder_id=e.context_info['conflicts'][0]['id']).get()
                else:
                    print("Caught an exception we didn't expect.")
                    raise
        else:
            #folder found get id
            for i in search_results:
                    if i.name == "iastateboxbackup":
                        backup_root = client.folder(folder_id=i.id).get()
                        break
                    else:
                        continue
        # should have folder now
        # how about we actually check that
        if not backup_root:
            raise BoxBackupException("Failed to get a backup directory.")

        # either get directory we're backing up or assume it's cwd TODO decide which or both
        # interactive or specified at invocation time?

        # TODO: create subfolder in backup_root with unqiue name probably (folder we're backing up)-datestamp

        # TODO: recurse through tree backing up things to this folder
        # will need logic for recreating folder structure  (which will suck ass) probably recursion
        # could ignore and do flat folder, but that would be ruinous for people who understand and use heirachies in their heirachical filesystems (most sane people)
        # Also need logic to check file size against limit and log error and skip file if too large

        # Done backing up


    except BoxException as e:
        print("Caught a Box exception: "+e)
    # done
    logout_client(client)

if __name__ == "__main__":
    main()
