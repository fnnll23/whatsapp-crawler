# -*- coding: utf-8 -*-

#Flask
import flask
from flask import Flask, render_template, request, send_file, redirect, url_for, session
from werkzeug.utils import secure_filename

import requests
import json
import pandas as pd
from time import sleep

#Google Auth
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data

#Modules
from utils.modules.user_check import userCheck
from utils.modules.wpc import WhatsappCrawler
from utils.modules.google_auth import gAuth




API_SERVICE_NAME = 'contacts'
API_VERSION = 'v2'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)

#config
import os
app.config.from_object(os.environ.get("APP_SETTINGS"))


@app.route('/', methods=['GET', 'POST'])
def index():
    step = '1'
    if request.args.get('step'):
        step = request.args.get('step')

    return render_template('base.html', step=step)

@app.route('/download')
def download_example():
    path = 'uploads/example.csv'
    return send_file(path, as_attachment=True)

"""PASO 1: Autorización"""
@app.route('/authorize')
def authorize():

    authorization_url, state = gAuth.generate_url()
    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():

    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    credentials = gAuth.authorize_tokens(state)
    session['credentials'] = credentials_to_dict(credentials)
    session['step'] = '2'

    return redirect(url_for('index', step=session['step']))



"""PASO 2: Carga de CSV"""
@app.route('/data', methods=['GET', 'POST'])
def data():
    try:
        session['step'] == '2'
    except:
        #flash("No se autorizo")
        return redirect(url_for('index', step='error'))
    else:
        if request.method =='POST':
            file = request.files['file']
            if file:
                filename = secure_filename(file.filename)

                if filename[-4:] == '.csv':
                    df = pd.read_csv(file)
                    print(df[df.columns[0]])

                    if len(df.columns) == 2 and df.columns[0].lower() == 'contacts' and df.columns[1].lower() == 'messages':
                        flask.session['csv'] = df.to_dict('dict')
                        flask.session['step'] = '2.0'
                        # a = json.dumps(flask.session['csv'], indent=2, sort_keys=True)
                        # file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
                        return redirect(url_for('index', step=flask.session['step']))
                    else:
                        #flash("El archivo subido tiene otro formato")
                        return redirect(url_for('index'), step='error')
                else:
                    #flash("El archivo subido no es del tipo csv")
                    return redirect(url_for('index'), step='error')        

@app.route('/creating_contacts', methods=['GET', 'POST'])
def execute_batch_request(): 
    # Feed that holds the batch request entries.
    request_feed = gdata.contacts.data.ContactsFeed()

    # Create a ContactEntry for the retrieve request.
    #retrieve_contact = gdata.contacts.data.ContactEntry()
    #retrieve_contact.id = atom.data.Id(
    #    text='https://www.google.com/m8/feeds/contacts/default/private/full/retrieveContactId')

    # Create a ContactEntry for the create request.
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
    token = gdata.gauth.OAuth2Token(
        client_id=flask.session['credentials']['client_id'],
        client_secret=flask.session['credentials']['client_secret'],
        scope='https://www.googleapis.com/auth/contacts',
        user_agent='app.testing',
        access_token=flask.session['credentials']['token'],
        refresh_token=flask.session['credentials']['refresh_token'])
    
    gd_client = gdata.contacts.client.ContactsClient()
    gd_client = token.authorize(gd_client)
    
    #Uso el grupo My Contacts para que se agregue a whatsapp:
    contact_group_url = 'http://www.google.com/m8/feeds/groups/userEmail/base/6'
    group = gd_client.GetGroup(contact_group_url)
    group_atom_id_mc = group.id.text

    #Ademas creo un grupo custom para referenciar los contactos agregados:
    new_group = gdata.contacts.data.GroupEntry(title=atom.data.Title(text='Nice people'))
    created_group = gd_client.CreateGroup(new_group)
    group_atom_id_np = created_group.id.text



    df = pd.DataFrame(flask.session['csv'])
    df['status'] = [None] * len(df)


    for i in range(len(df)):
        try:
            numb = int(df.iloc[i, 0])
            if numb < 10000:
                df.iloc[i, 2] = 'error de formato'
                continue
            else:
                df.iloc[i, 2] = 'ok'
        except:
            df.iloc[i, 2] = 'error de formato'
            continue

        #Create new contact:
        create_contact = gdata.contacts.data.ContactEntry()
        create_contact.name = gdata.data.Name(given_name=gdata.data.GivenName(text= 'WhatsappCrawler_' + str(i)))
        create_contact.phone_number.append(gdata.data.PhoneNumber(text=str(df.iloc[i, 0]), rel=gdata.data.WORK_REL, primary='true'))
        #Agrego contacto a lista My Contacts
        create_contact.group_membership_info.append(gdata.contacts.data.GroupMembershipInfo(href=group_atom_id_mc))
        #Agrego contacto a lista provisoria
        create_contact.group_membership_info.append(gdata.contacts.data.GroupMembershipInfo(href=group_atom_id_np))
        request_feed.AddInsert(entry=create_contact, batch_id_string='create')


    # Retrieve the ContactEntry to update.
    #update_contact = gd_client.GetContact('https://www.google.com/m8/feeds/contacts/default/full/updateContactId')
    #update_contact.name.full_name = 'New Name'
    #update_contact.name.given_name = 'New'
    #update_contact.name.family_name = 'Name'

    # Retrieve the ContactEntry to delete.
    #delete_contact = gd_client.GetContact('https://www.google.com/m8/feeds/contacts/default/full/deleteContactId')

    # Insert the entries to the batch feed.
    #request_feed.AddQuery(entry=retrieve_contact, batch_id_string='retrieve')
    #request_feed.AddInsert(entry=create_contact, batch_id_string='create')
    #request_feed.AddUpdate(entry=update_contact, batch_id_string='update')
    #request_feed.AddDelete(entry=delete_contact, batch_id_string='delete')

    # submit the batch request to the server.
    response_feed = gd_client.ExecuteBatch(request_feed,
        'https://www.google.com/m8/feeds/contacts/default/full/batch')

    for entry in response_feed.entry:
        print('%s: %s (%s)' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason))

    flask.session['csv'] = df.to_dict('dict')
    flask.session['credentials'] = credentials_to_dict(credentials)
    flask.session['group_atom_id_np'] = group_atom_id_np
    flask.session['step'] = '3'

    sleep(20)
    session['step'] = '3'
    return redirect(url_for('index', step=session['step']))

