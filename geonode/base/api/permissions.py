# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2020 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from rest_framework import permissions
from django.conf import settings
from rest_framework.filters import BaseFilterBackend


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class ResourceBasePermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    shortcut_kwargs = {
        'accept_global_perms': True,
    }

    def filter_queryset(self, request, queryset, view):
        # We want to defer this import until runtime, rather than import-time.
        # See https://github.com/encode/django-rest-framework/issues/4608
        # (Also see #1624 for why we need to make this import explicitly)
        from guardian.shortcuts import get_objects_for_user
        from geonode.security.utils import get_visible_resources

        user = request.user
        # perm_format = '%(app_label)s.view_%(model_name)s'
        # permission = self.perm_format % {
        #     'app_label': queryset.model._meta.app_label,
        #     'model_name': queryset.model._meta.model_name,
        # }

        resources = get_objects_for_user(
            user,
            'base.view_resourcebase',
            **self.shortcut_kwargs
        )

        obj_with_perms = get_visible_resources(
            resources,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)

        return queryset.filter(id__in=obj_with_perms.values('id'))
