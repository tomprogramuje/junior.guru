from typing import Iterable, Self

from peewee import CharField, IntegerField, TextField, DateField

from juniorguru.models.base import BaseModel, JSONField


class Page(BaseModel):
    src_uri = CharField(unique=True)
    dest_uri = CharField(unique=True)
    meta = JSONField(default=dict)
    size = IntegerField(null=True)
    notes = TextField(null=True)
    date = DateField(null=True)
    thumbnail_path = CharField(null=True)

    @property
    def notes_size(self) -> int:
        return len(self.notes) if self.notes else 0

    @classmethod
    def get_by_src_uri(cls, src_uri) -> Self:
        return cls.get(cls.src_uri == src_uri)

    @classmethod
    def listing(cls) -> Iterable[Self]:
        return cls.select()

    @classmethod
    def handbook_listing(cls) -> Iterable[Self]:
        return cls.select() \
            .where(cls.src_uri.startswith('handbook/')) \
            .order_by(cls.src_uri)

    @classmethod
    def handbook_total_size(cls) -> int:
        return sum([page.size for page in cls.handbook_listing()])

    @classmethod
    def stories_listing(cls) -> Iterable[Self]:
        return cls.select() \
            .where(cls.src_uri.startswith('stories/')) \
            .order_by(cls.date.desc())


class LegacyThumbnail(BaseModel):  # can be deleted once Flask is gone
    url = CharField(index=True, unique=True)
    image_path = CharField()

    @classmethod
    def image_path_by_url(cls, url: str) -> str:
        return cls.get(cls.url == url).image_path
