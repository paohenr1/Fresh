"""Exercise the local HTTP interface against the existing Python calculation engine."""

from copy import deepcopy
from datetime import date
from http.client import HTTPConnection
import json
from pathlib import Path
import threading
import unittest

from app import create_server
from inputs import scenario_from_dict
from projection import project
from reporting import summary


class InteractivePlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = json.loads((Path(__file__).parents[1] / 'examples/fictional.json').read_text())
        cls.server = create_server(cls.inputs, 0)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def request(self, data=None, origin=None, path='/api/project', binary=False):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        if data is None:
            connection.request('GET', '/')
        else:
            connection.request('POST', path, json.dumps(data), headers)
        response = connection.getresponse()
        body = response.read()
        if not binary:
            body = body.decode()
        status = response.status
        connection.close()
        return status, body

    def test_initial_page_exposes_editable_rates_and_balances(self):
        status, html = self.request()
        self.assertEqual(status, 200)
        self.assertIn('data-input="client.accounts.RRSP.indexation_percent"', html)
        self.assertIn('data-input="client.accounts.RRSP.balance"', html)
        self.assertIn('id="include-spouse" role="switch"', html)
        self.assertIn('data-input="client.dob" type="date"', html)
        self.assertIn('data-input="client.plan_end" type="date"', html)
        self.assertIn('data-age="client.current_age"', html)
        self.assertIn('class="date-edit"', html)
        self.assertNotIn('id="dollar-basis"', html)
        self.assertLess(html.index('data-pdf="advisor"'), html.index('data-pdf="client"'))

    def test_changed_inputs_and_downloads_match_python(self):
        data = deepcopy(self.inputs)
        data['client']['income'] = 82000
        data['client']['pension_indexation_percent'] = 2.5
        data['spouse']['accounts']['RRSP']['indexation_percent'] = 3.75
        data['retirement_return_percent'] = 0
        status, body = self.request(data)
        self.assertEqual(status, 200)
        result = json.loads(body)
        scenario = scenario_from_dict(data)
        expected = summary(project(scenario, date.fromisoformat(data['as_of'])), scenario)
        self.assertEqual(result['projection']['summary'], expected)
        self.assertEqual(result['projection']['inputs'], data)
        self.assertIn('2026', result['csv'])
        self.assertIn('polygon data-series', result['html'])
        # Stateless requests cannot leak edits from another browser tab.
        _, original = self.request(self.inputs)
        self.assertEqual(json.loads(original)['projection']['inputs'], self.inputs)

    def test_invalid_input_returns_error_without_stale_results(self):
        for bad_value in (-101, None, 'not a rate'):
            with self.subTest(rate=bad_value):
                data = deepcopy(self.inputs)
                data['client']['accounts']['Cash']['indexation_percent'] = bad_value
                status, body = self.request(data)
                self.assertEqual(status, 400)
                self.assertIn('indexation_percent', json.loads(body)['error'])
                self.assertNotIn('projection', json.loads(body))

    def test_spouse_toggle_and_zero_indexation(self):
        data = deepcopy(self.inputs)
        data['spouse'] = None
        for account in data['client']['accounts'].values():
            account['indexation_percent'] = 0
        status, body = self.request(data)
        self.assertEqual(status, 200)
        result = json.loads(body)
        self.assertNotIn('<th scope="col">Spouse age</th>', result['html'])
        self.assertIsNone(result['projection']['inputs']['spouse'])

    def test_other_website_cannot_submit_to_local_calculator(self):
        status, _ = self.request(self.inputs, 'https://example.invalid')
        self.assertEqual(status, 403)

    def test_both_pdf_exports_accept_the_current_scenario(self):
        data = deepcopy(self.inputs)
        data['client']['accounts']['Cash']['balance'] = 87654.32
        for kind in ('client', 'advisor'):
            with self.subTest(kind=kind):
                status, body = self.request(data, path='/api/pdf/' + kind, binary=True)
                self.assertEqual(status, 200)
                self.assertTrue(body.startswith(b'%PDF-'))
                self.assertTrue(body.rstrip().endswith(b'%%EOF'))

    def test_invalid_inputs_cannot_be_exported_as_pdf(self):
        data = deepcopy(self.inputs)
        data['client']['accounts']['Cash']['balance'] = -1
        status, body = self.request(data, path='/api/pdf/advisor')
        self.assertEqual(status, 400)
        self.assertIn('balance', json.loads(body)['error'])


if __name__ == '__main__':
    unittest.main()