"""PASO 3: Carga de contactos"""
# @app.route('/creating_contacts', methods=['GET', 'POST'])
# def creating_contacts():
#     flask.session['step'] = '2.1'
#     return redirect(url_for('index', step=session['step']))
 


# @app.route('/esperando', methods=['GET', 'POST'])
# def execute_batch_request(): 

                
# @app.route('/delete_contacts')
# def delete_contacts():
#     # Load credentials from the session. GD_CLIENT TAERLO COMO UN MODULO APARTE YA QUE SE REPITE EN VARIAS RUTAS
#     credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
#     token = gdata.gauth.OAuth2Token(
#         client_id=flask.session['credentials']['client_id'],
#         client_secret=flask.session['credentials']['client_secret'],
#         scope='https://www.googleapis.com/auth/contacts',
#         user_agent='app.testing',
#         access_token=flask.session['credentials']['token'],
#         refresh_token=flask.session['credentials']['refresh_token'])
    
#     gd_client = gdata.contacts.client.ContactsClient()
#     gd_client = token.authorize(gd_client)

#     #Busco la variable guardada en flask.session para nice people
#     group_atom_id_np = flask.session.get('group_atom_id_np', None)

#     #feed = gd_client.GetGroups()

#     #group = gd_client.GetGroup('https://www.google.com/m8/feeds/groups/userEmail/base/' + 'group_atom_id_np')
#     group = group_atom_id_np
#     query = gdata.contacts.client.ContactsQuery()
#     query.group = group
#     feed = gd_client.GetContacts(q = query)

#     contact_url = feed.entry[0].id.text
#     contact = gd_client.GetContact(contact_url)
#     gd_client.Delete(contact)
#     # for contact in feed.entry:
#     #     print (contact.name.full_name)
#     #     print ('Updated on %s' % contact.updated.text)

#     #     # Retrieving the contact is required in order to get the Etag.
#     #     #contact_url = 'https://www.google.com/m8/feeds/contacts/userEmail/full/{contactId}'
#     #     #contact = gd_client.GetContact(contact_url)

#     #     # try:
#     #     #     gd_client.Delete(contact)
#     #     # except gdata.client.RequestError, e:
#     #     #     if e.status == 412:
#     #     #     # Etags mismatch: handle the exception.
#     #     #     pass

#     return str('BORRADO')

"""PASO 5: Borro contactos"""

@app.route('/delete_contacts', methods=['GET', 'POST'])
def execute_batch_request_delete():
    credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
    token = gdata.gauth.OAuth2Token(
        client_id=flask.session['credentials']['client_id'],
        client_secret=flask.session['credentials']['client_secret'],
        scope='https://www.googleapis.com/auth/contacts',
        user_agent='app.testing',
        access_token=flask.session['credentials']['token'],
        refresh_token=flask.session['credentials']['refresh_token'])
    
    gd_client = gdata.contacts.client.ContactsClient()
    gd_client = token.authorize(gd_client)

    #Busco la variable guardada en flask.session para nice people
    group_atom_id_np = flask.session.get('group_atom_id_np', None)

    #feed = gd_client.GetGroups()

    #group = gd_client.GetGroup('https://www.google.com/m8/feeds/groups/userEmail/base/' + 'group_atom_id_np')
    group = group_atom_id_np
    query = gdata.contacts.client.ContactsQuery()
    query.group = group
    feed = gd_client.GetContacts(q = query)

    # # Feed that holds the batch request entries.
    request_feed = gdata.contacts.data.ContactsFeed()

    for i in range(len(feed.entry)):
        contact_url = feed.entry[i].id.text
        delete_contact = gd_client.GetContact(str(contact_url))
        request_feed.AddDelete(entry=delete_contact, batch_id_string='delete')
    """Hasta aca viene de delete contacts. Lo siguiente es de batch"""

    # # Create a ContactEntry for the retrieve request.
    # retrieve_contact = gdata.contacts.data.ContactEntry()
    # retrieve_contact.id = atom.data.Id(
    #     text='https://www.google.com/m8/feeds/contacts/default/private/full/retrieveContactId')


    # Retrieve the ContactEntry to delete.
    #delete_contact = gd_client.GetContact(str(contact_url))

    # Insert the entries to the batch feed.
    #request_feed.AddDelete(entry=delete_contact, batch_id_string='delete')

    # submit the batch request to the server.
    response_feed = gd_client.ExecuteBatch(request_feed,
        'https://www.google.com/m8/feeds/contacts/default/full/batch')

    for entry in response_feed.entry:
        print('%s: %s (%s)' % (entry.batch_id.text, entry.batch_status.code, entry.batch_status.reason))

    return redirect(url_for('index'))


"""FUNCIONES AUXILIARES: IMPORTAR COMO MODULOS"""
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


"""ESTO ME LO QUEDO"""
@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.')
    else:
        return('An error occurred.')

@app.route('/clear')
def clear_credentials():
    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>')


if __name__ == '__main__':
    app.run()


# TODO
# pasar al archivo config: rutas de archivos (client_secret.json, example, secret_key, extensiones_permitidas)

