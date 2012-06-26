from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User # Mostly just to put this into our namespace if we import *
import guardian.shortcuts
import random
    
# Model inheritance seems to work well. A new db table is created for each sub class, and the records are joined
# when selecting them. But they don't appear to inherit Meta info, such as permissions. Subclassing a meta type
# seems to work.

class VehicleMeta:
    permissions = (
            ('can_operate','Can operate this vehicle.'),
        )
        
class Vehicle(models.Model):
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    
    class Meta(VehicleMeta):
        pass
    
    def __repr__(self):
        return "Vehicle(make=\"%s\",model=\"%s\",year=%s)" % (self.make,self.model,self.year)
        
class Motorcycle(Vehicle):
    has_sidecart = models.BooleanField(default=False)
    class Meta(VehicleMeta):
        pass
    
class Bicycle(Vehicle):
    class Meta(VehicleMeta):
        pass
        
class GroupMeta(object):
    # These are the permissions available to all groups
    permissions = (
            ("can_manage", "Can manage this group."),
        )
        
class Group(models.Model):
    name = models.TextField()
    group_id = models.IntegerField()
    # The ForeignKey field handles both directions. From the parent we get a field named "children", because
    # of the related_name, and this gives us a query set. From the child we have a field named parent_group, which
    # gives us None or a single Group instance.
    parent_group = models.ForeignKey('Group',blank=True,null=True,related_name='children')
    
    def has_perm(self, permission, user):
        """
        Check the permissions of this group, and of the parent(s) of this group, until we find 
        the specified permission. If it's not found, the user does not have permission. Permissions
        of the child override those of the parent, but a parent can reset the permissions of a child.
        Args:
            permission: A string. The codename of the permission to check.
            user: A User. The user to check permissions in this group for.
        """
        has = False
        if user.has_perm(permission,self):
            has = True
        elif self.parent_group is not None:
            is_sub_type = False
            # The parent group could be a subclass of group, and since permission lookup is based off of
            # Django ContentTypes, we have to make sure we do the lookup with the right class type.
            parent_as_subtype = self.parent_group.__get_as_subtype__()
            has = parent_as_subtype.has_perm(permission,user)
                
        return has
        
    def set_perm(self, permission, user):
        """
        Set a permission for a user for this group.
        Args:
            permission: A string. The codename of the permission to set.
            user: A User. The user to alter permissions for.
        """
        content_type = ContentType.objects.get_for_model(self)
        try:
            pm = Permission.objects.get(content_type=content_type,codename=permission)
        except ObjectDoesNotExist:
            # This group class doesn't have the specified permission, look through subclasses of Group
            # to see if any of them have that permission. If one does, use the name and codename, but
            # change content type to that of THIS class and save, so that there is now a permission
            # for this class.
            for group_sub_type in Group.__subclasses__():
                try:
                    sub_type_content_type_id = ContentType.objects.get_for_model(group_sub_type).id
                    base_permission = Permission.objects.get(content_type=sub_type_content_type_id,codename=permission)
                    Permission(name=base_permission.name,codename=base_permission.codename,content_type=content_type).save()
                except ObjectDoesNotExist:
                    raise                    
        guardian.shortcuts.assign(permission,user,self)
        
    def remove_perm(self,permission,user):
        """
        Remove the specified permission from this instance and the parent.
        Args:
            permission: A string. The codename of the permission.
            user: A User. THe user to alter permissions for.
        """
        if self.parent_group is not None:
            guardian.shortcuts.remove_perm(permission,user,self.parent_group.__get_as_subtype__())
        guardian.shortcuts.remove_perm(permission,user,self)        
    
    def __get_as_subtype__(self):
        """
        Get this Group instance as the subtype of Group that it was declared as.
        """
        instance = self
        for group_sub_type in Group.__subclasses__():
            try:
                instance = group_sub_type.objects.get(group_id=instance.group_id)
                return instance
            except ObjectDoesNotExist:
                pass
        return instance
    
    class Meta(GroupMeta):
        pass
    
    def save(self):
        if self.id is None:
            self.group_id = random.randint(0,999999)
            
        super(Group,self).save()
        
    def __repr__(self):
       return "<Group: name=\"%s\", group_id=%s, parent_group=%s>" % (self.name,self.group_id,"\"%s\"" % (self.parent_group.name) if self.parent_group else None)
        
class LabGroup(Group):
    class Meta(GroupMeta):
        permissions = (
                ("can_submit_final","Can submit completed test to CTS."),
            )

# One way to inherit permissions is by using a base class for permissions (must be new-style class), 
# and then running through it's subclasses and adding the base permissions to the child permissions            
for group_meta_sub in GroupMeta.__subclasses__():
    group_meta_sub.permissions += GroupMeta.permissions
    
    
        