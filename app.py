from flask import Flask, render_template, request, redirect, url_for, session

import csv
import os
from datetime import datetime, timedelta
from Classes import *
import threading 
from datetime import timedelta, datetime

app = Flask(__name__, static_folder='static')
app.secret_key = 'xdd'
app.permanent_session_lifetime = timedelta(minutes=20)

@app.before_request
def make_session_permanent():
    session.permanent = True


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        with open('data/userdata.csv') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['login'] == login and row['password'] == password:
                    print(row)
                    session['login'] = login
                    session['userid'] = row['id']
                    return redirect(url_for('show_workspace'))
            return render_template('login.html', status= 'Invalid credentials.')
     
    return render_template('login.html', status= 'Waiting for login...')

@app.route('/workspace', methods=['POST', 'GET'])
def show_workspace():
    login = session.get('login', None)

    if not login:
        return (
            'This page cannot be used without logging in first. '
            '<a href="/login">Login</a>'
        )

    user_data = None
    with open('data/userdata.csv', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['login'] == login:
                user_data = row
                break

    user_type = user_data['type']  
    if user_type == 'Tenant':
        return tenant_mode(user_data)
    elif user_type == 'Landlord':
        return landlord_mode(user_data)
    else: 
        return 'Incorrect user type.'
    

def tenant_mode(user_data, methods=['GET', 'POST']):
    user = Tenant(user_data['name'], user_data['surname'])
    user.leases.clear()
    with open('data/leasedata.csv') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['tenantid'] == session['userid']:
                propid = row['id']
                length = int(row['length'])
                ownerid = row['ownerid']
                with open('data/userdata.csv') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row['id'] == ownerid:
                            landlord = Landlord(row['name'], row['surname'])
                            break
                with open('data/propertydata.csv') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if row['id'] == propid:
                            if row['ownerid'] == ownerid:
                                area = float(row['area'])
                                address = row['address']
                                housing = Housing(area, address)
                                landlord._property.append(housing)
                            else:
                                raise Exception('Incorrect owner in leasedata/propertydata')

                user.leases.append(Lease(landlord, user, housing, length))
    
    item_id = request.args.get('item_address', type=str)
    end_time = 'Waiting for signing...'
    if item_id:
        selected_item = [i for i in user.leases if i.subject.address == item_id][0]
        session['sel_id'] = selected_item.subject.address

    if request.method == 'POST':
        if session['sel_id']:
            item_id = request.form.get('item_id', type=str)
            selected_item = [i for i in user.leases if i.subject.address == item_id][0]
            leasing_thread = threading.Thread(target=selected_item.sign, args=())
            leasing_thread.daemon = True
            leasing_thread.start()
            end_time = datetime.now() + timedelta(seconds=selected_item.length_months + 5)
            end_timestamp = int(end_time.timestamp() * 1000)
    
    return_kwargs = { 
            'name':user_data['name'],
            'surname':user_data['surname'],
            'type':user_data['type'],
            'id':user_data['id'],
            'items': user.leases
            }

    if 'selected_item' in locals():
        return_kwargs.update({
            'selected_item': selected_item
        })
    if type(end_time) == datetime:
        return_kwargs.update({
            'end_time': end_timestamp
        })

    return render_template('workspace_tenant.html', **return_kwargs)


def landlord_mode(user_data):

    user = Landlord(user_data['name'], user_data['surname'])
    user._property.clear()
    with open('data/propertydata.csv') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['ownerid'] == session['userid']:
                area = float(row['area'])
                address = row['address']
                housing = Housing(area, address)
                user._property.append(housing)

    item_id = request.args.get('item_address', type=str)
    if item_id:
        selected_item = [i for i in user._property if i.address == item_id][0]
        session['sel_id'] = selected_item.address

    return_kwargs = { 
            'name':user_data['name'],
            'surname':user_data['surname'],
            'type':user_data['type'],
            'id':user_data['id'],
            'items': user._property
            }
    
    if 'selected_item' in locals():
        return_kwargs.update({
            'selected_item': selected_item
        })

    return render_template('workspace_landlord.html', **return_kwargs)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)