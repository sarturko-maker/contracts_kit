"""Reruns must not reuse readings of a changed source or escape the account directory."""
import argparse
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import kit_common
import prepare
import sort


class RerunTests(unittest.TestCase):
    def test_unambiguous_customer_or_supplier_account_column_sets_side(self):
        for column, expected in [('customer_account', 'customers'), ('supplier_name', 'suppliers')]:
            self.assertEqual((expected, column), prepare.guess_side([column], [{column: 'Invented account'}]))
        self.assertEqual((None, None), prepare.guess_side(['customer_account', 'supplier_name'], []))
        self.assertEqual((None, None), prepare.guess_side(['customer_account', 'side'], [
            {'side': 'customer'}, {'side': 'supplier'}]))

    def test_portable_folder_names_cannot_escape(self):
        for name in ('..', '.', '../escape', r'..\escape', '/tmp', 'CON', 'NUL.txt', 'x. '):
            with self.subTest(name=name):
                folder = kit_common.safe_folder_name(name)
                self.assertNotIn(folder, ('.', '..', ''))
                self.assertFalse(any(c in folder for c in '/\\'))
                self.assertFalse(folder.endswith((' ', '.')))
        self.assertEqual('Tallowfield Industries', kit_common.safe_folder_name('Tallowfield Industries'))

    def test_changed_source_archives_readings_and_invalidates_judgments(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            for path in ('cards/001.json', 'forms/001.json', 'cards/002.json', 'placements/A.csv', 'trees/A.json', 'logs/sort.csv'):
                target = work / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('old')
            old = {'doc_id': '001', 'sha256': 'a', 'original_path': 'invented.pdf', 'readable': 'yes'}
            with patch.object(prepare, 'WORK', work), patch.object(prepare, 'WORK_LOGS', work / 'logs'):
                prepare.invalidate_changed_sources({'001': old}, [{**old, 'sha256': 'b'}])
            self.assertFalse((work / 'cards/001.json').exists())
            self.assertFalse((work / 'forms/001.json').exists())
            self.assertFalse((work / 'placements/A.csv').exists())
            self.assertFalse((work / 'trees/A.json').exists())
            self.assertFalse((work / 'logs/sort.csv').exists())
            self.assertTrue((work / 'cards/002.json').exists())
            self.assertEqual(5, len([p for p in (work / 'history').rglob('*') if p.is_file()]))

    def test_unchanged_source_keeps_readings(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            old = {'doc_id': '001', 'sha256': 'a', 'original_path': 'same.pdf', 'readable': 'yes'}
            with patch.object(prepare, 'WORK', work):
                prepare.invalidate_changed_sources({'001': old}, [old])
            self.assertFalse((work / 'history').exists())

    def test_known_group_confidence_is_capped(self):
        kind, targets, _ = sort.decide_targets(['Made Up Ltd'], {'made up ltd': {
            'account': 'Invented Group', 'basis': 'known group', 'confidence': 'sure'}},
            {'invented group': 'Invented Group'}, {})
        self.assertEqual('account', kind)
        self.assertEqual('fairly sure', targets[0]['confidence'])

    def test_match_without_basis_needs_decision(self):
        kind, _, undecided = sort.decide_targets(['Made Up Ltd'], {'made up ltd': {
            'account': 'Invented Group', 'basis': '', 'confidence': 'sure'}},
            {'invented group': 'Invented Group'}, {})
        self.assertEqual('_not-sure', kind)
        self.assertEqual(['Made Up Ltd'], undecided)


if __name__ == '__main__':
    unittest.main()
