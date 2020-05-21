from flask import url_for, session, request

#Google Auth
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/contacts']

class gAuth():

    def generate_url():
        # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

        # The URI created here must exactly match one of the authorized redirect URIs
        # for the OAuth 2.0 client, which you configured in the API Console. If this
        # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
        # error.
        flow.redirect_uri = url_for('oauth2callback', _external=True)

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true')

        return authorization_url, state

    def authorize_tokens(state):
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.
        state = session['state']

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
        flow.redirect_uri = url_for('oauth2callback', _external=True)

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials in the session.
        # ACTION ITEM: In a production app, you likely want to save these
        #              credentials in a persistent database instead.
        credentials = flow.credentials

        return credentials
