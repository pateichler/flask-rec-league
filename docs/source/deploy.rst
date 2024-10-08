Deploying your website
======================

If you want the website to be accessible from the internet, you will need to deploy to a web server with a static address. The hardware requirements for a machine are low end especially if you intend the traffic to be low on your rec league website. Virtual machines offer a quick way to deploy a web application.

Buying a domain name is recommended, but not necessary to run the web application. Custom domain names can be bought at various websites.

Correy Schafer has a great `YouTube video <https://youtu.be/goToXTC96Co>`_ on deploying Flask applications. Make sure to check out his video if anything remains unclear.

.. note::

	For security reasons, it is recommended that you don't run the app on your web server's root user. Also, enable SSH key authentication on your web server instead of password authentication to help increase security.

Setting production mode
-----------------------

Once you have a web server running, transfer the repository files either through git or a file transfer. Once transferred to your server, make sure to set CONFIG_PATH and FLASK_CONFIG_PATH environment variables. Also make sure to install the required Python packages again, preferably in a virtual environment.

The application currently runs in debug mode, which will show debug logs on server errors. This is helpful in development, but in production it is necessary to remove this for security reasons. Debug mode is turned off by setting DEBUG to False in the Flask config file:

.. code-block::
	:caption: Flask config file

	...

	DEBUG = False


Disable firewall
----------------

The app running connected with the internet will need a firewall. Check out setting up a firewall on your web server machine. The following is how to set up a firewall on Ubuntu using `UncomplicatedFirewall (UFW) <https://wiki.ubuntu.com/UncomplicatedFirewall>`_.

Install UFW using apt install:

.. code-block::

	sudo apt install ufw

Configure the firewall to allow SSH, HTTP, and HTTPS traffic by the following commands:

.. code-block::
	:linenos:

	sudo ufw default allow outgoing
	sudo ufw default deny incoming
	sudo ufw allow ssh
	sudo ufw allow http/tcp
	sudo ufw allow https

	sudo ufw enable

.. warning::
	
	If you don't allow SSH (line 3 above), you will be unable to login into to your web server remotely!


Check that all changes to UFW worked by running the command:

.. code-block::

	sudo ufw status

.. admonition:: Quick test

	For a quick test to see if your site working on the internet, open up the port 5000:

	.. code-block::

		sudo ufw allow 5000

	Next, to run the application on your web address (instead of local address 127.0.0.1), we will use the `Flask CLI <https://flask.palletsprojects.com/en/3.0.x/cli/>`_ to set our host name and run the application. The host name ``0.0.0.0`` will open the Flask application to all addresses on the server. Run the following flask CLI command:

	.. code-block::

		flask --app run run --host=0.0.0.0

	Then check the website out at: ``<your_web_server_ip>:5000``, where ``<your_web_server_ip>`` is the static IP address of your running web server. All functionality should work with the application.

	Once finished testing, disable the port on the firewall:

	.. code-block::

		sudo ufw delete allow 5000


Serving the application
-----------------------

The website can be served to the internet in a variety of ways. A straightforward approach would be to run the Flask application with the port of HTTPS, but this would lack in performance compared to other methods.

The approach shown here is using `NGINX <https://nginx.org>`_, `Gunicorn <https://gunicorn.org>`_, and `Supervisor <http://supervisord.org>`_ on Ubuntu to serve the Flask application. 

* **NGINX** is a performant web server that will be used to host our static files and direct all other traffic to Gunicorn.
* **Gunicorn** is the middle man between the NGINX web server and the Flask application. It allows communication between the two and ensures web requests are handled smoothly and efficiently. 
* **Supervisor** is a program that monitors running processes. It will make sure Gunicorn is running, and restart it if it crashes.

NGINX
^^^^^

NGINX can be installed on Ubuntu with apt install:

.. code-block::

	sudo apt install nginx

NGINX will need to be able to access your repository folder (to serve the static files), so ensure NGINX is able to access the repository by the following command on Ubuntu:

.. code-block::
	
	sudo -u www-data namei <path_to_repo>/recLeague/static/

If result shows Permission denied, add the ``www-data`` user to the user that contains the repository (also make sure that user has proper privileges itself):

.. code-block::

	sudo gpasswd -a www-data <your_user>

Next, remove the default NGINX configuration file at ``/etc/nginx/sites-enabled/default`` and create your own configuration file at ``/etc/nginx/sites-enabled/<your_app_name_here>`` with the following information:

.. code-block::

	server{
		listen 80;
		server_name <your_domain_or_ip>;

		# Serve static files through NGINX
		location /static {
			# Set all static files to require authentication
			auth_request /auth;
			alias <path_to_repo>/recLeague/static;

			# Turn off authentication for static files in the public folder
			location /static/public {
				auth_request off;
			}
		}

		# Pass off to Gunicorn for all other routes
		location / {
			proxy_pass http://localhost:8000;
			include /etc/nginx/proxy_params;
			proxy_redirect off;
		}
	}

Where the following variables are:

* **<your_domain_or_ip>**: Use your custom domain name if you have one. Otherwise use the static IP address of the web server.
* **<path_to_repo>**: Path to the root repository folder.

.. note::

	In the configuration, the static route is protected by the ``auth_request`` to prevent outside users gaining access to scorecard pictures.

If you planning to upload scorecard pictures and expect the file size to be large, increase the max file size by adding the following line in ``/etc/nginx/nginx.connf`` in the ``http`` section:

.. code-block::
	
	...

	client_max_body_size <number_of_megabytes>M;

