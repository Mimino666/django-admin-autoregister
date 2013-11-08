from types import ModuleType

from django.contrib import admin
from django.contrib.admin.util import quote
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models import ForeignKey, OneToOneField, Count
from django.db.models.base import ModelBase


def _get_admin_change_url(field):
    '''Return function to generate admin change view url for a related object.

    @param field: field pointing to a related object
    @type field: ForeignKey or OneToOneField
    '''
    related_model = field.related.parent_model

    def f(self, obj):
        link_args = getattr(obj, field.attname)
        if link_args is None:
            return u'(None)'
        # we could use field.name to output __unicode__() of the related object,
        # but that would require to prefetch related objects, which can be slow
        link_text = getattr(obj, field.attname)

        try:
            url = reverse('admin:%s_%s_change' %
                            (related_model._meta.app_label, related_model._meta.module_name),
                          args=[quote(link_args)])
        except NoReverseMatch:
            return link_text
        return u'<a href="%s">%s</a>' % (url, link_text)
    f.allow_tags = True
    f.short_description = field.name
    return f


def _get_admin_changelist_url(field):
    '''Return function to generate admin changlelist view url for the related
    objects.

    @param field: field pointing to the related objects
    @type field: ManyToManyField
    '''

    related_model = field.related.parent_model

    def f(self, obj):
        link_cond = '%s=%s' % (field.related_query_name(), quote(obj.pk))
        link_text = u'%s (%s)' % (field.name.title(), getattr(obj, '%s__count' % field.name))

        try:
            url = reverse('admin:%s_%s_changelist' %
                            (related_model._meta.app_label, related_model._meta.module_name))
        except NoReverseMatch:
            return link_text
        return u'<a href="%s?%s">%s</a>' % (url, link_cond, link_text)
    f.allow_tags = True
    f.short_description = field.name
    return f


def _get_admin_queryset(admin_class, count_field_names):
    '''Return function to generate queryset to efficiently fetch counts()
    of related objects.
    '''

    counts = map(Count, count_field_names)
    def queryset(self, request):
        qs = super(admin_class, self).queryset(request)
        if counts:
            qs = qs.annotate(*counts)
        return qs
    return queryset


def autoregister_admin(module, exclude=None, model_fields=None,
                          admin_fields=None):
    '''
    @param module: module containing django.db.models classes
    @type module: str or __module__
                  If you are providing str, use absolute path.

    @param exclude: list of classes to exclude from auto-register
    @type exclude: iterable of strings or None

    @param model_fields: dictionary of additional fields for list_display
        {'model name': [field1, field2, ...]}
    @type model_fields: dict or None

    @param admin_fields: dictionary of additional admin fields
        {'model name': {name: value, ...}}
    @type admin_fields: dict or None
    '''

    exclude = exclude or []
    model_fields = model_fields or {}
    admin_fields = admin_fields or {}
    if isinstance(module, basestring):
        module = __import__(module, fromlist=[module.split('.')[-1]])
    elif not isinstance(module, ModuleType):
        raise TypeError('invalid type of argument `module`, expected `str` or '
                        '`ModuleType`, got %s.' % type(module))

    # collect the models to register
    models = []
    for model in module.__dict__.values():
        if (isinstance(model, ModelBase) and
                model.__module__ == module.__name__ and
                not model._meta.abstract and
                model.__name__ not in exclude):
            models.append(model)

    # for each model prepare an admin class `<model_name>Admin`
    for model in models:
        admin_class = type('%sAdmin' % model.__name__, (admin.ModelAdmin,), dict())
        # list pk as the first value
        admin_class.list_display = [model._meta.pk.name]
        # list all the other fields
        for field in model._meta.fields:
            if field == model._meta.pk:
                continue

            admin_field_name = field.name
            # create link for related objects
            if isinstance(field, (ForeignKey, OneToOneField)):
                admin_field_name += '_link'
                setattr(admin_class, admin_field_name, _get_admin_change_url(field))

            admin_class.list_display.append(admin_field_name)

        count_field_names = []
        for field in model._meta.many_to_many:
            count_field_names.append(field.name)
            admin_field_name = field.name + '_link'
            setattr(admin_class, admin_field_name, _get_admin_changelist_url(field))
            admin_class.list_display.append(admin_field_name)

        # add custom model fields
        for name in model_fields.get(model.__name__, []):
            admin_class.list_display.append(name)

        # prefetch related fields
        admin_class.queryset = _get_admin_queryset(admin_class, count_field_names)

        # add custom admin fields
        for (name, value) in admin_fields.get(model.__name__, {}).iteritems():
            setattr(admin_class, name, value)

        try:
            admin.site.register(model, admin_class)
        # pass gracefully on duplicate registration errors
        except admin.sites.AlreadyRegistered:
            pass
