mobileapps-edx-platform-extensions
==================================

mobileapps-edx-platform-extensions (``mobileapps``) 
is a Django application responsible for managing the mobile 
applications. Mobile apps information can be stored and retrieved via 
RESTful APIs which can be consumed by LMS or mobile apps.


Open edX Platform Integration
-----------------------------
1. Update the version of ``mobileapps-edx-platform-extensions`` in the 
appropriate requirements file (e.g. ``requirements/edx/custom.txt``).
2. Add ‘mobileapps’ to the list of installed apps in ``common.py``.
3. Install mobileapps app via requirements file

```sh
  $ pip install -r requirements/edx/custom.txt
```

4. (Optional) Run tests:

```sh
   $ paver test_system -s lms -t mobileapps
```