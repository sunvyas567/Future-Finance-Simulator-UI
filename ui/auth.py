#import streamlit as st
#import streamlit_authenticator as stauth
#from services.api_client import get_users_for_auth

#_authenticator = None  # module-level singleton


#def get_authenticator():
#    global _authenticator

#    if _authenticator is None:
#        users_config = get_users_for_auth()
#        for u, data in users_config["credentials"]["usernames"].items():
#            pwd = data.get("password")
#            #print(f"[AUTH DEBUG NEW] {u} password =", pwd, type(pwd))

#        if not isinstance(pwd, str):
#            raise RuntimeError(
#                f"❌ User '{u}' has invalid password field: {pwd}"
#            )

#        _authenticator = stauth.Authenticate(
#            users_config["credentials"],
#            users_config["cookie"]["name"],
#            users_config["cookie"]["key"],
#            users_config["cookie"]["expiry_days"],
#        )

#    return _authenticator

import streamlit_authenticator as stauth
from services.api_client import get_users_for_auth

#_authenticator = None


def get_authenticator():
    #global _authenticator

   # if _authenticator is None:

        users_config = get_users_for_auth()

      #  _authenticator = stauth.Authenticate(
        return stauth.Authenticate(
            users_config["credentials"],
            users_config["cookie"]["name"],
            users_config["cookie"]["key"],
            users_config["cookie"]["expiry_days"],
        )

    #return _authenticator
