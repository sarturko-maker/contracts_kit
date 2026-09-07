"""Graph correctness at registry, lifecycle and identity boundaries."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import graph
from test_validate_forms import empty_form


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.ctx = {'side': 'customers', 'accounts': ['Invented Group'], 'streams': {},
                    'sort_rows': [{'doc_id': '001', 'account': 'Invented Group'}],
                    'entity_by_name': {}, 'inventory': {'001': {}}}
        self.form = empty_form()
        self.form['B']['B2_document_kind'] = 'master_or_framework'
        self.form['B']['B1_cover_title'] = 'Invented agreement'

    def export(self, forms=None, proposals=None):
        return graph.build_graph(self.ctx, forms or {'001': self.form}, proposals or {})

    def test_unknown_part_dates_and_scope_stay_unknown(self):
        self.form['B']['B9_layered'] = 'yes'
        self.form['F'] = [{'F1_part_name': 'Unknown schedule', 'F3_part_kind': 'other',
                          'F4_D': 'not_found', 'F5_E': 'not_found', 'F1_evidence': None,
                          'F6_internal_precedence': 'not_found'}]
        result = self.export()
        part = next(n for n in result.nodes.values() if n[':LABEL'] == 'component')
        self.assertEqual('provisional', part['status'])
        self.assertNotIn('valid_to', part)

    def test_registry_headers_are_exact_and_no_dangling_edges(self):
        result = self.export()
        self.assertEqual(graph.header('sample-nodes-header.csv'), result.node_columns)
        self.assertEqual(graph.header('sample-edges-header.csv'), result.edge_columns)
        for row in result.nodes.values():
            self.assertTrue(set(row) <= set(result.node_columns))
        for source, target, relation in result.edges:
            self.assertIn(source, result.nodes)
            self.assertIn(target, result.nodes)
            self.assertIn(relation, result.edge_types)
        self.assertTrue(any('source_key' == r['property'] for r in result.node_properties.values()))

    def test_entities_survive_unresolved_and_group_matches_do_not_assert_ownership(self):
        self.form['C']['C1_their_entities'] = [
            {'name_as_printed': 'Invented Subsidiary', 'role': 'signatory', 'page': '1'}]
        self.ctx['entity_by_name']['invented subsidiary'] = {
            'account': 'Invented Group', 'confidence': 'fairly sure', 'basis': 'known group'}
        result = self.export()
        self.assertTrue(any(e[2] == 'party_to' for e in result.edges))
        self.assertFalse(any(e[2] in ('belongs_to', 'owns') for e in result.edges))
        match = next(iter(result.matches.values()))
        self.assertEqual('known group', match['basis'])
        self.assertEqual('fairly sure', match['confidence'])

    def test_invalid_registry_endpoint_is_a_gap_and_audit_row(self):
        self.form['B']['B2_document_kind'] = 'order_or_quote'
        result = self.export()
        self.assertFalse(any(e[2] == 'party_to' for e in result.edges))
        self.assertTrue(any(r['relation'] == 'party_to' and r['exported'] == 'no' for r in result.edge_evidence.values()))
        self.assertTrue(any(e[2] == 'ordered_by' for e in result.edges))

    def test_absent_topics_do_not_invent_clauses(self):
        self.form['I'] = [{'topic': 'freight', 'part': 'not_found', 'page_or_clause': 'not_found',
                           'words': 'not_found', 'reading': 'silent'}]
        result = self.export()
        self.assertFalse(any(n[':LABEL'] == 'clause' for n in result.nodes.values()))
        self.assertTrue(any('silent' in g[1] for g in result.gaps))

    def test_governing_orders_does_not_assert_commercial_completeness(self):
        self.form['G']['G1_governs_orders'] = 'yes'
        result = self.export()
        self.assertNotIn('commercial_completeness', result.nodes['DOC-001'])

    def test_missing_document_link_gets_provisional_endpoint(self):
        self.form['B']['B2_document_kind'] = 'amendment_or_side_letter'
        self.form['H']['H1_attaches_to'] = [{'doc_id': 'not_in_pile', 'as_printed': 'Missing agreement', 'relation': 'amends'}]
        result = self.export()
        target = next(e[1] for e in result.edges if e[2] == 'amends')
        self.assertEqual('provisional', result.nodes[target]['status'])

    def test_cycles_are_rejected(self):
        result = graph.Export()
        result.node('A', 'master', 'A')
        result.node('B', 'master', 'B')
        result.edge('A', 'B', 'supersedes')
        result.edge('B', 'A', 'supersedes')
        with self.assertRaisesRegex(ValueError, 'cycle'):
            result.check_cycles()

    def test_component_cannot_have_two_structural_parents(self):
        result = graph.Export()
        result.node('part', 'component', 'Part')
        for node in ('A', 'B'):
            result.node(node, 'master', node)
            result.edge('part', node, 'forms_part_of')
        with self.assertRaisesRegex(ValueError, 'one structural parent'):
            result.check_cycles()

    def test_stable_ids_and_rows_ignore_form_iteration_order(self):
        second = copy.deepcopy(self.form)
        second['A']['doc_id'] = '002'
        a = self.export({'001': self.form, '002': second})
        b = self.export({'002': second, '001': self.form})
        self.assertEqual(a.nodes, b.nodes)
        self.assertEqual(a.edges, b.edges)

    def test_later_supersession_settles_status_without_changing_old_form(self):
        self.form['D']['D4_status_as_read'] = 'live_rolling_presumed'
        new = copy.deepcopy(self.form)
        new['A']['doc_id'] = '002'
        new['D']['D1_start_date'] = '2026-01-01'
        new['H']['H2_replaces'] = [{'doc_id': '001', 'as_printed': 'Old agreement', 'relation': 'supersedes'}]
        forms = {'001': self.form, '002': new}
        result = graph.build_graph(self.ctx, forms, {}, as_of='2026-09-06')
        self.assertEqual('superseded', result.nodes['DOC-001']['status'])
        self.assertEqual('live_rolling_presumed', self.form['D']['D4_status_as_read'])
        before = graph.build_graph(self.ctx, forms, {}, as_of='2025-12-31')
        self.assertEqual('active', before.nodes['DOC-001']['status'])

    def test_form_gaps_survive_when_document_has_no_node_mapping(self):
        self.form['B']['B2_document_kind'] = 'internal_playbook'
        self.form['K'] = [{'type': 'missing_field', 'description': 'Invented practice limitation', 'page': 'paragraph 1'}]
        self.assertTrue(any(g[1] == 'Invented practice limitation' for g in self.export().gaps))

    def test_none_commitment_is_retained_as_a_value(self):
        result = self.export()
        self.assertEqual('none', result.node_properties[('DOC-001', 'commitment')]['value'])

    def test_health_counts_repeated_unknown_part_answers_separately(self):
        values = list(graph.health_fields({'F': [{'F4_D': 'not_found'}, {'F4_D': 'inherits'}]}))
        self.assertEqual([('F.F4_D', 'not_found'), ('F.F4_D', 'inherits')], values)
        values = list(graph.health_fields({'D': {'D3_ended_evidence': 'none_found', 'D3_evidence': None}}))
        self.assertEqual([('D.D3_ended_evidence', 'none_found')], values)


if __name__ == '__main__':
    unittest.main()
