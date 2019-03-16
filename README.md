# Project: Linux Server Configuration

Install a Linux server and prepare it to host the web applications (Catalog item). securing the server from a number of attack vectors, install and configure a database server, and deploy one of the existing web applications onto it.

- **IP address:** 142.93.49.78
- **SSH port:** 2200
- **web application URL :** [catalog item](http://142.93.49.78)
- **Connect Using ssh:** ``` $ ssh -i ~/.ssh/id_rsa -p 2200 grader@142.93.49.78 ```



## Get your server:

1. create an account on [DigitalOcean](https://m.do.co/c/379434780044), then add a new project and new droplet.
![new project](images/new_project.png)
![new droplet](images/choose_ubunto.png)
choose ubunto

2. verify your mail, you will receive an email contain the default password to login using ssh.
```
$ ssh root@142.93.49.78 -p 22 
```
For security reasons, you will be required to change this Droplet’s root password when you login.

## Secure your server.

3. Update all currently installed packages.

	Run the following command:
	```
	$ sudo apt-get update
	$ sudo apt-get upgrade
	```

4. Change the SSH port from 22 to 2200. [source](https://www.godaddy.com/help/changing-the-ssh-port-for-your-linux-server-7306)

	- Connect to your server via SSH 

	- Switch to the root user

	- Run the following command : 
	```
	$ nano /etc/ssh/sshd_config 
	```

	- Locate the following line:  #Port 22

	- Remove # and change 22 to 2200.

	- Restart the sshd service by running the following command: 
	```
	$ service sshd restart 
	```

5. Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123).

	Run the following command

	``` $ sudo ufw status ``` show status of firewall and ufw managed rules.

	``` $ sudo ufw default deny incoming ``` To deny all incoming connections.

	``` $ sudo ufw default allow outgoing ``` To allow all outgoing connections. 

	``` $ sudo ufw allow 2200/tcp ``` To allow connection for ssh port 2200.

	``` $ sudo ufw allow www ``` To allow connection for  HTTP (port 80).

	``` $ sudo ufw allow 123/udp ``` To allow UDP traffic on port 123 in order to communicate with the NTP pool.

	``` $ sudo ufw enable ``` To enable the firewall.

	``` $ sudo ufw status ``` To check whether firewall is enable or not.

	expected results:

	![ufw status](images/ufw_status.png)

	Resource : [ufw community](https://help.ubuntu.com/community/UFW) , [NTP](https://www.digitalocean.com/community/tutorials/how-to-configure-ntp-for-use-in-the-ntp-pool-project-on-ubuntu-16-04)

## Give grader access.

6. Create a new user account named **grader**

	create user using the command: ``` $ sudo adduser grader ``` 

7. Give grader the permission to sudo.

	Create a file using the command : ``` $ sudo touch /etc/sudoers.d/grader ``` open it using ``` $ sudo nano /etc/sudoers.d/grader ```, add the text ``` grader ALL=(ALL) NOPASSWD:ALL ``` and save it.

	Verify:

	- switch to grader using ``` $ su - grader ```

	- run the command ``` sudo -l ```

	The output should look like this:

	![sudo -l ](images/grader-sudo-l.png)

8. Create an SSH key pair for grader using the ssh-keygen tool.

	- Switch to your local machine
	- Run ```ssh-keygen```
	- Enter file in which to save the key (/home/soumer/.ssh/id_rsa): 
	- Enter passphrase (empty for no passphrase): 
	- copy the contents of the file ~/.ssh/id_rsa.pub
	- Switch to  grader's virtual machine
	- Create a new directory called ~/.ssh using the command : ```$ mkdir .ssh```
	- Create the file ~/.ssh/authorized_keys using the command ```$ touch ~/.ssh/authorized_keys```, open it using ```$ nano ~/.ssh/authorized_keys```, past the content of the key and save it.
	- Change the permissions using ```$ chmod 700 .ssh``` and ```$ chmod 644 .ssh/authorized_keys```
	- Run the command ``` $ sudo nano /etc/ssh/sshd_config```
	- edit the line ```PasswordAuthentication yes ``` to become ```PasswordAuthentication no ```, so we only authenticate using key rsa.
	- restart the service ```$ sudo service ssh restart```
	- Switch to your local machine and run:```$ ssh -i ~/.ssh/id_rsa -p 2200 grader@142.93.49.78 ```


## Prepare to deploy your project.

9. Configure the local timezone to UTC. [source](https://askubuntu.com/questions/138423/how-do-i-change-my-timezone-to-utc-gmt)

	To switch to UTC, simply execute ```$ sudo dpkg-reconfigure tzdata```, scroll to the bottom of the Continents list and **select Etc or None of the above**; in the second list, **select UTC**. 

10. Install and configure Apache to serve a Python mod_wsgi application.

	- Run the following command: 
	```
	$ sudo apt-get update
	$ sudo apt-get install python3-pip apache2 libapache2-mod-wsgi-py3
	```
	- visit [http://your_server_ip](http://142.93.49.78) you should see the default page like in the picture bellow:

	![apache2 default page](images/Apache2_default.png) 

	- You then need to configure Apache to handle requests using the WSGI module. You’ll do this by editing the */etc/apache2/sites-enabled/000-default.conf* file. This file tells Apache how to respond to requests, where to find the files for a particular site and much more. You can read up on everything this file can do within the [Apache documentation.](http://httpd.apache.org/docs/current/configuring.html)

	For now, add the following line at the end of the ```<VirtualHost *:80>``` block, right before the closing ```</VirtualHost>``` line: ```WSGIScriptAlias / /var/www/html/myapp.wsgi```

	Finally, restart Apache with the ```$ sudo apache2ctl restart``` command.

	>You might get a warning saying "Could not reliably determine the server's fully qualified domain name". If you do, don't worry about it. Check out this [AskUbuntu thread](https://askubuntu.com/questions/256013/apache-error-could-not-reliably-determine-the-servers-fully-qualified-domain-n) for a discussion of the cause of this message.

	- Create the /var/www/html/myapp.wsgi file using the command ```$ sudo nano /var/www/html/myapp.wsgi```. Within this file, write the following application:
```python
	def application(environ, start_response):
	    status = '200 OK'
	    output = b'Hello Udacity!'

	    response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
	    start_response(status, response_headers)

	    return [output]

```

11. Install and configure PostgreSQL: 

	- Run the following command:
	```
	$ sudo apt-get update
	$ sudo apt-get install postgresql postgresql-contrib
	```

	- Switch over to the postgres account on your server by typing:
	```
	$ sudo -i -u postgres
	```
	You can now access a Postgres prompt immediately by typing:
	```
	$ psql
	```
	You will be logged in and able to interact with the database management system right away.

	Exit out of the PostgreSQL prompt by typing:
	```
	postgres=# \q
	```

	- Do Not Allow Remote Connections

	One simple way to remove a potential attack vector is to not allow remote connections to the database. This is the current default when installing PostgreSQL from the Ubuntu repositories.

	We can double check that no remote connections are allowed by looking in the host based authentication file:
	```
	$ sudo nano /etc/postgresql/10/main/pg_hba.conf
	```

	```
	local   all             postgres                                peer
	local   all             all                                     peer
	host    all             all             127.0.0.1/32            md5
	host    all             all             ::1/128                 md5
	```


	- Create a new database user named catalog that has limited permissions to your catalog application database.

	**Create a New User**

	If you are logged in as the postgres account, you can create a new user by typing:

	```postgres@server:~$  createuser --interactive```

	If, instead, you prefer to use sudo for each command without switching from your normal account, you can type:

	```$ sudo -u postgres createuser --interactive```

	The script will prompt you with some choices and, based on your responses, execute the correct Postgres commands to create a user to your specifications.
	![new postgres user](images/new_postgres_user.png)

	Give the catalog user a password by running 

	```
	$ sudo -u postgres psql
	postgres=#  \password catalog
	```

	**Create a New Database**

	If you are logged in as the postgres account, you would type something like:

    ``` createdb catalog```

	If, instead, you prefer to use sudo for each command without switching from your normal account, you would type:

    ```$ sudo -u postgres createdb catalog```

    **Open a Postgres Prompt with the New Role**

    To log in with ident based authentication, you'll need a Linux user with the same name as your Postgres role and database.

	If you don't have a matching Linux user available, you can create one with the adduser command. You will have to do this from an account with sudo privileges (not logged in as the postgres user):

	```$ sudo adduser catalog```

	Once you have the appropriate account available, you can switch over and connect to the database by typing:

	```$ sudo -u catalog psql ```



12. Install git.
	
	First, use the apt package management tools to update your local package index. With the update complete, you can download and install Git:

	```
	$ sudo apt update
    $ sudo apt install git
	```

	You can confirm that you have installed Git correctly by running the following command:

	```$ git --version ```

	Now that you have Git installed, you should configure it so that the generated commit messages will contain your correct information.

	This can be achieved by using the `git config` command. Specifically, we need to provide our name and email address because Git embeds this information into each commit we do. We can go ahead and add this information by typing:

	```
	$ git config --global user.name "Your Name"
	$ git config --global user.email "youremail@domain.com"
	```

	**Resource:**

	[How To Install and Use PostgreSQL on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-16-04)

	[How To Secure PostgreSQL on an Ubuntu VPS ](https://www.digitalocean.com/community/tutorials/how-to-secure-postgresql-on-an-ubuntu-vps)

	[How To Serve Django Applications with Apache and mod_wsgi on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-16-04)

	[How To Deploy a Flask Application on an Ubuntu VPS](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)

	[How To Install Git on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-install-git-on-ubuntu-18-04)

13. Clone and setup the Item Catalog project from the Github repository .

	- Move to the **/var/www** directory
	- Clone this repository by using the command: 
	```$ sudo git clone https://github.com/abderrahimsoumer/Linux-Server-Configuration.git Catalog```
	- Move to the *Catalog/Catalog* directory by using the command: 
	```$ cd Catalog/Catalog```
	- Use the following command to rename the file application.py :
	```$ sudo mv application.py __init__.py```
	- Open the file `__init__.py` by using the command : ```$ sudo nano __init__.py```, and change the line as shown in the picture below:

	![app.run](images/app_run.png)

	Save and close the file.

14. Set it up in your server so that it functions correctly when visiting your server’s IP address in a browser. Make sure that your .git directory is not publicly accessible via a browser!

	In this step, we will create a virtual environment for our flask application.

	If virtualenv is not installed, use pip to install it using following command:

	```$ sudo pip install virtualenv ```

	Give the following command (where venv3 is the name you would like to give your temporary environment):

	```$ sudo virtualenv venv3```

	Now, install Flask in that environment by activating the virtual environment with the following command:

	```$ source venv3/bin/activate ```

	-Install the following dependencies:
	```
	$ sudo pip3 install flask
	$ sudo  pip3 install sqlalchemy
	$ sudo pip3 install passlib
	$ sudo pip3 install oauth2client
	$ sudo pip3 install psycopg2
	```


	- Configure and Enable a New Virtual Host

	Issue the following command in your terminal:
	```$ sudo nano /etc/apache2/sites-available/Catalog.conf ```

	Add the following lines of code to the file to configure the virtual host. Be sure to change the ServerName to your domain or cloud server's IP address:

	```
		<VirtualHost *:80>
			ServerName 142.93.49.78
			ServerAdmin webmaster@localhost
			WSGIScriptAlias / /var/www/Catalog/catalog.wsgi
			<Directory /var/www/Catalog/Catalog/>
				Order allow,deny
				Allow from all
			</Directory>
			Alias /static /var/www/Catalog/Catalog/static
			<Directory /var/www/Catalog/Catalog/static/>
				Order allow,deny
				Allow from all
			</Directory>
			ErrorLog ${APACHE_LOG_DIR}/error.log
			LogLevel warn
			CustomLog ${APACHE_LOG_DIR}/access.log combined
		</VirtualHost>
	```

	Save and close the file.

	Enable the virtual host with the following command:

	```
	$ sudo a2ensite Catalog
	```

	- Create the .wsgi File

	Apache uses the .wsgi file to serve the Flask app. Move to the /var/www/Catalog directory and create a file named catalog.wsgi with following commands:
	```
	$ cd /var/www/Catalog
	$ sudo nano catalog.wsgi 
	```

	Add the following lines of code to the catalog.wsgi file:

```python
	#!/usr/bin/python

	filename = '/var/www/Catalog/Catalog/venv3/bin/activate_this.py'
	exec(compile(open(filename, "rb").read(), filename, 'exec'),  dict(__file__=filename))

	import sys
	import logging

	if sys.version_info[0]<3:
	    raise Exception("Python3 required! Current (wrong) version: '%s'" % sys.version_info)
	logging.basicConfig(stream=sys.stderr)
	sys.path.insert(0,"/var/www/Catalog")

	from Catalog import app as application
	application.secret_key = 'Your secret key'
```

- Restart Apache with the following command to apply the changes:

```$ sudo service apache2 restart```

- Change engine in the files `models.py`, `lotsofCategory.py` and `__init__.py`

```python 
engine = create_engine('postgresql://catalog:YOUR_PASSWOR@localhost/catalog')
```

![change engine](images/change_engine.png)

Use the following command to move the files :
```
$ sudo mv /var/www/Catalog/Catalog/models.py /var/www/Catalog/models.py
$ sudo mv /var/www/Catalog/Catalog/login_with_providers.py /var/www/Catalog/login_with_providers.py
$ sudo mv /var/www/Catalog/Catalog/lotsofCategory.py /var/www/Catalog/lotsofCategory.py
$ sudo mv /var/www/Catalog/Catalog/client_secrets.json /var/www/Catalog/client_secrets.json 
$ sudo mv /var/www/Catalog/Catalog/fb_client_secrets.json /var/www/Catalog/fb_client_secrets.json 
``` 
Run the command and edit the file as shown in the picture:
```
$ sudo nano /var/www/Catalog/login_with_providers.py 
```

![change dir ](images/change_dir_cles.png)

Run the command to setup database and add some cateogy:
```
$ python3 /var/www/Catalog/models.py
$ python3 /var/www/Catalog/lotsofCategory.py
```
if you get this error :

![error](images/psycopg2-binary.png)

Install **psycopg2-binary**

``` 
$ pip3 install psycopg2-binary
```

**Add Client OAuth**

- Follow the steps in [this page](https://developers.google.com/identity/sign-in/web/sign-in) to create OAuth 2.0 client ID in the Google API Console.

Edit the file  **client_secrets.json**
```
$ sudo nano /var/www/Catalog/client_secrets.json
```

```json
{
"web":{
"client_id":"YOUR_CLIENT_ID",
"client_secret":"YOUR_CLIENT_SECRET"
}

```
- Create an application facebook 

[Facebook Login pour le web avec le SDK JavaScript](https://developers.facebook.com/docs/facebook-login/web)

[Quickstart: Facebook SDK for JavaScript](https://developers.facebook.com/docs/javascript/quickstart/)

Edit the file  **fb_client_secrets.json**
```
$ sudo nano /var/www/Catalog/fb_client_secrets.json
```

```json
{
  "web": {
    "app_id": "APP_ID",
    "app_secret": "APP_SECRET"
  }
}

```
- Restart Apache with the following command to apply the changes:

```$ sudo service apache2 restart```


**Resource:**

[How To Deploy a Flask Application on an Ubuntu VPS ](https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps)
