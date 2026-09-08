"""Regression checks for the enterprise readiness findings; no model calls or real corpus."""

import json
from pathlib import Path
import shutil
import unittest

import test_filing as filing_test
from test_filing import ROOT, ACCOUNT1, ACCOUNT2, hashes, read_csv, write_csv
from test_place import KitFixture
from kit_common import safe_folder_name


class ScopedAnalysis(unittest.TestCase):
    def setUp(self):
        self.kit = filing_test.FilingAcceptance()
        self.kit.setUp()
        self.addCleanup(self.kit.doCleanups)
        self.root = self.kit.root
        for doc in ('001', '004'):
            self.kit.save(self.kit.record(doc))
        self.kit.filing('--report')

    def read(self, *docs):
        target = self.root / 'work/cards'
        target.mkdir(exist_ok=True)
        for doc in docs:
            for ext in ('json', 'md'):
                shutil.copyfile(ROOT / 'sample/expected/cards' / f'{doc}.{ext}', target / f'{doc}.{ext}')

    def judge(self, account, docs):
        oracle = ROOT / 'sample/expected/placements'
        target = self.root / 'work/placements'
        target.mkdir(exist_ok=True)
        write_csv(target / f'{account}.csv', [r for r in read_csv(oracle / f'{account}.csv') if r['doc_id'] in docs])
        shutil.copyfile(oracle / f'{account}.md', target / f'{account}.md')

    def test_account_analysis_preserves_other_filing_and_can_continue_account_by_account(self):
        original = hashes(self.root / 'work/files')
        self.read('001')
        self.kit.command('sort.py', '--account', ACCOUNT1, '--force')
        self.judge(ACCOUNT1, ['001'])
        self.kit.command('place.py', '--all', '--visuals')
        other = self.root / 'out/customers' / ACCOUNT2
        listing = read_csv(other / 'documents.csv')
        self.assertEqual(['004'], [r['doc_id'] for r in listing])
        self.assertEqual('filing only', listing[0]['analysis_stage'])
        self.assertEqual('unassessed (filing only)', listing[0]['status'])
        self.assertIn('1 documents are filed here', (other / 'README.md').read_text())
        self.assertFalse((other / 'position.html').exists())
        self.assertEqual((self.root / 'work/files/004.docx').read_bytes(),
                         (other / 'files' / listing[0]['filed_as']).read_bytes())
        global_rows = read_csv(self.root / 'out/customers/CORPUS.csv')
        self.assertEqual(listing, [r for r in global_rows if r['account'] == ACCOUNT2])
        self.assertEqual(10, len({r['doc_id'] for r in global_rows}))
        self.assertIn('analysis incomplete', (self.root / 'out/INDEX.md').read_text())
        self.assertEqual(['001.json'], sorted(p.name for p in (self.root / 'work/cards').glob('*.json')))

        # Completing B must not alter the already judged account A.
        first = self.root / 'out/customers' / ACCOUNT1
        before = hashes(first)
        self.read('004')
        self.kit.command('sort.py', '--account', ACCOUNT2, '--force')
        self.judge(ACCOUNT2, ['004'])
        self.kit.command('place.py', '--all', '--visuals')
        self.assertEqual(before, hashes(first))
        self.assertTrue((other / 'position.html').is_file())
        self.assertEqual(original, hashes(self.root / 'work/files'))

    def test_missing_selected_reading_cannot_change_any_report_or_placement(self):
        before_out = hashes(self.root / 'out')
        before_log = (self.root / 'work/logs/sort.csv').read_bytes()
        self.kit.command('sort.py', '--account', ACCOUNT1, success=False)
        self.assertEqual(before_out, hashes(self.root / 'out'))
        self.assertEqual(before_log, (self.root / 'work/logs/sort.csv').read_bytes())

    def test_global_matching_also_keeps_known_filing_when_some_cards_are_missing(self):
        self.read('001')
        self.kit.command('sort.py', '--force')
        self.kit.command('place.py', '--all', '--visuals')
        rows = read_csv(self.root / 'out/customers/CORPUS.csv')
        self.assertEqual(ACCOUNT2, next(r for r in rows if r['doc_id'] == '004')['account'])

    def test_completing_full_analysis_after_a_scoped_run_retires_cheap_leftovers(self):
        self.read('001')
        self.kit.command('sort.py', '--account', ACCOUNT1)
        self.judge(ACCOUNT1, ['001'])
        self.kit.command('place.py', '--all', '--visuals')
        self.assertTrue((self.root / 'out/customers/_needs-reading').is_dir())
        self.kit.full_cards()
        self.kit.command('sort.py')
        shutil.copytree(ROOT / 'sample/expected/placements', self.root / 'work/placements', dirs_exist_ok=True)
        self.kit.command('place.py', '--all', '--visuals')
        self.assertFalse((self.root / 'out/customers/_needs-reading').exists())
        self.assertEqual(10, len(read_csv(self.root / 'out/customers/CORPUS.csv')))
        self.assertTrue(list((self.root / 'work/history').glob('analysis-transition-*/out')))

    def test_incomplete_card_pair_cannot_start_account_matching(self):
        self.read('001')
        (self.root / 'work/cards/001.md').rename(self.root / 'work/cards/001.pending')
        before = hashes(self.root / 'out')
        self.kit.command('sort.py', '--account', ACCOUNT1, success=False)
        self.assertEqual(before, hashes(self.root / 'out'))


