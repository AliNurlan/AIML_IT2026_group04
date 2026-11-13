import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class ElementIds(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        element_id = dict(attrs).get('id')
        if element_id:
            self.ids.append((tag, element_id))


class WebMarkupTests(unittest.TestCase):
    def test_ids_are_unique_and_download_identifies_button(self):
        parser = ElementIds()
        parser.feed((Path(__file__).resolve().parents[1] / 'web' / 'index.html').read_text(encoding='utf-8'))
        counts = Counter(element_id for _, element_id in parser.ids)
        self.assertEqual({key: count for key, count in counts.items() if count > 1}, {})
        self.assertEqual([tag for tag, element_id in parser.ids if element_id == 'download'], ['button'])


if __name__ == '__main__':
    unittest.main()