Where <number_of_megabytes> is an integer number of megabytes for the largest accepted file size. Learn more about `client_max_body_size <https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size>`_ on NGINX.

Restart NGINX to apply the changes by running:

.. code-block::

	sudo systemctl restart nginx

Gunicorn
^^^^^^^^

Gunicorn can be installed with pip. Make sure your Python virtual environment is activated.

.. code-block::

	pip install gunicorn


.. admonition:: Quick test
	
	For a quick test to see if NGINX and Gunicorn are working correctly, run the application using Gunicorn in the root folder of the project repository:

	.. code-block::

		gunicorn run:app

	The application should be viewable at your web server static IP address on port ``80``, and all functionality should work.


Supervisor
^^^^^^^^^^

Finally, install Supervisor on Ubuntu with apt install:

.. code-block::

	sudo apt install supervisor

Configure Supervisor to run Gunicorn by adding the following configuration file at ``/etc/supervisor/conf.d/<your_app_name_here>.conf``:

.. code-block::
	
	[program:<your_app_name_here>]
	user=<your_ubuntu_user>
	directory=<path_to_repository_folder>
	command=<path_to_gunicorn_executable> -w <number_of_workers> run:app
	environment=<your_environment_variables>
	
	autostart=true
	autorestart=true
	stopasgroup=true
	killasgroup=true

	stderr_logfile=<your_err_log_path>/app.err.log
	stdout_logfile=<your_out_log_path>/app.out.log


Where the following variables in the configuration file are:

* **<your_app_name_here>**: Choose a name for your program.
* **<your_ubuntu_user>**: User account name on Ubuntu.
* **<path_to_repository_folder>**: Path to the Rec League repository.
* **command**
	* **<path_to_gunicorn_executable>**: Path to the installed Gunicorn executable. Importantly, use the Gunicorn from your virtual environment to ensure the required Python packages.
	* **<number_of_workers>**: Integer number of workers Gunicorn will use to run application. This number should usually be ``2*n + 1``, where ``n`` is the number of cpu cores on your computer. See `Gunicorn's FAQ <https://docs.gunicorn.org/en/latest/design.html#how-many-workers>`_ for more information.
	* Example: 

	.. code-block::

		command=/home/user/flask-rec-league/venv/bin/gunicorn -w 3 run:app

* **<environment>**: Optional list of your environment variables. This can include all environment variables for running the application, otherwise make sure the variables are set either on server boot up or by executing a script in the command using the ``&&`` operator.
	* Example: 
	
	.. code-block::

		environment=FLASK_CONFIG_PATH="<path_to_config>",LEAGUE_CONFIG_PATH="<league_config_path>"

* **<your_err_log_path>**, **<your_out_log_path>**: Optional paths for log files from the application. Make sure the log path exists before running Supervisor. A good place for logs on Ubuntu are in ``/var/log/<your_app_name_here>/<log_file_name>``.

See `Supervisor program configuration <http://supervisord.org/configuration.html#program-x-section-values>`_ for more details.

Restart Supervisor to apply the configuration:

.. code-block::

	sudo supervisorctl reload


Your application should now be running. If you can't view the web application check the application logs or the log from Supervisor.

.. note::

	Anytime you want to apply code or configuration changes to the app, make sure to reload the server by running the command above.

Custom domain name
------------------

If you have a custom domain name for this website, make sure to add the records to the web server static IP address. The records will take a while to update. Check out the website where you purchased the domain name for more information on adding records.

Enabling TLS
------------

It is highly recommended to use TLS with this application to encrypt all web traffic with HTTPS. There are a variety of ways to generate TLS certificates. In this example, we will use a certificate from `Lets Encrypt <https://letsencrypt.org>`_, but you can choose any certificate authority.

Let's Encrypt only allows certificates for domain names, so you must have a custom domain named linked as described in the section before.

We will install the Let's Encrypt certificate by using certbot. certbot is a tool created by Lets Encrypt to install and manage certificates. Refer to `certbot installation <https://certbot.eff.org/instructions>`_ for instructions on installing certbot (choose running on NGINX).

Once certbot is installed, run the certificate generation:

.. code-block::
	
	sudo certbot --nginx

.. note::

	If you run into the problem ``"The requested Nginx plugin does not appear to be installed"``, install the plugin on Ubuntu via ``sudo apt-get install python3-certbot-nginx``. Currently, for some reason the certbot installation page doesn't mention this.

Answer all the prompts. For the prompt on redirecting HTTP traffic, it recommended you choose redirect traffic to ensure all users are using HTTPS. After completion, certbot will automatically update your NGINX configuration file.

Auto-renewal
^^^^^^^^^^^^

The generated TLS certificate will typically expire after a period of time. 

Its recommended to program your web server to automatically renew your certificate before this deadline, so you don't have to do it manually. On Linux, you can program auto-renewal by using `CronTab <https://man7.org/linux/man-pages/man5/crontab.5.html>`_. Add a Cronjob by running:

.. code-block::

	sudo crontab -e

Then in your editor of choice, add a Cronjob to execute the certificate renewal program before it expires. With cerbot, the command is ``sudo certbot renew``. Below is a full example for a Cronjob running cerbot renew on the fifth day of every month at 3 am:

.. code-block::
	:caption: crontab configuration

	0 3 5 * * sudo certbot renew


View your application
---------------------

Your Rec League application is now fully deployed. View your website by either typing in the static IP address into your web browser or using your custom domain name. Test out all features to make sure everything is working correctly.

If you notice any issues with the application, please report on GitHub issues. Continue on to learn about the source code if you are interested in contributing to this project, or if you want to make personal changes to the code.
