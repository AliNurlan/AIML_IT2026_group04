import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from generator import GeneratedSite, validate_site
from server import Handler

VALID_HTML = '<!doctype html><html><head><title>Demo</title></head><body><h1>Hello</h1><script>const x = 1;</script></body></html>'


class ValidationTests(unittest.TestCase):
    def test_self_contained_document_passes_structure_checks(self):
        checks = {item['name']: item for item in validate_site(VALID_HTML)}
        self.assertEqual(checks['HTML document']['status'], 'passed')
        self.assertEqual(checks['Page title']['status'], 'passed')
        self.assertEqual(checks['Self-contained assets']['status'], 'passed')

    def test_missing_document_and_external_scripts_are_reported(self):
        checks = {item['name']: item for item in validate_site('<script src="https://example.com/x.js"></script>')}
        self.assertEqual(checks['HTML document']['status'], 'failed')
        self.assertEqual(checks['Self-contained assets']['status'], 'failed')

    def test_javascript_syntax_is_checked_without_execution(self):
        checks = {item['name']: item for item in validate_site('<script>const broken = ;</script>')}
        self.assertIn(checks['JavaScript syntax']['status'], {'failed', 'skipped'})

    def test_empty_html_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_site('')


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, body, origin=None):
        req = Request(self.origin + path, data=json.dumps(body).encode(), method='POST', headers={
            'Content-Type': 'application/json', 'Origin': origin or self.origin,
        })
        return urlopen(req, timeout=3)

    def test_generation_passes_request_to_provider_and_returns_checks(self):
        with patch('server.generate_site', return_value=GeneratedSite(title='Demo', html=VALID_HTML)) as generate:
            with self.post('/api/generate', {'prompt': 'Build a small portfolio', 'model': 'gemini-test'}) as response:
                result = json.load(response)
        generate.assert_called_once_with('Build a small portfolio', 'gemini-test')
        self.assertEqual(result['html'], VALID_HTML)
        self.assertTrue(result['tests'])

    def test_cross_origin_request_is_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.post('/api/validate', {'html': VALID_HTML}, origin='https://untrusted.example')
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_missing_prompt_is_rejected_without_provider_call(self):
        with patch('server.generate_site') as generate:
            with self.assertRaises(HTTPError) as error:
                self.post('/api/generate', {'prompt': 'short', 'model': 'gemini-test'})
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        generate.assert_not_called()


if __name__ == '__main__':
    unittest.main()
