Django admin autoregister
=========================

Problem
-------

Even though Django provides a very easy way to create admin views for your models,
in 90% of situations you only need to display all the fields in the model with links between the related models.
Retyping all the fields for all the models doesn't respect DRY principle.

Solution
--------

One call to *autoregister_admin()* automatically creates and registers admin
for all the models in the specified module with intelligent linking between
ForeignKey, OneToOneField and ManyToManyField fields.

Installation
------------

Because this is just a simple code snippet, it *doesn't* have an app.
Instead copy the snippet to some module in your project. E.g.:

    <your_project>/utils/autoregister.py


Usage
-----

Supposing you have admin app correctly installed
(see [Admin installation](https://docs.djangoproject.com/en/1.6/ref/contrib/admin/#overview)).
In your *admin.py* files add:

```python
from . import models
from your_project.utils.autoregister import autoregister_admin
autoregister_admin(models)
```

And that's it! All the models in the module have admin views successfully created and registered.


If you want to exclude some models and manully create admin for them, use optional *exclude_models* parameter:

```python
autoregister(models, exclude_models=['ModelName1', 'ModelName2'])
```

If you want to display some additional fields for the models (e.g. some properties),
use optional *model_fields* parameter:

```python
autoregister(models, model_fields={'ModelName': ['property_1', 'property_2']})
```

On the other hand, if you want to exclude some field from displaying, use
optional *exclude_fields* parameter:

```python
autoregister(models, exclude_fields={'ModelName': ['exclude_field1', 'exclude_field2']})
```

If you want to do a little modifications to the generated admins (e.g. add search fields),
use optional *admin_fields* parameter:

```python
autoregister(models,
  admin_fields={
    'ModelName': {'search_fields': ['name'], 'list_filter': ['active']}
  }
)
```
