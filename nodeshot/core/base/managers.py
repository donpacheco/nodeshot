import sys

from netfields.managers import NetQuery, NetManager

if not 'synchronize' in sys.argv and not 'celery' in sys.argv:
    from django.contrib.auth import get_user_model
    User = get_user_model()

from django.db.models import Manager, Q
from django.contrib.gis.db.models import GeoManager
from django.db.models.query import QuerySet
from django.contrib.gis.db.models.query import GeoQuerySet
from django.conf import settings

from nodeshot.core.base.choices import ACCESS_LEVELS

HSTORE_ENABLED = settings.NODESHOT['SETTINGS'].get('HSTORE', True)


### ------ MIXINS ------ ###


class PublishedMixin(object):
    """ adds published filter to queryset """
    
    def published(self):
        """ return only published items """
        return self.filter(is_published=True)


class ACLMixin(object):
    """ adds acl filters to queryset """
    
    def access_level_up_to(self, access_level):
        """ returns all items that have an access level equal or lower than the one specified """
        # if access_level is number
        if isinstance(access_level, int):
            value = access_level
        # else if is string get the numeric value
        else:
            value = ACCESS_LEVELS.get(access_level)
        # return queryset
        return self.filter(access_level__lte=value)
    
    def accessible_to(self, user):
        """
        returns all the items that are accessible to the specified user
        if user is not authenticated will return public items
        
        :param user: an user instance or integer representing user id
        """
        # if user param is an integer
        if isinstance(user, int):
            user = User.objects.get(pk=user)
        
        if user.is_superuser:
            try:
                queryset = self.get_query_set()
            except AttributeError:
                queryset = self
        elif user.is_authenticated():
            # get user group (higher id)
            group = user.groups.all().order_by('-id')[0]
            queryset = self.filter(access_level__lte=ACCESS_LEVELS.get(group.name))
        else:
            queryset = self.filter(access_level__lte=ACCESS_LEVELS.get('public'))
        return queryset


class ExtendedManagerMixin(object):
    """ add this mixin to chainable custom methods support to your manager """
    
    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)


### ------ QUERYSETS ------ ###


class PublishedQuerySet(QuerySet, PublishedMixin):
    """ Custom queryset to filter only published items """
    pass


class GeoPublishedQuerySet(GeoQuerySet, PublishedMixin):
    """ PublishedQuerySet with GeoDjango queryset """
    pass


class AccessLevelQuerySet(QuerySet, ACLMixin):
    """ Custom queryset to filter depending on access levels """
    pass


class AccessLevelPublishedQuerySet(QuerySet, ACLMixin, PublishedMixin):
    """ AccessLevelQuerySet and PublishedQuerySet """
    pass


class NetAccessLevelQuerySet(NetQuery, ACLMixin):
    """ Custom queryset to filter depending on access levels + NetQuery """
    pass


class GeoAccessLevelPublishedQuerySet(GeoQuerySet, ACLMixin, PublishedMixin):
    """ AccessLevelQuerySet, PublishedQuerySet with GeoDjango queryset """
    pass


if HSTORE_ENABLED:
    from django_hstore.query import HStoreQuerySet, HStoreGeoQuerySet
    
    class HStoreAccessLevelQuerySet(HStoreQuerySet, ACLMixin):
        """ HStoreQuerySet, PublishedQuerySet with GeoDjango queryset """
        pass
    
    class HStoreGeoAccessLevelPublishedQuerySet(HStoreGeoQuerySet, ACLMixin, PublishedMixin):
        """ HStoreGeoQuerySet, AccessLevelQuerySet, PublishedQuerySet with GeoDjango queryset """
        pass



### ------ MANAGERS ------ ###


class PublishedManager(Manager, ExtendedManagerMixin, PublishedMixin):
    """ Returns published items """
    
    def get_query_set(self): 
        return PublishedQuerySet(self.model, using=self._db)


class GeoPublishedManager(GeoManager, ExtendedManagerMixin, PublishedMixin):
    """ PublishedManager and GeoManager in one """
    
    def get_query_set(self): 
        return GeoPublishedQuerySet(self.model, using=self._db)


#class GeoAccessLevelManager(AccessLevelManager, GeoManager):
#    """ AccessLevelManager and Geodjango manager in one """
#    pass



class AccessLevelManager(Manager, ExtendedManagerMixin, ACLMixin):
    """ Manager to filter depending on access level """

    def get_query_set(self): 
        return AccessLevelQuerySet(self.model, using=self._db)


class NetAccessLevelManager(NetManager, ExtendedManagerMixin, ACLMixin):
    """ NetManager + AccessLevelManager """

    def get_query_set(self): 
        return AccessLevelQuerySet(self.model, using=self._db)


class AccessLevelPublishedManager(Manager, ExtendedManagerMixin, ACLMixin, PublishedMixin):
    """
    AccessLeveManager and Publishedmanager in one
    """
    
    def get_query_set(self): 
        return AccessLevelPublishedQuerySet(self.model, using=self._db)


class GeoAccessLevelPublishedManager(GeoManager, ExtendedManagerMixin, ACLMixin, PublishedMixin):
    """
    GeoManager, AccessLeveManager and Publishedmanager in one
    """
    
    def get_query_set(self): 
        return GeoAccessLevelPublishedQuerySet(self.model, using=self._db)


if HSTORE_ENABLED:
    from django_hstore.managers import HStoreManager, HStoreGeoManager
    
    class HStoreAccessLevelManager(HStoreGeoManager, ExtendedManagerMixin, ACLMixin):
        """
        HStoreManager and AccessLeveManager in one
        """
        
        def get_query_set(self): 
            return HStoreAccessLevelQuerySet(self.model, using=self._db)
    
    class HStoreGeoAccessLevelPublishedManager(HStoreGeoManager, ExtendedManagerMixin, ACLMixin, PublishedMixin):
        """
        HStoreManager, GeoManager, AccessLeveManager and Publishedmanager in one
        """
        
        def get_query_set(self): 
            return HStoreGeoAccessLevelPublishedQuerySet(self.model, using=self._db)