class JudgedOutput(KitFixture):
    def prepare_judgments(self):
        self.command('sort.py')
        for account in (ACCOUNT1, ACCOUNT2):
            self.judge(account, self.sorted_docs(account))

    def test_judge_status_wins_in_csv_full_note_and_diagram(self):
        self.prepare_judgments()
        placement = self.root / 'work/placements' / f'{ACCOUNT1}.csv'
        records = read_csv(placement)
        for row in records:
            if row['doc_id'] == '001':
                row['folder'] = '4-not-live'
        write_csv(placement, records)
        self.command('place.py', '--all', '--visuals')
        row = self.corpus()['001']
        self.assertEqual('not live', row['status'])
        self.assertEqual('live', row['status_per_document'])
        self.assertEqual('judged', row['analysis_stage'])
        folder = self.root / 'out/customers' / ACCOUNT1
        diagram = (folder / 'position.mmd').read_text()
        self.assertIn('not live', diagram)
        self.assertNotIn('not live · live', diagram)
        self.assertEqual(row, next(r for r in read_csv(folder / 'documents.csv') if r['doc_id'] == '001'))

    def test_shared_document_rematch_invalidates_other_judgment_without_spending_on_it(self):
        self.prepare_judgments()
        self.command('place.py', '--all', '--visuals')
        card_path = self.root / 'work/cards/001.json'
        card = json.loads(card_path.read_text())
        card['q2_their_signing_entities'] = ACCOUNT1 + ' | ' + ACCOUNT2
        card_path.write_text(json.dumps(card))
        self.command('sort.py', '--account', ACCOUNT1, '--force')
        self.judge(ACCOUNT1, self.sorted_docs(ACCOUNT1))
        self.command('place.py', '--all', '--visuals')
        folder = self.root / 'out/customers' / ACCOUNT2
        self.assertIn('001', self.sorted_docs(ACCOUNT2))
        self.assertFalse((self.root / 'work/placements' / f'{ACCOUNT2}.csv').exists())
        self.assertFalse((folder / 'position.html').exists())
        self.assertFalse((folder / 'ANALYSIS.md').exists())
        self.assertIn('Analysis is incomplete', (folder / 'README.md').read_text())
        self.assertTrue(all(r['analysis_stage'] == 'read; awaiting judgment' for r in read_csv(folder / 'documents.csv')))
        self.assertTrue(list((self.root / 'work/history/scoped-placements').glob(f'*/{ACCOUNT2}.csv')))

    def test_brief_is_bounded_and_full_qualifications_and_evidence_are_retained(self):
        self.prepare_judgments()
        prose = self.root / 'work/placements' / f'{ACCOUNT1}.md'
        text = '## The position\n' + 'Detailed position. ' * 150 + '\nCritical qualification at the end.\n'
        text += '## Overlaps and conflicts\nExact evidence and unresolved precedence.\n'
        prose.write_text(text)
        self.command('place.py', '--all', '--visuals')
        folder = self.root / 'out/customers' / ACCOUNT1
        brief = (folder / 'README.md').read_text()
        full = (folder / 'ANALYSIS.md').read_text()
        self.assertLess(len(brief.split()), 450)
        self.assertIn('ANALYSIS.md', brief)
        self.assertIn('Critical qualification at the end.', full)
        self.assertIn('Exact evidence and unresolved precedence.', full)
        self.assertIn('Critical qualification at the end.', (folder / 'position.html').read_text())
        self.command('visualise.py', '--all', '--analysis')
        self.assertIn('Critical qualification at the end.', (folder / 'position.html').read_text())

    def test_governing_index_lists_roots_and_keeps_amendment_in_document_list(self):
        self.prepare_judgments()
        placement = self.root / 'work/placements' / f'{ACCOUNT1}.csv'
        records = read_csv(placement)
        for row in records:
            if row['doc_id'] == '002':
                row.update(attaches_to='001', attach_kind='amends')
        write_csv(placement, records)
        self.command('place.py', '--all')
        account = next(r for r in read_csv(self.root / 'out/customers/ACCOUNTS.csv') if r['account'] == ACCOUNT1)
        self.assertIn('doc 001', account['governing_docs'])
        self.assertNotIn('doc 002', account['governing_docs'])
        self.assertEqual('1-governs-trade', self.corpus()['002']['folder'])

    def test_bad_relationship_targets_stop_before_replacing_reports(self):
        self.prepare_judgments()
        self.command('place.py', '--all', '--visuals')
        before = hashes(self.root / 'out')
        placement = self.root / 'work/placements' / f'{ACCOUNT1}.csv'
        original = read_csv(placement)
        for field in ('attaches_to', 'replaces'):
            for bad_target in ('supersedes the earlier framework', '001|002', '999999', original[0]['doc_id']):
                with self.subTest(field=field, target=bad_target):
                    records = [dict(row) for row in original]
                    records[0][field] = bad_target
                    write_csv(placement, records)
                    message = self.command('place.py', '--all', '--visuals', success=False)
                    self.assertIn(field, message)
                    self.assertEqual(before, hashes(self.root / 'out'))

    def test_numeric_relationship_ids_are_normalised_and_rendered(self):
        self.prepare_judgments()
        placement = self.root / 'work/placements' / f'{ACCOUNT1}.csv'
        records = read_csv(placement)
        for row in records:
            if row['doc_id'] == '002':
                row.update(attaches_to='1', attach_kind='amends', replaces='not found')
            if row['doc_id'] == '003':
                row.update(replaces='1')
        write_csv(placement, records)
        self.command('place.py', '--all', '--visuals')
        diagram = (self.root / 'out/customers' / ACCOUNT1 / 'position.mmd').read_text()
        self.assertIn('D002 -- amends --> D001', diagram)
        self.assertIn('D003 -- replaces --> D001', diagram)

    def test_unconfirmed_governance_is_distinct_from_absence_everywhere(self):
        self.prepare_judgments()
        placement = self.root / 'work/placements' / f'{ACCOUNT1}.csv'
        records = read_csv(placement)
        for row in records:
            row.update(folder='unsure', reason='rule 3: current use unconfirmed')
        write_csv(placement, records)
        self.command('place.py', '--all', '--visuals')
        account = next(r for r in read_csv(self.root / 'out/customers/ACCOUNTS.csv') if r['account'] == ACCOUNT1)
        self.assertEqual('', account['governing_docs'])  # This remains a document list.
        self.assertEqual('governing position unconfirmed', account['review_status'])
        for name in ('README.md', 'ANALYSIS.md', 'position.html'):
            self.assertIn('No governing agreement is confirmed',
                          (self.root / 'out/customers' / ACCOUNT1 / name).read_text())
        for name in ('INDEX.md', 'INDEX.html'):
            self.assertIn('not confirmed', (self.root / 'out' / name).read_text())
        self.assertTrue(all(self.corpus()[r['doc_id']]['folder'] == 'unsure' for r in records))
        # Settled non-trade documents alone must not be labelled as unresolved governance.
        for row in records:
            row.update(folder='3-live-not-trade', reason='rule 5: no trade function')
        write_csv(placement, records)
        self.command('place.py', '--all', '--visuals')
        self.assertNotIn('No governing agreement is confirmed',
                         (self.root / 'out/customers' / ACCOUNT1 / 'README.md').read_text())


