Flask configuration
===================

In this application, there are Flask extensions that need to be configured for full functionality of Rec Leagues. The Flask application can be configured by using a configuration file.

Create a ``.cfg`` configuration file anywhere on your computer. The name of the configuration file can be anything you want. Once you have created the file, set the environment variable :ref:`FLASK_CONFIG_PATH <FLASK_CONFIG_PATH>` to the path of the newly created file:

.. code-block::
	
	export FLASK_CONFIG_PATH=<your_flask_config_path>


Test the empty configuration file by running the application. If it works, you should see ``Using Flask config at <your_flask_config_path>`` in the logs.


Secret key
----------

The `Flask secret key <https://flask.palletsprojects.com/en/3.0.x/config/#SECRET_KEY>`_ is responsible signing user cookies (used to login users) and for protection against cross-site request forgery (CSRF) with WTForms. This key should be randomly generated to ensure the best security.

Run the following command to generate a strong secret key:

.. code-block:: 
	
	python -c 'import secrets; print(secrets.token_hex(16))'

Once you have generated a secret key, set it in the Flask configuration file:

.. code-block::
	:caption: Flask config file

	SECRET_KEY = '<your_secret_key>'

.. important::
	
	It is important that you keep the secret key secret! Otherwise, your site may be vulnerable to attacks. Avoid publishing the secret key to public repositories.

Mail
----

The `Flask mail <https://flask-mail.readthedocs.io>`_ extension in Rec Leagues allows the ability for users to reset their password through an email link.

The Flask mail extension needs a email account to send the reset password emails. Add the configuration variables to your Flask configuration file:

.. code-block::
	:caption: Flask config file

	MAIL_USERNAME = '<your_mail_username>'
	MAIL_PASSWORD = '<your_mail_password>'
	MAIL_SERVER = '<your_mail_server_name>'

Where the following variables are:

* **<your_mail_username>**: Your email username. It is the name before the ``@`` symbol in your email address.
* **<your_mail_password>**: Your email password. 
	
	.. note::

		Many email servers don't allow using your actual email password. You will most likely need to generate an API password to use instead.

		For Gmail, you can generate an API password by creating an `app password <https://knowledge.workspace.google.com/kb/how-to-create-app-passwords-000009237>`_

* **<your_mail_server_name>**: The SMTP mail server name. For gmail the server name is ``smtp.googlemail.com``.

Example
-------

Here is a full Flask configuration file filled with dummy data:

.. code-block::
	:caption: Example Flask config file

	SECRET_KEY = 'SECRET_KEY'
	
	MAIL_USERNAME = 'test'
	MAIL_PASSWORD = 'password'
	MAIL_SERVER = 'smtp.googlemail.com'