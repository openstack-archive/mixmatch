#   Copyright 2016 Massachusetts Open Cloud
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

from oslo_db.sqlalchemy import enginefacade
from oslo_db.sqlalchemy import models


BASE = declarative_base(cls=models.ModelBase)


class ResourceMapping(BASE):
    """The location of a particular resource."""

    __tablename__ = 'resource_mapping'
    id = sql.Column(sql.Integer, primary_key=True)
    resource_type = sql.Column(sql.String(60), nullable=False)
    resource_id = sql.Column(sql.String(255), nullable=False)
    resource_sp = sql.Column(sql.String(255), nullable=False)
    tenant_id = sql.Column(sql.String(255), nullable=False)

    def __init__(self, resource_type, resource_id, tenant_id, resource_sp):
        self.resource_type = resource_type
        self.resource_id = resource_id.replace("-", "")
        self.tenant_id = tenant_id.replace("-", "")
        self.resource_sp = resource_sp

    def __repr__(self):
        return str((self.resource_type, self.resource_id, self.resource_sp))

    def __eq__(self, other):
        return (self.resource_type == other.resource_type and
                self.resource_id == other.resource_id and
                self.resource_sp == other.resource_sp and
                self.tenant_id == other.tenant_id)

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def find(cls, resource_type, resource_id):
        context = enginefacade.transaction_context()
        with enginefacade.reader.using(context) as session:
            mapping = session.query(ResourceMapping).filter_by(
                resource_type=resource_type,
                resource_id=resource_id.replace("-", "")
            ).first()
        return mapping


def insert(entity):
    context = enginefacade.transaction_context()
    with enginefacade.writer.using(context) as session:
        session.add(entity)


def delete(entity):
    context = enginefacade.transaction_context()
    with enginefacade.writer.using(context) as session:
        session.delete(entity)


def create_tables():
    BASE.metadata.create_all(enginefacade.get_legacy_facade().get_engine())