class NamedStreams(KitFixture):
    depot = ACCOUNT1 + ' Northern Depot'
    erp_accounts = [ACCOUNT1, ACCOUNT2, depot]

    def setUp(self):
        super().setUp()
        mapping = read_csv(self.root / 'inputs/entity-map.csv')
        mapping.append(dict(name_as_printed=self.depot, account=ACCOUNT1, basis='same name',
                            confidence='sure', decided_by='claude', note='stream candidate'))
        write_csv(self.root / 'inputs/entity-map.csv', mapping)
        card_path = self.root / 'work/cards/001.json'
        card = json.loads(card_path.read_text())
        card['q2_their_signing_entities'] = self.depot
        card['q2_their_group_companies'] = 'not found'
        card_path.write_text(json.dumps(card))

    def test_explicit_depot_is_filed_and_judged_in_its_own_folder_in_both_stages(self):
        self.command('filing.py', '--report')
        self.assertEqual(['001'], self.sorted_docs(self.depot))
        accounts = read_csv(self.root / 'out/customers/ACCOUNTS.csv')
        self.assertEqual('', next(r for r in accounts if r['account'] == self.depot)['treated_as_stream_of'])
        self.command('sort.py')
        self.assertEqual(['001'], self.sorted_docs(self.depot))
        self.assertIn(self.depot, self.command('place.py', '--accounts-with-documents'))
        self.judge(self.depot, ['001'])
        self.command('place.py', '--all', '--visuals')
        self.assertTrue((self.root / 'out/customers' / self.depot / 'position.html').is_file())

    def test_user_parent_mapping_wins_over_automatic_named_stream_exception(self):
        path = self.root / 'inputs/entity-map.csv'
        mapping = read_csv(path)
        for row in mapping:
            if row['name_as_printed'] == self.depot:
                row['decided_by'] = 'user'
        write_csv(path, mapping)
        self.command('sort.py')
        self.assertEqual([], self.sorted_docs(self.depot))
        self.assertIn('001', self.sorted_docs(ACCOUNT1))
        self.assertNotIn(self.depot, self.command('place.py', '--accounts-with-documents'))


if __name__ == '__main__':
    unittest.main()
