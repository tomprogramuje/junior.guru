from pathlib import Path

from strictyaml import Datetime, Map, Seq, Str, Url, load

from juniorguru.cli.sync import main as cli
from juniorguru.models.base import db
from juniorguru.models.story import Story


schema = Seq(
    Map({
        'url': Url(),
        'date': Datetime(),
        'title': Str(),
        'image_path': Str(),
        'tags': Seq(Str()),
    })
)


@cli.sync_command()
@db.connection_context()
def main():
    path = Path(__file__).parent.parent / 'data' / 'stories.yml'
    records = [record.data for record in load(path.read_text(), schema)]

    Story.drop_table()
    Story.create_table()

    for record in records:
        Story.create(**record)
