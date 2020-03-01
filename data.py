# Copyright 2019-2020 Twixes

# This file is part of Somsiad - the Polish Discord bot.

# Somsiad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

# Somsiad is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with Somsiad.
# If not, see <https://www.gnu.org/licenses/>.

from typing import Any, Union, Sequence, Dict
from contextlib import contextmanager
from sqlalchemy import (
    func, create_engine, Column, Boolean, Integer, SmallInteger, BigInteger, String, Date, DateTime, ForeignKey
)
from sqlalchemy.orm import Session as RawSession, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects import postgresql
import discord
from configuration import configuration

engine = create_engine(configuration['database_url'])
Session = sessionmaker(bind=engine)


@contextmanager
def session(*, commit: bool = False):
    _session = Session()
    try:
        yield _session
        if commit: _session.commit()
    except:
        _session.rollback()
        raise
    finally:
        _session.close()


class Base:
    @declared_attr
    def __tablename__(cls):
        class_name = cls.__name__
        class_name_case = tuple(map(lambda char: char.isupper(), class_name))
        table_name_chars = []
        for i, char in enumerate(class_name):
            if class_name_case[i]:
                if i > 0: table_name_chars.append('_')
                table_name_chars.append(char.lower())
            else:
                table_name_chars.append(char)
        table_name_chars.append('s')
        return ''.join(table_name_chars)


Base = declarative_base(cls=Base)


def create_all_tables():
    Base.metadata.create_all(engine)


def insert_or_ignore(
        model: Base, values: Union[Sequence[Dict[str, Any]], Dict[str, Any]], *, session: RawSession = None
):
    use_own_session = session is None
    if use_own_session:
        session = Session()
    dialect_name = str(session.bind.dialect.name)
    if dialect_name == 'postgresql':
        inserter = postgresql.insert(model.__table__).values(values).on_conflict_do_nothing()
    elif dialect_name == 'mysql':
        inserter = model.__table__.insert().prefix_with('IGNORE').values(values)
    elif dialect_name == 'sqlite':
        inserter = model.__table__.insert().prefix_with('OR IGNORE').values(values)
    else:
        raise Exception(
            f'database dialect {dialect_name} is not supported, only postgresql, mysql and sqlite'
        )
    session.execute(inserter)
    session.commit()
    if use_own_session:
        session.close()


class Server(Base):
    COMMAND_PREFIX_MAX_LENGTH = 12

    id = Column(BigInteger, primary_key=True)
    command_prefix = Column(String(COMMAND_PREFIX_MAX_LENGTH))
    joined_at = Column(DateTime, nullable=False)

    @classmethod
    def register(cls, server: Sequence[discord.Guild]):
        values = {'id': server.id, 'joined_at': server.me.joined_at}
        insert_or_ignore(cls, values)

    @classmethod
    def register_all(cls, servers: Sequence[discord.Guild]):
        values = [{'id': server.id, 'joined_at': server.me.joined_at} for server in servers]
        insert_or_ignore(cls, values)
