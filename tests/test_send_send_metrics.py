from datetime import date, datetime
from pathlib import Path

import pytest
from jinja2 import Template

from juniorguru.models import Job
from juniorguru.send.send_metrics import create_message
from testing_utils import prepare_job_data


class JobMock():
    __names = dir(Job())

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            if name in self.__names:
                setattr(self, name, value)
            else:
                raise AttributeError(f"The Job model doesn't have '{name}'")


@pytest.fixture
def job_mock():
    return JobMock(**prepare_job_data('123'))


@pytest.fixture
def template():
    template_path = Path(__file__).parent.parent / 'juniorguru' / 'send' / 'templates' / 'metrics.html'
    return Template(template_path.read_text())


def test_create_message(job_mock, template):
    job_mock.company_name = 'Honza Ltd.'
    job_mock.effective_approved_at = date(2020, 6, 1)
    job_mock.expires_at = date(2020, 7, 1)
    job_mock.metrics = dict(users=15, pageviews=25, applications=3)

    message = create_message(job_mock, template, today=date(2020, 6, 23))
    html = message.get()['content'][0]['value']
    print(html)

    assert '22&nbsp;dní' in html
    assert 'schválen 1.6.2020' in html
    assert '8&nbsp;dní' in html
    assert 'vyprší 1.7.2020' in html
    assert '<b>15</b>' in html
    assert '<b>25</b>' in html
    assert '&entry.681099058=Honza+Ltd.' in html
